import logging
from unittest.mock import patch, MagicMock
from backend.services.mock_occupancy_service import seed_mock_occupancy_data

logging.basicConfig(level=logging.INFO)
db = MagicMock()
with patch('backend.services.mock_occupancy_service.OccupancyRepository') as mock_repo_class:
    mock_repo = mock_repo_class.return_value
    mock_repo.get_latest_occupancy.return_value = None
    # Run 5 times to see the range
    for _ in range(5):
        occ, sec = seed_mock_occupancy_data(db, 'FAC-002', 30)
        print(f'Events: {sec}')
