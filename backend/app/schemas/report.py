"""Report and analytics response schemas.

@MX:NOTE
Pydantic models for API responses and requests.
"""

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DateRange(BaseModel):
    """Date range for reports."""

    start_date: date
    end_date: date


class MilestoneBrief(BaseModel):
    """Brief milestone information for dashboard."""

    id: UUID
    title: str
    type: str
    threshold: int
    achieved: bool
    achieved_at: datetime | None = None


class GrowthDashboardResponse(BaseModel):
    """Growth dashboard data for child app.

    @MX:ANCHOR
    Primary dashboard response with comprehensive stats.
    """

    total_points_earned: int = Field(..., description="Total points earned all time")
    current_streak: int = Field(..., description="Current consecutive days", ge=0)
    longest_streak: int = Field(..., description="Longest streak achieved", ge=0)
    tasks_completed_total: int = Field(..., description="Total tasks completed", ge=0)
    tasks_completed_this_week: int = Field(..., description="Tasks completed this week", ge=0)
    completion_rate_weekly: float = Field(
        ..., description="Weekly completion rate", ge=0, le=100
    )
    completion_rate_monthly: float = Field(
        ..., description="Monthly completion rate", ge=0, le=100
    )
    achievements_unlocked: int = Field(..., description="Unlocked achievements count", ge=0)
    achievements_total: int = Field(..., description="Total achievements count", ge=0)
    milestones: list[MilestoneBrief] = Field(
        default_factory=list, description="Recent milestones"
    )


class CategoryStats(BaseModel):
    """Task statistics by category."""

    total: int = Field(..., description="Total tasks in category", ge=0)
    completed: int = Field(..., description="Completed tasks", ge=0)
    rate: float = Field(..., description="Completion rate", ge=0, le=100)


class DailyStats(BaseModel):
    """Daily task statistics."""

    date: date
    total: int = Field(..., ge=0)
    completed: int = Field(..., ge=0)
    points_earned: int = Field(..., ge=0)


class TrendPoint(BaseModel):
    """Single trend data point."""

    date: date
    value: float


class TaskReportResponse(BaseModel):
    """Task performance report response."""

    by_category: dict[str, CategoryStats] = Field(
        ..., description="Task stats grouped by category"
    )
    by_day: list[DailyStats] = Field(..., description="Daily task breakdown")
    completion_trend: list[TrendPoint] = Field(
        ..., description="Completion rate trend over time"
    )


class DailyPointStats(BaseModel):
    """Daily point statistics."""

    date: date
    earned: int = Field(..., ge=0)
    spent: int = Field(..., ge=0)
    balance: int = Field(..., ge=0)


class PointReportResponse(BaseModel):
    """Point activity report response."""

    total_earned: int = Field(..., description="Total points earned", ge=0)
    total_spent: int = Field(..., description="Total points spent", ge=0)
    by_source: dict[str, int] = Field(
        ..., description="Points by source (task, exchange, etc.)"
    )
    daily_breakdown: list[DailyPointStats] = Field(
        ..., description="Daily point breakdown"
    )


class ReportSummaryResponse(BaseModel):
    """Report summary for parent dashboard.

    @MX:ANCHOR
    High-level summary for quick overview.
    """

    child_id: UUID
    child_name: str
    date_range: DateRange
    tasks_completed: int = Field(..., ge=0)
    tasks_total: int = Field(..., ge=0)
    completion_rate: float = Field(..., ge=0, le=100)
    points_earned: int = Field(..., ge=0)
    points_spent: int = Field(..., ge=0)
    current_streak: int = Field(..., ge=0)
    most_completed_category: str | None = None


class TrendDataResponse(BaseModel):
    """Trend analysis response."""

    metric: str = Field(..., description="points, tasks, streak, etc.")
    period: str = Field(..., description="week, month, quarter")
    data_points: list[TrendPoint] = Field(..., description="Trend data points")
    average: float = Field(..., description="Average value")
    trend_direction: str = Field(..., description="up, down, stable")


class AchievementResponse(BaseModel):
    """Achievement detail response."""

    id: UUID
    name: str
    description: str
    icon: str
    category: str
    unlocked: bool
    unlocked_at: datetime | None = None
    progress: int = Field(..., description="Progress percentage 0-100", ge=0, le=100)


class MilestoneResponse(BaseModel):
    """Milestone detail response."""

    id: UUID
    title: str
    description: str | None = None
    type: str
    threshold: int
    achieved: bool
    achieved_at: datetime | None = None


class ExportRequest(BaseModel):
    """Report export request."""

    child_id: UUID | None = Field(None, description="Child ID, null for family report")
    format: str = Field(..., description="pdf or csv")
    date_range: DateRange
    sections: list[str] = Field(
        default_factory=list,
        description="Report sections to include",
    )


class ExportResponse(BaseModel):
    """Report export response."""

    export_id: UUID
    status: str
    download_url: str | None = None
    error_message: str | None = None


class FamilyOverviewResponse(BaseModel):
    """Family overview response."""

    total_children: int = Field(..., ge=0)
    total_points_earned: int = Field(..., ge=0)
    total_tasks_completed: int = Field(..., ge=0)
    average_completion_rate: float = Field(..., ge=0, le=100)
    child_summaries: list[ReportSummaryResponse] = Field(
        default_factory=list, description="Per-child summaries"
    )
