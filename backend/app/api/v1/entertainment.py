"""Entertainment content API routes."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser
from app.core.database import get_db
from app.schemas.entertainment import (
    CompleteContentRequest,
    ContentCreateRequest,
    ContentListResponse,
    ContentProgressResponse,
    ContentResponse,
    ContentUnlockResponse,
    QuestionSessionRequest,
    QuestionSessionResponse,
    UpdateProgressRequest,
)
from app.services.child_profile_service import ChildProfileService
from app.services.entertainment_service import (
    ContentAccessError,
    ContentNotFoundError,
    EntertainmentService,
)
from app.models.entertainment import ContentCategory, ContentType

router = APIRouter()


# ==================
# Dependencies
# ==================


def get_child_profile_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ChildProfileService:
    """Get child profile service instance."""
    return ChildProfileService(db)


def get_entertainment_service(
    db: Annotated[AsyncSession, Depends(get_db)]
) -> EntertainmentService:
    """Get entertainment service instance."""
    return EntertainmentService(db)


# ==================
# Content Management
# ==================


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreateRequest,
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> ContentResponse:
    """Create new content."""
    # Verify user has family context
    children = await child_service.list_profiles(current_user.id)
    if not children:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No family context found",
        )
    family_id = children[0].parent_id
    content = await entertainment_service.create_content(
        family_id=family_id,
        created_by=current_user.id,
        title=content_data.title,
        description=content_data.description,
        content_url=content_data.content_url,
        category=content_data.category,
        type=content_data.type,
        duration_seconds=content_data.duration_seconds,
        age_min=content_data.age_min,
        age_max=content_data.age_max,
        thumbnail_url=content_data.thumbnail_url,
        status=content_data.status,
        points_cost=content_data.points_cost,
        points_reward=content_data.points_reward,
        is_premium=content_data.is_premium,
        author=content_data.author,
        enabled=content_data.enabled,
    )
    return ContentResponse.model_validate(content)


@router.get("/", response_model=ContentListResponse)
async def list_contents(
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
    category: ContentCategory | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ContentListResponse:
    """List contents for a family."""
    children = await child_service.list_profiles(current_user.id)
    if not children:
        return ContentListResponse(
            contents=[], total=0, page=page, page_size=page_size
        )
    family_id = children[0].parent_id
    contents, total = await entertainment_service.list_content(
        family_id=family_id,
        category=category,
        page=page,
        page_size=page_size,
    )
    return ContentListResponse(
        contents=[ContentResponse.model_validate(c) for c in contents],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: UUID,
    current_user: CurrentUser,
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> ContentResponse:
    """Get a specific content."""
    content = await entertainment_service.get_content(content_id)
    if not content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Content not found",
        )
    return ContentResponse.model_validate(content)


@router.get("/{content_id}/progress/{child_id}", response_model=ContentProgressResponse | None)
async def get_content_progress(
    content_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> ContentProgressResponse | None:
    """Get child's progress on content."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    progress = await entertainment_service.get_progress(child_id, content_id)
    return ContentProgressResponse.model_validate(progress) if progress else None


@router.post("/{content_id}/progress/{child_id}", response_model=ContentProgressResponse)
async def update_content_progress(
    content_id: UUID,
    child_id: UUID,
    progress_data: UpdateProgressRequest,
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> ContentProgressResponse:
    """Update child's progress on content."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    progress = await entertainment_service.update_progress(
        child_id=child_id,
        content_id=content_id,
        progress_seconds=progress_data.progress_seconds,
        last_position=progress_data.last_position,
        completed=progress_data.completed,
    )
    return ContentProgressResponse.model_validate(progress)


@router.post("/{content_id}/complete/{child_id}", response_model=ContentProgressResponse)
async def complete_content(
    content_id: UUID,
    child_id: UUID,
    complete_data: CompleteContentRequest,
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> ContentProgressResponse:
    """Complete content and award points."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    progress = await entertainment_service.complete_content(
        child_id=child_id,
        content_id=content_id,
        points_bonus=complete_data.points_bonus,
    )
    return ContentProgressResponse.model_validate(progress)


@router.post("/{content_id}/unlock/{child_id}", response_model=ContentUnlockResponse)
async def unlock_content(
    content_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> ContentUnlockResponse:
    """Unlock premium content for child."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    try:
        unlock = await entertainment_service.unlock_content(child_id, content_id)
        return ContentUnlockResponse.model_validate(unlock)
    except ContentAccessError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{content_id}/questions", response_model=QuestionSessionResponse)
async def start_question_session(
    content_id: UUID,
    child_id: UUID,
    request: QuestionSessionRequest,
    current_user: CurrentUser,
    child_service: Annotated[ChildProfileService, Depends(get_child_profile_service)],
    entertainment_service: Annotated[EntertainmentService, Depends(get_entertainment_service)],
) -> QuestionSessionResponse:
    """Start AI question session for content."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    questions = await entertainment_service.generate_questions(content_id, request.child_age)
    # Return mock response for now
    return QuestionSessionResponse(
        id=content_id,
        content_id=content_id,
        questions=[],
        total_questions=0,
        correct_answers=0,
        points_earned=0,
        completed_at=datetime.utcnow(),
    )
