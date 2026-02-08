from src.objects.target_models.target_model import TargetModel


class Gemini(TargetModel):
    name: str = "Gemini"


class GeminiFlash(TargetModel):
    name: str = "Gemini-Flash"


class Gemini25Flash(TargetModel):
    name: str = "Gemini-2.5-Flash"


class GeminiPro(TargetModel):
    name: str = "Gemini-Pro"
