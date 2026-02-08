from pydantic import BaseModel

class JudgeModel(BaseModel):
    name: str
    version: str

