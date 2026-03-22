"""Test data fixtures for integration testing.

This module provides factory functions and fixtures for creating test data:
- Test users (parents and children)
- Test tasks
- Test rewards
- Sample data for all major entities

All fixtures include cleanup utilities to ensure test isolation.
"""

from datetime import date, datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child import ChildProfile
from app.models.child_auth import ChildAuthCredential
from app.models.points import PointsTransaction
from app.models.task import Task, TaskCompletion
from app.models.user import User


class UserFixtures:
    """Factory functions for creating test users.

    @MX:NOTE Static class providing user creation utilities
    Methods handle password hashing and database persistence
    """

    @staticmethod
    async def create_parent(
        db: AsyncSession,
        phone: str | None = None,
        name: str = "Test Parent",
        password: str = "TestPass123",
    ) -> User:
        """Create a parent user for testing.

        @MX:ANCHOR User creation fixture
        @MX:REASON Centralized user creation ensures consistent test data

        Args:
            db: Database session
            phone: Phone number (auto-generated if None)
            name: User's display name
            password: Plain text password (will be hashed)

        Returns:
            Created User instance
        """
        from app.core.security import get_password_hash

        if phone is None:
            phone = f"+86138{uuid4().int % 100000000:08d}"

        user = User(
            phone=phone,
            hashed_password=get_password_hash(password),
            name=name,
            status="active",
        )

        db.add(user)
        await db.flush()

        return user

    @staticmethod
    async def create_parent_with_email(
        db: AsyncSession,
        email: str,
        phone: str | None = None,
        name: str = "Test Parent",
        password: str = "TestPass123",
    ) -> User:
        """Create a parent user with email for testing.

        Args:
            db: Database session
            email: Email address
            phone: Phone number (auto-generated if None)
            name: User's display name
            password: Plain text password (will be hashed)

        Returns:
            Created User instance
        """
        from app.core.security import get_password_hash

        if phone is None:
            phone = f"+86138{uuid4().int % 100000000:08d}"

        user = User(
            phone=phone,
            email=email,
            hashed_password=get_password_hash(password),
            name=name,
            status="active",
        )

        db.add(user)
        await db.flush()

        return user


class ChildFixtures:
    """Factory functions for creating test child profiles.

    @MX:NOTE Static class providing child profile creation utilities
    Includes support for child authentication credentials
    """

    @staticmethod
    async def create_child(
        db: AsyncSession,
        parent_id: int,
        name: str = "Test Child",
        birth_date: date | None = None,
        avatar_url: str | None = None,
    ) -> ChildProfile:
        """Create a child profile for testing.

        @MX:ANCHOR Child profile creation fixture
        @MX:REASON Centralized child creation ensures consistent test data

        Args:
            db: Database session
            parent_id: Parent user ID
            name: Child's name
            birth_date: Birth date (defaults to 8 years ago)
            avatar_url: Optional avatar URL

        Returns:
            Created ChildProfile instance
        """
        if birth_date is None:
            birth_date = date.today() - timedelta(days=8 * 365)

        child = ChildProfile(
            parent_id=parent_id,
            name=name,
            birth_date=birth_date,
            avatar_url=avatar_url,
            status="active",
        )

        db.add(child)
        await db.flush()

        return child

    @staticmethod
    async def create_child_with_pin(
        db: AsyncSession,
        parent_id: int,
        pin: str = "1234",
        name: str = "Test Child",
        birth_date: date | None = None,
    ) -> tuple[ChildProfile, ChildAuthCredential]:
        """Create a child profile with PIN authentication.

        Args:
            db: Database session
            parent_id: Parent user ID
            pin: 4-digit PIN code
            name: Child's name
            birth_date: Birth date (defaults to 8 years ago)

        Returns:
            Tuple of (ChildProfile, ChildAuthCredential)
        """
        from app.core.security import hash_pin

        child = await ChildFixtures.create_child(
            db=db,
            parent_id=parent_id,
            name=name,
            birth_date=birth_date,
        )

        credential = ChildAuthCredential(
            child_id=child.id,
            auth_method="pin",
            auth_identifier=pin,
            auth_secret_hash=hash_pin(pin),
            is_active=True,
        )

        db.add(credential)
        await db.flush()

        return child, credential


class TaskFixtures:
    """Factory functions for creating test tasks.

    @MX:NOTE Static class providing task creation utilities
    Supports both one-time and recurring tasks
    """

    @staticmethod
    async def create_task(
        db: AsyncSession,
        child_id: int,
        title: str = "Test Task",
        description: str | None = None,
        task_type: str = "one_time",
        points: int = 10,
        due_date: datetime | None = None,
        recurring_rule: dict | None = None,
    ) -> Task:
        """Create a task for testing.

        @MX:ANCHOR Task creation fixture
        @MX:REASON Centralized task creation ensures consistent test data

        Args:
            db: Database session
            child_id: Child profile ID
            title: Task title
            description: Optional task description
            task_type: Task type (one_time, daily, weekly)
            points: Points awarded for completion
            due_date: Optional due date
            recurring_rule: Recurrence rule for recurring tasks

        Returns:
            Created Task instance
        """
        if description is None:
            description = "This is a test task description"

        if due_date is None and task_type == "one_time":
            due_date = datetime.now() + timedelta(days=1)

        task = Task(
            child_id=child_id,
            title=title,
            description=description,
            task_type=task_type,
            points=points,
            due_date=due_date,
            recurring_rule=recurring_rule,
            status="pending",
        )

        db.add(task)
        await db.flush()

        return task

    @staticmethod
    async def create_completed_task(
        db: AsyncSession,
        task: Task,
        verified_by: int,
        completed_at: datetime | None = None,
        notes: str | None = None,
    ) -> TaskCompletion:
        """Create a task completion record.

        Args:
            db: Database session
            task: Task to mark as completed
            verified_by: Parent user ID who verified completion
            completed_at: Completion timestamp (defaults to now)
            notes: Optional verification notes

        Returns:
            Created TaskCompletion instance
        """
        if completed_at is None:
            completed_at = datetime.now()

        completion = TaskCompletion(
            task_id=task.id,
            verified_by=verified_by,
            completed_at=completed_at,
            verified_at=datetime.now(),
            status="approved",
            notes=notes,
        )

        db.add(completion)
        await db.flush()

        return completion


class PointsFixtures:
    """Factory functions for creating test points transactions.

    @MX:NOTE Static class providing points transaction creation utilities
    """

    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        child_id: int,
        amount: int,
        transaction_type: str = "earned",
        task_id: int | None = None,
        reward_id: int | None = None,
        notes: str | None = None,
    ) -> PointsTransaction:
        """Create a points transaction for testing.

        @MX:ANCHOR Points transaction creation fixture
        @MX:REASON Centralized transaction creation ensures consistent test data

        Args:
            db: Database session
            child_id: Child profile ID
            amount: Points amount (positive for earned, negative for redeemed)
            transaction_type: Transaction type (earned, redeemed, adjusted)
            task_id: Optional related task ID
            reward_id: Optional related reward ID
            notes: Optional transaction notes

        Returns:
            Created PointsTransaction instance
        """
        transaction = PointsTransaction(
            child_id=child_id,
            amount=amount,
            transaction_type=transaction_type,
            task_id=task_id,
            reward_id=reward_id,
            notes=notes,
        )

        db.add(transaction)
        await db.flush()

        return transaction


class SampleData:
    """Pre-defined sample data for common test scenarios.

    @MX:NOTE Static class providing sample data templates
    Use these for consistent test data across multiple tests
    """

    # Sample parent user data
    PARENT_USER = {
        "phone": "+8613812345678",
        "password": "TestPass123",
        "name": "Test Parent",
        "email": "parent@example.com",
    }

    # Sample child profile data
    CHILD_PROFILE = {
        "name": "Test Child",
        "birth_date": "2016-05-15",
        "avatar_url": None,
    }

    # Sample task data
    TASK_ONE_TIME = {
        "title": "Clean your room",
        "description": "Clean and organize your bedroom",
        "task_type": "one_time",
        "points": 10,
    }

    TASK_DAILY = {
        "title": "Brush teeth",
        "description": "Brush teeth twice a day",
        "task_type": "daily",
        "points": 5,
        "recurring_rule": {"frequency": "daily", "interval": 1},
    }

    TASK_WEEKLY = {
        "title": "Do homework",
        "description": "Complete all homework assignments",
        "task_type": "weekly",
        "points": 20,
        "recurring_rule": {"frequency": "weekly", "interval": 1},
    }

    # Sample authentication data
    CHILD_PIN = "1234"

    @staticmethod
    def random_phone() -> str:
        """Generate a random phone number for testing.

        @MX:NOTE Use this to avoid duplicate phone errors in tests
        """
        return f"+86138{uuid4().int % 100000000:08d}"
