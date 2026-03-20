"""Exchange system API routes for reward management and redemptions."""

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser
from app.core.database import get_db
from app.schemas.exchange import (
    PinnedRewardResponse,
    RedemptionResponse,
    RewardCreateRequest,
    RewardListResponse,
    RewardResponse,
    RewardUpdateRequest,
    RedeemRequest,
    TimerSessionResponse,
)
from app.services.child_profile_service import ChildProfileService
from app.services.exchange_service import (
    ActiveTimerError,
    ExchangeService,
    InsufficientPointsError,
    InvalidTimerStateError,
    OutOfStockError,
)
from app.models.exchange import (
    Redemption,
    Reward,
    RewardType,
    TimerSession,
    TimerSessionStatus,
)
from app.services.point_service import PointService


router = APIRouter()


# ==================
# Dependencies
# ==================


def get_child_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChildProfileService:
    """Get child profile service instance."""
    return ChildProfileService(db)


def get_point_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> PointService:
    """Get point service instance."""
    return PointService(db)


def get_exchange_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    point_service: Annotated[PointService, Depends(get_point_service)],
) -> ExchangeService:
    """Get exchange service instance."""
    return ExchangeService(db, point_service)


# ==================
# Reward Management (Parent)
# ==================


@router.post("/", response_model=RewardResponse, status_code=status.HTTP_201_CREATED)
async def create_reward(
    reward_data: RewardCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> RewardResponse:
    """Create a new reward."""
    # Verify user has children (family context)
    children = await child_service.list_profiles(current_user.id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No children found. Create a child profile first.",
        )
    family_id = children[0].parent_id
    reward = await exchange_service.create_reward(
        family_id=family_id,
        name=reward_data.name,
        description=reward_data.description,
        image_url=reward_data.image_url,
        type=reward_data.type,
        cost=reward_data.cost,
        duration_minutes=reward_data.duration_minutes,
        stock=reward_data.stock,
        enabled=reward_data.enabled,
    )
    return RewardResponse.model_validate(reward)


@router.get("/", response_model=RewardListResponse)
async def list_rewards(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
    enabled_only: bool = Query(True),
    reward_type: RewardType | None = Query(None),
) -> RewardListResponse:
    """List all rewards for a family."""
    children = await child_service.list_profiles(current_user.id)
    if not children:
        return RewardListResponse(rewards=[], total=0, enabled_count=0, disabled_count=0)
    family_id = children[0].parent_id
    rewards = await exchange_service.get_rewards_by_family(
        family_id=family_id,
        enabled_only=enabled_only,
    )
    if reward_type:
        rewards = [r for r in rewards if r.type == reward_type]
    return RewardListResponse(
        rewards=[RewardResponse.model_validate(r) for r in rewards],
        total=len(rewards),
        enabled_count=sum(1 for r in rewards if r.enabled),
        disabled_count=sum(1 for r in rewards if not r.enabled),
    )


@router.get("/{reward_id}", response_model=RewardResponse)
async def get_reward(
    reward_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> RewardResponse:
    """Get a specific reward by ID."""
    reward = await exchange_service.get_reward(reward_id)
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    # Verify family owns this reward
    children = await child_service.list_profiles(current_user.id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    family_id = children[0].parent_id
    if reward.family_id != family_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    return RewardResponse.model_validate(reward)


@router.put("/{reward_id}", response_model=RewardResponse)
async def update_reward(
    reward_id: UUID,
    reward_data: RewardUpdateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> RewardResponse:
    """Update a reward."""
    reward = await exchange_service.get_reward(reward_id)
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    # Verify family owns this reward
    children = await child_service.list_profiles(current_user.id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    family_id = children[0].parent_id
    if reward.family_id != family_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    updated_reward = await exchange_service.update_reward(
        reward_id,
        name=reward_data.name,
        description=reward_data.description,
        image_url=reward_data.image_url,
        type=reward_data.type,
        cost=reward_data.cost,
        duration_minutes=reward_data.duration_minutes,
        stock=reward_data.stock,
        enabled=reward_data.enabled,
    )
    return RewardResponse.model_validate(updated_reward)


@router.patch("/{reward_id}/toggle", response_model=RewardResponse)
async def toggle_reward(
    reward_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
    enabled: bool = Query(...),
) -> RewardResponse:
    """Enable or disable a reward."""
    reward = await exchange_service.get_reward(reward_id)
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    # Verify family owns this reward
    children = await child_service.list_profiles(current_user.id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    family_id = children[0].parent_id
    if reward.family_id != family_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    updated_reward = await exchange_service.toggle_reward(reward_id, enabled)
    return RewardResponse.model_validate(updated_reward)


@router.delete("/{reward_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reward(
    reward_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> None:
    """Delete a reward."""
    reward = await exchange_service.get_reward(reward_id)
    if not reward:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    # Verify family owns this reward
    children = await child_service.list_profiles(current_user.id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    family_id = children[0].parent_id
    if reward.family_id != family_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )
    await exchange_service.delete_reward(reward_id)


# ==================
# Redemption (Child)
# ==================


@router.post("/{reward_id}/redeem", response_model=RedemptionResponse)
async def redeem_reward(
    reward_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> RedemptionResponse:
    """Redeem a reward for points."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    try:
        redemption = await exchange_service.redeem_reward(
            child_id=child_id,
            reward_id=reward_id,
        )
    except OutOfStockError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except InsufficientPointsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ActiveTimerError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Build response
    timer_session_data = None
    if redemption.timer_session_id:
        timer = await exchange_service.get_timer_session(redemption.timer_session_id)
        if timer:
            timer_session_data = TimerSessionResponse.model_validate(timer)

    return RedemptionResponse(
        id=redemption.id,
        child_id=redemption.child_id,
        reward=RewardResponse.model_validate(redemption.reward),
        points_spent=redemption.points_spent,
        type=redemption.type,
        status=redemption.status,
        redeemed_at=redemption.redeemed_at,
        timer_session_id=redemption.timer_session_id,
        completed_at=redemption.completed_at,
        notes=redemption.notes,
    )


@router.get("/redemptions", response_model=list[RedemptionResponse])
async def get_redemption_history(
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
    page: int = Query(1, ge=1, le=100),
    page_size: int = Query(20, ge=1, le=100),
) -> list[RedemptionResponse]:
    """Get redemption history for a child."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    redemptions, total = await exchange_service.get_redemption_history(
        child_id=child_id,
        page=page,
        page_size=page_size,
    )
    return [
        RedemptionResponse.model_validate(r) for r in redemptions
    ]


# ==================
# Timer Management
# ==================


@router.get("/timers/active", response_model=TimerSessionResponse | None)
async def get_active_timer(
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> TimerSessionResponse | None:
    """Get active timer for a child."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    timer = await exchange_service.get_active_timer(child_id)
    if not timer:
        return None
    return TimerSessionResponse.model_validate(timer)


@router.post("/timers/{timer_id}/pause", response_model=TimerSessionResponse)
async def pause_timer(
    timer_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> TimerSessionResponse:
    """Pause a running timer."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    try:
        timer = await exchange_service.pause_timer(timer_id, child_id)
    except InvalidTimerStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return TimerSessionResponse.model_validate(timer)


@router.post("/timers/{timer_id}/resume", response_model=TimerSessionResponse)
async def resume_timer(
    timer_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> TimerSessionResponse:
    """Resume a paused timer."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    try:
        timer = await exchange_service.resume_timer(timer_id, child_id)
    except InvalidTimerStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return TimerSessionResponse.model_validate(timer)


@router.post("/timers/{timer_id}/complete", response_model=TimerSessionResponse)
async def complete_timer(
    timer_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> TimerSessionResponse:
    """Complete a timer session."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    try:
        timer = await exchange_service.complete_timer(timer_id, child_id)
    except InvalidTimerStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return TimerSessionResponse.model_validate(timer)


# ==================
# Pinned Rewards
# ==================


@router.post("/{reward_id}/pin", response_model=PinnedRewardResponse)
async def pin_reward(
    reward_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> PinnedRewardResponse:
    """Pin a reward for goal tracking."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    pinned = await exchange_service.pin_reward(child_id, reward_id)
    return PinnedRewardResponse.model_validate(pinned)


@router.delete("/pin", status_code=status.HTTP_204_NO_CONTENT)
async def unpin_reward(
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    exchange_service: Annotated[ExchangeService, Depends(get_exchange_service)],
) -> None:
    """Remove pinned reward for child's goal."""
    # Verify child belongs to current user
    child = await child_service.get_profile(child_id, current_user.id)
    await exchange_service.unpin_reward(child_id)
