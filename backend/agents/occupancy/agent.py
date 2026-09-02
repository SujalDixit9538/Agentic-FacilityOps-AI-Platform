import logging
import pandas as pd
from sqlalchemy.orm import Session
from backend.repositories.occupancy_repository import OccupancyRepository
from backend.agents.occupancy.analyzer import OccupancyAnalyzer
from backend.agents.occupancy.actions import OccupancyActionEngine
from backend.services.alert_service import generate_alert

logger = logging.getLogger(__name__)


class OccupancyAgent:
    """
    Controller for Occupancy & Security Intelligence.
    Orchestrates zone/capacity lookup, cross-correlation analysis, and
    platform alert generation — same alert_service pattern as every
    other agent (Maintenance, Security).
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = OccupancyRepository(db)
        self.analyzer = OccupancyAnalyzer()
        self.action_engine = OccupancyActionEngine()

    def analyze_facility(self, facility_id: str):
        logger.info(f"OccupancyAgent initiating facility-wide analysis for {facility_id}")

        # 1. Fetch zones (real per-facility capacity/type data)
        zones = self.repository.get_zones_for_facility(facility_id)
        zone_map = {z.zone_id: z for z in zones}

        # 2. Fetch latest occupancy reading per zone — source-agnostic
        #    (sensor and CNN readings are both written to occupancy_records,
        #    so this naturally handles tabular-only, CNN-only, or hybrid facilities)
        latest_records = self.repository.get_latest_occupancy_by_zone(facility_id)
        joined_data = []
        for rec in latest_records:
            z = zone_map.get(rec.zone_id)
            if z:
                joined_data.append({
                    "zone_id": z.zone_id,
                    "zone_name": z.zone_name,
                    "zone_type": z.zone_type,
                    "max_capacity": z.max_capacity,
                    "occupancy_count": rec.occupancy_count,
                    "source": rec.source,
                    "timestamp": rec.timestamp,
                })
        df_occ = pd.DataFrame(joined_data)

        # 3. Fetch recent security events
        sec_events = self.repository.get_security_events(facility_id, limit=50)
        sec_dicts = [{
            "event_type": e.event_type,
            "severity": e.severity,
            "status": e.status,
            "event_time": e.event_time,
            "zone_level": e.zone_level,
            "recent_failed_attempts": e.recent_failed_attempts,
        } for e in sec_events]
        df_sec = pd.DataFrame(sec_dicts)

        # 4. Run cross-correlation analysis
        anomalies, state_summary = self.analyzer.analyze_facility_state(df_occ, df_sec)

        # 5. Process anomalies into standard alerts + recommendations
        alerts_generated = []
        recommendations = []

        if anomalies:
            recommendations = self.action_engine.generate_recommendations(anomalies)
            for anomaly in anomalies:
                alert = generate_alert(
                    source_agent="OccupancyAgent",
                    alert_type=anomaly["type"],
                    severity=anomaly["severity"],
                    message=anomaly["message"],
                )
                alerts_generated.append(alert)
        else:
            recommendations = self.action_engine.generate_recommendations([])

        logger.info(
            f"OccupancyAgent completed analysis. Generated {len(alerts_generated)} alerts "
            f"and {len(recommendations)} recommendations."
        )

        return {
            "facility_id": facility_id,
            "status": "Critical" if anomalies else "Normal",
            "anomalies_detected": len(anomalies),
            "summary": state_summary,
            "alerts": alerts_generated,
            "recommendations": recommendations,
            "provenance": {"source": "OccupancyAnalyzer", "security_reasoning": "rules_based", "facility_id": facility_id},
            "freshness": {"status": "available" if joined_data or sec_dicts else "unavailable"},
            "degraded": not bool(joined_data or sec_dicts),
            "quality_flags": ([] if joined_data or sec_dicts else ["occupancy_and_security_data_unavailable"]),
        }