"""The tools the revision agent can call: their definitions for the model, and the code behind them."""

import datetime as dt
import json
from collections.abc import Callable

from openai.types.responses import FunctionToolParam

from data import TripData
from formatting import to_json

DATE_PARAMETER = {
    "type": "object",
    "properties": {
        "date": {"type": "string", "description": "The date, in YYYY-MM-DD format."},
    },
    "required": ["date"],
    "additionalProperties": False,
}

TOOLS: list[FunctionToolParam] = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get the weather forecast for one date of the trip.",
        "parameters": DATE_PARAMETER,
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_activities_by_date",
        "description": "List every activity available on one date of the trip, with its "
                       "activity_id, times, location, description, price per person and interests.",
        "parameters": DATE_PARAMETER,
        "strict": True,
    },
]

def get_weather(data: TripData, date: dt.date) -> str:
    forecast = data.weather.get(date)
    if forecast is None:
        return f"No forecast for {date}. Forecasts exist for: {', '.join(map(str, data.weather))}."
    return forecast.model_dump_json(indent=2)


def get_activities_by_date(data: TripData, date: dt.date) -> str:
    if date not in data.activities:
        return f"{date} isn't part of this trip. Trip dates: {', '.join(map(str, data.activities))}."
    return to_json(data.activities[date])

TOOL_FUNCTIONS: dict[str, Callable[[TripData, dt.date], str]] = {
    "get_weather": get_weather,
    "get_activities_by_date": get_activities_by_date,
}

def run_tool(name: str, arguments: str, data: TripData) -> str:
    """Run the tool the model asked for. Problems are returned as text, so the model can recover."""
    function = TOOL_FUNCTIONS.get(name)
    if function is None:
        return f"Error: there is no tool called {name}."
    try:
        date = dt.date.fromisoformat(json.loads(arguments)["date"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return f"Error: invalid arguments ({e}). Pass a date in YYYY-MM-DD format."
    return function(data, date)