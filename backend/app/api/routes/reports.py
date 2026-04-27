from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reports import (
    ActionEffectivenessResponse,
    BenchmarkReportResponse,
    DimensionBreakdownRow,
    OperationsSummaryResponse,
    TrendPoint,
)
from app.services.reports import ReportsService

router = APIRouter()


@router.get("/benchmark", response_model=BenchmarkReportResponse)
def get_benchmark_report(db: Session = Depends(get_db)) -> BenchmarkReportResponse:
    return ReportsService(db).get_benchmark_report()


@router.get("/operations-summary", response_model=OperationsSummaryResponse)
def get_operations_summary(db: Session = Depends(get_db)) -> OperationsSummaryResponse:
    return ReportsService(db).get_operations_summary()


@router.get("/no-show-trends", response_model=list[TrendPoint])
def get_no_show_trends(db: Session = Depends(get_db)) -> list[TrendPoint]:
    return ReportsService(db).get_no_show_trends()


@router.get("/channel-breakdown", response_model=list[DimensionBreakdownRow])
def get_channel_breakdown(db: Session = Depends(get_db)) -> list[DimensionBreakdownRow]:
    return ReportsService(db).get_channel_breakdown()


@router.get("/segment-breakdown", response_model=list[DimensionBreakdownRow])
def get_segment_breakdown(db: Session = Depends(get_db)) -> list[DimensionBreakdownRow]:
    return ReportsService(db).get_segment_breakdown()


@router.get("/action-effectiveness", response_model=ActionEffectivenessResponse)
def get_action_effectiveness(db: Session = Depends(get_db)) -> ActionEffectivenessResponse:
    return ReportsService(db).get_action_effectiveness()
