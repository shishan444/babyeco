"""Report service for analytics and data aggregation.

@MX:ANCHOR
Service layer for report generation and aggregation.
Provides cached access to computed statistics.
"""

import json
from datetime import date, datetime, timedelta
from uuid import UUID
from typing import Any

from sqlalchemy import and_, case, cast, Date, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.child_profile import ChildProfile
from app.models.point import PointTransaction, TransactionType
from app.models.report import (
    Achievement,
    AchievementCategory,
    ExportStatus,
    Milestone,
    MilestoneType,
    ReportExport,
)
from app.models.task import Task, TaskCategory, TaskCompletion, TaskStatus
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
    TrendPoint,
)

# Achievement definitions
ACHIEVEMENT_DEFINITIONS = [
    {
        "key": "streak-3",
        "name": "3-Day Streak",
        "description": "Complete tasks for 3 days in a row",
        "icon": "🔥",
        "category": AchievementCategory.STREAK,
        "criteria": {"type": "streak", "value": 3},
    },
    {
        "key": "streak-7",
        "name": "Week Warrior",
        "description": "Complete tasks for 7 days in a row",
        "icon": "⚡",
        "category": AchievementCategory.STREAK,
        "criteria": {"type": "streak", "value": 7},
    },
    {
        "key": "points-100",
        "name": "Century Club",
        "description": "Earn 100 points total",
        "icon": "💯",
        "category": AchievementCategory.POINTS,
        "criteria": {"type": "total_points", "value": 100},
    },
    {
        "key": "points-500",
        "name": "Point Collector",
        "description": "Earn 500 points total",
        "icon": "💎",
        "category": AchievementCategory.POINTS,
        "criteria": {"type": "total_points", "value": 500},
    },
    {
        "key": "tasks-25",
        "name": "Task Starter",
        "description": "Complete 25 tasks",
        "icon": "⭐",
        "category": AchievementCategory.TASKS,
        "criteria": {"type": "tasks_completed", "value": 25},
    },
    {
        "key": "tasks-100",
        "name": "Task Champion",
        "description": "Complete 100 tasks",
        "icon": "🏆",
        "category": AchievementCategory.TASKS,
        "criteria": {"type": "tasks_completed", "value": 100},
    },
]

# Milestone definitions
MILESTONE_DEFINITIONS = [
    {
        "title": "First Steps",
        "description": "Complete your first task",
        "type": MilestoneType.TASKS,
        "threshold": 1,
    },
    {
        "title": "Task Master",
        "description": "Complete 50 tasks",
        "type": MilestoneType.TASKS,
        "threshold": 50,
    },
    {
        "title": "Point Earner",
        "description": "Earn 100 points",
        "type": MilestoneType.POINTS,
        "threshold": 100,
    },
    {
        "title": "Point Hero",
        "description": "Earn 1000 points",
        "type": MilestoneType.POINTS,
        "threshold": 1000,
    },
    {
        "title": "Streak Starter",
        "description": "3-day streak",
        "type": MilestoneType.STREAK,
        "threshold": 3,
    },
    {
        "title": "Streak Legend",
        "description": "30-day streak",
        "type": MilestoneType.STREAK,
        "threshold": 30,
    },
]


class ReportService:
    """Service for generating reports and analytics.

    @MX:ANCHOR
    Central service for all report generation.
    Uses caching for performance optimization.
    """

    def __init__(self, db: AsyncSession, cache: Any):
        """Initialize report service.

        Args:
            db: Database session
            cache: Redis cache client
        """
        self.db = db
        self.cache = cache

    async def get_growth_dashboard(
        self, child_id: UUID
    ) -> GrowthDashboardResponse:
        """Get growth dashboard data for child.

        @MX:ANCHOR
        Primary dashboard endpoint. Aggregates all stats.
        Results cached for 5 minutes.

        Args:
            child_id: Child profile ID

        Returns:
            Growth dashboard data
        """
        # Check cache
        cache_key = f"growth:{child_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return GrowthDashboardResponse(**json.loads(cached))

        # Get child profile
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.id == child_id)
        )
        child = result.scalar_one_or_none()
        if not child:
            raise ValueError(f"Child not found: {child_id}")

        # Calculate stats
        total_points = child.total_points_earned or 0
        current_streak = child.current_streak or 0
        longest_streak = child.longest_streak or 0

        # Task completion stats
        one_week_ago = date.today() - timedelta(days=7)
        one_month_ago = date.today() - timedelta(days=30)

        # Total completed tasks
        total_completed_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.child_id == child_id)
            .where(Task.status == TaskStatus.APPROVED)
        )
        tasks_completed_total = total_completed_result.scalar() or 0

        # This week completed
        weekly_completed_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.child_id == child_id)
            .where(Task.status == TaskStatus.APPROVED)
            .where(Task.approved_at >= one_week_ago)
        )
        tasks_completed_this_week = weekly_completed_result.scalar() or 0

        # Weekly completion rate
        weekly_total_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.child_id == child_id)
            .where(Task.created_at >= one_week_ago)
        )
        weekly_total = weekly_total_result.scalar() or 0
        completion_rate_weekly = (
            (tasks_completed_this_week / weekly_total * 100) if weekly_total > 0 else 0
        )

        # Monthly completion rate
        monthly_total_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.child_id == child_id)
            .where(Task.created_at >= one_month_ago)
        )
        monthly_total = monthly_total_result.scalar() or 0
        monthly_completed_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.child_id == child_id)
            .where(Task.status == TaskStatus.APPROVED)
            .where(Task.created_at >= one_month_ago)
        )
        monthly_completed = monthly_completed_result.scalar() or 0
        completion_rate_monthly = (
            (monthly_completed / monthly_total * 100) if monthly_total > 0 else 0
        )

        # Achievement stats
        achievements = await self._get_achievement_stats(child_id)

        # Get milestones
        milestones = await self._get_recent_milestones(child_id)

        result = GrowthDashboardResponse(
            total_points_earned=total_points,
            current_streak=current_streak,
            longest_streak=longest_streak,
            tasks_completed_total=tasks_completed_total,
            tasks_completed_this_week=tasks_completed_this_week,
            completion_rate_weekly=completion_rate_weekly,
            completion_rate_monthly=completion_rate_monthly,
            achievements_unlocked=achievements["unlocked"],
            achievements_total=achievements["total"],
            milestones=milestones,
        )

        # Cache for 5 minutes
        await self.cache.setex(
            cache_key, 300, result.model_dump_json()
        )

        return result

    async def get_task_report(
        self, child_id: UUID, start_date: date, end_date: date
    ) -> TaskReportResponse:
        """Get task performance report.

        @MX:NOTE
        Groups by category and aggregates by day.

        Args:
            child_id: Child profile ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Task report with category and daily breakdown
        """
        # Validate date range
        if start_date > end_date:
            raise ValueError("Invalid date range: start_date after end_date")
        if end_date > date.today():
            raise ValueError("Invalid date range: future dates not allowed")

        # Get tasks in range
        result = await self.db.execute(
            select(Task)
            .where(Task.child_id == child_id)
            .where(Task.created_at >= start_date)
            .where(Task.created_at <= end_date)
            .options(selectinload(Task.child))
        )
        tasks = result.scalars().all()

        # Group by category
        by_category: dict[str, dict[str, Any]] = {}
        for task in tasks:
            category = task.category.value
            if category not in by_category:
                by_category[category] = {"total": 0, "completed": 0, "points": 0}
            by_category[category]["total"] += 1
            if task.status == TaskStatus.APPROVED:
                by_category[category]["completed"] += 1
                by_category[category]["points"] += task.points

        # Convert to response format
        category_stats: dict[str, CategoryStats] = {}
        for category, stats in by_category.items():
            total = stats["total"]
            completed = stats["completed"]
            rate = (completed / total * 100) if total > 0 else 0
            category_stats[category] = CategoryStats(
                total=total, completed=completed, rate=rate
            )

        # Group by day
        by_day = await self._aggregate_tasks_by_day(child_id, start_date, end_date)

        # Calculate trend
        completion_trend = self._calculate_completion_trend(by_day)

        return TaskReportResponse(
            by_category=category_stats,
            by_day=by_day,
            completion_trend=completion_trend,
        )

    async def get_point_report(
        self, child_id: UUID, start_date: date, end_date: date
    ) -> PointReportResponse:
        """Get point activity report.

        Args:
            child_id: Child profile ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Point report with source breakdown
        """
        # Validate date range
        if start_date > end_date:
            raise ValueError("Invalid date range: start_date after end_date")
        if end_date > date.today():
            raise ValueError("Invalid date range: future dates not allowed")

        # Get transactions in range
        result = await self.db.execute(
            select(PointTransaction)
            .where(PointTransaction.child_id == child_id)
            .where(cast(PointTransaction.created_at, Date) >= start_date)
            .where(cast(PointTransaction.created_at, Date) <= end_date)
            .order_by(PointTransaction.created_at)
        )
        transactions = result.scalars().all()

        # Calculate totals
        total_earned = sum(
            t.amount for t in transactions if t.type == TransactionType.EARN
        )
        total_spent = sum(
            t.amount for t in transactions if t.type == TransactionType.SPEND
        )

        # Breakdown by source
        by_source: dict[str, int] = {}
        for transaction in transactions:
            if transaction.type == TransactionType.EARN:
                source = transaction.source_type or "unknown"
                by_source[source] = by_source.get(source, 0) + transaction.amount

        # Daily breakdown
        daily_breakdown = await self._aggregate_points_by_day(
            child_id, start_date, end_date
        )

        return PointReportResponse(
            total_earned=total_earned,
            total_spent=total_spent,
            by_source=by_source,
            daily_breakdown=daily_breakdown,
        )

    async def get_report_summary(
        self, child_id: UUID, start_date: date, end_date: date
    ) -> ReportSummaryResponse:
        """Get report summary for parent dashboard.

        Args:
            child_id: Child profile ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Report summary
        """
        # Get child
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.id == child_id)
        )
        child = result.scalar_one_or_none()
        if not child:
            raise ValueError(f"Child not found: {child_id}")

        # Get task stats
        task_result = await self.db.execute(
            select(Task).where(Task.child_id == child_id)
            .where(Task.created_at >= start_date)
            .where(Task.created_at <= end_date)
        )
        tasks = task_result.scalars().all()
        tasks_total = len(tasks)
        tasks_completed = sum(1 for t in tasks if t.status == TaskStatus.APPROVED)
        completion_rate = (
            (tasks_completed / tasks_total * 100) if tasks_total > 0 else 0
        )

        # Get point stats
        point_result = await self.db.execute(
            select(PointTransaction)
            .where(PointTransaction.child_id == child_id)
            .where(cast(PointTransaction.created_at, Date) >= start_date)
            .where(cast(PointTransaction.created_at, Date) <= end_date)
        )
        transactions = point_result.scalars().all()
        points_earned = sum(
            t.amount for t in transactions if t.type == TransactionType.EARN
        )
        points_spent = sum(
            t.amount for t in transactions if t.type == TransactionType.SPEND
        )

        # Most completed category
        category_counts: dict[str, int] = {}
        for task in tasks:
            if task.status == TaskStatus.APPROVED:
                category = task.category.value
                category_counts[category] = category_counts.get(category, 0) + 1

        most_completed_category = (
            max(category_counts, key=category_counts.get) if category_counts else None
        )

        return ReportSummaryResponse(
            child_id=child_id,
            child_name=child.name,
            date_range={"start_date": start_date, "end_date": end_date},
            tasks_completed=tasks_completed,
            tasks_total=tasks_total,
            completion_rate=completion_rate,
            points_earned=points_earned,
            points_spent=points_spent,
            current_streak=child.current_streak or 0,
            most_completed_category=most_completed_category,
        )

    async def get_achievements(self, child_id: UUID) -> list[AchievementResponse]:
        """Get all achievements for child.

        Args:
            child_id: Child profile ID

        Returns:
            List of achievements
        """
        result = await self.db.execute(
            select(Achievement).where(Achievement.child_id == child_id)
        )
        achievements = result.scalars().all()

        return [
            AchievementResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                icon=a.icon,
                category=a.category.value,
                unlocked=a.unlocked,
                unlocked_at=a.unlocked_at,
                progress=a.progress,
            )
            for a in achievements
        ]

    async def check_achievements(
        self, child_id: UUID
    ) -> list[AchievementResponse]:
        """Check and unlock newly earned achievements.

        Args:
            child_id: Child profile ID

        Returns:
            List of newly unlocked achievements
        """
        # Get current stats
        stats = await self._get_all_stats(child_id)
        unlocked = []

        for definition in ACHIEVEMENT_DEFINITIONS:
            # Check if achievement exists
            result = await self.db.execute(
                select(Achievement).where(Achievement.child_id == child_id)
                .where(Achievement.achievement_key == definition["key"])
            )
            achievement = result.scalar_one_or_none()

            # Calculate progress
            progress = self._calculate_achievement_progress(definition, stats)

            if achievement is None:
                # Create new achievement
                achievement = Achievement(
                    id=uuid4(),
                    child_id=child_id,
                    achievement_key=definition["key"],
                    name=definition["name"],
                    description=definition["description"],
                    icon=definition["icon"],
                    category=definition["category"],
                    unlocked=progress >= 100,
                    unlocked_at=datetime.utcnow() if progress >= 100 else None,
                    progress=progress,
                )
                self.db.add(achievement)
                await self.db.flush()

                if achievement.unlocked:
                    unlocked.append(achievement)
            elif not achievement.unlocked and progress >= 100:
                # Unlock existing achievement
                achievement.unlocked = True
                achievement.unlocked_at = datetime.utcnow()
                achievement.progress = 100
                await self.db.flush()
                unlocked.append(achievement)
            else:
                # Update progress
                achievement.progress = progress

        await self.db.commit()

        return [
            AchievementResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                icon=a.icon,
                category=a.category.value,
                unlocked=a.unlocked,
                unlocked_at=a.unlocked_at,
                progress=a.progress,
            )
            for a in unlocked
        ]

    async def get_milestones(self, child_id: UUID) -> list[MilestoneResponse]:
        """Get all milestones for child.

        Args:
            child_id: Child profile ID

        Returns:
            List of milestones
        """
        result = await self.db.execute(
            select(Milestone).where(Milestone.child_id == child_id)
        )
        milestones = result.scalars().all()

        return [
            MilestoneResponse(
                id=m.id,
                title=m.title,
                description=m.description,
                type=m.type.value,
                threshold=m.threshold,
                achieved=m.achieved,
                achieved_at=m.achieved_at,
            )
            for m in milestones
        ]

    async def check_milestones(self, child_id: UUID) -> list[MilestoneResponse]:
        """Check and unlock newly reached milestones.

        Args:
            child_id: Child profile ID

        Returns:
            List of newly reached milestones
        """
        # Get current stats
        stats = await self._get_all_stats(child_id)
        unlocked = []

        for definition in MILESTONE_DEFINITIONS:
            # Check if milestone exists
            result = await self.db.execute(
                select(Milestone).where(Milestone.child_id == child_id)
                .where(Milestone.title == definition["title"])
            )
            milestone = result.scalar_one_or_none()

            # Check if threshold reached
            current_value = stats.get(definition["type"].value, 0)
            achieved = current_value >= definition["threshold"]

            if milestone is None:
                # Create new milestone
                milestone = Milestone(
                    id=uuid4(),
                    child_id=child_id,
                    title=definition["title"],
                    description=definition.get("description"),
                    type=definition["type"],
                    threshold=definition["threshold"],
                    achieved=achieved,
                    achieved_at=datetime.utcnow() if achieved else None,
                )
                self.db.add(milestone)
                await self.db.flush()

                if milestone.achieved:
                    unlocked.append(milestone)
            elif not milestone.achieved and achieved:
                # Unlock existing milestone
                milestone.achieved = True
                milestone.achieved_at = datetime.utcnow()
                await self.db.flush()
                unlocked.append(milestone)

        await self.db.commit()

        return [
            MilestoneResponse(
                id=m.id,
                title=m.title,
                description=m.description,
                type=m.type.value,
                threshold=m.threshold,
                achieved=m.achieved,
                achieved_at=m.achieved_at,
            )
            for m in unlocked
        ]

    async def get_trends(
        self, child_id: UUID, metric: str, period: str
    ) -> TrendDataResponse:
        """Get trend analysis for metric.

        Args:
            child_id: Child profile ID
            metric: Metric to analyze (points, tasks, streak)
            period: Time period (week, month, quarter)

        Returns:
            Trend data with direction
        """
        # Determine date range
        if period == "week":
            days = 7
        elif period == "month":
            days = 30
        else:  # quarter
            days = 90

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        data_points: list[TrendPoint] = []

        if metric == "points":
            # Get daily point earnings
            daily_stats = await self._aggregate_points_by_day(
                child_id, start_date, end_date
            )
            data_points = [
                TrendPoint(date=d.date, value=d.earned) for d in daily_stats
            ]
        elif metric == "tasks":
            # Get daily task completions
            daily_stats = await self._aggregate_tasks_by_day(
                child_id, start_date, end_date
            )
            data_points = [
                TrendPoint(date=d.date, value=d.completed) for d in daily_stats
            ]
        else:
            # Default: empty trend
            data_points = []

        # Calculate average
        average = sum(p.value for p in data_points) / len(data_points) if data_points else 0

        # Determine trend direction
        if len(data_points) < 2:
            trend_direction = "stable"
        else:
            recent_avg = sum(p.value for p in data_points[-3:]) / min(3, len(data_points))
            if recent_avg > average * 1.1:
                trend_direction = "up"
            elif recent_avg < average * 0.9:
                trend_direction = "down"
            else:
                trend_direction = "stable"

        return TrendDataResponse(
            metric=metric,
            period=period,
            data_points=data_points,
            average=average,
            trend_direction=trend_direction,
        )

    async def create_export(
        self, user_id: UUID, child_id: UUID | None, request: ExportRequest
    ) -> tuple[UUID, ExportStatus]:
        """Create export job for report generation.

        Args:
            user_id: User ID creating export
            child_id: Child ID (None for family report)
            request: Export request details

        Returns:
            Tuple of export ID and status
        """
        export = ReportExport(
            id=uuid4(),
            family_id=user_id,
            requested_by=user_id,
            child_id=child_id,
            format=request.format,
            sections=json.dumps(request.sections),
            date_range_start=request.date_range["start_date"],
            date_range_end=request.date_range["end_date"],
            status=ExportStatus.PENDING,
        )
        self.db.add(export)
        await self.db.commit()

        return export.id, export.status

    async def get_export_status(self, export_id: UUID) -> ReportExport | None:
        """Get export job status.

        Args:
            export_id: Export job ID

        Returns:
            Export record or None
        """
        result = await self.db.execute(
            select(ReportExport).where(ReportExport.id == export_id)
        )
        return result.scalar_one_or_none()

    async def get_family_overview(
        self, family_id: UUID, start_date: date, end_date: date
    ) -> FamilyOverviewResponse:
        """Get family overview report.

        Args:
            family_id: Family (parent user) ID
            start_date: Report start date
            end_date: Report end date

        Returns:
            Family overview with per-child summaries
        """
        # Get all children
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.parent_id == family_id)
            .where(ChildProfile.status == "active")
        )
        children = result.scalars().all()

        if not children:
            return FamilyOverviewResponse(
                total_children=0,
                total_points_earned=0,
                total_tasks_completed=0,
                average_completion_rate=0,
                child_summaries=[],
            )

        # Generate per-child summaries
        child_summaries = []
        total_points = 0
        total_tasks = 0
        completion_rates = []

        for child in children:
            summary = await self.get_report_summary(child.id, start_date, end_date)
            child_summaries.append(summary)
            total_points += summary.points_earned
            total_tasks += summary.tasks_completed
            completion_rates.append(summary.completion_rate)

        # Calculate average completion rate
        average_completion_rate = (
            sum(completion_rates) / len(completion_rates) if completion_rates else 0
        )

        return FamilyOverviewResponse(
            total_children=len(children),
            total_points_earned=total_points,
            total_tasks_completed=total_tasks,
            average_completion_rate=average_completion_rate,
            child_summaries=child_summaries,
        )

    # Private helper methods

    async def _get_achievement_stats(self, child_id: UUID) -> dict[str, int]:
        """Get achievement statistics for child.

        Args:
            child_id: Child profile ID

        Returns:
            Dict with unlocked and total counts
        """
        result = await self.db.execute(
            select(Achievement).where(Achievement.child_id == child_id)
        )
        achievements = result.scalars().all()

        return {
            "unlocked": sum(1 for a in achievements if a.unlocked),
            "total": len(achievements) if achievements else len(ACHIEVEMENT_DEFINITIONS),
        }

    async def _get_recent_milestones(self, child_id: UUID) -> list[MilestoneBrief]:
        """Get recent milestones for child.

        Args:
            child_id: Child profile ID

        Returns:
            List of milestone briefs
        """
        result = await self.db.execute(
            select(Milestone).where(Milestone.child_id == child_id)
            .order_by(Milestone.created_at.desc())
            .limit(5)
        )
        milestones = result.scalars().all()

        return [
            MilestoneBrief(
                id=m.id,
                title=m.title,
                type=m.type.value,
                threshold=m.threshold,
                achieved=m.achieved,
                achieved_at=m.achieved_at,
            )
            for m in milestones
        ]

    async def _aggregate_tasks_by_day(
        self, child_id: UUID, start_date: date, end_date: date
    ) -> list[DailyStats]:
        """Aggregate task statistics by day.

        Args:
            child_id: Child profile ID
            start_date: Start date
            end_date: End date

        Returns:
            List of daily statistics
        """
        result = await self.db.execute(
            select(
                cast(Task.created_at, Date).label("date"),
                func.count(Task.id).label("total"),
                func.sum(
                    case(
                        (Task.status == TaskStatus.APPROVED, 1),
                        else_=0,
                    )
                ).label("completed"),
                func.sum(
                    case(
                        (Task.status == TaskStatus.APPROVED, Task.points),
                        else_=0,
                    )
                ).label("points_earned"),
            )
            .where(Task.child_id == child_id)
            .where(Task.created_at >= start_date)
            .where(Task.created_at <= end_date)
            .group_by(cast(Task.created_at, Date))
            .order_by(cast(Task.created_at, Date))
        )
        rows = result.all()

        return [
            DailyStats(
                date=row.date,
                total=row.total or 0,
                completed=row.completed or 0,
                points_earned=row.points_earned or 0,
            )
            for row in rows
        ]

    async def _aggregate_points_by_day(
        self, child_id: UUID, start_date: date, end_date: date
    ) -> list[DailyPointStats]:
        """Aggregate point statistics by day.

        Args:
            child_id: Child profile ID
            start_date: Start date
            end_date: End date

        Returns:
            List of daily point statistics
        """
        result = await self.db.execute(
            select(
                cast(PointTransaction.created_at, Date).label("date"),
                func.sum(
                    case(
                        (PointTransaction.type == TransactionType.EARN,
                         PointTransaction.amount),
                        else_=0,
                    )
                ).label("earned"),
                func.sum(
                    case(
                        (PointTransaction.type == TransactionType.SPEND,
                         PointTransaction.amount),
                        else_=0,
                    )
                ).label("spent"),
            )
            .where(PointTransaction.child_id == child_id)
            .where(cast(PointTransaction.created_at, Date) >= start_date)
            .where(cast(PointTransaction.created_at, Date) <= end_date)
            .group_by(cast(PointTransaction.created_at, Date))
            .order_by(cast(PointTransaction.created_at, Date))
        )
        rows = result.all()

        # Calculate running balance
        balance = 0
        daily_stats = []
        for row in rows:
            balance += (row.earned or 0) - (row.spent or 0)
            daily_stats.append(
                DailyPointStats(
                    date=row.date,
                    earned=row.earned or 0,
                    spent=row.spent or 0,
                    balance=balance,
                )
            )

        return daily_stats

    def _calculate_completion_trend(self, by_day: list[DailyStats]) -> list[TrendPoint]:
        """Calculate completion rate trend.

        Args:
            by_day: Daily statistics

        Returns:
            List of trend points
        """
        return [
            TrendPoint(
                date=d.date,
                value=(d.completed / d.total * 100) if d.total > 0 else 0,
            )
            for d in by_day
        ]

    async def _get_all_stats(self, child_id: UUID) -> dict[str, int]:
        """Get all statistics for achievement/milestone checking.

        Args:
            child_id: Child profile ID

        Returns:
            Dict with all stats
        """
        # Get child profile
        result = await self.db.execute(
            select(ChildProfile).where(ChildProfile.id == child_id)
        )
        child = result.scalar_one_or_none()
        if not child:
            return {}

        # Get completed tasks count
        tasks_result = await self.db.execute(
            select(func.count(Task.id))
            .where(Task.child_id == child_id)
            .where(Task.status == TaskStatus.APPROVED)
        )
        tasks_completed = tasks_result.scalar() or 0

        return {
            "total_points": child.total_points_earned or 0,
            "tasks_completed": tasks_completed,
            "streak": child.current_streak or 0,
            "points": child.total_points_earned or 0,
        }

    def _calculate_achievement_progress(
        self, definition: dict[str, Any], stats: dict[str, int]
    ) -> int:
        """Calculate achievement progress percentage.

        Args:
            definition: Achievement definition
            stats: Current stats

        Returns:
            Progress percentage (0-100)
        """
        criteria = definition["criteria"]
        criteria_type = criteria["type"]
        target_value = criteria["value"]

        current_value = stats.get(criteria_type, 0)

        if target_value <= 0:
            return 100 if current_value > 0 else 0

        progress = min(100, int((current_value / target_value) * 100))
        return progress
