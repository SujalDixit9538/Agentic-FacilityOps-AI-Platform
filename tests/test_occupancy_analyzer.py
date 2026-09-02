from unittest.mock import patch
from datetime import datetime
from backend.agents.occupancy.analyzer import OccupancyAnalyzer

a = OccupancyAnalyzer()
a._load_models()

fixed_now = datetime(2026, 6, 16, 9, 0, 0)  # Tuesday, 9AM — matches original test intent

with patch('backend.agents.occupancy.analyzer.datetime') as mock_dt:
    mock_dt.utcnow.return_value = fixed_now
    mock_dt.fromisoformat = datetime.fromisoformat

    test_records = [
        {'room': 'Main Lobby', 'occupancy_count': 130, 'timestamp': '2026-06-16T09:00:00'},
        {'room': 'Cafeteria', 'occupancy_count': 160, 'timestamp': '2026-06-16T09:00:00'},
        {'room': 'Meeting Room A', 'occupancy_count': 15, 'timestamp': '2026-06-16T09:00:00'},
        {'room': 'Server Room', 'occupancy_count': 1, 'timestamp': '2026-06-16T09:00:00'},
    ]
    result = a.analyze_facility_state(test_records, [])
    print('intelligence_source:', result['metrics']['intelligence_source'])
    print('anomalies:', result['anomalies'])
