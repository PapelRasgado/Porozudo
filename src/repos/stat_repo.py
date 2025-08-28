from typing import Any, Dict

from sqlalchemy import Integer, func, select
from sqlmodel import Session

from src.model.database import Match, Player, PlayerTeam, Team


def get_players_stat(session: Session) -> Dict[str, Any]:
    win_condition = Team.side == Match.result

    query = (
        select(
            Player.id,
            Player.discord_id,
            func.sum(func.cast(win_condition, Integer)).label("wins"),
            func.sum(func.cast(~win_condition, Integer)).label("losses"),
        )
        .join(PlayerTeam, Player.id == PlayerTeam.player_id)
        .join(Team, PlayerTeam.team_id == Team.id)
        .join(Match, Team.match_id == Match.id)
        .group_by(Player.id, Player.discord_id)
    )

    results = session.exec(query).all()

    stats = {}
    for id, discord_id, wins, losses in results:
        stats[id] = {
            "discord_id": discord_id,
            "wins": wins,
            "losses": losses,
            "games": wins + losses,
            "winrate": (wins / (wins + losses)) * 100,
        }

    return stats
