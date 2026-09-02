import logging
from datetime import datetime

import pandas as pd
from sklearn.ensemble import IsolationForest
from backend.agents.occupancy.config import OCCUPANCY_RULES

OVERCROWDING_THRESHOLD_PCT = OCCUPANCY_RULES['OVERCROWDING_THRESHOLD_PCT']
WORKING_HOURS = OCCUPANCY_RULES['WORKING_HOURS']
SECURITY_ACTIVE_STATUSES = OCCUPANCY_RULES['SECURITY_ACTIVE_STATUSES']

class OccupancyAnalysisResult(tuple):
    """Compatibility wrapper: tuple unpacking for agents and dict-style access for legacy tests."""

    def __new__(cls, anomalies, state_summary):
        obj = super().__new__(cls, (anomalies, state_summary))
        obj._payload = {
            "anomalies": anomalies,
            "summary": state_summary,
            "metrics": {
                "intelligence_source": "Rules Only",
                "overcrowding_threshold": OVERCROWDING_THRESHOLD_PCT,
                "active_security_threats": state_summary.get("active_security_threats", 0),
            },
        }
        return obj

    def __getitem__(self, key):
        if isinstance(key, str):
            return self._payload[key]
        return super().__getitem__(key)

    @property
    def metrics(self):
        return self._payload["metrics"]

    @property
    def anomalies(self):
        return self._payload["anomalies"]

    @property
    def summary(self):
        return self._payload["summary"]


class OccupancyAnalyzer:
    def __init__(self):
        self.overcrowding_limit = OVERCROWDING_THRESHOLD_PCT
        self.work_start = WORKING_HOURS['start']
        self.work_end = WORKING_HOURS['end']

    def _load_models(self):
        """Compatibility hook for tests and callers expecting model initialization."""
        return None

    def analyze_facility_state(self, df_occ, df_sec):
        if df_occ is None:
            df_occ = pd.DataFrame()
        elif not isinstance(df_occ, pd.DataFrame):
            df_occ = pd.DataFrame(df_occ)

        if df_sec is None:
            df_sec = pd.DataFrame()
        elif not isinstance(df_sec, pd.DataFrame):
            df_sec = pd.DataFrame(df_sec)

        anomalies = []
        state_summary = {'overcrowded_zones': [], 'active_security_threats': 0}
        if not df_occ.empty:
            for _, row in df_occ.iterrows():
                if row.get('max_capacity', 0) > 0:
                    utilization = row['occupancy_count'] / row['max_capacity']
                    if utilization >= self.overcrowding_limit:
                        state_summary['overcrowded_zones'].append(row['zone_id'])
                        anomalies.append({'type': 'Overcrowding Detected', 'severity': 'High', 'message': 'Exceeds capacity.'})
        if not df_sec.empty:
            df_sec = df_sec.copy()
            df_sec['severity_norm'] = df_sec['severity'].astype(str).str.strip().str.lower()
            df_sec['status_norm'] = df_sec['status'].astype(str).str.strip().str.lower()
            sev_map = {'low': 1, 'medium': 2, 'high': 3}
            df_sec['severity_num'] = df_sec['severity_norm'].map(sev_map).fillna(1)
            state_summary['active_security_threats'] = int(df_sec['status_norm'].isin(SECURITY_ACTIVE_STATUSES).sum())
            state_summary['threat_level'] = "High" if (df_sec['severity_norm'] == OCCUPANCY_RULES['SECURITY_HIGH_SEVERITY']).any() else "Low"
            det_indices = set()
            for idx, row in df_sec.iterrows():
                if row['severity_norm'] == OCCUPANCY_RULES['SECURITY_HIGH_SEVERITY'] or (row['severity_norm'] in ['medium', 'high'] and row['status_norm'] in SECURITY_ACTIVE_STATUSES):
                    anomalies.append({'type': 'Security Breach', 'severity': row['severity'], 'message': 'Deterministic breach.'})
                    det_indices.add(idx)
            if len(df_sec) > 5:
                df_sec['hour'] = pd.to_datetime(df_sec['event_time']).dt.hour
                feat = df_sec[['hour', 'severity_num', 'zone_level', 'recent_failed_attempts']].fillna(0)
                preds = IsolationForest(contamination=0.1, random_state=42).fit_predict(feat)
                for i, idx in enumerate(df_sec.index):
                    if preds[i] == -1 and idx not in det_indices:
                        event = df_sec.loc[idx]
                        anomalies.append({'type': 'Active Security Breach', 'severity': event['severity'], 'message': 'Unusual pattern.'})

        unique_anomalies = []
        seen = set()
        for anomaly in anomalies:
            key = (anomaly.get('type'), anomaly.get('severity'), anomaly.get('message'), anomaly.get('timestamp'))
            if key not in seen:
                seen.add(key)
                unique_anomalies.append(anomaly)
        return OccupancyAnalysisResult(unique_anomalies, state_summary)
