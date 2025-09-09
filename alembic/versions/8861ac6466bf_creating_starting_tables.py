"""Creating starting tables

Revision ID: 8861ac6466bf
Revises:
Create Date: 2025-09-09 14:44:30.721301

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8861ac6466bf"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "player",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("puuid", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("discord_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_player_discord_id"), "player", ["discord_id"], unique=False)
    op.create_index(op.f("ix_player_id"), "player", ["id"], unique=False)
    op.create_index(op.f("ix_player_puuid"), "player", ["puuid"], unique=False)
    op.create_index(op.f("ix_player_username"), "player", ["username"], unique=False)

    op.create_table(
        "season",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_season_id"), "season", ["id"], unique=False)

    op.create_table(
        "activeplayer",
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["player.id"],
        ),
        sa.PrimaryKeyConstraint("player_id"),
    )

    op.create_table(
        "match",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("mode", sa.Integer(), nullable=False),
        sa.Column("season_id", sa.Integer(), nullable=True),
        sa.Column("champions_registered", sa.Boolean(), nullable=False),
        sa.Column("result", sa.Enum("blue", "red", name="teamside"), nullable=True),
        sa.ForeignKeyConstraint(
            ["season_id"],
            ["season.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_match_id"), "match", ["id"], unique=False)

    op.create_table(
        "playerelohistory",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.Column("is_reverted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("points_before", sa.Integer(), nullable=False),
        sa.Column("points_after", sa.Integer(), nullable=False),
        sa.Column("change", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["match.id"],
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["player.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_playerelohistory_match_id"), "playerelohistory", ["match_id"], unique=False)
    op.create_index(op.f("ix_playerelohistory_player_id"), "playerelohistory", ["player_id"], unique=False)

    op.create_table(
        "playermatchchampion",
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=False),
        sa.Column("champion_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["match.id"],
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["player.id"],
        ),
        sa.PrimaryKeyConstraint("player_id", "match_id"),
    )
    op.create_index(op.f("ix_playermatchchampion_champion_id"), "playermatchchampion", ["champion_id"], unique=False)
    op.create_index(op.f("ix_playermatchchampion_match_id"), "playermatchchampion", ["match_id"], unique=False)
    op.create_index(op.f("ix_playermatchchampion_player_id"), "playermatchchampion", ["player_id"], unique=False)

    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("side", sa.Enum("blue", "red", name="teamside"), nullable=False),
        sa.Column("champions", sa.JSON(), nullable=True),
        sa.Column("team_rating", sa.Integer(), nullable=False),
        sa.Column("match_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["match_id"],
            ["match.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_team_id"), "team", ["id"], unique=False)

    op.create_table(
        "playerteam",
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["player.id"],
        ),
        sa.ForeignKeyConstraint(
            ["team_id"],
            ["team.id"],
        ),
        sa.PrimaryKeyConstraint("player_id", "team_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("playerteam")
    op.drop_index(op.f("ix_team_id"), table_name="team")
    op.drop_table("team")
    op.drop_index(op.f("ix_playermatchchampion_player_id"), table_name="playermatchchampion")
    op.drop_index(op.f("ix_playermatchchampion_match_id"), table_name="playermatchchampion")
    op.drop_index(op.f("ix_playermatchchampion_champion_id"), table_name="playermatchchampion")
    op.drop_table("playermatchchampion")
    op.drop_index(op.f("ix_playerelohistory_player_id"), table_name="playerelohistory")
    op.drop_index(op.f("ix_playerelohistory_match_id"), table_name="playerelohistory")
    op.drop_table("playerelohistory")
    op.drop_index(op.f("ix_match_id"), table_name="match")
    op.drop_table("match")
    op.drop_table("activeplayer")
    op.drop_index(op.f("ix_season_id"), table_name="season")
    op.drop_table("season")
    op.drop_index(op.f("ix_player_username"), table_name="player")
    op.drop_index(op.f("ix_player_puuid"), table_name="player")
    op.drop_index(op.f("ix_player_id"), table_name="player")
    op.drop_index(op.f("ix_player_discord_id"), table_name="player")
    op.drop_table("player")
    # ### end Alembic commands ###
