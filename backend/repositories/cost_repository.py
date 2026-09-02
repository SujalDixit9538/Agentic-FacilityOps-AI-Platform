from sqlalchemy.orm import Session
import json
from backend.database.models.cost import CostRecord, CostAnalysisReport, CostRecommendation
from backend.schemas.cost import CostRecordBase
import uuid
import hashlib

class CostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_costs_by_facility(self, facility_id: str, limit: int = 100):
        return self.db.query(CostRecord).filter(
            CostRecord.facility_id == facility_id
        ).order_by(CostRecord.incurred_date.desc()).limit(limit).all()

    def get_costs_by_category(self, facility_id: str, category: str, limit: int = 100):
        return self.db.query(CostRecord).filter(
            CostRecord.facility_id == facility_id,
            CostRecord.category == category
        ).order_by(CostRecord.incurred_date.desc()).limit(limit).all()

    def create_cost_record(self, data: CostRecordBase):
        db_record = CostRecord(
            record_id=f"CST-{uuid.uuid4().hex[:6].upper()}",
            **data.model_dump()
        )
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    def get_analysis_report_by_fingerprint(self, facility_id: str, fingerprint: str):
        return self.db.query(CostAnalysisReport).filter(
            CostAnalysisReport.facility_id == facility_id,
            CostAnalysisReport.payload.like(f'%' + fingerprint + '%'),
        ).order_by(CostAnalysisReport.generated_at.desc()).first()

    def create_analysis_report(self, facility_id: str, analysis: dict, fingerprint: str | None = None):
        payload = json.dumps(analysis, default=str, sort_keys=True)
        fingerprint = fingerprint or hashlib.sha256(payload.encode()).hexdigest()
        report = CostAnalysisReport(
            report_id=f"CAR-{uuid.uuid4().hex[:10].upper()}",
            facility_id=facility_id,
            intelligence_source=analysis.get("analysis", {}).get("metrics", {}).get("intelligence_source", "Unknown"),
            financial_status=analysis.get("analysis", {}).get("financial_status", "Unknown"),
            payload=json.dumps({"fingerprint": fingerprint, "analysis": analysis}, default=str, sort_keys=True),
        )
        self.db.add(report)
        self.db.flush()
        for recommendation in analysis.get("recommendations", []):
            self.db.add(CostRecommendation(
                recommendation_id=f"CRA-{uuid.uuid4().hex[:10].upper()}",
                report_id=report.report_id,
                facility_id=facility_id,
                action=recommendation.get("action", "Review facility costs."),
                trigger=recommendation.get("trigger"),
                priority=recommendation.get("priority", "Medium"),
                estimated_savings_usd=recommendation.get("estimated_savings_usd"),
                status=recommendation.get("status", "Proposed"),
            ))
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_analysis_reports(self, facility_id: str, limit: int = 20):
        return self.db.query(CostAnalysisReport).filter(
            CostAnalysisReport.facility_id == facility_id
        ).order_by(CostAnalysisReport.generated_at.desc()).limit(limit).all()

    def update_recommendation(self, recommendation_id: str, status: str, realized_savings_usd=None, outcome_notes=None):
        recommendation = self.db.query(CostRecommendation).filter(
            CostRecommendation.recommendation_id == recommendation_id
        ).first()
        if not recommendation:
            return None
        recommendation.status = status
        recommendation.realized_savings_usd = realized_savings_usd
        recommendation.outcome_notes = outcome_notes
        self.db.commit()
        self.db.refresh(recommendation)
        return recommendation