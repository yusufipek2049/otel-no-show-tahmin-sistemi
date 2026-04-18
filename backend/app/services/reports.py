from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories.artifact_views import ArtifactViewRepository
from app.repositories.reports import ReportsRepository
from app.schemas.reports import BenchmarkReportResponse


class ReportsService:
    def __init__(self, db: Session) -> None:
        self.repository = ReportsRepository(db)
        self.artifact_repository = ArtifactViewRepository()

    def get_benchmark_report(self) -> BenchmarkReportResponse:
        if self.artifact_repository.exists():
            return BenchmarkReportResponse.model_validate(self.artifact_repository.get_benchmark_report())
        return BenchmarkReportResponse.model_validate(self.repository.get_bootstrap_benchmark_report())
