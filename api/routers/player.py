from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from api.config.database import get_session
from api.schemas import PaginatedRanking
from shared.repos import player_repo

router = APIRouter(prefix="/v1/player", tags=["players"])


@router.get("/ranking", response_model=PaginatedRanking, status_code=status.HTTP_200_OK)
def ranking_users(
    session: Session = Depends(get_session),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    ranked_players, total_players = player_repo.get_all_players_ranked_paginated(session, limit, offset)

    if not ranked_players:
        raise HTTPException(status_code=204, detail="Ainda não há jogadores no ranking.")

    return PaginatedRanking(total=total_players, limit=limit, offset=offset, items=ranked_players)
