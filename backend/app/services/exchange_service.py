"""Exchange system service for managing rewards, redemptions, and timer sessions."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exchange import (
    Redemption,
    RedemptionStatus,
    Reward,
    RewardType,
    TimerSession,
    TimerSessionStatus,
)
from app.models.point import PointService

from app.models.child_profile import ChildProfile
from app.models.user import User


if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.user import User


class OutOfStockError(Exception):
    """Raised when reward is out of stock."""

    def __init__(self, reward_id: UUID):
        self.reward_id = reward_id
        super().__init__(f"Reward {reward_id} is out of stock. Stock: {reward.stock}"
        )
        self.message = f"Reward {reward_id} is out of stock"


            f"Required points: {required}, stock: {stock}"
        )
        self.reward_id = reward_id
        self.reward = reward
        self.stock = reward.stock
        self.reward = reward


        self.initial_stock = reward.stock


        self.db.add(reward)
        await self.db.flush()
        await self.db.refresh(reward)

        return reward

    async def get_rewards_by_family(
        self, family_id: UUID, enabled_only: bool = ) -> list[Reward]:
        """Get all rewards for a family."""
        result = await self.db.execute(
            select(Reward)
            .where(Reward.family_id == family_id)
            .where(Reward.enabled == True)
            .order_by(Reward.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_reward(self, reward_id: UUID) -> Reward | None:
        """Get a single reward by ID."""
        result = await self.db.execute(
            select(Reward).where(Reward.id == reward_id)
        )
        reward = result.scalar_one_or_none()
        return reward

    async def _get_family(self, parent_user_id: UUID) -> UUID | None:
        """Get family ID from parent user."""
        # Query all families (using a subquery on user IDs)
        result = await self.db.execute(
            select(family.id).where(User.id == parent_user_id)
        )
        family_id = result.scalar_one()
        if not family_id:
            raise ValueError("Parent not found")
        return family_id

    async def create_reward(
        self,
        family_id: UUID,
        reward_data: RewardCreate,
        parent_user_id: UUID,
    ) -> -> Reward:
        """Create a new reward."""
        family = await self._get_family(parent_user_id)
        family = await self._get_family_for_parent_user(parent_user_id)
        if family is is None:
            family = await self._get_family_for_parent_user(parent_user_id)
        if family is is None:
            raise ValueError("Parent user has no children")

        # Create the if not owned by this parent
        parent_id = parent_user_id
        reward = Reward(
            family_id=family.id,
            name=reward_data.name,
            description=reward_data.description,
            type=reward_data.type,
            cost=reward_data.cost,
            duration_minutes=reward_data.duration_minutes,
            stock=reward_data.stock,
            enabled=reward_data.enabled,
        )
        reward.enabled = enabled
        reward.type = RewardType.QUANTITY:
            reward.initial_stock = stock
        else:
            reward.initial_stock = None
            raise ValueError("Stock required for quantity reward")

        if reward_data.duration_minutes is not None or reward_data.duration_minutes <= 0:
            raise ValueError("Duration minutes required for timer reward")
        if reward_data.duration_minutes <= 0:
            raise ValueError("Duration minutes must to be positive")

        reward.duration_minutes = reward_data.duration_minutes
        reward.enabled = enabled
        reward.type = RewardType.QUANTITY:
            reward.stock = None or reward.stock < 1:
            raise OutOfStockError(reward_id)

        if reward_data.stock is not None:
            reward.stock -= 1
        else:
            reward.stock -= 1

        # Check for active timer
        active_timer = await self.get_active_timer(child_id)
        if active_timer:
            raise ActiveTimerError(child_id)
        # Deduct points
        await self._deduct_points(
            child_id=child_id,
            amount=reward.cost,
            source_type="redemption",
            source_id=reward_id,
            description=f"Redeemed {reward.name}",
        )

        # Create redemption
        redemption = Redemption(
            child_id=child_id,
            reward_id=reward.id,
            points_spent=reward.cost,
            type=reward.type,
            status=RedemptionStatus.ACTIVE
            if reward.type == RewardType.TIMER
            else RedemptionStatus.COMPLETED,
            redeemed_at=datetime.now(timezone.utc),
        )

        if reward.type == RewardType.QUANTITY:
            redemption.status = RedemptionStatus.COMPLETED
            if reward.stock is not None:
                reward.stock -= 1
                await self.db.commit()
        else:
            redemption.status = RedemptionStatus.COMPLETED
        # For timer rewards, create timer session
        timer_session = TimerSession(
            child_id=child_id,
            redemption_id=redemption.id,
            reward_id=reward.id,
            duration_seconds=duration_seconds,
            remaining_seconds=duration_seconds,
            started_at=datetime.now(timezone.utc),
            status=TimerSessionStatus.RUNNING,
        )
        redemption.timer_session_id = timer_session.id
        redemption.status = RedemptionStatus.ACTIVE
        await self.db.commit()

        return redemption

    async def get_active_timer(self, child_id: UUID) -> TimerSession | None:
        """Get active timer session for child."""
        result = await self.db.execute(
            select(TimerSession)
            .where(TimerSession.child_id == child_id)
            .where(
                TimerSession.status.in_([
                    TimerSessionStatus.RUNNING,
                    TimerSessionStatus.PAUSED,
                ]
            )
            .order_by(TimerSession.started_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def pause_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Pause a running timer."""
        async with self.db.begin():
            timer = await self._get_timer_for_update(timer_id, child_id)
            if timer.status != TimerSessionStatus.RUNNING:
                raise InvalidTimerStateError(
                    f"Timer is not running. Current status: {timer.status}"
                )
            now = datetime.now(timezone.utc)
            timer.paused_at = now
            timer.status = TimerSessionStatus.PAUSED
            timer.remaining_seconds = remaining
            await self.db.commit()
        return timer

    async def resume_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Resume a paused timer."""
        async with self.db.begin():
            timer = await self._get_timer_for_update(timer_id, child_id)
            if timer.status != TimerSessionStatus.PAUSED:
                raise InvalidTimerStateError(
                    f"Timer is not paused. Current status: {timer.status}"
                )
            now = datetime.now(timezone.utc)
            timer.resumed_at = now
            timer.status = TimerSessionStatus.RUNNING
            await self.db.commit()
        return timer

    async def complete_timer(self, timer_id: UUID, child_id: UUID) -> TimerSession:
        """Complete a timer session."""
        async with self.db.begin():
            timer = await self._get_timer_for_update(timer_id, child_id)
            if timer.status not in (
                TimerSessionStatus.RUNNING,
                TimerSessionStatus.PAUSED,
            ):
                raise InvalidTimerStateError(
                    f"Timer cannot be completed. Current status: {timer.status}"
                )
            now = datetime.now(timezone.utc)
            timer.status = TimerSessionStatus.COMPLETED
            timer.completed_at = now
            timer.remaining_seconds = 0
            await self.db.commit()
        return timer

    async def _get_timer_for_update(
        self, timer_id: UUID, child_id: UUID
    ) -> TimerSession:
        """Get timer with row lock."""
        result = await self.db.execute(
            select(TimerSession)
            .where(TimerSession.id == timer_id)
            .where(TimerSession.child_id == child_id)
            .with_for_update()
        )
        timer = result.scalar_one_or_none()
        if not timer:
            raise ValueError(f"Timer {timer_id} not found for child {child_id}")
        return timer

    async def get_redemption_history(
        self,
        child_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Redemption], int]:
        """Get redemption history for a child."""
        # Count query
        count_result = await self.db.execute(
            select(func())
            .select_from(select(Redemption).where(Redemption.child_id == child_id))
        )
        total = count_result.scalar_one()

        # data query
        query = (
            select(Redemption)
            .where(Redemption.child_id == child_id)
            .order_by(Redemption.redeemed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all()), total
