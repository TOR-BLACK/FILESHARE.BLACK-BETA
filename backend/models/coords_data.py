# Подгружаем необходимые зависимости
import json
from typing import List
from pydantic import BaseModel, model_validator

# Класс, используемый для координат в запросе
class CoordsData(BaseModel):
	name: str | None
	coords: List[str] | None

	@model_validator(mode='before')
	@classmethod
	def validate_to_json(cls, value):
		if isinstance(value, str):
			return cls(**json.loads(value))
		return value