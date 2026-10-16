"""Single-call steps: the first draft of the itinerary, and the trip story at the end."""

from openai import OpenAI

from config import PLANNER_MODEL, WRITER_MODEL
from data import TripData
from formatting import describe_plan, trip_context
from models import TravelPlan, VacationInfo
from prompts import PLANNER_INSTRUCTIONS, STORY_INSTRUCTIONS


def draft_itinerary(client: OpenAI, vacation: VacationInfo, data: TripData) -> TravelPlan:
    response = client.responses.parse(
        model=PLANNER_MODEL,
        instructions=PLANNER_INSTRUCTIONS,
        input=trip_context(vacation, data),
        text_format=TravelPlan,
        reasoning={"effort": "medium"},
        store=False,
    )
    plan = response.output_parsed
    if plan is None:
        raise RuntimeError("The planner didn't return an itinerary.")
    return plan


def write_trip_story(client: OpenAI, vacation: VacationInfo, plan: TravelPlan, data: TripData) -> str:
    names = ", ".join(t.name for t in vacation.travelers)
    response = client.responses.create(
        model=WRITER_MODEL,
        instructions=STORY_INSTRUCTIONS,
        input=f"<travelers>{names}</travelers>\n\n"
              f"<itinerary>{describe_plan(plan, vacation, data)}\n</itinerary>",
        reasoning={"effort": "low"},
        store=False,
    )
    return response.output_text