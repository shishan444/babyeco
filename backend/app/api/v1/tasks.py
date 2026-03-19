"""Task management API routes."""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser
from app.core.database import get_db
from app.repositories.child_profile_repository import ChildProfileRepository
from app.schemas.task import (
    TaskApproveRequest,
    TaskCompleteRequest,
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatus,
    TaskUpdate,
)
from app.services.child_profile_service import ChildProfileService

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Create a new task for a child.

    Parents can create tasks for their children with point values.
    """
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    child = await child_service.get_profile(task_data.child_id, current_user.id)

    # Create task (simplified - in real implementation would have TaskService)
    from app.models.task import Task

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
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.get("/child/{child_id}", response_model=TaskListResponse)
async def list_child_tasks(
    child_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: TaskStatus | None = Query(None, alias="status"),
    date_filter: date | None = Query(None, alias="date"),
) -> TaskListResponse:
    """List all tasks for a specific child.

    Optionally filter by status and date.
    """
    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(child_id, current_user.id)

    # Query tasks
    from sqlalchemy import select

    from app.models.task import Task

    query = select(Task).where(Task.child_id == child_id, Task.is_active == True)

    if status_filter:
        query = query.where(Task.status == status_filter)

    if date_filter:
        query = query.where(Task.due_date == date_filter)

    query = query.order_by(Task.due_date.asc(), Task.created_at.desc())

    result = await db.execute(query)
    tasks = list(result.scalars().all())

    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=len(tasks),
        pending_count=len([t for t in tasks if t.status == TaskStatus.PENDING]),
        completed_count=len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Get a specific task by ID."""
    from sqlalchemy import select

    from app.models.task import Task

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    return TaskResponse.model_validate(task)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Update a task's details."""
    from sqlalchemy import select

    from app.models.task import Task

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    # Update fields
    update_data = task_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    await db.flush()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    complete_data: TaskCompleteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Mark a task as completed by child.

    This endpoint is used by child devices to submit task completion.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models.task import Task, TaskStatus

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    if task.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task already {task.status.value}",
        )

    # Update task status
    task.status = TaskStatus.AWAITING_APPROVAL
    task.completed_at = datetime.now(timezone.utc)

    if complete_data.image_proof_url:
        task.image_url = complete_data.image_proof_url

    await db.flush()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
    task_id: UUID,
    approve_data: TaskApproveRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Approve or reject a completed task.

    Parents review and approve/reject task completions.
    """
    from datetime import datetime, timezone

    from sqlalchemy import select

    from app.models.task import Task, TaskStatus

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    if task.status != TaskStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is not awaiting approval",
        )

    # Update status
    if approve_data.approved:
        task.status = TaskStatus.APPROVED
        task.approved_at = datetime.now(timezone.utc)

        # Award points to child
        total_points = task.points + approve_data.bonus_points
        await child_service.add_points(task.child_id, total_points)
    else:
        task.status = TaskStatus.REJECTED

    await db.flush()
    await db.refresh(task)

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a task (soft delete by setting is_active=False)."""
    from sqlalchemy import select

    from app.models.task import Task

    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    task.is_active = False
    await db.flush()
