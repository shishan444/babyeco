"""Point management API routes."""

from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser
from app.core.database import get_db
from app.repositories.child_profile_repository import ChildProfileRepository
from app.schemas.point import (
    EarnRequest,
    PointBalanceResponse,
    SpendRequest,
    TransactionListResponse,
    TransactionResponse,
    TransactionType,
)
from app.services.child_profile_service import ChildProfileService
from app.services.point_service import (
    InsufficientPointsError,
    PointService,
)

 from app.models.point import PointTransaction


router = APIRouter()


@router.get("/child/{child_id}/balance", response_model=PointBalanceResponse)
async def get_child_balance(
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PointBalanceResponse:
    """Get current point balance for a child."""
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(child_id, current_user.id)

    # Get balance
    point_service = PointService(db)
    balance = await point_service.get_balance(child_id)

    if not balance:
        return PointBalanceResponse(
            balance=0,
            frozen=0,
            available=0,
            total_earned=0,
            total_spent=0,
        )

    return PointBalanceResponse(
        balance=balance.balance,
        frozen=balance.frozen,
        available=balance.available,
        total_earned=balance.total_earned,
        total_spent=balance.total_spent,
    )


@router.get(
    "/child/{child_id}/transactions",
    response_model=TransactionListResponse,
)
async def get_transaction_history(
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    transaction_type: TransactionType | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TransactionListResponse:
    """Get transaction history for a child."""
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(child_id, current_user.id)

    # Get transactions
    point_service = PointService(db)
    transactions, total = await point_service.get_transaction_history(
        child_id=child_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )

    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post(
    "/child/{child_id}/points/earn",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def earn_points(
    child_id: UUID,
    request: EarnRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Award points to a child (parent action)."""
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(child_id, current_user.id)

    # Earn points
    point_service = PointService(db)
    transaction = await point_service.earn(
        child_id=child_id,
        amount=request.amount,
        source_type=request.source_type,
        source_id=request.source_id,
        description=request.description,
    )

    return TransactionResponse.model_validate(transaction)


@router.post(
    "/child/{child_id}/points/spend",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def spend_points(
    child_id: UUID,
    request: SpendRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Spend points from child's balance."""
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(child_id, current_user.id)

    # Spend points
    point_service = PointService(db)
    try:
        transaction = await point_service.spend(
            child_id=child_id,
            amount=request.amount,
            source_type=request.source_type,
            source_id=request.source_id,
            description=request.description,
        )
    except InsufficientPointsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return TransactionResponse.model_validate(transaction)


@router.post(
    "/child/{child_id}/points/adjust",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def adjust_points(
    child_id: UUID,
    amount: int,
    reason: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TransactionResponse:
    """Manually adjust child's balance (parent admin action)."""
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(child_id, current_user.id)

    # Adjust points
    point_service = PointService(db)
    transaction = await point_service.adjust(
        child_id=child_id,
        amount=amount,
        reason=reason,
    )

    return TransactionResponse.model_validate(transaction)
