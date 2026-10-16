import json
from data import TripData
from models import Activity, TravelPlan, VacationInfo, Weather

def to_json(items: list[Weather] | list[Activity]) -> str:
    return json.dumps([item.model_dump(mode="json") for item in items], indent=2)

def trip_context(vacation: VacationInfo, data: TripData) -> str:
    """Everything the planner needs, in tagged sections."""
    all_weather = list(data.weather.values())
    all_activities = [a for day in data.activities.values() for a in day]
    return f"""<vacation>
{vacation.model_dump_json(indent=2)}
</vacation>

<weather>
{to_json(all_weather)}
</weather>

<activities>
{to_json(all_activities)}
</activities>"""

def plan_cost(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> int:
    """The total cost, worked out in code. Unknown IDs are skipped (an eval reports them)."""
    total = 0
    for day in plan.days:
        for planned in day.activities:
            activity = data.find_activity(planned.activity_id)
            if activity is not None:
                total += activity.price * len(vacation.travelers)
    return total

def describe_plan(plan: TravelPlan, vacation: VacationInfo, data: TripData) -> str:
    """The itinerary as readable text, with details looked up from the activity data."""
    lines = []
    for day in plan.days:
        forecast = data.weather.get(day.date)
        weather = f"{forecast.condition}, {forecast.temperature_c}°C" if forecast else "no forecast"
        lines.append(f"\n{day.date:%A %d %B} ({weather})")
        for planned in day.activities:
            activity = data.find_activity(planned.activity_id)
            if activity is None:
                lines.append(f"  ?? Unknown activity {planned.activity_id}")
                continue
            lines.append(f"  {activity.start_time:%H:%M}-{activity.end_time:%H:%M}  "
                         f"{activity.name} (${activity.price} pp)")
            lines.append(f"      {planned.reason}")
    cost = plan_cost(plan, vacation, data)
    lines.append(f"\nTotal cost: ${cost} of ${vacation.budget} budget")
    return "\n".join(lines)