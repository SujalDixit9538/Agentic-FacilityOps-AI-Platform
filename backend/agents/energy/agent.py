import logging

from sqlalchemy.orm import Session

from backend.agents.energy.actions import EnergyActionEngine
from backend.agents.energy.analyzer import EnergyAnalyzer
from backend.repositories.energy_repository import EnergyRepository

logger = logging.getLogger(__name__)


class EnergyAgent:
    """Orchestrate energy telemetry retrieval, analysis, and recommendations."""

    def __init__(self, db: Session):
        self.repository = EnergyRepository(db)
        self.analyzer = EnergyAnalyzer()
        self.action_engine = EnergyActionEngine()

    def analyze_facility(self, facility_id: str, days: int = 7):
        """Analyze recent facility energy data without inventing missing telemetry."""
        if days < 1:
            raise ValueError("days must be greater than zero")

        records = self.repository.get_records_by_facility(
            facility_id,
            limit=days * 24,
        )
        records_dict = [
            {
                "timestamp": record.timestamp.isoformat() if record.timestamp else None,
                "energy_kwh": record.energy_kwh,
                "peak_demand_kw": record.peak_demand_kw,
            }
            for record in records
        ]

        analysis = self.analyzer.analyze_consumption(records_dict)
        anomalies = analysis.get("anomalies", [])
        recommendations = self.action_engine.generate_recommendations(anomalies)

        metrics = analysis.setdefault("metrics", {})
        metrics["records_evaluated"] = len(records)
        metrics["intelligence_source"] = analysis.get("intelligence_source", "Rules Only")

        if not records:
            analysis["degraded"] = True
            analysis["degradation_reason"] = "energy_telemetry_unavailable"
            # Avoid presenting a generic recommendation as if it were evidence-based.
            recommendations = []

        return {
            "facility_id": facility_id,
            "alerts": anomalies,
            "recommendations": recommendations,
            "analysis": analysis,
            "provenance": {
                "source": "EnergyAgent",
                "facility_id": facility_id,
                "records_evaluated": len(records),
            },
            "freshness": {"status": "available" if records else "unavailable"},
            "degraded": bool(analysis.get("degraded", analysis.get("status") != "success")),
            "quality_flags": (
                [analysis["degradation_reason"]]
                if analysis.get("degradation_reason")
                else []
            ),
        }
