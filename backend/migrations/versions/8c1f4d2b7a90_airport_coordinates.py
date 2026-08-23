"""Give airports coordinates

The weather proxy needs to ask a forecast provider about a station. An
airport's position is airport reference data, so it belongs in the airports
row next to its IANA zone rather than in a second lookup table in code.

Backfilled for the eight stations the network actually serves before the
columns are made NOT NULL, so this applies cleanly to a populated database
rather than only to an empty one.

Revision ID: 8c1f4d2b7a90
Revises: 539e47fa08f4
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '8c1f4d2b7a90'
down_revision: Union[str, None] = '539e47fa08f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Every station in the published network. A row outside this set would block
# the NOT NULL below, which is the correct outcome: a station with no position
# cannot be given weather, and silently defaulting one to 0,0 would put it in
# the Atlantic.
_COORDINATES = [
    ("ATH", 37.9364, 23.9445),
    ("SKG", 40.5197, 22.9709),
    ("LHR", 51.4700, -0.4543),
    ("CDG", 49.0097, 2.5479),
    ("FRA", 50.0379, 8.5622),
    ("MUC", 48.3538, 11.7861),
    ("FCO", 41.8003, 12.2389),
    ("BCN", 41.2974, 2.0833),
]


def upgrade() -> None:
    op.add_column("airports", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("airports", sa.Column("longitude", sa.Float(), nullable=True))

    airports = sa.table(
        "airports",
        sa.column("iata_code", sa.String),
        sa.column("latitude", sa.Float),
        sa.column("longitude", sa.Float),
    )
    for iata, lat, lon in _COORDINATES:
        op.execute(
            airports.update()
            .where(airports.c.iata_code == op.inline_literal(iata))
            .values(latitude=lat, longitude=lon)
        )

    op.alter_column("airports", "latitude", nullable=False)
    op.alter_column("airports", "longitude", nullable=False)

    op.create_check_constraint(
        "ck_airport_latitude_range", "airports", "latitude >= -90 AND latitude <= 90"
    )
    op.create_check_constraint(
        "ck_airport_longitude_range",
        "airports",
        "longitude >= -180 AND longitude <= 180",
    )


def downgrade() -> None:
    op.drop_constraint("ck_airport_longitude_range", "airports", type_="check")
    op.drop_constraint("ck_airport_latitude_range", "airports", type_="check")
    op.drop_column("airports", "longitude")
    op.drop_column("airports", "latitude")
