"""Report and analytics API endpoints.

@MX:NOTE
Provides endpoints for child growth dashboard and parent reports.
All endpoints require authentication.
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps.auth import get_current_child, get_current_parent
from app.core.database import get_db
from app.models.child_profile import ChildProfile
from app.models.user import User
from app.schemas.report import (
    AchievementResponse,
    ExportRequest,
    ExportResponse,
    FamilyOverviewResponse,
    GrowthDashboardResponse,
    MilestoneResponse,
    PointReportResponse,
    ReportSummaryResponse,
    TaskReportResponse,
    TrendDataResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


@router.get("/growth", response_model=GrowthDashboardResponse)
async def get_growth_dashboard(
    current_child: ChildProfile = Depends(get_current_child),
    db: AsyncSession = Depends(get_db),
):
    """Get growth dashboard for child.

    @MX:ANCHOR
    Primary child dashboard endpoint with comprehensive stats.
    Results cached for 5 minutes.

    Args:
        current_child: Authenticated child profile
        db: Database session

    Returns:
        Growth dashboard data
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    try:
        result = await service.get_growth_dashboard(current_child.id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/achievements", response_model=list[AchievementResponse])
async def get_achievements(
    current_child: ChildProfile = Depends(get_current_child),
    db: AsyncSession = Depends(get_db),
):
    """Get all achievements for child.

    Args:
        current_child: Authenticated child profile
        db: Database session

    Returns:
        List of achievements
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_achievements(current_child.id)


@router.post("/achievements/check", response_model=list[AchievementResponse])
async def check_achievements(
    current_child: ChildProfile = Depends(get_current_child),
    db: AsyncSession = Depends(get_db),
):
    """Check and unlock new achievements.

    @MX:NOTE
    Triggers achievement evaluation and unlocks newly earned achievements.

    Args:
        current_child: Authenticated child profile
        db: Database session

    Returns:
        List of newly unlocked achievements
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.check_achievements(current_child.id)


@router.get("/milestones", response_model=list[MilestoneResponse])
async def get_milestones(
    current_child: ChildProfile = Depends(get_current_child),
    db: AsyncSession = Depends(get_db),
):
    """Get all milestones for child.

    Args:
        current_child: Authenticated child profile
        db: Database session

    Returns:
        List of milestones
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_milestones(current_child.id)


@router.post("/milestones/check", response_model=list[MilestoneResponse])
async def check_milestones(
    current_child: ChildProfile = Depends(get_current_child),
    db: AsyncSession = Depends(get_db),
):
    """Check and unlock new milestones.

    Args:
        current_child: Authenticated child profile
        db: Database session

    Returns:
        List of newly unlocked milestones
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.check_milestones(current_child.id)


# Parent report endpoints
@router.get(
    "/children/{child_id}/summary",
    response_model=ReportSummaryResponse,
)
async def get_child_summary(
    child_id: UUID,
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get report summary for child.

    Args:
        child_id: Child profile ID
        start_date: Report start date
        end_date: Report end date
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Report summary
    """
    from app.core.cache import get_cache

    # Verify child belongs to parent
    child = await _verify_child_ownership(db, child_id, current_parent.id)

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_report_summary(child.id, start_date, end_date)


@router.get(
    "/children/{child_id}/tasks",
    response_model=TaskReportResponse,
)
async def get_child_task_report(
    child_id: UUID,
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get task performance report for child.

    Args:
        child_id: Child profile ID
        start_date: Report start date
        end_date: Report end date
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Task report
    """
    from app.core.cache import get_cache

    # Verify child belongs to parent
    child = await _verify_child_ownership(db, child_id, current_parent.id)

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_task_report(child.id, start_date, end_date)


@router.get(
    "/children/{child_id}/points",
    response_model=PointReportResponse,
)
async def get_child_point_report(
    child_id: UUID,
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get point activity report for child.

    Args:
        child_id: Child profile ID
        start_date: Report start date
        end_date: Report end date
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Point report
    """
    from app.core.cache import get_cache

    # Verify child belongs to parent
    child = await _verify_child_ownership(db, child_id, current_parent.id)

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_point_report(child.id, start_date, end_date)


@router.get(
    "/children/{child_id}/trends",
    response_model=TrendDataResponse,
)
async def get_child_trends(
    child_id: UUID,
    metric: str = Query(..., description="Metric: points, tasks, streak"),
    period: str = Query(..., description="Period: week, month, quarter"),
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get trend analysis for child.

    Args:
        child_id: Child profile ID
        metric: Metric to analyze
        period: Time period
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Trend data
    """
    from app.core.cache import get_cache

    # Verify child belongs to parent
    child = await _verify_child_ownership(db, child_id, current_parent.id)

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_trends(child.id, metric, period)


@router.get(
    "/family/overview",
    response_model=FamilyOverviewResponse,
)
async def get_family_overview(
    start_date: date = Query(..., description="Report start date"),
    end_date: date = Query(..., description="Report end date"),
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get family overview report.

    Args:
        start_date: Report start date
        end_date: Report end date
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Family overview
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    return await service.get_family_overview(current_parent.id, start_date, end_date)


@router.post("/export", response_model=ExportResponse)
async def create_export(
    request: ExportRequest,
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Create export job for report generation.

    Args:
        request: Export request details
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Export job details
    """
    from app.core.cache import get_cache

    # Verify child ownership if specified
    if request.child_id:
        await _verify_child_ownership(db, request.child_id, current_parent.id)

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    export_id, export_status = await service.create_export(
        current_parent.id, request.child_id, request
    )

    return ExportResponse(
        export_id=export_id,
        status=export_status.value,
    )


@router.get("/export/{export_id}", response_model=ExportResponse)
async def get_export_status(
    export_id: UUID,
    current_parent: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get export job status.

    Args:
        export_id: Export job ID
        current_parent: Authenticated parent user
        db: Database session

    Returns:
        Export status
    """
    from app.core.cache import get_cache

    cache = await get_cache()
    service = ReportService(db=db, cache=cache)

    export = await service.get_export_status(export_id)

    if not export:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Export not found",
        )

    # Verify ownership
    if export.family_id != current_parent.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return ExportResponse(
        export_id=export.id,
        status=export.status.value,
        download_url=export.file_url,
        error_message=export.error_message,
    )


# Helper functions
async def _verify_child_ownership(
    db: AsyncSession, child_id: UUID, parent_id: UUID
) -> ChildProfile:
    """Verify child belongs to parent.

    @MX:NOTE
    Critical security check to prevent cross-family data access.

    Args:
        db: Database session
        child_id: Child profile ID
        parent_id: Parent user ID

    Returns:
        Child profile if ownership verified

    Raises:
        HTTPException: If child not found or not owned by parent
    """
    from sqlalchemy import select

    result = await db.execute(
        select(ChildProfile).where(ChildProfile.id == child_id)
        .where(ChildProfile.parent_id == parent_id)
    )
    child = result.scalar_one_or_none()

    if not child:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Child not found",
        )

    return child
