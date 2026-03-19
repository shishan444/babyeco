# SPEC-BE-REPORT-001: Report & Analytics API

## Overview

Implement the reporting and analytics API for tracking child progress, task completion, and point activity.

**Business Context**: Reports help parents understand their children's progress and habits. This API provides data for growth dashboards, trend analysis, and exportable reports.

**Target Users**:
- Primary: Parent app (reports dashboard)
- Secondary: Child app (growth dashboard)

---

## Technical Constraints

### Framework and Versions
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- PostgreSQL 15+
- Redis for caching aggregated data

### Dependencies
- SPEC-BE-AUTH-001 (Authentication API)
- SPEC-BE-TASK-001 (Task System)
- SPEC-BE-POINT-001 (Point System)

---

## Functional Requirements (EARS Format)

### Ubiquitous Requirements

**UR-001**: The system shall aggregate data per child for accurate reporting.

```
Given a report request
When processed
Then data is scoped to the specific child
And cross-child data is never mixed
```

**UR-002**: The system shall support configurable date ranges.

```
Given a report request with date range
When processed
Then only data within the range is included
And invalid ranges are rejected
```

**UR-003**: The system shall cache frequently accessed aggregates.

```
Given a common report query
When requested
Then cached result may be returned
And cache is invalidated on data changes
```

### Event-Driven Requirements

**EDR-001**: When a weekly report is requested, the system shall compile task and point summaries.

```
Given a weekly report request
When processed
Then task completion counts are aggregated
And point earnings are totaled
And comparison to previous week is calculated
```

**EDR-002**: When a growth dashboard loads, the system shall return streak and achievement data.

```
Given a growth dashboard request
When processed
Then current streak is calculated
And achievements are checked for unlocks
And milestones are identified
```

**EDR-003**: When an export is requested, the system shall generate downloadable report.

```
Given an export request
When processed
Then data is formatted as PDF/CSV
And file is generated and stored
And download link is returned
```

### State-Driven Requirements

**SDR-001**: While aggregating large date ranges, the system shall paginate or stream results.

```
Given a request spanning many months
When processed
Then data is processed in chunks
And response time remains acceptable
```

**SDR-002**: While data is being aggregated, the system shall show loading state.

```
Given a complex aggregation query
When processing
Then async processing is initiated
And progress may be tracked
```

### Optional Requirements

**OR-001**: The system MAY support comparison between siblings.

```
Given multiple children in family
When comparison report requested
Then anonymized comparison data is provided
And no direct ranking is shown
```

**OR-002**: The system MAY support scheduled report delivery.

```
Given scheduled report configuration
When schedule triggers
Then report is generated
And delivered via configured channel (email)
```

### Unwanted Behavior Requirements

**UBR-001**: The system shall NOT expose other families' data.

```
Given any report request
When processed
Then only requesting family's data is included
```

---

## Technical Solution

### API Endpoints

```yaml
# Child Growth Dashboard
GET /api/v1/child/reports/growth
  Headers: Authorization: Bearer {token}
  Response: GrowthDashboard

GET /api/v1/child/reports/achievements
  Headers: Authorization: Bearer {token}
  Response: [Achievement]

GET /api/v1/child/reports/milestones
  Headers: Authorization: Bearer {token}
  Response: [Milestone]

# Parent Reports
GET /api/v1/children/{child_id}/reports/summary
  Headers: Authorization: Bearer {token}
  Query: start_date, end_date
  Response: ReportSummary

GET /api/v1/children/{child_id}/reports/tasks
  Headers: Authorization: Bearer {token}
  Query: start_date, end_date, group_by?
  Response: TaskReport

GET /api/v1/children/{child_id}/reports/points
  Headers: Authorization: Bearer {token}
  Query: start_date, end_date
  Response: PointReport

GET /api/v1/children/{child_id}/reports/trends
  Headers: Authorization: Bearer {token}
  Query: metric, period
  Response: TrendData

# Family Reports
GET /api/v1/family/reports/overview
  Headers: Authorization: Bearer {token}
  Query: start_date, end_date
  Response: FamilyOverview

# Export
POST /api/v1/reports/export
  Headers: Authorization: Bearer {token}
  Request: { child_id?, format, date_range, sections }
  Response: { export_id, status }

GET /api/v1/reports/export/{export_id}
  Headers: Authorization: Bearer {token}
  Response: { status, download_url? }
```

### Data Models

```python
# models/report.py
class CachedAggregate(Base):
    """Cached aggregated data for performance"""
    __tablename__ = "cached_aggregates"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    child_id: Mapped[UUID] = mapped_column(ForeignKey("children.id"))
    aggregate_type: Mapped[str]  # daily_tasks, weekly_points, etc.
    period_start: Mapped[date]
    period_end: Mapped[date]
    data: Mapped[dict] = mapped_column(JSON)
    computed_at: Mapped[datetime] = mapped_column(default=utcnow)

class ReportExport(Base):
    __tablename__ = "report_exports"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    family_id: Mapped[UUID] = mapped_column(ForeignKey("families.id"))
    requested_by: Mapped[UUID] = mapped_column(ForeignKey("parents.id"))
    format: Mapped[str]  # pdf, csv
    sections: Mapped[list[str]]
    date_range_start: Mapped[date]
    date_range_end: Mapped[date]
    status: Mapped[str]  # pending, processing, completed, failed
    file_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(default=utcnow)
    completed_at: Mapped[datetime | None]
```

### Response Schemas

```python
# schemas/report.py
class GrowthDashboardResponse(BaseModel):
    total_points_earned: int
    current_streak: int
    longest_streak: int
    tasks_completed_total: int
    tasks_completed_this_week: int
    completion_rate_weekly: float
    completion_rate_monthly: float
    achievements_unlocked: int
    achievements_total: int
    milestones: list[MilestoneBrief]

class ReportSummaryResponse(BaseModel):
    child_id: UUID
    child_name: str
    date_range: DateRange
    tasks_completed: int
    tasks_total: int
    completion_rate: float
    points_earned: int
    points_spent: int
    current_streak: int
    most_completed_category: str | None

class TaskReportResponse(BaseModel):
    by_category: dict[str, CategoryStats]
    by_day: list[DailyStats]
    completion_trend: TrendPoint

class PointReportResponse(BaseModel):
    total_earned: int
    total_spent: int
    by_source: dict[str, int]  # task, exchange, etc.
    daily_breakdown: list[DailyPointStats]

class TrendDataResponse(BaseModel):
    metric: str
    period: str
    data_points: list[TrendPoint]
    average: float
    trend_direction: str  # up, down, stable

class AchievementResponse(BaseModel):
    id: UUID
    name: str
    description: str
    icon: str
    category: str
    unlocked: bool
    unlocked_at: datetime | None
    progress: float  # 0-100

class MilestoneResponse(BaseModel):
    id: UUID
    title: str
    type: str  # points, tasks, streak
    threshold: int
    achieved_at: datetime | None
    achieved: bool
```

### Service Implementation

```python
# services/report_service.py
class ReportService:
    def __init__(self, db: AsyncSession, cache: Redis):
        self.db = db
        self.cache = cache

    async def get_growth_dashboard(
        self, child_id: UUID
    ) -> GrowthDashboardResponse:
        # Check cache first
        cache_key = f"growth:{child_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return GrowthDashboardResponse.parse_raw(cached)

        # Aggregate data
        total_points = await self._get_total_points_earned(child_id)
        streak_data = await self._get_streak_data(child_id)
        task_stats = await self._get_task_completion_stats(child_id)
        achievements = await self._get_achievement_progress(child_id)
        milestones = await self._get_milestones(child_id)

        result = GrowthDashboardResponse(
            total_points_earned=total_points,
            current_streak=streak_data["current"],
            longest_streak=streak_data["longest"],
            tasks_completed_total=task_stats["total"],
            tasks_completed_this_week=task_stats["this_week"],
            completion_rate_weekly=task_stats["weekly_rate"],
            completion_rate_monthly=task_stats["monthly_rate"],
            achievements_unlocked=achievements["unlocked"],
            achievements_total=achievements["total"],
            milestones=milestones,
        )

        # Cache for 5 minutes
        await self.cache.setex(cache_key, 300, result.json())
        return result

    async def get_task_report(
        self, child_id: UUID, start_date: date, end_date: date
    ) -> TaskReportResponse:
        # Get task instances in range
        instances = await self.db.execute(
            select(TaskInstance)
            .where(TaskInstance.child_id == child_id)
            .where(TaskInstance.date >= start_date)
            .where(TaskInstance.date <= end_date)
        )

        # Group by category
        by_category = {}
        for instance in instances:
            task = await self._get_task(instance.task_id)
            category = task.type
            if category not in by_category:
                by_category[category] = {
                    "total": 0, "completed": 0, "rate": 0
                }
            by_category[category]["total"] += 1
            if instance.status in ["approved"]:
                by_category[category]["completed"] += 1

        for cat in by_category:
            total = by_category[cat]["total"]
            completed = by_category[cat]["completed"]
            by_category[cat]["rate"] = completed / total if total > 0 else 0

        # Group by day
        by_day = await self._aggregate_by_day(instances, start_date, end_date)

        return TaskReportResponse(
            by_category=by_category,
            by_day=by_day,
            completion_trend=self._calculate_trend(by_day),
        )

    async def _get_streak_data(self, child_id: UUID) -> dict:
        """Calculate current and longest streak"""
        # Get consecutive days with completed tasks
        result = await self.db.execute(
            select(TaskInstance.date, TaskInstance.status)
            .where(TaskInstance.child_id == child_id)
            .where(TaskInstance.status == "approved")
            .distinct(TaskInstance.date)
            .order_by(TaskInstance.date.desc())
            .limit(365)  # Look back up to a year
        )
        dates = [row.date for row in result.all()]

        if not dates:
            return {"current": 0, "longest": 0}

        current_streak = 0
        longest_streak = 0
        temp_streak = 1

        for i in range(len(dates) - 1):
            if (dates[i] - dates[i + 1]).days == 1:
                temp_streak += 1
            else:
                longest_streak = max(longest_streak, temp_streak)
                if i == 0:
                    break  # Current streak ended
                temp_streak = 1

        longest_streak = max(longest_streak, temp_streak)
        current_streak = temp_streak if dates[0] == date.today() else 0

        return {"current": current_streak, "longest": longest_streak}

    async def check_achievements(self, child_id: UUID) -> list[Achievement]:
        """Check and unlock any newly earned achievements"""
        unlocked = []
        stats = await self._get_all_stats(child_id)

        for achievement_def in ACHIEVEMENT_DEFINITIONS:
            if await self._check_achievement_criteria(achievement_def, stats):
                # Unlock achievement
                unlocked_achievement = await self._unlock_achievement(
                    child_id, achievement_def
                )
                if unlocked_achievement:
                    unlocked.append(unlocked_achievement)

        return unlocked
```

### Achievement Definitions

```python
# constants/achievements.py
ACHIEVEMENT_DEFINITIONS = [
    # Streak achievements
    AchievementDef(
        id="streak-3",
        name="3-Day Streak",
        description="Complete tasks for 3 days in a row",
        icon="🔥",
        category="streak",
        criteria={"type": "streak", "value": 3},
    ),
    AchievementDef(
        id="streak-7",
        name="Week Warrior",
        description="Complete tasks for 7 days in a row",
        icon="⚡",
        category="streak",
        criteria={"type": "streak", "value": 7},
    ),

    # Point achievements
    AchievementDef(
        id="points-100",
        name="Century Club",
        description="Earn 100 points total",
        icon="💯",
        category="points",
        criteria={"type": "total_points", "value": 100},
    ),
    AchievementDef(
        id="points-500",
        name="Point Collector",
        description="Earn 500 points total",
        icon="💎",
        category="points",
        criteria={"type": "total_points", "value": 500},
    ),

    # Task achievements
    AchievementDef(
        id="tasks-25",
        name="Task Starter",
        description="Complete 25 tasks",
        icon="⭐",
        category="tasks",
        criteria={"type": "tasks_completed", "value": 25},
    ),
    AchievementDef(
        id="tasks-100",
        name="Task Champion",
        description="Complete 100 tasks",
        icon="🏆",
        category="tasks",
        criteria={"type": "tasks_completed", "value": 100},
    ),
]
```

---

## Dependencies

| Dependency | Type | Status | Notes |
|-----------|------|--------|-------|
| SPEC-BE-AUTH-001 | Upstream | Pending | Auth context |
| SPEC-BE-TASK-001 | Upstream | Pending | Task data |
| SPEC-BE-POINT-001 | Upstream | Pending | Point data |
| Redis | Cache | Required | Aggregation caching |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Query performance | Medium | Medium | Caching, materialized views |
| Data consistency | Low | Low | Transaction isolation |
| Export file size | Low | Low | Pagination, streaming |

---

## Acceptance Criteria

### Growth Dashboard
- [ ] Given child request, when dashboard loads, then all stats accurate
- [ ] Given streak data, when calculated, then current and longest correct
- [ ] Given achievements, when checked, then unlocked accurately

### Reports
- [ ] Given date range, when report requested, then correct data returned
- [ ] Given group by, when specified, then data grouped correctly
- [ ] Given trends, when calculated, then direction accurate

### Exports
- [ ] Given export request, when processed, then file generated
- [ ] Given PDF format, when exported, then formatted correctly
- [ ] Given CSV format, when exported, then parseable

---

## Related SPECs

| SPEC ID | Relationship | Description |
|---------|-------------|-------------|
| SPEC-FE-GROWTH-001 | Upstream | Child growth dashboard |
| SPEC-FE-PARENT-001 | Upstream | Parent reports |
| SPEC-BE-TASK-001 | Upstream | Task data source |
| SPEC-BE-POINT-001 | Upstream | Point data source |

---

**Version**: 1.0
**Created**: 2024-03-19
**Status**: Draft
