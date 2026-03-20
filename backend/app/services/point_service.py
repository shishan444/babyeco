"""Point system service for managing balances and transactions."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.point import PointBalance, PointFreeze, PointTransaction

if TYPE_CHECKING:
    pass


class InsufficientPointsError(Exception):
    """Raised when child has insufficient points."""

    def __init__(self, available: int, required: int):
        self.available = available
        self.required = required
        super().__init__(
            f"Insufficient points. Available: {available}, Required: {required}"
        )


        self.message = f"Insufficient points. Available: {available}, Required: {required}"


class FrozenPointsError(Exception):
    """Raised when trying to spend frozen points."""

    pass


class PointService:
    """Service for point balance and transaction management.

    @MX:ANCHOR
    Central service for all point operations.
    Handles earning, spending, freezing, and adjustments.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_balance(self, child_id: UUID) -> PointBalance:
        """Get point balance for a child."""
        result = await self.db.execute(
            select(PointBalance).where(PointBalance.child_id == child_id)
        )
        return result.scalar_one_or_none()

    async def _get_or_create_balance(self, child_id: UUID) -> PointBalance:
        """Get existing balance or create new one."""
        balance = await self.get_balance(child_id)

        if not balance:
            balance = PointBalance(
                child_id=child_id,
                balance=0,
                frozen=0,
                total_earned=0,
                total_spent=0,
            )
            self.db.add(balance)
            await self.db.flush()

        return balance

    async def earn(
        self,
        child_id: UUID,
        amount: int,
        source_type: str,
        source_id: UUID | None = None,
        description: str | None = None,
    ) -> PointTransaction:
        """Add points to child's balance."""
        # Use existing transaction context from FastAPI
        balance = await self._get_or_create_balance(child_id)

        # Update balance
        balance.balance += amount
        balance.total_earned += amount
        balance.updated_at = datetime.now(UTC)

        # Create transaction record
        transaction = PointTransaction(
            child_id=child_id,
            type="earn",
            amount=amount,
            balance_after=balance.balance,
            source_type=source_type,
            source_id=source_id,
            description=description,
        )
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)

        return transaction

    async def spend(
        self,
        child_id: UUID,
        amount: int,
        source_type: str,
        source_id: UUID | None = None,
        description: str | None = None,
    ) -> PointTransaction:
        """Spend points from child's balance."""
        # Use existing transaction context from FastAPI
        balance = await self._get_or_create_balance(child_id)

        # Check available balance
        available = balance.balance - balance.frozen
        if available < amount:
            raise InsufficientPointsError(available, amount)

        # Update balance
        balance.balance -= amount
        balance.total_spent += amount
        balance.updated_at = datetime.now(UTC)

        # Create transaction record
        transaction = PointTransaction(
            child_id=child_id,
            type="spend",
            amount=-amount,
            balance_after=balance.balance,
            source_type=source_type,
            source_id=source_id,
            description=description,
        )
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)

        return transaction

    async def freeze(
        self,
        child_id: UUID,
        amount: int,
        source_type: str,
        source_id: UUID | None = None,
    ) -> PointFreeze:
        """Freeze points for a pending reward."""
        # Use existing transaction context from FastAPI
        balance = await self._get_or_create_balance(child_id)

        # Check available balance
        available = balance.balance - balance.frozen
        if available < amount:
            raise InsufficientPointsError(available, amount)

        # Update frozen amount
        balance.frozen += amount
        balance.updated_at = datetime.now(UTC)

        # Create freeze record
        freeze = PointFreeze(
            child_id=child_id,
            amount=amount,
            source_type=source_type,
            source_id=source_id,
        )
        self.db.add(freeze)
        await self.db.flush()
        await self.db.refresh(freeze)

        # Create freeze transaction
        transaction = PointTransaction(
            child_id=child_id,
            type="freeze",
            amount=-amount,
            balance_after=balance.balance,
            source_type=source_type,
            source_id=source_id,
        )
        self.db.add(transaction)
        await self.db.flush()

        return freeze

    async def unfreeze(
        self,
        child_id: UUID,
        freeze_id: UUID,
    ) -> PointTransaction:
        """Unfreeze previously frozen points."""
        # Use existing transaction context from FastAPI
        # Get freeze record
        result = await self.db.execute(
            select(PointFreeze).where(
                PointFreeze.id == freeze_id,
                PointFreeze.child_id == child_id,
                PointFreeze.status == "active",
            )
        )
        freeze = result.scalar_one_or_none()

        if not freeze:
            raise ValueError("Freeze record not found or not active")

        # Get balance
        balance = await self._get_or_create_balance(child_id)

        # Update frozen amount
        balance.frozen -= freeze.amount
        balance.updated_at = datetime.now(UTC)

        # Mark freeze as released
        freeze.status = "released"
        freeze.released_at = datetime.now(UTC)

        # Create unfreeze transaction
        transaction = PointTransaction(
            child_id=child_id,
            type="unfreeze",
            amount=freeze.amount,
            balance_after=balance.balance,
            source_type="freeze_release",
            source_id=freeze_id,
        )
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)

        return transaction

    async def adjust(
        self,
        child_id: UUID,
        amount: int,
        reason: str,
    ) -> PointTransaction:
        """Manually adjust child's balance (parent action)."""
        # Use existing transaction - no nested begin needed
        balance = await self._get_or_create_balance(child_id)

        # Update balance
        balance.balance += amount
        if amount > 0:
            balance.total_earned += amount
        else:
            balance.total_spent += abs(amount)
        balance.updated_at = datetime.now(UTC)

        # Create adjustment transaction
        transaction = PointTransaction(
            child_id=child_id,
            type="adjust",
            amount=amount,
            balance_after=balance.balance,
            source_type="manual_adjustment",
            description=reason,
        )
        self.db.add(transaction)
        await self.db.flush()
        await self.db.refresh(transaction)

        return transaction

    async def get_transaction_history(
        self,
        child_id: UUID,
        transaction_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PointTransaction], int]:
        """Get paginated transaction history for a child."""
        query = select(PointTransaction).where(
            PointTransaction.child_id == child_id
        )

        if transaction_type:
            query = query.where(PointTransaction.type == transaction_type)

        if start_date:
            query = query.where(PointTransaction.created_at >= start_date)

        if end_date:
            query = query.where(PointTransaction.created_at <= end_date)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Get paginated results
        query = query.order_by(PointTransaction.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        transactions = list(result.scalars().all())

        return transactions, total
