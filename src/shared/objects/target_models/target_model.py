from pydantic import BaseModel


class TargetModel(BaseModel):
    name: str
