import datetime as dt
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

class Interest(StrEnum):
    ART = "art"
    FOOD = "food"
    HIKING = "hiking"
    HISTORY = "history"
    MUSIC = "music"
    TECHNOLOGY = "technology"

class Traveler(BaseModel):
    name: str
    age: int = Field(ge=0)
    interests: list[Interest] = Field(min_length=1)

class VacationInfo(BaseModel):
    destination: str
    start_date: dt.date
    end_date: dt.date
    budget: int = Field(gt=0, description="Total activity budget for the whole group, in dollars.")
    travelers: list[Traveler] = Field(min_length=1)

    @model_validator(mode="after")
    def check_dates(self) -> VacationInfo:
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self

    @property
    def dates(self) -> list[dt.date]:
        number_of_days = (self.end_date - self.start_date).days + 1
        return [self.start_date + dt.timedelta(days=x) for x in range(number_of_days)]

class Weather(BaseModel):
    date: dt.date
    condition: str
    temperature_c: int
    precipitation_chance: int = Field(ge=0, le=100)
    description: str

class Activity(BaseModel):
    activity_id: str
    name: str
    date: dt.date
    start_time: dt.time
    end_time: dt.time
    location: str
    description: str
    price: int = Field(ge=0, description="Price per person, in dollars.")
    interests: list[Interest]

class PlannedActivity(BaseModel):
    activity_id: str = Field(description="The exact activity_id from the list of available activities.")
    reason: str = Field(description="One sentence on why this suits the traveler and the weather.")

class DayPlan(BaseModel):
    date: dt.date
    activities: list[PlannedActivity]

class TravelPlan(BaseModel):
    days: list[DayPlan] = Field(description="One entry per day of the trip, in date order.")



