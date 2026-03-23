"""Task service for managing child tasks and check-in workflow.

@MX:ANCHOR
Central service for all task operations including CRUD,
completion workflow, approval, and point integration.
Handles business logic for task lifecycle management.
"""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID
from typing import list

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskCategory, TaskStatus, TaskCompletion
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.point_service import PointService


class TaskNotFoundError(Exception):
    """Raised when task is not found."""

    pass


class InvalidTaskStatusError(Exception):
    """Raised when task status doesn't allow the operation."""

    pass


class TaskService:
    """Service for task management and check-in workflow.

    @MX:ANCHOR
    Handles task CRUD operations, completion workflow, approval,
    streak calculation, and point awarding integration.
    This is the main business logic layer for task management.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Initialize TaskService with database session.

        Args:
            db: Async database session
        """
        self.db = db
        self.point_service = PointService(db)

    async def create_task(self, task_data: TaskCreate) -> Task:
        """Create a new task for a child.

        @MX:ANCHOR
        Creates task with validation per UR-002.
        Verifies child exists before creation.

        Args:
            task_data: Task creation data

        Returns:
            Created task

        Raises:
            HTTPException: If child not found
        """
        # Verify child exists
        from app.models.child_profile import ChildProfile

        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.id == task_data.child_id)
        )
        child = result.scalar_one_or_none()

        if not child:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Child profile not found",
            )

        # Create task
        task = Task(
            child_id=task_data.child_id,
            title=task_data.title,
            description=task_data.description,
            category=task_data.category,
            points=task_data.points,
            due_date=task_data.due_date,
            due_time=task_data.due_time,
            is_recurring=task_data.is_recurring,
            recurrence_pattern=task_data.recurrence_pattern,
            status=TaskStatus.PENDING,
        )

        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def get_task_by_id(self, task_id: UUID) -> Task | None:
        """Get a task by ID.

        Args:
            task_id: Task UUID

        Returns:
            Task if found, None otherwise
        """
        result = await self.db.execute(
            select(Task).where(Task.id == task_id, Task.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update_task(self, task_id: UUID, update_data: TaskUpdate) -> Task:
        """Update a task's details.

        Args:
            task_id: Task UUID
            update_data: Fields to update

        Returns:
            Updated task

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task_by_id(task_id)

        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(task, field, value)

        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def complete_task(
        self,
        task_id: UUID,
        child_id: UUID,
        image_proof_url: str | None = None,
    ) -> Task:
        """Mark a task as completed by child.

        @MX:ANCHOR
        Changes status to AWAITING_APPROVAL per EDR-002.
        Validates task is in PENDING status per SDR-002.

        Args:
            task_id: Task UUID
            child_id: Child's UUID (for verification)
            image_proof_url: Optional proof image URL

        Returns:
            Updated task

        Raises:
            TaskNotFoundError: If task not found
            InvalidTaskStatusError: If task not in PENDING status
        """
        task = await self.get_task_by_id(task_id)

        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        if task.status != TaskStatus.PENDING:
            raise InvalidTaskStatusError(
                f"Task is {task.status.value}, cannot complete"
            )

        # Update status
        task.status = TaskStatus.AWAITING_APPROVAL
        task.completed_at = datetime.now(UTC)
        if image_proof_url:
            task.image_url = image_proof_url

        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def approve_task(
        self,
        task_id: UUID,
        approved: bool,
        bonus_points: int = 0,
    ) -> Task:
        """Approve or reject a completed task.

        @MX:ANCHOR
        Approves: Awards points via PointService per EDR-003.
        Rejects: No points awarded per EDR-004.
        Creates TaskCompletion record for analytics.

        Args:
            task_id: Task UUID
            approved: True to approve, False to reject
            bonus_points: Additional bonus points (if approved)

        Returns:
            Updated task

        Raises:
            TaskNotFoundError: If task not found
            InvalidTaskStatusError: If task not awaiting approval
        """
        task = await self.get_task_by_id(task_id)

        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        if task.status != TaskStatus.AWAITING_APPROVAL:
            raise InvalidTaskStatusError(
                f"Task is {task.status.value}, cannot approve"
            )

        if approved:
            # Calculate streak
            completed_date = task.completed_at.date() if task.completed_at else date.today()
            streak_day = await self._calculate_streak_day(
                child_id=task.child_id,
                task_title=task.title,
                completed_date=completed_date,
            )

            # Award points (base + bonus)
            total_points = task.points + bonus_points
            await self.point_service.earn(
                child_id=task.child_id,
                amount=total_points,
                source_type="task_completion",
                source_id=task.id,
                description=f"Task: {task.title}",
            )

            # Create completion record
            completion = TaskCompletion(
                task_id=task.id,
                child_id=task.child_id,
                completed_date=completed_date,
                points_earned=total_points,
                streak_day=streak_day,
            )
            self.db.add(completion)

            # Update task
            task.status = TaskStatus.APPROVED
            task.approved_at = datetime.now(UTC)
            task.streak_bonus = bonus_points
        else:
            # Reject - no points
            task.status = TaskStatus.REJECTED

        await self.db.flush()
        await self.db.refresh(task)

        return task

    async def delete_task(self, task_id: UUID) -> None:
        """Soft delete a task by setting is_active=False.

        Args:
            task_id: Task UUID

        Raises:
            TaskNotFoundError: If task not found
        """
        task = await self.get_task_by_id(task_id)

        if not task:
            raise TaskNotFoundError(f"Task {task_id} not found")

        task.is_active = False
        await self.db.flush()

    async def list_tasks_by_child(
        self,
        child_id: UUID,
        status_filter: TaskStatus | None = None,
        date_filter: date | None = None,
    ) -> list[Task]:
        """List tasks for a child with optional filters.

        Args:
            child_id: Child's UUID
            status_filter: Optional status filter
            date_filter: Optional due date filter

        Returns:
            List of active tasks matching filters
        """
        query = select(Task).where(
            Task.child_id == child_id,
            Task.is_active == True,
        )

        if status_filter:
            query = query.where(Task.status == status_filter)

        if date_filter:
            query = query.where(Task.due_date == date_filter)

        query = query.order_by(Task.due_date.asc(), Task.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _calculate_streak_day(
        self,
        child_id: UUID,
        task_title: str,
        completed_date: date,
    ) -> int:
        """Calculate the current streak day for a task.

        @MX:NOTE
        Checks previous completions to determine consecutive days.
        Returns 1 if no previous completion or gap > 1 day.
        Looks for ANY task completion yesterday, not just same title.
        This encourages consistent task completion across all tasks.

        Args:
            child_id: Child's UUID
            task_title: Task title (currently unused, reserved for future)
            completed_date: Current completion date

        Returns:
            Streak day number (1-based)
        """
        # Find most recent completion for this child from yesterday
        yesterday = completed_date - timedelta(days=1)

        result = await self.db.execute(
            select(TaskCompletion)
            .where(
                TaskCompletion.child_id == child_id,
                TaskCompletion.completed_date == yesterday,
            )
            .order_by(TaskCompletion.created_at.desc())
            .limit(1)
        )
        previous_completion = result.scalar_one_or_none()

        if previous_completion:
            # Consecutive day - increment streak
            return previous_completion.streak_day + 1
        else:
            # No previous completion or gap - start new streak
            return 1
