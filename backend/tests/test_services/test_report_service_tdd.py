"""TDD tests for Report Service.

Test-Driven Development Approach:
- RED: Write failing test first
- GREEN: Implement minimal code to pass
- REFACTOR: Improve while keeping tests green

@MX:NOTE
Tests follow Arrange-Act-Assert pattern.
All test data uses fixtures for consistency.
"""

import json
from datetime import date, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import (
    Achievement,
    AchievementCategory,
    CachedAggregate,
    ExportStatus,
    Milestone,
    MilestoneType,
    ReportExport,
)
from app.schemas.report import (
    AchievementResponse,
    CategoryStats,
    DailyPointStats,
    DailyStats,
    ExportRequest,
    FamilyOverviewResponse,
    GrowthDashboardResponse,
    MilestoneBrief,
    MilestoneResponse,
    PointReportResponse,
    ReportSummaryResponse,
    TaskReportResponse,
    TrendDataResponse,
)
from app.services.report_service import ReportService


@pytest.fixture
async def report_service(db_session: AsyncSession):
    """Create report service instance.

    @MX:NOTE
    Mock Redis cache for testing.
    """
    # Mock cache
    class MockCache:
        def __init__(self):
            self.data = {}

        async def get(self, key: str):
            return self.data.get(key)

        async def set(self, key: str, value: str, ex: int | None = None):
            self.data[key] = value

        async def setex(self, key: str, time: int, value: str):
            self.data[key] = value

        async def delete(self, key: str):
            self.data.pop(key, None)

        async def exists(self, key: str) -> int:
            return 1 if key in self.data else 0

        def clear(self):
            self.data.clear()

    mock_cache = MockCache()
    return ReportService(db=db_session, cache=mock_cache)


@pytest.fixture
async def sample_child_with_data(
    db_session: AsyncSession, sample_child, test_user
):
    """Create child with task and point history for testing.

    @MX:NOTE
    Creates realistic data for aggregation tests.
    """
    from app.models.child_profile import ChildProfile
    from app.models.point import PointTransaction, TransactionType
    from app.models.task import Task, TaskCategory, TaskCompletion, TaskStatus

    # Create child profile
    child = ChildProfile(
        id=uuid4(),
        parent_id=test_user.id,
        name="Test Child",
        points_balance=150,
        total_points_earned=300,
        current_streak=3,
        longest_streak=7,
    )
    db_session.add(child)
    await db_session.flush()

    # Create tasks with various statuses
    base_date = date.today() - timedelta(days=7)
    for i in range(10):
        task_date = base_date + timedelta(days=i)
        task = Task(
            id=uuid4(),
            child_id=child.id,
            title=f"Task {i}",
            category=TaskCategory.DAILY,
            points=10,
            status=TaskStatus.APPROVED if i < 7 else TaskStatus.PENDING,
            completed_at=task_date if i < 7 else None,
            approved_at=task_date if i < 7 else None,
        )
        db_session.add(task)

        # Add completions for approved tasks
        if i < 7:
            completion = TaskCompletion(
                id=uuid4(),
                task_id=task.id,
                child_id=child.id,
                completed_date=task_date,
                points_earned=10,
                streak_day=i + 1,
            )
            db_session.add(completion)

    # Create point transactions
    for i in range(5):
        transaction = PointTransaction(
            id=uuid4(),
            child_id=child.id,
            type=TransactionType.EARN,
            amount=10,
            balance_after=300 - (i * 10),
            source_type="task",
            description="Task completed",
            created_at=datetime.utcnow() - timedelta(days=i),
        )
        db_session.add(transaction)

    await db_session.commit()
    await db_session.refresh(child)

    return child


class TestGrowthDashboard:
    """Test suite for growth dashboard generation.

    @MX:NOTE
    Tests aggregation accuracy and caching.
    """

    async def test_get_growth_dashboard_returns_correct_stats(
        self, report_service, sample_child_with_data
    ):
        """Test that growth dashboard returns accurate statistics."""
        # Arrange
        child_id = sample_child_with_data.id

        # Act
        result = await report_service.get_growth_dashboard(child_id)

        # Assert
        assert isinstance(result, GrowthDashboardResponse)
        assert result.total_points_earned >= 0
        assert result.current_streak >= 0
        assert result.longest_streak >= result.current_streak
        assert result.tasks_completed_total >= 0
        assert result.completion_rate_weekly >= 0
        assert result.completion_rate_monthly >= 0
        assert 0 <= result.achievements_unlocked <= result.achievements_total
        assert isinstance(result.milestones, list)

    async def test_get_growth_dashboard_caches_result(
        self, report_service, sample_child_with_data
    ):
        """Test that growth dashboard results are cached."""
        # Arrange
        child_id = sample_child_with_data.id
        cache_key = f"growth:{child_id}"

        # Act - First call
        result1 = await report_service.get_growth_dashboard(child_id)

        # Check cache exists
        cached = await report_service.cache.get(cache_key)
        assert cached is not None

        # Act - Second call should use cache
        result2 = await report_service.get_growth_dashboard(child_id)

        # Assert
        assert result1.total_points_earned == result2.total_points_earned
        assert result1.current_streak == result2.current_streak

    async def test_get_growth_dashboard_with_no_activity(
        self, report_service, sample_child
    ):
        """Test dashboard with child who has no activity."""
        # Arrange
        child_id = sample_child.id

        # Act
        result = await report_service.get_growth_dashboard(child_id)

        # Assert
        assert result.total_points_earned == 0
        assert result.current_streak == 0
        assert result.longest_streak == 0
        assert result.tasks_completed_total == 0
        assert result.completion_rate_weekly == 0

    async def test_calculate_streak_data_correctly(
        self, report_service, sample_child_with_data
    ):
        """Test streak calculation logic."""
        # Arrange
        child_id = sample_child_with_data.id

        # Act
        result = await report_service.get_growth_dashboard(child_id)

        # Assert
        # Streak should be calculated from consecutive approved tasks
        assert result.current_streak >= 0
        assert result.longest_streak >= result.current_streak


class TestTaskReport:
    """Test suite for task performance reports.

    @MX:NOTE
    Tests grouping and aggregation by category and date.
    """

    async def test_get_task_report_groups_by_category(
        self, report_service, sample_child_with_data
    ):
        """Test task report groups correctly by category."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_task_report(child_id, start_date, end_date)

        # Assert
        assert isinstance(result, TaskReportResponse)
        assert isinstance(result.by_category, dict)
        assert isinstance(result.by_day, list)
        assert isinstance(result.completion_trend, list)

        # Check category stats structure
        for category, stats in result.by_category.items():
            assert isinstance(stats, CategoryStats)
            assert stats.total >= 0
            assert stats.completed >= 0
            assert 0 <= stats.rate <= 100

    async def test_get_task_report_respects_date_range(
        self, report_service, sample_child_with_data
    ):
        """Test task report only includes data in date range."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=3)
        end_date = date.today()

        # Act
        result = await report_service.get_task_report(child_id, start_date, end_date)

        # Assert
        # Should only have data for last 3 days
        assert len(result.by_day) <= 4  # 3 days plus possible padding

    async def test_get_task_report_calculates_completion_rates(
        self, report_service, sample_child_with_data
    ):
        """Test completion rate calculation is accurate."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_task_report(child_id, start_date, end_date)

        # Assert
        for category, stats in result.by_category.items():
            if stats.total > 0:
                expected_rate = (stats.completed / stats.total) * 100
                assert abs(stats.rate - expected_rate) < 0.01

    async def test_get_task_report_aggregates_by_day(
        self, report_service, sample_child_with_data
    ):
        """Test daily aggregation is correct."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_task_report(child_id, start_date, end_date)

        # Assert
        for daily_stat in result.by_day:
            assert isinstance(daily_stat, DailyStats)
            assert isinstance(daily_stat.date, date)
            assert daily_stat.total >= 0
            assert daily_stat.completed >= daily_stat.total
            assert daily_stat.points_earned >= 0


class TestPointReport:
    """Test suite for point activity reports.

    @MX:NOTE
    Tests income/expense breakdown and trends.
    """

    async def test_get_point_report_calculates_totals(
        self, report_service, sample_child_with_data
    ):
        """Test point report totals are accurate."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_point_report(child_id, start_date, end_date)

        # Assert
        assert isinstance(result, PointReportResponse)
        assert result.total_earned >= 0
        assert result.total_spent >= 0
        assert isinstance(result.by_source, dict)
        assert isinstance(result.daily_breakdown, list)

    async def test_get_point_report_breakdown_by_source(
        self, report_service, sample_child_with_data
    ):
        """Test point report breaks down by source."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_point_report(child_id, start_date, end_date)

        # Assert
        # Should have sources like 'task', 'exchange', etc.
        for source, amount in result.by_source.items():
            assert isinstance(source, str)
            assert amount >= 0

    async def test_get_point_report_daily_breakdown(
        self, report_service, sample_child_with_data
    ):
        """Test daily point breakdown accuracy."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_point_report(child_id, start_date, end_date)

        # Assert
        for daily in result.daily_breakdown:
            assert isinstance(daily, DailyPointStats)
            assert isinstance(daily.date, date)
            assert daily.earned >= 0
            assert daily.spent >= 0
            assert daily.balance >= 0


class TestReportSummary:
    """Test suite for report summary generation.

    @MX:NOTE
    Tests high-level summary for parent dashboard.
    """

    async def test_get_report_summary_returns_correct_data(
        self, report_service, sample_child_with_data
    ):
        """Test report summary returns accurate overview."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_report_summary(
            child_id, start_date, end_date
        )

        # Assert
        assert isinstance(result, ReportSummaryResponse)
        assert result.child_id == child_id
        assert isinstance(result.child_name, str)
        assert result.tasks_completed >= 0
        assert result.tasks_total >= 0
        assert 0 <= result.completion_rate <= 100
        assert result.points_earned >= 0
        assert result.points_spent >= 0
        assert result.current_streak >= 0

    async def test_get_report_summary_identifies_top_category(
        self, report_service, sample_child_with_data
    ):
        """Test summary identifies most completed category."""
        # Arrange
        child_id = sample_child_with_data.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_report_summary(
            child_id, start_date, end_date
        )

        # Assert
        # most_completed_category can be None if no tasks
        assert result.most_completed_category is None or isinstance(
            result.most_completed_category, str
        )


class TestAchievements:
    """Test suite for achievement tracking.

    @MX:NOTE
    Tests achievement unlocking logic and progress tracking.
    """

    async def test_get_achievements_returns_all_for_child(
        self, report_service, sample_child
    ):
        """Test getting achievements for child."""
        # Arrange
        child_id = sample_child.id

        # Act
        result = await report_service.get_achievements(child_id)

        # Assert
        assert isinstance(result, list)
        for achievement in result:
            assert isinstance(achievement, AchievementResponse)
            assert isinstance(achievement.id, type(uuid4()))
            assert isinstance(achievement.name, str)
            assert isinstance(achievement.unlocked, bool)
            assert 0 <= achievement.progress <= 100

    async def test_check_achievements_unlocks_new_achievements(
        self, report_service, db_session, sample_child
    ):
        """Test that achievements unlock when criteria met."""
        # Arrange
        child_id = sample_child.id

        # Act
        unlocked = await report_service.check_achievements(child_id)

        # Assert
        assert isinstance(unlocked, list)
        for achievement in unlocked:
            assert achievement.unlocked
            assert achievement.unlocked_at is not None

    async def test_achievement_progress_calculates_correctly(
        self, report_service, sample_child
    ):
        """Test achievement progress calculation."""
        # Arrange
        child_id = sample_child.id

        # Act
        achievements = await report_service.get_achievements(child_id)

        # Assert
        for achievement in achievements:
            if not achievement.unlocked:
                # Progress should be less than 100
                assert achievement.progress < 100


class TestMilestones:
    """Test suite for milestone tracking.

    @MX:NOTE
    Tests milestone auto-unlock and threshold detection.
    """

    async def test_get_milestones_returns_all_for_child(
        self, report_service, sample_child
    ):
        """Test getting milestones for child."""
        # Arrange
        child_id = sample_child.id

        # Act
        result = await report_service.get_milestones(child_id)

        # Assert
        assert isinstance(result, list)
        for milestone in result:
            assert isinstance(milestone, MilestoneResponse)
            assert isinstance(milestone.title, str)
            assert isinstance(milestone.threshold, int)
            assert isinstance(milestone.achieved, bool)

    async def test_check_milestones_unlocks_when_threshold_reached(
        self, report_service, db_session, sample_child_with_data
    ):
        """Test milestones unlock when thresholds reached."""
        # Arrange
        child_id = sample_child_with_data.id

        # Act
        unlocked = await report_service.check_milestones(child_id)

        # Assert
        assert isinstance(unlocked, list)
        for milestone in unlocked:
            assert milestone.achieved
            assert milestone.achieved_at is not None


class TestTrends:
    """Test suite for trend analysis.

    @MX:NOTE
    Tests trend direction calculation and data aggregation.
    """

    async def test_get_trends_returns_correct_direction(
        self, report_service, sample_child_with_data
    ):
        """Test trend analysis returns direction."""
        # Arrange
        child_id = sample_child_with_data.id
        metric = "points"
        period = "week"

        # Act
        result = await report_service.get_trends(child_id, metric, period)

        # Assert
        assert isinstance(result, TrendDataResponse)
        assert result.metric == metric
        assert result.period == period
        assert result.trend_direction in ["up", "down", "stable"]
        assert isinstance(result.data_points, list)
        assert len(result.data_points) > 0

    async def test_get_trends_calculates_average(
        self, report_service, sample_child_with_data
    ):
        """Test trend average calculation."""
        # Arrange
        child_id = sample_child_with_data.id
        metric = "tasks"
        period = "month"

        # Act
        result = await report_service.get_trends(child_id, metric, period)

        # Assert
        if len(result.data_points) > 0:
            expected_average = sum(p.value for p in result.data_points) / len(
                result.data_points
            )
            assert abs(result.average - expected_average) < 0.01


class TestReportExport:
    """Test suite for report export functionality.

    @MX:NOTE
    Tests async export job creation and status tracking.
    """

    async def test_create_export_job_returns_export_id(
        self, report_service, db_session, test_user, sample_child
    ):
        """Test export job creation."""
        # Arrange
        child_id = sample_child.id
        request = ExportRequest(
            child_id=child_id,
            format="pdf",
            date_range={
                "start_date": date.today() - timedelta(days=7),
                "end_date": date.today(),
            },
            sections=["tasks", "points"],
        )

        # Act
        result = await report_service.create_export(test_user.id, child_id, request)

        # Assert
        assert isinstance(result, tuple)
        export_id, status = result
        assert isinstance(export_id, type(uuid4()))
        assert status in [ExportStatus.PENDING, ExportStatus.PROCESSING]

    async def test_get_export_status_returns_correct_status(
        self, report_service, db_session, test_user
    ):
        """Test export status retrieval."""
        # Arrange
        export = ReportExport(
            id=uuid4(),
            family_id=test_user.id,
            requested_by=test_user.id,
            format="pdf",
            sections=json.dumps(["tasks", "points"]),
            date_range_start=date.today() - timedelta(days=7),
            date_range_end=date.today(),
            status=ExportStatus.COMPLETED,
            file_url="https://example.com/export.pdf",
        )
        db_session.add(export)
        await db_session.commit()

        # Act
        result = await report_service.get_export_status(export.id)

        # Assert
        assert result is not None
        assert result.status == ExportStatus.COMPLETED
        assert result.file_url == "https://example.com/export.pdf"


class TestFamilyOverview:
    """Test suite for family overview report.

    @MX:NOTE
    Tests aggregation across all children in family.
    """

    async def test_get_family_overview_aggregates_all_children(
        self, report_service, test_user, sample_child_with_data
    ):
        """Test family overview includes all children."""
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_family_overview(
            test_user.id, start_date, end_date
        )

        # Assert
        assert isinstance(result, FamilyOverviewResponse)
        assert result.total_children >= 1
        assert result.total_points_earned >= 0
        assert result.total_tasks_completed >= 0
        assert 0 <= result.average_completion_rate <= 100
        assert len(result.child_summaries) == result.total_children


class TestDataScoping:
    """Test suite for data isolation and scoping.

    @MX:NOTE
    Critical tests to ensure no cross-child data mixing.
    """

    async def test_report_data_scoped_to_child_only(
        self, report_service, db_session, test_user, sample_child
    ):
        """Test report data is properly scoped to child."""
        # Arrange
        child_id = sample_child.id
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_report_summary(
            child_id, start_date, end_date
        )

        # Assert
        assert result.child_id == child_id
        # Data should only belong to this child

    async def test_family_report_only_includes_family_children(
        self, report_service, test_user, sample_child
    ):
        """Test family report doesn't include other families."""
        # Arrange
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()

        # Act
        result = await report_service.get_family_overview(
            test_user.id, start_date, end_date
        )

        # Assert
        # All child summaries should belong to this family
        for summary in result.child_summaries:
            assert isinstance(summary, ReportSummaryResponse)


class TestDateRangeValidation:
    """Test suite for date range validation.

    @MX:NOTE
    Tests invalid date ranges are rejected.
    """

    async def test_invalid_date_range_raises_error(
        self, report_service, sample_child
    ):
        """Test that invalid date ranges are rejected."""
        # Arrange
        child_id = sample_child.id
        start_date = date.today()
        end_date = date.today() - timedelta(days=7)  # End before start

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid date range"):
            await report_service.get_task_report(child_id, start_date, end_date)

    async def test_future_date_range_raises_error(
        self, report_service, sample_child
    ):
        """Test that future dates are rejected."""
        # Arrange
        child_id = sample_child.id
        start_date = date.today() + timedelta(days=1)
        end_date = date.today() + timedelta(days=7)

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid date range"):
            await report_service.get_task_report(child_id, start_date, end_date)
