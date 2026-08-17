import random
from backend.database.models.occupancy import OccupancyZone

# Facility types that get a dedicated server_room zone
_SERVER_ROOM_TYPES = {"Office", "Technology/science", "Healthcare"}

def generate_zones_for_facility(facility_id: str, facility_type: str,
                                  total_area_sqft: float, total_floors: int) -> list[OccupancyZone]:
    """Deterministic-ish, type-aware zone generator. Mirrors the correlated
    seeder pattern used for Security so zone data has realistic variance
    instead of flat mock values."""
    zones = []
    per_floor_area = total_area_sqft / max(total_floors, 1)
    zone_seq = 0

    for floor in range(1, total_floors + 1):
        zone_seq += 1
        # Main working area on every floor
        office_area = per_floor_area * 0.6
        zones.append(OccupancyZone(
            zone_id=f"Z-{facility_id}-{zone_seq:03d}",
            facility_id=facility_id, floor=floor,
            zone_name=f"Floor {floor} Work Area",
            zone_type="office_floor",
            max_capacity=max(int(office_area / 100), 5),  # ~1 person / 100 sqft
            area_sqft=round(office_area, 1)
        ))

        # 1-2 meeting rooms per floor
        for _ in range(random.randint(1, 2)):
            zone_seq += 1
            cap = random.choice([8, 12, 16, 20])
            zones.append(OccupancyZone(
                zone_id=f"Z-{facility_id}-{zone_seq:03d}",
                facility_id=facility_id, floor=floor,
                zone_name=f"Meeting Room {zone_seq}",
                zone_type="meeting_room",
                max_capacity=cap,
                area_sqft=round(cap * 15, 1)
            ))

        # Ground floor: lobby + parking
        if floor == 1:
            zone_seq += 1
            common_area = per_floor_area * 0.15
            zones.append(OccupancyZone(
                zone_id=f"Z-{facility_id}-{zone_seq:03d}",
                facility_id=facility_id, floor=floor,
                zone_name="Main Lobby",
                zone_type="common_area",
                max_capacity=max(int(common_area / 30), 10),
                area_sqft=round(common_area, 1)
            ))
            zone_seq += 1
            parking_area = per_floor_area * 0.25
            zones.append(OccupancyZone(
                zone_id=f"Z-{facility_id}-{zone_seq:03d}",
                facility_id=facility_id, floor=floor,
                zone_name="Parking Area",
                zone_type="parking",
                max_capacity=max(int(parking_area / 300), 5),
                area_sqft=round(parking_area, 1)
            ))

            if facility_type in _SERVER_ROOM_TYPES:
                zone_seq += 1
                zones.append(OccupancyZone(
                    zone_id=f"Z-{facility_id}-{zone_seq:03d}",
                    facility_id=facility_id, floor=floor,
                    zone_name="Server Room",
                    zone_type="server_room",
                    max_capacity=5,
                    area_sqft=200.0
                ))

    return zones