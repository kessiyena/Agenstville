"""Checks that an itinerary is valid. Code checks what code can; an LLM judges the weather."""

import datetime as dt
import json

from openai import OpenAI
from pydantic import BaseModel

from config import JUDGE_MODEL
from data import TripData
from formatting import plan_cost
from models import Activity, TravelPlan, VacationInfo
from prompts import WEATHER_JUDGE_INSTRUCTIONS

class EvalResult(BaseModel):
    name: str
    passed: bool
    problems: list[str] = []


def result(name: str, problems: list[str]) -> EvalResult:
    return EvalResult(name=name, passed=not problems, problems=problems)

def check_dates(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> EvalResult:
    planned = [day.date for day in plan.days]
    problems = []
    if planned != vacation.dates:
        problems.append(f"The plan covers {[d.isoformat() for d in planned]}, "
                        f"but the trip is {[d.isoformat() for d in vacation.dates]}.")
    return result("Covers every trip date, in order", problems)

def check_activities_exist(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> EvalResult:
    problems = []
    for day in plan.days:
        available = {a.activity_id for a in data.activities.get(day.date, [])}
        for planned in day.activities:
            if planned.activity_id in available:
                continue
            elsewhere = data.find_activity(planned.activity_id)
            if elsewhere is not None:
                problems.append(f"{planned.activity_id} runs on {elsewhere.date}, not {day.date}.")
            else:
                problems.append(f"{planned.activity_id} on {day.date} doesn't exist.")
    return result("Only uses real activities on the right dates", problems)

def check_no_overlaps(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> EvalResult:
    problems = []
    for day in plan.days:
        activities = sorted(known_activities(day.activities, data), key=lambda a: a.start_time)
        for earlier, later in zip(activities, activities[1:]):
            if later.start_time < earlier.end_time:
                problems.append(f"On {day.date}, {earlier.name} ({earlier.start_time:%H:%M}-"
                                f"{earlier.end_time:%H:%M}) overlaps {later.name} "
                                f"({later.start_time:%H:%M}-{later.end_time:%H:%M}).")
    return result("No overlapping activities", problems)

def check_budget(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> EvalResult:
    cost = plan_cost(plan, vacation, data)
    problems = []
    if cost > vacation.budget:
        problems.append(f"The plan costs ${cost}, which is ${cost - vacation.budget} over "
                        f"the ${vacation.budget} budget.")
    return result("Within budget", problems)

def check_interests(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> EvalResult:
    chosen = [a for day in plan.days for a in known_activities(day.activities, data)]
    problems = []
    for traveler in vacation.travelers:
        if not any(set(traveler.interests) & set(a.interests) for a in chosen):
            interests = ", ".join(traveler.interests)
            problems.append(f"Nothing matches {traveler.name}'s interests ({interests}).")
    return result("Every traveler gets something they're interested in", problems)

def check_activities_per_day(plan: TravelPlan, minimum: int) -> EvalResult:
    problems = [f"{day.date} has {len(day.activities)} activities; the travelers want at least {minimum}."
                for day in plan.days if len(day.activities) < minimum]
    return result(f"At least {minimum} activities per day", problems)

def known_activities(planned: list, data: TripData) -> list[Activity]:
    """The full Activity for each planned ID, skipping IDs that don't exist."""
    found = (data.find_activity(p.activity_id) for p in planned)
    return [a for a in found if a is not None]

class WeatherVerdict(BaseModel):
    activity_id: str
    compatible: bool
    reason: str

class WeatherVerdicts(BaseModel):
    verdicts: list[WeatherVerdict]

class WeatherJudge:
    """Asks an LLM whether activities suit the weather, and remembers every answer.

    An activity's verdict on a given date never changes, so when the reviser keeps
    most of the plan, re-checking it costs nothing.
    """

    def __init__(self, client: OpenAI):
        self.client = client
        self.cache: dict[tuple[dt.date, str], WeatherVerdict] = {}

    def check(self, plan: TravelPlan, data: TripData) -> EvalResult:
        problems = []
        for day in plan.days:
            forecast = data.weather.get(day.date)
            activities = known_activities(day.activities, data)
            if forecast is None or not activities:
                continue
            unjudged = [a for a in activities if (day.date, a.activity_id) not in self.cache]
            if unjudged:
                self._judge(day.date, unjudged, data)
            for activity in activities:
                verdict = self.cache.get((day.date, activity.activity_id))
                if verdict is None:
                    problems.append(f"Couldn't check {activity.name} against the weather on {day.date}.")
                elif not verdict.compatible:
                    problems.append(f"{activity.name} on {day.date} doesn't suit the weather "
                                    f"({forecast.condition}): {verdict.reason}")
        return result("Activities suit the weather", problems)

    def _judge(self, date: dt.date, activities: list[Activity], data: TripData) -> None:
        forecast = data.weather[date]
        listed = [{"activity_id": a.activity_id, "name": a.name, "location": a.location,
                   "description": a.description} for a in activities]
        response = self.client.responses.parse(
            model=JUDGE_MODEL,
            instructions=WEATHER_JUDGE_INSTRUCTIONS,
            input=f"<weather>\n{forecast.model_dump_json(indent=2)}\n</weather>\n\n"
                  f"<activities>\n{json.dumps(listed, indent=2)}\n</activities>",
            text_format=WeatherVerdicts,
            reasoning={"effort": "low"},
            store=False,
        )
        verdicts = response.output_parsed
        if verdicts is None:
            return
        wanted = {a.activity_id for a in activities}
        for verdict in verdicts.verdicts:
            if verdict.activity_id in wanted:
                self.cache[(date, verdict.activity_id)] = verdict

def run_evals(plan: TravelPlan, vacation: VacationInfo, data: TripData, judge: WeatherJudge,
              min_activities_per_day: int | None = None) -> list[EvalResult]:
    results = [
        check_dates(plan, vacation, data),
        check_activities_exist(plan, vacation, data),
        check_no_overlaps(plan, vacation, data),
        check_budget(plan, vacation, data),
        check_interests(plan, vacation, data),
        judge.check(plan, data),
    ]
    if min_activities_per_day is not None:
        results.append(check_activities_per_day(plan, min_activities_per_day))
    return results

def all_passed(results: list[EvalResult]) -> bool:
    return all(r.passed for r in results)


def report(results: list[EvalResult]) -> str:
    lines = []
    for r in results:
        lines.append(f"{'PASS' if r.passed else 'FAIL'}  {r.name}")
        lines.extend(f"      - {problem}" for problem in r.problems)
    return "\n".join(lines)
