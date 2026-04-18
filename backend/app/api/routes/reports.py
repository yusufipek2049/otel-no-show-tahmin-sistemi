from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.reports import BenchmarkReportResponse
from app.services.reports import ReportsService

router = APIRouter()


@router.get("/benchmark", response_model=BenchmarkReportResponse)
def get_benchmark_report(db: Session = Depends(get_db)) -> BenchmarkReportResponse:
    return ReportsService(db).get_benchmark_report()
