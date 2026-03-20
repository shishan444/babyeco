"""Entertainment service for content management and reading progress."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entertainment import (
    Content,
    ContentCategory,
    ContentProgress,
    ContentQuestion,
    ContentStatus,
    ContentType,
    ContentUnlock,
)
from app.services.point_service import PointService

if TYPE_CHECKING:
    from app.models.child_profile import ChildProfile
    from app.models.user import User


class ContentNotFoundError(Exception):
    """Raised when content is not found."""

    def __init__(self, content_id: UUID):
        self.content_id = content_id
        super().__init__(f"Content {content_id} not found")
        self.message = f"Content {content_id} not found"


class ContentAccessError(Exception):
    """Raised when child lacks access to content."""

    def __init__(self, content_id: UUID, reason: str):
        self.content_id = content_id
        self.reason = reason
        super().__init__(f"Cannot access content {content_id}: {reason}")
        self.message = f"Cannot access content {content_id}: {reason}"


class EntertainmentService:
    """Service for content management and reading progress.

    @MX:ANCHOR
    Central service for entertainment content operations.
    Manages content, progress tracking, and point rewards.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._point_service = PointService(db)

    # ==================
    # Content Management
    # ==================

    async def create_content(
        self,
        family_id: UUID,
        created_by: UUID,
        title: str,
        description: str | None = None,
        content_url: str | None = None,
        category: ContentCategory = ContentCategory.STORY,
        type: ContentType = ContentType.FREE,
        duration_seconds: int | None = None,
        age_min: int | None = None,
        age_max: int | None = None,
        thumbnail_url: str | None = None,
        status: ContentStatus = ContentStatus.PUBLISHED,
        points_cost: int = 0,
        points_reward: int = 10,
        is_premium: bool = False,
        author: str | None = None,
        enabled: bool = True,
    ) -> Content:
        """Create new content."""
        content = Content(
            family_id=family_id,
            title=title,
            description=description,
            content_url=content_url,
            category=category,
            type=type,
            duration_seconds=duration_seconds,
            age_min=age_min,
            age_max=age_max,
            thumbnail_url=thumbnail_url,
            status=status,
            points_cost=points_cost,
            points_reward=points_reward,
            is_premium=is_premium,
            author=author,
            created_by=created_by,
            enabled=enabled,
        )
        self.db.add(content)
        await self.db.flush()
        await self.db.refresh(content)
        return content

    async def get_content(self, content_id: UUID) -> Content | None:
        """Get content by ID."""
        result = await self.db.execute(
            select(Content).where(Content.id == content_id)
        )
        return result.scalar_one_or_none()

    async def list_content(
        self,
        family_id: UUID,
        category: ContentCategory | None = None,
        status: ContentStatus | None = ContentStatus.PUBLISHED,
        enabled_only: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Content], int]:
        """List content for a family."""
        query = select(Content).where(Content.family_id == family_id)

        if category:
            query = query.where(Content.category == category)
        if status:
            query = query.where(Content.status == status)
        if enabled_only:
            query = query.where(Content.enabled == True)

        # Count
        count_query = select(func.count(Content.id)).where(Content.family_id == family_id)
        if category:
            count_query = count_query.where(Content.category == category)
        if status:
            count_query = count_query.where(Content.status == status)
        if enabled_only:
            count_query = count_query.where(Content.enabled == True)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Data
        query = query.order_by(Content.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update_content(
        self,
        content_id: UUID,
        **kwargs,
    ) -> Content:
        """Update content."""
        content = await self.get_content(content_id)
        if not content:
            raise ContentNotFoundError(content_id)

        for key, value in kwargs.items():
            if value is not None and hasattr(content, key):
                setattr(content, key, value)

        await self.db.flush()
        await self.db.refresh(content)
        return content

    async def delete_content(self, content_id: UUID) -> None:
        """Delete content."""
        content = await self.get_content(content_id)
        if content:
            await self.db.delete(content)
            await self.db.flush()

    # ==================
    # Progress Tracking
    # ==================

    async def get_progress(self, child_id: UUID, content_id: UUID) -> ContentProgress | None:
        """Get progress for a child on content."""
        result = await self.db.execute(
            select(ContentProgress)
            .where(ContentProgress.child_id == child_id)
            .where(ContentProgress.content_id == content_id)
        )
        return result.scalar_one_or_none()

    async def update_progress(
        self,
        child_id: UUID,
        content_id: UUID,
        progress_seconds: int,
        last_position: int | None = None,
        completed: bool = False,
    ) -> ContentProgress:
        """Update reading progress."""
        progress = await self.get_progress(child_id, content_id)

        if not progress:
            content = await self.get_content(content_id)
            if not content:
                raise ContentNotFoundError(content_id)

            progress = ContentProgress(
                child_id=child_id,
                content_id=content_id,
                progress_seconds=progress_seconds,
                last_position=last_position,
                completed=completed,
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(progress)
        else:
            progress.progress_seconds = progress_seconds
            if last_position is not None:
                progress.last_position = last_position
            if completed:
                progress.completed = True
                progress.completed_at = datetime.now(timezone.utc)

        await self.db.flush()
        await self.db.refresh(progress)
        return progress

    async def complete_content(
        self,
        child_id: UUID,
        content_id: UUID,
        points_bonus: int = 0,
    ) -> ContentProgress:
        """Mark content as completed and award points."""
        content = await self.get_content(content_id)
        if not content:
            raise ContentNotFoundError(content_id)

        progress = await self.get_progress(child_id, content_id)
        if not progress:
            progress = ContentProgress(
                child_id=child_id,
                content_id=content_id,
                progress_seconds=content.duration_seconds or 0,
                completed=True,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
            )
            self.db.add(progress)
        else:
            progress.completed = True
            progress.completed_at = datetime.now(timezone.utc)

        # Award points
        total_points = content.points_reward + points_bonus
        if total_points > 0:
            await self._point_service.earn(
                child_id=child_id,
                amount=total_points,
                source_type="content_completion",
                source_id=content_id,
                description=f"Completed: {content.title}",
            )
            progress.points_earned = total_points

        await self.db.flush()
        await self.db.refresh(progress)
        return progress

    # ==================
    # Content Unlock
    # ==================

    async def unlock_content(
        self,
        child_id: UUID,
        content_id: UUID,
    ) -> ContentUnlock:
        """Unlock premium content by spending points."""
        content = await self.get_content(content_id)
        if not content:
            raise ContentNotFoundError(content_id)

        if content.type != ContentType.PREMIUM:
            raise ContentAccessError(content_id, "Content is not premium")

        # Check if already unlocked
        result = await self.db.execute(
            select(ContentUnlock)
            .where(ContentUnlock.child_id == child_id)
            .where(ContentUnlock.content_id == content_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        # Deduct points
        if content.points_cost > 0:
            await self._point_service.spend(
                child_id=child_id,
                amount=content.points_cost,
                source_type="content_unlock",
                source_id=content_id,
                description=f"Unlocked: {content.title}",
            )

        unlock = ContentUnlock(
            child_id=child_id,
            content_id=content_id,
            points_spent=content.points_cost,
            unlocked_at=datetime.now(timezone.utc),
        )
        self.db.add(unlock)
        await self.db.flush()
        await self.db.refresh(unlock)
        return unlock

    async def is_content_unlocked(self, child_id: UUID, content_id: UUID) -> bool:
        """Check if content is unlocked for child."""
        result = await self.db.execute(
            select(ContentUnlock)
            .where(ContentUnlock.child_id == child_id)
            .where(ContentUnlock.content_id == content_id)
        )
        return result.scalar_one_or_none() is not None

    # ==================
    # Questions
    # ==================

    async def generate_questions(
        self,
        content_id: UUID,
        child_age: int,
    ) -> list[ContentQuestion]:
        """Generate AI questions for content."""
        content = await self.get_content(content_id)
        if not content:
            raise ContentNotFoundError(content_id)

        # In a real implementation, this would call AI service
        # For now, return empty list
        return []

    async def get_questions(self, content_id: UUID) -> list[ContentQuestion]:
        """Get questions for content."""
        result = await self.db.execute(
            select(ContentQuestion)
            .where(ContentQuestion.content_id == content_id)
        )
        return list(result.scalars().all())

    async def answer_question(
        self,
        question_id: UUID,
        child_id: UUID,
        answer: str,
    ) -> bool:
        """Submit answer to a question."""
        result = await self.db.execute(
            select(ContentQuestion).where(ContentQuestion.id == question_id)
        )
        question = result.scalar_one_or_none()
        if not question:
            return False

        # Check if answer is correct
        is_correct = answer == question.correct_answer
        return is_correct
