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
# Content Management
# ==================


@router.post("/", response_model=ContentResponse, status_code=status.HTTP_201_CREATED)
async def create_content(
    content_data: ContentCreateRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
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
    content = await entertainment_service.create_content(family_id, content_data)
    return ContentResponse.model_validate(content)
@router.get("/", response_model=ContentListResponse)
async def list_contents(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
    category: ContentCategory | None = Query(None),
    age: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ContentListResponse:
    """List contents for a family."""
    children = await child_service.list_profiles(current_user.id)
    if not children:
        return ContentListResponse(contents=[], total=0, page=page, page_size=page_size, has_more=False)
    family_id = children[0].parent_id
    contents, total = await entertainment_service.list_contents(
        family_id=family_id,
        category=category,
        age=age,
        page=page,
        page_size=page_size,
    )
    has_more = (page * page_size) < total
    return ContentListResponse(
        contents=[ContentResponse.model_validate(c) for c in contents],
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )
@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
) -> ContentResponse:
    """Get a specific content."""
    try:
        content = await entertainment_service.get_content(content_id)
        return ContentResponse.model_validate(content)
    except ContentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
@router.get("/{content_id}/progress/{child_id}", response_model=ContentProgressResponse)
async def get_content_progress(
    content_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
) -> ContentProgressResponse:
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
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
) -> ContentProgressResponse:
    """Update child's progress on content."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    progress = await entertainment_service.update_progress(
        child_id=child_id,
        content_id=content_id,
        progress_seconds=progress_data.progress_seconds,
        last_position=progress_data.last_position,
    )
    return ContentProgressResponse.model_validate(progress)
@router.post("/{content_id}/complete/{child_id}", response_model=ContentProgressResponse)
async def complete_content(
    content_id: UUID,
    child_id: UUID,
    complete_data: CompleteContentRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
) -> ContentProgressResponse:
    """Complete content and award points."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    progress = await entertainment_service.complete_content(
        child_id=child_id,
        content_id=content_id,
        points_bonus=complete_data.points_bonus,
        answers_correct=complete_data.answers_correct,
    )
    return ContentProgressResponse.model_validate(progress)
@router.post("/{content_id}/unlock/{child_id}", response_model=ContentUnlockResponse)
async def unlock_content(
    content_id: UUID,
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
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
    db: Annotated[AsyncSession, Depends(get_db)],
    child_service: ChildProfileService = Depends(ChildProfileService),
    entertainment_service: EntertainmentService = Depends(EntertainmentService),
) -> QuestionSessionResponse:
    """Start AI question session for content."""
    # Verify child belongs to current parent
    await child_service.get_profile(child_id, current_user.id)
    session = await entertainment_service.start_question_session(child_id, content_id)
    return QuestionSessionResponse.model_validate(session)
