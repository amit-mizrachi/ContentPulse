from pydantic import BaseModel


class ArticleEntity(BaseModel):
    name: str
    type: str  # player, team, league, sport, venue
    normalized: str
