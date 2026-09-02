"""Add canonical facility catalog and facility-scoped indexes."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from backend.database.base import Base
from backend.database import models  # noqa: F401

revision = "20260902_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "facilities",
        sa.Column("facility_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("facility_type", sa.String(length=64)),
        sa.Column("total_area_sqft", sa.Float),
        sa.Column("total_floors", sa.Integer),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    bind = op.get_bind()
    # The repository has no pre-catalog migration history, so create the current
    # ORM tables on a fresh database before applying data-preserving changes.
    Base.metadata.create_all(bind=bind)
    existing_tables = set(inspect(bind).get_table_names())
    for table, column in [
        ("energy_usage", "facility_id"),
        ("cost_records", "facility_id"),
        ("cost_analysis_reports", "facility_id"),
        ("cost_recommendations", "facility_id"),
        ("assets", "facility_id"),
        ("occupancy_zones", "facility_id"),
        ("occupancy_records", "facility_id"),
        ("occupancy_images", "facility_id"),
        ("occupancy_forecasts", "facility_id"),
        ("security_events", "facility_id"),
    ]:
        if table in existing_tables:
            rows = bind.execute(sa.text(f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL"))
            for (facility_id,) in rows:
                exists = bind.execute(
                    sa.text("SELECT 1 FROM facilities WHERE facility_id = :id"),
                    {"id": facility_id},
                ).first()
                if exists is None:
                    bind.execute(
                        sa.text("INSERT INTO facilities (facility_id, name, is_active, created_at) VALUES (:id, :name, :active, CURRENT_TIMESTAMP)"),
                        {"id": facility_id, "name": facility_id, "active": True},
                    )
            # Facility columns already have single-column indexes in the ORM.
            pass

    for table, index, columns in [
        ("energy_usage", "ix_energy_usage_facility_timestamp", ["facility_id", "timestamp"]),
        ("cost_records", "ix_cost_records_facility_incurred_date", ["facility_id", "incurred_date"]),
        ("assets", "ix_assets_facility_status", ["facility_id", "status"]),
        ("occupancy_zones", "ix_occupancy_zones_facility_zone", ["facility_id", "zone_id"]),
        ("occupancy_records", "ix_occupancy_records_facility_zone_timestamp", ["facility_id", "zone_id", "timestamp"]),
        ("security_events", "ix_security_events_facility_time", ["facility_id", "event_time"]),
    ]:
        if table in existing_tables and index not in {item["name"] for item in inspect(bind).get_indexes(table)}:
            op.create_index(index, table, columns)

    for table, constraint in [
        ("energy_usage", "fk_energy_usage_facility"),
        ("cost_records", "fk_cost_records_facility"),
        ("cost_analysis_reports", "fk_cost_analysis_reports_facility"),
        ("cost_recommendations", "fk_cost_recommendations_facility"),
        ("assets", "fk_assets_facility"),
        ("occupancy_zones", "fk_occupancy_zones_facility"),
        ("occupancy_records", "fk_occupancy_records_facility"),
        ("occupancy_images", "fk_occupancy_images_facility"),
        ("occupancy_forecasts", "fk_occupancy_forecasts_facility"),
        ("security_events", "fk_security_events_facility"),
    ]:
        if table in existing_tables and constraint not in {
            item.get("name") for item in inspect(bind).get_foreign_keys(table)
        }:
            with op.batch_alter_table(table, recreate="always") as batch_op:
                batch_op.create_foreign_key(constraint, "facilities", ["facility_id"], ["facility_id"])


def downgrade():
    for table, index in [
        ("security_events", "ix_security_events_facility_time"),
        ("occupancy_records", "ix_occupancy_records_facility_zone_timestamp"),
        ("occupancy_zones", "ix_occupancy_zones_facility_zone"),
        ("assets", "ix_assets_facility_status"),
        ("cost_records", "ix_cost_records_facility_incurred_date"),
        ("energy_usage", "ix_energy_usage_facility_timestamp"),
    ]:
        op.drop_index(index, table_name=table)
    op.drop_table("facilities")
