"""TDD tests for PointService - SPEC-BE-POINT-001.

These tests verify all acceptance criteria from the SPEC document.
Tests follow RED-GREEN-REFACTOR cycle.
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point import PointBalance, PointFreeze, PointTransaction
from app.services.point_service import InsufficientPointsError, PointService


class TestPointServiceBalance:
    """Test balance management - UR-001, UR-003."""

    @pytest.mark.asyncio
    async def test_get_balance_creates_initial_balance(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting balance for new child creates zero balance."""
        child_id = uuid4()
        service = PointService(db_session)

        balance = await service.get_balance(child_id)

        assert balance is None  # No balance exists yet

    @pytest.mark.asyncio
    async def test_get_or_create_balance_creates_if_not_exists(
        self, db_session: AsyncSession
    ) -> None:
        """Test _get_or_create_balance creates balance when none exists."""
        child_id = uuid4()
        service = PointService(db_session)

        balance = await service._get_or_create_balance(child_id)

        assert balance is not None
        assert balance.child_id == child_id
        assert balance.balance == 0
        assert balance.frozen == 0
        assert balance.total_earned == 0
        assert balance.total_spent == 0

    @pytest.mark.asyncio
    async def test_get_or_create_balance_returns_existing(
        self, db_session: AsyncSession
    ) -> None:
        """Test _get_or_create_balance returns existing balance."""
        child_id = uuid4()
        service = PointService(db_session)

        # Create initial balance
        balance1 = await service._get_or_create_balance(child_id)
        await db_session.commit()

        # Get same balance
        balance2 = await service._get_or_create_balance(child_id)

        assert balance1.id == balance2.id
        assert balance1.child_id == balance2.child_id


class TestPointServiceEarn:
    """Test earning points - EDR-001, UR-001."""

    @pytest.mark.asyncio
    async def test_earn_increases_balance(
        self, db_session: AsyncSession
    ) -> None:
        """Test earning points increases balance correctly."""
        child_id = uuid4()
        service = PointService(db_session)

        transaction = await service.earn(
            child_id=child_id,
            amount=100,
            source_type="task_completion",
            source_id=uuid4(),
            description="Completed morning routine",
        )
        await db_session.commit()

        # Verify transaction
        assert transaction.type == "earn"
        assert transaction.amount == 100
        assert transaction.balance_after == 100
        assert transaction.source_type == "task_completion"

        # Verify balance
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 100
        assert balance.total_earned == 100
        assert balance.total_spent == 0
        assert balance.frozen == 0

    @pytest.mark.asyncio
    async def test_earn_multiple_transactions_accumulate(
        self, db_session: AsyncSession
    ) -> None:
        """Test multiple earn transactions accumulate correctly."""
        child_id = uuid4()
        service = PointService(db_session)

        await service.earn(child_id, amount=50, source_type="task")
        await service.earn(child_id, amount=30, source_type="task")
        await service.earn(child_id, amount=20, source_type="task")
        await db_session.commit()

        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 100
        assert balance.total_earned == 100

    @pytest.mark.asyncio
    async def test_earn_creates_transaction_record(
        self, db_session: AsyncSession
    ) -> None:
        """Test earn creates complete transaction audit trail - UR-002."""
        child_id = uuid4()
        source_id = uuid4()
        service = PointService(db_session)

        transaction = await service.earn(
            child_id=child_id,
            amount=100,
            source_type="check_in",
            source_id=source_id,
            description="Task completion",
        )
        await db_session.commit()

        assert transaction.child_id == child_id
        assert transaction.type == "earn"
        assert transaction.amount == 100
        assert transaction.balance_after == 100
        assert transaction.source_type == "check_in"
        assert transaction.source_id == source_id
        assert transaction.description == "Task completion"
        assert transaction.created_at is not None


class TestPointServiceSpend:
    """Test spending points - EDR-002, UR-003."""

    @pytest.mark.asyncio
    async def test_spend_decreases_balance(
        self, db_session: AsyncSession
    ) -> None:
        """Test spending points decreases balance correctly."""
        child_id = uuid4()
        service = PointService(db_session)

        # Earn points first
        await service.earn(child_id, amount=100, source_type="test")

        # Spend points
        transaction = await service.spend(
            child_id=child_id,
            amount=30,
            source_type="exchange",
            source_id=uuid4(),
            description="Reward redemption",
        )
        await db_session.commit()

        # Verify transaction
        assert transaction.type == "spend"
        assert transaction.amount == -30
        assert transaction.balance_after == 70

        # Verify balance
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 70
        assert balance.total_earned == 100
        assert balance.total_spent == 30

    @pytest.mark.asyncio
    async def test_spend_with_insufficient_balance_fails(
        self, db_session: AsyncSession
    ) -> None:
        """Test spending more than available balance fails - UR-003."""
        child_id = uuid4()
        service = PointService(db_session)

        # Earn only 50 points
        await service.earn(child_id, amount=50, source_type="test")

        # Try to spend 100 points
        with pytest.raises(InsufficientPointsError) as exc_info:
            await service.spend(
                child_id=child_id,
                amount=100,
                source_type="exchange",
            )

        assert exc_info.value.available == 50
        assert exc_info.value.required == 100

    @pytest.mark.asyncio
    async def test_spend_cannot_exceed_available_balance(
        self, db_session: AsyncSession
    ) -> None:
        """Test spend checks available balance - UR-003."""
        child_id = uuid4()
        service = PointService(db_session)

        # Earn 100 points
        await service.earn(child_id, amount=100, source_type="test")

        # Freeze 30 points
        await service.freeze(
            child_id=child_id,
            amount=30,
            source_type="pending_exchange",
        )

        # Available is 70, try to spend 80
        with pytest.raises(InsufficientPointsError) as exc_info:
            await service.spend(
                child_id=child_id,
                amount=80,
                source_type="exchange",
            )

        assert exc_info.value.available == 70
        assert exc_info.value.required == 80


class TestPointServiceFreeze:
    """Test freezing points - EDR-003, SDR-001."""

    @pytest.mark.asyncio
    async def test_freeze_reserves_points(
        self, db_session: AsyncSession
    ) -> None:
        """Test freezing points reserves them from spending."""
        child_id = uuid4()
        service = PointService(db_session)

        # Earn points
        await service.earn(child_id, amount=100, source_type="test")

        # Freeze some points
        freeze = await service.freeze(
            child_id=child_id,
            amount=30,
            source_type="pending_exchange",
            source_id=uuid4(),
        )
        await db_session.commit()

        # Verify freeze record
        assert freeze.child_id == child_id
        assert freeze.amount == 30
        assert freeze.status == "active"

        # Verify balance
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 100  # Balance unchanged
        assert balance.frozen == 30  # Frozen amount increased
        assert balance.available == 70  # Available decreased

    @pytest.mark.asyncio
    async def test_freeze_creates_transaction(
        self, db_session: AsyncSession
    ) -> None:
        """Test freeze creates transaction record."""
        child_id = uuid4()
        service = PointService(db_session)

        await service.earn(child_id, amount=100, source_type="test")

        # Verify freeze transaction was created
        result = await db_session.execute(
            select(PointTransaction).where(
                PointTransaction.child_id == child_id,
                PointTransaction.type == "freeze",
            )
        )
        freeze_tx = result.scalar_one_or_none()

        # Freeze points
        await service.freeze(
            child_id=child_id,
            amount=30,
            source_type="pending_exchange",
        )
        await db_session.commit()

        # Check freeze transaction
        result = await db_session.execute(
            select(PointTransaction).where(
                PointTransaction.child_id == child_id,
                PointTransaction.type == "freeze",
            )
        )
        freeze_tx = result.scalar_one()

        assert freeze_tx.type == "freeze"
        assert freeze_tx.amount == -30

    @pytest.mark.asyncio
    async def test_freeze_with_insufficient_balance_fails(
        self, db_session: AsyncSession
    ) -> None:
        """Test freezing more than available fails."""
        child_id = uuid4()
        service = PointService(db_session)

        # Only 100 points
        await service.earn(child_id, amount=100, source_type="test")

        # Freeze 30 (leaving 70 available)
        await service.freeze(
            child_id=child_id,
            amount=30,
            source_type="pending",
        )

        # Try to freeze 80 more (only 70 available)
        with pytest.raises(InsufficientPointsError):
            await service.freeze(
                child_id=child_id,
                amount=80,
                source_type="pending",
            )


class TestPointServiceUnfreeze:
    """Test unfreezing points - EDR-003."""

    @pytest.mark.asyncio
    async def test_unfreeze_releases_points(
        self, db_session: AsyncSession
    ) -> None:
        """Test unfreezing points makes them available again."""
        child_id = uuid4()
        service = PointService(db_session)

        # Setup: earn and freeze
        await service.earn(child_id, amount=100, source_type="test")
        freeze = await service.freeze(
            child_id=child_id,
            amount=30,
            source_type="pending_exchange",
        )
        await db_session.commit()

        # Unfreeze
        await service.unfreeze(child_id=child_id, freeze_id=freeze.id)
        await db_session.commit()

        # Verify freeze status
        result = await db_session.execute(
            select(PointFreeze).where(PointFreeze.id == freeze.id)
        )
        updated_freeze = result.scalar_one()
        assert updated_freeze.status == "released"
        assert updated_freeze.released_at is not None

        # Verify balance
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 100  # Unchanged
        assert balance.frozen == 0  # Released back
        assert balance.available == 100  # All available

    @pytest.mark.asyncio
    async def test_unfreeze_creates_transaction(
        self, db_session: AsyncSession
    ) -> None:
        """Test unfreeze creates transaction record."""
        child_id = uuid4()
        service = PointService(db_session)

        # Setup
        await service.earn(child_id, amount=100, source_type="test")
        freeze = await service.freeze(
            child_id=child_id,
            amount=30,
            source_type="pending",
        )

        # Unfreeze
        transaction = await service.unfreeze(
            child_id=child_id,
            freeze_id=freeze.id,
        )
        await db_session.commit()

        # Verify unfreeze transaction
        assert transaction.type == "unfreeze"
        assert transaction.amount == 30  # Positive amount
        assert transaction.source_type == "freeze_release"
        assert transaction.source_id == freeze.id

    @pytest.mark.asyncio
    async def test_unfreeze_nonexistent_freeze_fails(
        self, db_session: AsyncSession
    ) -> None:
        """Test unfreezing non-existent freeze fails."""
        child_id = uuid4()
        service = PointService(db_session)

        with pytest.raises(ValueError, match="Freeze record not found"):
            await service.unfreeze(
                child_id=child_id,
                freeze_id=uuid4(),
            )


class TestPointServiceAdjust:
    """Test manual adjustments - EDR-004."""

    @pytest.mark.asyncio
    async def test_adjust_increase_adds_points(
        self, db_session: AsyncSession
    ) -> None:
        """Test positive adjustment adds points."""
        child_id = uuid4()
        service = PointService(db_session)

        transaction = await service.adjust(
            child_id=child_id,
            amount=50,
            reason="Parent bonus for good behavior",
        )
        await db_session.commit()

        # Verify transaction
        assert transaction.type == "adjust"
        assert transaction.amount == 50
        assert transaction.description == "Parent bonus for good behavior"
        assert transaction.source_type == "manual_adjustment"

        # Verify balance
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 50
        assert balance.total_earned == 50

    @pytest.mark.asyncio
    async def test_adjust_decrease_removes_points(
        self, db_session: AsyncSession
    ) -> None:
        """Test negative adjustment removes points."""
        child_id = uuid4()
        service = PointService(db_session)

        # Setup
        await service.earn(child_id, amount=100, source_type="test")

        # Adjust down
        transaction = await service.adjust(
            child_id=child_id,
            amount=-30,
            reason="Correction for error",
        )
        await db_session.commit()

        # Verify transaction
        assert transaction.amount == -30

        # Verify balance
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == 70
        assert balance.total_spent == 30  # Negative adjustments count as spent

    @pytest.mark.asyncio
    async def test_adjust_allows_negative_balance(
        self, db_session: AsyncSession
    ) -> None:
        """Test manual adjustment can go negative (parent override)."""
        child_id = uuid4()
        service = PointService(db_session)

        # Adjust negative without any points
        transaction = await service.adjust(
            child_id=child_id,
            amount=-50,
            reason="Penalty for bad behavior",
        )
        await db_session.commit()

        # Verify balance went negative
        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.balance == -50


class TestPointServiceTransactionHistory:
    """Test transaction history - SDR-002, UR-002."""

    @pytest.mark.asyncio
    async def test_get_transaction_history_returns_all(
        self, db_session: AsyncSession
    ) -> None:
        """Test getting transaction history returns all transactions."""
        child_id = uuid4()
        service = PointService(db_session)

        # Create transactions
        await service.earn(child_id, amount=100, source_type="task")
        await service.spend(child_id, amount=30, source_type="exchange")
        await service.earn(child_id, amount=50, source_type="task")
        await db_session.commit()

        # Get history
        transactions, total = await service.get_transaction_history(
            child_id=child_id,
        )

        assert total == 3
        assert len(transactions) == 3
        # Most recent first
        assert transactions[0].amount == 50
        assert transactions[1].amount == -30
        assert transactions[2].amount == 100

    @pytest.mark.asyncio
    async def test_get_transaction_history_with_type_filter(
        self, db_session: AsyncSession
    ) -> None:
        """Test filtering by transaction type."""
        child_id = uuid4()
        service = PointService(db_session)

        # Create different transaction types
        await service.earn(child_id, amount=100, source_type="task")
        await service.spend(child_id, amount=30, source_type="exchange")
        await service.earn(child_id, amount=50, source_type="task")
        await db_session.commit()

        # Filter by type
        transactions, total = await service.get_transaction_history(
            child_id=child_id,
            transaction_type="earn",
        )

        assert total == 2
        assert all(t.type == "earn" for t in transactions)

    @pytest.mark.asyncio
    async def test_get_transaction_history_with_date_range(
        self, db_session: AsyncSession
    ) -> None:
        """Test filtering by date range."""
        child_id = uuid4()
        service = PointService(db_session)

        # Create transactions at different times
        now = datetime.now(UTC)
        await service.earn(child_id, amount=100, source_type="task")

        # Wait a tiny bit to ensure different timestamp
        await service.spend(child_id, amount=30, source_type="exchange")
        await db_session.commit()

        # Get all transactions
        all_transactions, total_all = await service.get_transaction_history(
            child_id=child_id,
        )
        assert total_all == 2

    @pytest.mark.asyncio
    async def test_get_transaction_history_pagination(
        self, db_session: AsyncSession
    ) -> None:
        """Test pagination works correctly - SDR-002."""
        child_id = uuid4()
        service = PointService(db_session)

        # Create 25 transactions
        for i in range(25):
            await service.earn(child_id, amount=10, source_type=f"task_{i}")
        await db_session.commit()

        # Get first page
        page1, total = await service.get_transaction_history(
            child_id=child_id,
            page=1,
            page_size=10,
        )
        assert total == 25
        assert len(page1) == 10

        # Get second page
        page2, _ = await service.get_transaction_history(
            child_id=child_id,
            page=2,
            page_size=10,
        )
        assert len(page2) == 10

        # Get third page (partial)
        page3, _ = await service.get_transaction_history(
            child_id=child_id,
            page=3,
            page_size=10,
        )
        assert len(page3) == 5

        # Verify order (most recent first)
        assert page1[0].created_at >= page1[-1].created_at

    @pytest.mark.asyncio
    async def test_get_transaction_history_empty_for_new_child(
        self, db_session: AsyncSession
    ) -> None:
        """Test transaction history is empty for child with no transactions."""
        child_id = uuid4()
        service = PointService(db_session)

        transactions, total = await service.get_transaction_history(
            child_id=child_id,
        )

        assert total == 0
        assert transactions == []


class TestPointServiceBalanceConsistency:
    """Test balance consistency - UBR-001."""

    @pytest.mark.asyncio
    async def test_balance_equals_sum_of_transactions(
        self, db_session: AsyncSession
    ) -> None:
        """Test balance equals sum of all transaction amounts - UBR-001."""
        child_id = uuid4()
        service = PointService(db_session)

        # Create various transactions
        await service.earn(child_id, amount=100, source_type="task")
        await service.earn(child_id, amount=50, source_type="task")
        await service.spend(child_id, amount=30, source_type="exchange")
        await service.earn(child_id, amount=20, source_type="bonus")
        await service.spend(child_id, amount=40, source_type="exchange")
        await db_session.commit()

        # Get balance
        balance = await service.get_balance(child_id)
        assert balance is not None

        # Sum transactions: 100 + 50 - 30 + 20 - 40 = 100
        transactions, _ = await service.get_transaction_history(
            child_id=child_id,
        )
        transaction_sum = sum(t.amount for t in transactions)

        assert balance.balance == transaction_sum
        assert balance.balance == 100

    @pytest.mark.asyncio
    async def test_total_earned_matches_earn_transactions(
        self, db_session: AsyncSession
    ) -> None:
        """Test total_earned matches sum of earn transactions."""
        child_id = uuid4()
        service = PointService(db_session)

        await service.earn(child_id, amount=100, source_type="task")
        await service.earn(child_id, amount=50, source_type="task")
        await service.spend(child_id, amount=30, source_type="exchange")
        await db_session.commit()

        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.total_earned == 150

    @pytest.mark.asyncio
    async def test_total_spent_matches_spend_transactions(
        self, db_session: AsyncSession
    ) -> None:
        """Test total_spent matches sum of spend transactions."""
        child_id = uuid4()
        service = PointService(db_session)

        await service.earn(child_id, amount=100, source_type="task")
        await service.spend(child_id, amount=30, source_type="exchange")
        await service.spend(child_id, amount=20, source_type="exchange")
        await db_session.commit()

        balance = await service.get_balance(child_id)
        assert balance is not None
        assert balance.total_spent == 50


# Import select for queries
from sqlalchemy import select
