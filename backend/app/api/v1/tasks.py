"""Task management API routes."""

from datetime import UTC, date
from typing import Annotated

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import CurrentUser
from app.core.database import get_db
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
from app.services.task_service import TaskService, InvalidTaskStatusError

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

    # Use TaskService to create task
    task_service = TaskService(db)
    task = await task_service.create_task(task_data)

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

    # Use TaskService to list tasks
    task_service = TaskService(db)
    tasks = await task_service.list_tasks_by_child(
        child_id,
        status_filter=status_filter,
        date_filter=date_filter,
    )

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
    task_service = TaskService(db)
    task = await task_service.get_task_by_id(task_id)

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
    task_service = TaskService(db)

    # First get task to verify ownership
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    # Update task
    updated = await task_service.update_task(task_id, task_data)

    return TaskResponse.model_validate(updated)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    complete_data: TaskCompleteRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskResponse:
    """Mark a task as completed by child.

    This endpoint is used by child devices to submit task completion.
    """
    task_service = TaskService(db)

    try:
        completed = await task_service.complete_task(
            task_id=task_id,
            child_id=UUID("00000000-0000-0000-0000-000000000000"),  # TODO: Get from child token
            image_proof_url=complete_data.image_proof_url,
        )
        return TaskResponse.model_validate(completed)
    except InvalidTaskStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


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
    task_service = TaskService(db)

    # First get task to verify ownership
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    try:
        approved = await task_service.approve_task(
            task_id=task_id,
            approved=approve_data.approved,
            bonus_points=approve_data.bonus_points,
        )
        return TaskResponse.model_validate(approved)
    except InvalidTaskStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a task (soft delete by setting is_active=False)."""
    task_service = TaskService(db)

    # First get task to verify ownership
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Verify child belongs to current parent
    child_service = ChildProfileService(db)
    await child_service.get_profile(task.child_id, current_user.id)

    await task_service.delete_task(task_id)
