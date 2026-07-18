"""
Integration tests for the full pipeline.

Uses SQLite in-memory database to avoid filesystem state.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.engine import Base
from src.services.pipeline import run_pipeline
from src.models.models import PipelineRun, StandardizedRecord


@pytest.fixture
def db():
    """Create an in-memory SQLite DB for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


SAMPLE_FOLDER = str(Path(__file__).parent.parent / "sample-data")


class TestFullPipeline:
    def test_pipeline_runs_successfully(self, db):
        result = run_pipeline(db, folder=SAMPLE_FOLDER)
        assert result["status"] == "completed"
        assert result["total_files"] == 5
        assert result["processed"] == 5
        assert result["failed"] == 0

    def test_pipeline_creates_records(self, db):
        run_pipeline(db, folder=SAMPLE_FOLDER)
        count = db.query(StandardizedRecord).count()
        assert count > 0

    def test_pipeline_run_record(self, db):
        run_pipeline(db, folder=SAMPLE_FOLDER)
        run = db.query(PipelineRun).first()
        assert run is not None
        assert run.status == "completed"
        assert run.duration_seconds is not None
        assert run.duration_seconds > 0

    def test_duplicate_prevention(self, db):
        """Running the pipeline twice should not double insert the same records (idempotence)."""
        res1 = run_pipeline(db, folder=SAMPLE_FOLDER)
        count1 = db.query(StandardizedRecord).count()

        res2 = run_pipeline(db, folder=SAMPLE_FOLDER)
        count2 = db.query(StandardizedRecord).count()

        assert count2 == count1
        assert res2["total_records_inserted"] == 0
        assert res2["total_records_skipped"] > 0
