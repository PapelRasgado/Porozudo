from typing import Any, Dict

from sqlalchemy import Integer, func, select
from sqlmodel import Session

from shared.model.database import Match, Player, PlayerTeam, Team


def get_players_stat(session: Session, mode: int = 0, season: int = 0) -> Dict[str, Any]:
    win_condition = Team.side == Match.result

    query = (
        select(
            Player.id,
            Player.discord_id,
            func.sum(func.cast(win_condition, Integer)).label("wins"),
            func.count(Match.id).label("games"),
        )
        .join(PlayerTeam, Player.id == PlayerTeam.player_id)
        .join(Team, PlayerTeam.team_id == Team.id)
        .join(Match, Team.match_id == Match.id)
        .where(Match.result.is_not(None))
    )

    if mode != 0:
        query = query.where(Match.mode == mode)

    if season != 0:
        query = query.where(Match.season_id == season)

    query = query.group_by(Player.id, Player.discord_id)

    results = session.exec(query).all()

    stats = {}
    for id, discord_id, wins, games in results:
        wins = wins or 0
        losses = games - wins
        winrate = (wins / games) * 100 if games > 0 else 0

        stats[id] = {
            "discord_id": discord_id,
            "wins": wins,
            "losses": losses,
            "games": games,
            "winrate": winrate,
        }

    return stats
