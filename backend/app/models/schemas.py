from pydantic import BaseModel, Field, field_validator
from typing import Literal

class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    conversation_id: str | None = None
    context: dict[str, str] = Field(default_factory=dict)
    @field_validator('context')
    @classmethod
    def validate_context(cls, value):
        if len(value) > 10 or any(len(k) > 40 or len(v) > 120 for k, v in value.items()):
            raise ValueError('Context is too large. Limit it to 10 short fields.')
        return value

class CropRequest(BaseModel):
    state: str = Field(min_length=2, max_length=80)
    district: str = Field(min_length=2, max_length=80)
    soil_type: Literal['Alluvial','Black','Red','Sandy','Clay','Loamy','Laterite','Other']
    season: Literal['Kharif','Rabi','Zaid','Year-round']
    irrigation: Literal['Rain-fed','Limited','Assured']
    land_area_acres: float = Field(gt=0, le=10000)
    budget: Literal['Low','Moderate','Flexible']
    category: Literal['Any','Cereal','Pulse','Oilseed','Vegetable','Horticulture'] = 'Any'

class FertilizerRequest(BaseModel):
    crop: str = Field(min_length=2, max_length=80)
    stage: str = Field(min_length=2, max_length=80)
    soil_type: str = Field(min_length=2, max_length=80)
    soil_test: bool = False
    available: str | None = Field(default=None, max_length=100)

class IrrigationRequest(BaseModel):
    crop: str = Field(min_length=2, max_length=80)
    stage: str = Field(min_length=2, max_length=80)
    soil_type: str = Field(min_length=2, max_length=80)
    method: Literal['Drip','Sprinkler','Surface']
    rainfall: str = Field(max_length=100)
    weather: str = Field(max_length=100)
