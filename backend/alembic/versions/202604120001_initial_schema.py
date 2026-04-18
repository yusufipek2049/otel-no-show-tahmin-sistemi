"""initial schema

Revision ID: 202604120001
Revises:
Create Date: 2026-04-12 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "202604120001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reservation_import_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column(
            "source_files",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "metadata_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservation_import_batches")),
    )

    op.create_table(
        "reservation_import_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=False),
        sa.Column("error_message", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["reservation_import_batches.id"],
            name=op.f("fk_reservation_import_errors_batch_id_reservation_import_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservation_import_errors")),
    )

    op.create_table(
        "reservations_raw",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("property_code", sa.String(length=64), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("reservation_status", sa.String(length=32), nullable=True),
        sa.Column("reservation_status_date", sa.Date(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["reservation_import_batches.id"],
            name=op.f("fk_reservations_raw_batch_id_reservation_import_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservations_raw")),
        sa.UniqueConstraint(
            "batch_id",
            "source_file",
            "source_row_number",
            name="uq_reservations_raw_batch_file_row",
        ),
    )

    op.create_table(
        "reservations_clean",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("raw_reservation_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("property_id", sa.String(length=64), nullable=False),
        sa.Column("source_file", sa.String(length=255), nullable=False),
        sa.Column("arrival_date", sa.Date(), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("arrival_year", sa.Integer(), nullable=True),
        sa.Column("arrival_month_name", sa.String(length=32), nullable=True),
        sa.Column("arrival_week_number", sa.Integer(), nullable=True),
        sa.Column("arrival_day_of_month", sa.Integer(), nullable=True),
        sa.Column("weekend_nights", sa.Integer(), nullable=True),
        sa.Column("week_nights", sa.Integer(), nullable=True),
        sa.Column("adults", sa.Integer(), nullable=True),
        sa.Column("children", sa.Integer(), nullable=True),
        sa.Column("babies", sa.Integer(), nullable=True),
        sa.Column("meal_plan", sa.String(length=32), nullable=True),
        sa.Column("country_code", sa.String(length=8), nullable=True),
        sa.Column("market_segment", sa.String(length=64), nullable=True),
        sa.Column("distribution_channel", sa.String(length=64), nullable=True),
        sa.Column("is_repeated_guest", sa.Boolean(), nullable=True),
        sa.Column("previous_cancellations", sa.Integer(), nullable=True),
        sa.Column("previous_non_cancelled_bookings", sa.Integer(), nullable=True),
        sa.Column("reserved_room_type", sa.String(length=16), nullable=True),
        sa.Column("deposit_type", sa.String(length=32), nullable=True),
        sa.Column("agent_code", sa.String(length=64), nullable=True),
        sa.Column("company_code", sa.String(length=64), nullable=True),
        sa.Column("customer_type", sa.String(length=64), nullable=True),
        sa.Column("adr", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("required_car_parking_spaces", sa.Integer(), nullable=True),
        sa.Column("total_special_requests", sa.Integer(), nullable=True),
        sa.Column("booking_changes", sa.Integer(), nullable=True),
        sa.Column("days_in_waiting_list", sa.Integer(), nullable=True),
        sa.Column("assigned_room_type", sa.String(length=16), nullable=True),
        sa.Column("reservation_status", sa.String(length=32), nullable=True),
        sa.Column("reservation_status_date", sa.Date(), nullable=True),
        sa.Column("is_canceled", sa.Boolean(), nullable=True),
        sa.Column("no_show_flag", sa.Boolean(), nullable=True),
        sa.Column("excluded_from_training", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("exclusion_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["reservation_import_batches.id"],
            name=op.f("fk_reservations_clean_batch_id_reservation_import_batches"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_reservation_id"],
            ["reservations_raw.id"],
            name=op.f("fk_reservations_clean_raw_reservation_id_reservations_raw"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservations_clean")),
        sa.UniqueConstraint("raw_reservation_id", name=op.f("uq_reservations_clean_raw_reservation_id")),
    )
    op.create_index("ix_reservations_clean_arrival_date", "reservations_clean", ["arrival_date"], unique=False)
    op.create_index("ix_reservations_clean_property_id", "reservations_clean", ["property_id"], unique=False)

    op.create_table(
        "reservation_features",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reservation_clean_id", sa.Integer(), nullable=False),
        sa.Column("feature_set_version", sa.String(length=64), nullable=False),
        sa.Column("total_nights", sa.Integer(), nullable=True),
        sa.Column("total_guests", sa.Integer(), nullable=True),
        sa.Column("has_children", sa.Boolean(), nullable=True),
        sa.Column("is_family", sa.Boolean(), nullable=True),
        sa.Column("lead_time_bucket", sa.String(length=32), nullable=True),
        sa.Column("has_agent", sa.Boolean(), nullable=True),
        sa.Column("has_company", sa.Boolean(), nullable=True),
        sa.Column("special_request_flag", sa.Boolean(), nullable=True),
        sa.Column("adr_per_guest", sa.Float(), nullable=True),
        sa.Column("adr_per_night_proxy", sa.Float(), nullable=True),
        sa.Column("is_high_season", sa.Boolean(), nullable=True),
        sa.Column("is_weekend_heavy", sa.Boolean(), nullable=True),
        sa.Column("previous_cancel_ratio", sa.Float(), nullable=True),
        sa.Column(
            "feature_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["reservation_clean_id"],
            ["reservations_clean.id"],
            name=op.f("fk_reservation_features_reservation_clean_id_reservations_clean"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservation_features")),
        sa.UniqueConstraint(
            "reservation_clean_id",
            "feature_set_version",
            name="uq_reservation_features_reservation_version",
        ),
    )

    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reservation_clean_id", sa.Integer(), nullable=False),
        sa.Column("feature_id", sa.Integer(), nullable=True),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("risk_class", sa.String(length=16), nullable=False),
        sa.Column("threshold_used", sa.Float(), nullable=True),
        sa.Column("scoring_run_id", sa.String(length=64), nullable=True),
        sa.Column(
            "metadata_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["feature_id"],
            ["reservation_features.id"],
            name=op.f("fk_predictions_feature_id_reservation_features"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_clean_id"],
            ["reservations_clean.id"],
            name=op.f("fk_predictions_reservation_clean_id_reservations_clean"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_predictions")),
    )
    op.create_index("ix_predictions_model_version", "predictions", ["model_name", "model_version"], unique=False)
    op.create_index("ix_predictions_reservation_clean_id", "predictions", ["reservation_clean_id"], unique=False)

    op.create_table(
        "reservation_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("reservation_clean_id", sa.Integer(), nullable=False),
        sa.Column("prediction_id", sa.Integer(), nullable=True),
        sa.Column("action_type", sa.String(length=64), nullable=False),
        sa.Column("action_status", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("action_note", sa.String(length=500), nullable=True),
        sa.Column("acted_by", sa.String(length=128), nullable=False),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("acted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(
            ["prediction_id"],
            ["predictions.id"],
            name=op.f("fk_reservation_actions_prediction_id_predictions"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reservation_clean_id"],
            ["reservations_clean.id"],
            name=op.f("fk_reservation_actions_reservation_clean_id_reservations_clean"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reservation_actions")),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column(
            "change_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("reservation_actions")
    op.drop_index("ix_predictions_reservation_clean_id", table_name="predictions")
    op.drop_index("ix_predictions_model_version", table_name="predictions")
    op.drop_table("predictions")
    op.drop_table("reservation_features")
    op.drop_index("ix_reservations_clean_property_id", table_name="reservations_clean")
    op.drop_index("ix_reservations_clean_arrival_date", table_name="reservations_clean")
    op.drop_table("reservations_clean")
    op.drop_table("reservations_raw")
    op.drop_table("reservation_import_errors")
    op.drop_table("reservation_import_batches")
