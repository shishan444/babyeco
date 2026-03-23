"""TDD tests for TaskService.

Tests follow RED-GREEN-REFACTOR cycle:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve with test safety net
"""

import pytest
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child_profile import ChildProfile
from app.models.task import Task, TaskCategory, TaskStatus, TaskCompletion
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService, TaskNotFoundError, InvalidTaskStatusError
from app.services.point_service import PointService


@pytest.fixture
def task_service(db: AsyncSession) -> TaskService:
    """Create TaskService instance."""
    return TaskService(db)


@pytest.fixture
def point_service(db: AsyncSession) -> PointService:
    """Create PointService instance."""
    return PointService(db)


@pytest.fixture
async def sample_child(db: AsyncSession) -> ChildProfile:
    """Create a sample child profile."""
    from app.services.child_profile_service import ChildProfileService
    from app.schemas.auth import ChildProfileCreate
    from app.models.parent import Parent

    # Create parent
    parent = Parent(
        email="parent@example.com",
        hashed_password="hash",
        full_name="Test Parent",
    )
    db.add(parent)
    await db.flush()

    # Create child
    child_service = ChildProfileService(db)
    child_data = ChildProfileCreate(
        name="Test Child",
        birth_date=date.today() - timedelta(days=5 * 365),
    )
    child = await child_service.create_profile(parent.id, child_data)
    await db.flush()

    return child


class TestTaskCreation:
    """Tests for task creation (RED-GREEN-REFACTOR)."""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self,
        task_service: TaskService,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test successful task creation.

        Expected behavior: Task is created with all fields.
        """
        task_data = TaskCreate(
            child_id=sample_child.id,
            title="Clean room",
            description="Clean and organize your room",
            category=TaskCategory.DAILY,
            points=10,
            due_date=date.today() + timedelta(days=1),
        )

        task = await task_service.create_task(task_data)

        assert task.id is not None
        assert task.title == "Clean room"
        assert task.description == "Clean and organize your room"
        assert task.category == TaskCategory.DAILY
        assert task.points == 10
        assert task.status == TaskStatus.PENDING
        assert task.child_id == sample_child.id
        assert task.is_active is True

    @pytest.mark.asyncio
    async def test_create_task_with_recurring_pattern(
        self,
        task_service: TaskService,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test creating a recurring task.

        Expected behavior: Recurring fields are set correctly.
        """
        task_data = TaskCreate(
            child_id=sample_child.id,
            title="Brush teeth",
            category=TaskCategory.DAILY,
            points=5,
            is_recurring=True,
            recurrence_pattern="0 20 * * *",  # Daily at 8 PM
        )

        task = await task_service.create_task(task_data)

        assert task.is_recurring is True
        assert task.recurrence_pattern == "0 20 * * *"

    @pytest.mark.asyncio
    async def test_create_task_invalid_child(
        self,
        task_service: TaskService,
    ) -> None:
        """RED: Test creating task for non-existent child fails.

        Expected behavior: Raises exception or returns None.
        """
        task_data = TaskCreate(
            child_id=uuid4(),
            title="Test task",
            points=10,
        )

        with pytest.raises(Exception):  # Specific exception to be determined
            await task_service.create_task(task_data)


class TestTaskRetrieval:
    """Tests for task retrieval operations."""

    @pytest.mark.asyncio
    async def test_get_task_by_id_success(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test retrieving task by ID.

        Expected behavior: Returns task with matching ID.
        """
        # Create task first
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Retrieve it
        retrieved = await task_service.get_task_by_id(task.id)

        assert retrieved is not None
        assert retrieved.id == task.id
        assert retrieved.title == "Test task"

    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(
        self,
        task_service: TaskService,
    ) -> None:
        """RED: Test retrieving non-existent task.

        Expected behavior: Returns None or raises exception.
        """
        result = await task_service.get_task_by_id(uuid4())

        assert result is None  # Or raises exception


class TestTaskUpdate:
    """Tests for task update operations."""

    @pytest.mark.asyncio
    async def test_update_task_success(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test updating task fields.

        Expected behavior: Task fields are updated.
        """
        # Create task
        task = Task(
            child_id=sample_child.id,
            title="Original title",
            points=10,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Update it
        update_data = TaskUpdate(
            title="Updated title",
            points=20,
        )

        updated = await task_service.update_task(task.id, update_data)

        assert updated.title == "Updated title"
        assert updated.points == 20

    @pytest.mark.asyncio
    async def test_update_nonexistent_task(
        self,
        task_service: TaskService,
    ) -> None:
        """RED: Test updating non-existent task.

        Expected behavior: Raises exception.
        """
        update_data = TaskUpdate(title="Updated")

        with pytest.raises(TaskNotFoundError):
            await task_service.update_task(uuid4(), update_data)


class TestTaskCompletion:
    """Tests for task completion workflow."""

    @pytest.mark.asyncio
    async def test_complete_task_success(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test marking task as completed.

        Expected behavior: Status changes to AWAITING_APPROVAL.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        completed = await task_service.complete_task(
            task.id,
            sample_child.id,
            image_proof_url=None,
        )

        assert completed.status == TaskStatus.AWAITING_APPROVAL
        assert completed.completed_at is not None

    @pytest.mark.asyncio
    async def test_complete_task_with_proof(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test completing task with image proof.

        Expected behavior: Image URL is saved.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        completed = await task_service.complete_task(
            task.id,
            sample_child.id,
            image_proof_url="https://example.com/proof.jpg",
        )

        assert completed.image_url == "https://example.com/proof.jpg"

    @pytest.mark.asyncio
    async def test_complete_already_completed_task(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test completing already completed task.

        Expected behavior: Raises InvalidTaskStatusError.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.AWAITING_APPROVAL,  # Already completed
        )
        db.add(task)
        await db.flush()

        with pytest.raises(InvalidTaskStatusError):
            await task_service.complete_task(
                task.id,
                sample_child.id,
            )

    @pytest.mark.asyncio
    async def test_complete_nonexistent_task(
        self,
        task_service: TaskService,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test completing non-existent task.

        Expected behavior: Raises TaskNotFoundError.
        """
        with pytest.raises(TaskNotFoundError):
            await task_service.complete_task(
                uuid4(),
                sample_child.id,
            )


class TestTaskApproval:
    """Tests for task approval workflow and point awarding."""

    @pytest.mark.asyncio
    async def test_approve_task_awards_points(
        self,
        task_service: TaskService,
        point_service: PointService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test approving task awards points to child.

        Expected behavior: Points are awarded via PointService.
        """
        # Create task awaiting approval
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.AWAITING_APPROVAL,
            completed_at=datetime.now(UTC),
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Get initial balance
        initial_balance = await point_service.get_balance(sample_child.id)

        # Approve task
        approved = await task_service.approve_task(
            task.id,
            approved=True,
            bonus_points=0,
        )

        # Check points were awarded
        final_balance = await point_service.get_balance(sample_child.id)
        assert final_balance.balance == initial_balance.balance + 10 if initial_balance else 10
        assert approved.status == TaskStatus.APPROVED
        assert approved.approved_at is not None

    @pytest.mark.asyncio
    async def test_approve_task_with_bonus_points(
        self,
        task_service: TaskService,
        point_service: PointService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test approving with bonus points.

        Expected behavior: Base + bonus points are awarded.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.AWAITING_APPROVAL,
            completed_at=datetime.now(UTC),
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Approve with bonus
        await task_service.approve_task(
            task.id,
            approved=True,
            bonus_points=5,
        )

        # Check total points
        balance = await point_service.get_balance(sample_child.id)
        assert balance.balance == 15  # 10 base + 5 bonus

    @pytest.mark.asyncio
    async def test_reject_task_no_points(
        self,
        task_service: TaskService,
        point_service: PointService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test rejecting task awards no points.

        Expected behavior: Status changes but no points awarded.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.AWAITING_APPROVAL,
            completed_at=datetime.now(UTC),
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Get initial balance
        initial_balance = await point_service.get_balance(sample_child.id)

        # Reject task
        rejected = await task_service.approve_task(
            task.id,
            approved=False,
        )

        # Check no points awarded
        final_balance = await point_service.get_balance(sample_child.id)
        if initial_balance:
            assert final_balance.balance == initial_balance.balance
        assert rejected.status == TaskStatus.REJECTED

    @pytest.mark.asyncio
    async def test_approve_creates_completion_record(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test approval creates TaskCompletion record.

        Expected behavior: TaskCompletion is created with streak data.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.AWAITING_APPROVAL,
            completed_at=datetime.now(UTC),
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        # Approve
        await task_service.approve_task(
            task.id,
            approved=True,
            bonus_points=0,
        )

        # Check completion record exists
        from sqlalchemy import select

        result = await db.execute(
            select(TaskCompletion).where(TaskCompletion.task_id == task.id)
        )
        completion = result.scalar_one_or_none()

        assert completion is not None
        assert completion.points_earned == 10
        assert completion.streak_day >= 1


class TestStreakCalculation:
    """Tests for streak bonus calculation."""

    @pytest.mark.asyncio
    async def test_calculate_streak_day_first_completion(
        self,
        task_service: TaskService,
    ) -> None:
        """RED: Test first completion returns streak day 1.

        Expected behavior: Streak starts at 1.
        """
        streak_day = await task_service._calculate_streak_day(
            child_id=uuid4(),
            task_title="Test task",
            completed_date=date.today(),
        )

        assert streak_day == 1

    @pytest.mark.asyncio
    async def test_calculate_streak_consecutive_days(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test consecutive days increase streak.

        Expected behavior: Each consecutive day increments streak.
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Create completion for yesterday
        completion1 = TaskCompletion(
            task_id=uuid4(),
            child_id=sample_child.id,
            completed_date=yesterday,
            points_earned=10,
            streak_day=1,
        )
        db.add(completion1)
        await db.flush()

        # Calculate streak for today
        streak_day = await task_service._calculate_streak_day(
            child_id=sample_child.id,
            task_title="Test task",
            completed_date=today,
        )

        assert streak_day == 2

    @pytest.mark.asyncio
    async def test_calculate_streak_broken_gap(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test gap in days resets streak.

        Expected behavior: Non-consecutive days reset streak to 1.
        """
        today = date.today()
        two_days_ago = today - timedelta(days=2)

        # Create completion from 2 days ago
        completion = TaskCompletion(
            task_id=uuid4(),
            child_id=sample_child.id,
            completed_date=two_days_ago,
            points_earned=10,
            streak_day=1,
        )
        db.add(completion)
        await db.flush()

        # Calculate streak for today (should reset)
        streak_day = await task_service._calculate_streak_day(
            child_id=sample_child.id,
            task_title="Test task",
            completed_date=today,
        )

        assert streak_day == 1  # Reset


class TestTaskDeletion:
    """Tests for task deletion."""

    @pytest.mark.asyncio
    async def test_soft_delete_task(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test soft deleting a task.

        Expected behavior: is_active set to False, not deleted from DB.
        """
        task = Task(
            child_id=sample_child.id,
            title="Test task",
            points=10,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        await db.flush()
        await db.refresh(task)

        await task_service.delete_task(task.id)

        # Refresh from DB
        await db.refresh(task)
        assert task.is_active is False

    @pytest.mark.asyncio
    async def test_delete_nonexistent_task(
        self,
        task_service: TaskService,
    ) -> None:
        """RED: Test deleting non-existent task.

        Expected behavior: Raises TaskNotFoundError.
        """
        with pytest.raises(TaskNotFoundError):
            await task_service.delete_task(uuid4())


class TestTaskListing:
    """Tests for task listing with filters."""

    @pytest.mark.asyncio
    async def test_list_tasks_by_child(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test listing tasks for a child.

        Expected behavior: Returns only active tasks for the child.
        """
        # Create tasks
        for i in range(3):
            task = Task(
                child_id=sample_child.id,
                title=f"Task {i}",
                points=10,
                status=TaskStatus.PENDING,
            )
            db.add(task)

        # Create inactive task
        inactive = Task(
            child_id=sample_child.id,
            title="Inactive task",
            points=10,
            status=TaskStatus.PENDING,
            is_active=False,
        )
        db.add(inactive)
        await db.flush()

        tasks = await task_service.list_tasks_by_child(sample_child.id)

        assert len(tasks) == 3
        assert all(t.is_active for t in tasks)

    @pytest.mark.asyncio
    async def test_list_tasks_with_status_filter(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test filtering tasks by status.

        Expected behavior: Returns only tasks with matching status.
        """
        # Create pending task
        pending = Task(
            child_id=sample_child.id,
            title="Pending task",
            points=10,
            status=TaskStatus.PENDING,
        )
        db.add(pending)

        # Create completed task
        completed = Task(
            child_id=sample_child.id,
            title="Completed task",
            points=10,
            status=TaskStatus.APPROVED,
        )
        db.add(completed)
        await db.flush()

        tasks = await task_service.list_tasks_by_child(
            sample_child.id,
            status_filter=TaskStatus.PENDING,
        )

        assert len(tasks) == 1
        assert tasks[0].status == TaskStatus.PENDING

    @pytest.mark.asyncio
    async def test_list_tasks_with_date_filter(
        self,
        task_service: TaskService,
        db: AsyncSession,
        sample_child: ChildProfile,
    ) -> None:
        """RED: Test filtering tasks by due date.

        Expected behavior: Returns only tasks due on specified date.
        """
        today = date.today()
        tomorrow = today + timedelta(days=1)

        # Create task due today
        task_today = Task(
            child_id=sample_child.id,
            title="Today task",
            points=10,
            due_date=today,
            status=TaskStatus.PENDING,
        )
        db.add(task_today)

        # Create task due tomorrow
        task_tomorrow = Task(
            child_id=sample_child.id,
            title="Tomorrow task",
            points=10,
            due_date=tomorrow,
            status=TaskStatus.PENDING,
        )
        db.add(task_tomorrow)
        await db.flush()

        tasks = await task_service.list_tasks_by_child(
            sample_child.id,
            date_filter=today,
        )

        assert len(tasks) == 1
        assert tasks[0].due_date == today
