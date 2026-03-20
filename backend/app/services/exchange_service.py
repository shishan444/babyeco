"""Exchange system service for managing rewards, redemptions, and timer sessions."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exchange import (
    PinnedReward,
    Redemption,
    RedemptionStatus,
    Reward,
    RewardType,
    TimerSession,
    TimerSessionStatus,
)
from app.services.point_service import PointService

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.user import User


class OutOfStockError(Exception):
    """Raised when reward is out of stock."""

    def __init__(self, reward_id: UUID, stock: int = 0):
        self.reward_id = reward_id
        self.stock = stock
        super().__init__(f"Reward {reward_id} is out of stock. Available: {stock}")


class InsufficientPointsError(Exception):
    """Raised when child doesn't have enough points."""

    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"Insufficient points. Required: {required}, Available: {available}")


class ActiveTimerError(Exception):
    """Raised when child already has an active timer."""

    def __init__(self, child_id: UUID):
        self.child_id = child_id
        super().__init__(f"Child {child_id} already has an active timer session")


class InvalidTimerStateError(Exception):
    """Raised when timer operation is invalid for current state."""

    def __init__(self, message: str):
        super().__init__(message)


class ExchangeService:
    """Service for managing rewards, redemptions, and timer sessions.

    @MX:ANCHOR
    Core exchange service handling reward lifecycle.
    Manages redemptions, timer sessions, and point transactions.
    """

    def __init__(self, db: AsyncSession, point_service: PointService):
        self.db = db
        self._point_service = point_service

    # ==================
    # Reward Management
    # ==================

    async def create_reward(
        self,
        family_id: UUID,
        name: str,
        description: str | None = None,
        image_url: str | None = None,
        type: RewardType = RewardType.ONE_TIME,
        cost: int = 10,
        duration_minutes: int | None = None,
        stock: int | None = None,
        enabled: bool = True,
    ) -> Reward:
        """Create a new reward.

        @MX:NOTE
        Validates reward type constraints before creation.
        """
        if type == RewardType.TIMER and duration_minutes is None:
            raise ValueError("duration_minutes required for timer rewards")

        if type == RewardType.QUANTITY and stock is None:
            raise ValueError("stock required for quantity rewards")

        reward = Reward(
            family_id=family_id,
            name=name,
            description=description,
            image_url=image_url,
            type=type,
            cost=cost,
            duration_minutes=duration_minutes,
            stock=stock,
            initial_stock=stock,
            enabled=enabled,
        )
        self.db.add(reward)
        await self.db.flush()
        await self.db.refresh(reward)
        return reward

    async def get_rewards_by_family(
        self, family_id: UUID, enabled_only: bool = True
    ) -> list[Reward]:
        """Get all rewards for a family."""
        query = select(Reward).where(Reward.family_id == family_id)

        if enabled_only:
            query = query.where(Reward.enabled == True)

        query = query.order_by(Reward.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_reward(self, reward_id: UUID) -> Reward | None:
        """Get a single reward by ID."""
        result = await self.db.execute(
            select(Reward).where(Reward.id == reward_id)
        )
        return result.scalar_one_or_none()

    async def update_reward(
        self,
        reward_id: UUID,
        name: str | None = None,
        description: str | None = None,
        image_url: str | None = None,
        type: RewardType | None = None,
        cost: int | None = None,
        duration_minutes: int | None = None,
        stock: int | None = None,
        enabled: bool | None = None,
    ) -> Reward:
        """Update a reward."""
        reward = await self.get_reward(reward_id)
        if not reward:
            raise ValueError(f"Reward {reward_id} not found")

        if name is not None:
            reward.name = name
        if description is not None:
            reward.description = description
        if image_url is not None:
            reward.image_url = image_url
        if type is not None:
            reward.type = type
        if cost is not None:
            reward.cost = cost
        if duration_minutes is not None:
            reward.duration_minutes = duration_minutes
        if stock is not None:
            reward.stock = stock
        if enabled is not None:
            reward.enabled = enabled

        await self.db.flush()
        await self.db.refresh(reward)
        return reward

    async def toggle_reward(self, reward_id: UUID, enabled: bool) -> Reward:
        """Toggle reward enabled status."""
        return await self.update_reward(reward_id, enabled=enabled)

    async def delete_reward(self, reward_id: UUID) -> None:
        """Delete a reward."""
        reward = await self.get_reward(reward_id)
        if reward:
            await self.db.delete(reward)
            await self.db.flush()

    # ==================
    # Redemption
    # ==================

    async def redeem_reward(
        self,
        child_id: UUID,
        reward_id: UUID,
    ) -> Redemption:
        """Redeem a reward for a child.

        @MX:NOTE
        Handles point deduction, stock management, and timer session creation.
        """
        # Get reward
        reward = await self.get_reward(reward_id)
        if not reward:
            raise ValueError(f"Reward {reward_id} not found")

        if not reward.enabled:
            raise ValueError("Reward is not available")

        # Check stock for quantity type
        if reward.type == RewardType.QUANTITY:
            if reward.stock is None or reward.stock < 1:
                raise OutOfStockError(reward_id, reward.stock or 0)
            reward.stock -= 1

        # Deduct points
        await self._point_service.spend(
            child_id=child_id,
            amount=reward.cost,
            source_type="redemption",
            source_id=reward_id,
            description=f"Redeemed: {reward.name}",
        )

        # Create redemption
        redemption = Redemption(
            child_id=child_id,
            reward_id=reward.id,
            points_spent=reward.cost,
            type=reward.type,
            status=RedemptionStatus.COMPLETED,
            redeemed_at=datetime.now(timezone.utc),
        )

        if reward.type == RewardType.TIMER:
            redemption.status = RedemptionStatus.ACTIVE
            # Create timer session
            duration_seconds = (reward.duration_minutes or 30) * 60
            timer_session = TimerSession(
                child_id=child_id,
                redemption_id=redemption.id,
                reward_id=reward.id,
                duration_seconds=duration_seconds,
                remaining_seconds=duration_seconds,
                started_at=datetime.now(timezone.utc),
                status=TimerSessionStatus.RUNNING,
            )
            self.db.add(timer_session)
            await self.db.flush()
            redemption.timer_session_id = timer_session.id

        self.db.add(redemption)
        await self.db.flush()
        await self.db.refresh(redemption)
        return redemption

    async def get_redemption_history(
        self,
        child_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Redemption], int]:
        """Get redemption history for a child."""
        # Count query
        count_result = await self.db.execute(
            select(func.count(Redemption.id)).where(Redemption.child_id == child_id)
        )
        total = count_result.scalar_one()

        # Data query
        query = (
            select(Redemption)
            .where(Redemption.child_id == child_id)
            .order_by(Redemption.redeemed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    # ==================
    # Timer Management
    # ==================

    async def get_active_timer(self, child_id: UUID) -> TimerSession | None:
        """Get active timer session for child."""
        result = await self.db.execute(
            select(TimerSession)
            .where(TimerSession.child_id == child_id)
            .where(
                TimerSession.status.in_([
                    TimerSessionStatus.RUNNING,
                    TimerSessionStatus.PAUSED,
                ])
            )
            .order_by(TimerSession.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def pause_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Pause a running timer."""
        timer = await self._get_timer(timer_id, child_id)
        if timer.status != TimerSessionStatus.RUNNING:
            raise InvalidTimerStateError(
                f"Timer is not running. Current status: {timer.status}"
            )
        timer.status = TimerSessionStatus.PAUSED
        timer.paused_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(timer)
        return timer

    async def resume_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Resume a paused timer."""
        timer = await self._get_timer(timer_id, child_id)
        if timer.status != TimerSessionStatus.PAUSED:
            raise InvalidTimerStateError(
                f"Timer is not paused. Current status: {timer.status}"
            )
        timer.status = TimerSessionStatus.RUNNING
        timer.resumed_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(timer)
        return timer

    async def complete_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Complete a timer session."""
        timer = await self._get_timer(timer_id, child_id)
        if timer.status not in (
            TimerSessionStatus.RUNNING,
            TimerSessionStatus.PAUSED,
        ):
            raise InvalidTimerStateError(
                f"Timer cannot be completed. Current status: {timer.status}"
            )
        timer.status = TimerSessionStatus.COMPLETED
        timer.completed_at = datetime.now(timezone.utc)
        timer.remaining_seconds = 0

        # Update redemption status
        if timer.redemption_id:
            result = await self.db.execute(
                select(Redemption).where(Redemption.id == timer.redemption_id)
            )
            redemption = result.scalar_one_or_none()
            if redemption:
                redemption.status = RedemptionStatus.COMPLETED

        await self.db.flush()
        await self.db.refresh(timer)
        return timer

    async def _get_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Get timer session with validation."""
        result = await self.db.execute(
            select(TimerSession)
            .where(TimerSession.id == timer_id)
            .where(TimerSession.child_id == child_id)
        )
        timer = result.scalar_one_or_none()
        if not timer:
            raise ValueError(f"Timer {timer_id} not found for child {child_id}")
        return timer

    # ==================
    # Pinned Rewards
    # ==================

    async def pin_reward(self, child_id: UUID, reward_id: UUID) -> PinnedReward:
        """Pin a reward for child's goal tracking."""
        # Check if already pinned
        result = await self.db.execute(
            select(PinnedReward).where(PinnedReward.child_id == child_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            # Update existing pin
            existing.reward_id = reward_id
            existing.pinned_at = datetime.now(timezone.utc)
            await self.db.flush()
            await self.db.refresh(existing)
            return existing

        pinned = PinnedReward(
            child_id=child_id,
            reward_id=reward_id,
            pinned_at=datetime.now(timezone.utc),
        )
        self.db.add(pinned)
        await self.db.flush()
        await self.db.refresh(pinned)
        return pinned

    async def unpin_reward(self, child_id: UUID) -> None:
        """Remove pinned reward for child."""
        result = await self.db.execute(
            select(PinnedReward).where(PinnedReward.child_id == child_id)
        )
        pinned = result.scalar_one_or_none()
        if pinned:
            await self.db.delete(pinned)
            await self.db.flush()

    async def get_pinned_reward(self, child_id: UUID) -> PinnedReward | None:
        """Get pinned reward for child."""
        result = await self.db.execute(
            select(PinnedReward)
            .where(PinnedReward.child_id == child_id)
            .options(selectinload(PinnedReward.reward))
        )
        return result.scalar_one_or_none()
