"""Simulated AgentsVille weather and activity APIs, and a container for their results.

In a real product, fetch_weather and fetch_activities would make HTTP requests.
Here they read from the dictionaries below, which play the part of the API's JSON.
"""

import datetime as dt

from models import Activity, VacationInfo, Weather

_WEATHER = {
    "2026-06-10": {"condition": "sunny", "temperature_c": 24, "precipitation_chance": 5,
                   "description": "Clear skies all day with a light breeze."},
    "2026-06-11": {"condition": "thunderstorms", "temperature_c": 18, "precipitation_chance": 90,
                   "description": "Heavy rain and thunderstorms from late morning into the evening."},
    "2026-06-12": {"condition": "partly cloudy", "temperature_c": 21, "precipitation_chance": 20,
                   "description": "Sun and cloud, with a small chance of a brief afternoon shower."},
}

_ACTIVITIES = [
    # June 10: sunny
    {"activity_id": "ev-0610-01", "name": "Sunrise Ridge Hike", "date": "2026-06-10",
     "start_time": "07:00", "end_time": "10:00", "location": "Pine Ridge Trail",
     "description": "A guided hike along an exposed ridge with views over the whole valley.",
     "price": 15, "interests": ["hiking"]},
    {"activity_id": "ev-0610-02", "name": "Old Town Mural Walk", "date": "2026-06-10",
     "start_time": "10:30", "end_time": "12:00", "location": "Old Town",
     "description": "An outdoor walking tour of the street art and the stories behind it.",
     "price": 20, "interests": ["art", "history"]},
    {"activity_id": "ev-0610-03", "name": "Robotics Lab Open House", "date": "2026-06-10",
     "start_time": "13:00", "end_time": "15:00", "location": "AgentsVille Institute",
     "description": "Indoor demos of the robots built by local engineering students.",
     "price": 0, "interests": ["technology"]},
    {"activity_id": "ev-0610-04", "name": "Night Market Food Crawl", "date": "2026-06-10",
     "start_time": "18:00", "end_time": "20:30", "location": "Harbour Square",
     "description": "Tastings at a dozen stalls in the open-air night market.",
     "price": 35, "interests": ["food"]},
    {"activity_id": "ev-0610-05", "name": "Jazz on the Lawn", "date": "2026-06-10",
     "start_time": "19:00", "end_time": "21:30", "location": "Central Park Bandstand",
     "description": "An open-air jazz concert. Bring a blanket.",
     "price": 40, "interests": ["music"]},
    # June 11: thunderstorms
    {"activity_id": "ev-0611-01", "name": "Canyon Trail Run", "date": "2026-06-11",
     "start_time": "08:00", "end_time": "10:00", "location": "Red Canyon",
     "description": "A group trail run on an exposed canyon path.",
     "price": 10, "interests": ["hiking"]},
    {"activity_id": "ev-0611-02", "name": "Gallery Highlights Tour", "date": "2026-06-11",
     "start_time": "10:00", "end_time": "12:00", "location": "AgentsVille Museum of Modern Art",
     "description": "A guided indoor tour of the museum's best-known works.",
     "price": 18, "interests": ["art", "history"]},
    {"activity_id": "ev-0611-03", "name": "Lakeside Picnic and Sketching", "date": "2026-06-11",
     "start_time": "11:00", "end_time": "13:00", "location": "Mirror Lake Lawn",
     "description": "Sketch the lake with a local artist while enjoying a picnic lunch on the grass.",
     "price": 25, "interests": ["art", "food"]},
    {"activity_id": "ev-0611-04", "name": "Pasta-Making Workshop", "date": "2026-06-11",
     "start_time": "13:00", "end_time": "15:30", "location": "The Teaching Kitchen",
     "description": "Make fresh pasta from scratch in an indoor cooking school, then eat it.",
     "price": 55, "interests": ["food"]},
    {"activity_id": "ev-0611-05", "name": "Indoor Climbing Session", "date": "2026-06-11",
     "start_time": "16:00", "end_time": "18:00", "location": "Boulder Hall",
     "description": "An introductory session at an indoor climbing gym. Equipment included.",
     "price": 30, "interests": ["hiking"]},
    {"activity_id": "ev-0611-06", "name": "Acoustic Night at The Cellar", "date": "2026-06-11",
     "start_time": "20:00", "end_time": "22:00", "location": "The Cellar",
     "description": "Local singer-songwriters in a cosy basement venue.",
     "price": 25, "interests": ["music"]},
    # June 12: partly cloudy
    {"activity_id": "ev-0612-01", "name": "Waterfall Loop Hike", "date": "2026-06-12",
     "start_time": "09:00", "end_time": "12:00", "location": "Silver Falls",
     "description": "A forest hike to two waterfalls. Mostly shaded.",
     "price": 0, "interests": ["hiking"]},
    {"activity_id": "ev-0612-02", "name": "Garden Watercolour Class", "date": "2026-06-12",
     "start_time": "09:30", "end_time": "11:30", "location": "Botanical Garden Pavilion",
     "description": "Paint the gardens from a covered pavilion. All materials provided.",
     "price": 30, "interests": ["art"]},
    {"activity_id": "ev-0612-03", "name": "Street Food Cooking Class", "date": "2026-06-12",
     "start_time": "13:00", "end_time": "15:30", "location": "The Teaching Kitchen",
     "description": "Cook three AgentsVille street-food classics indoors.",
     "price": 45, "interests": ["food"]},
    {"activity_id": "ev-0612-04", "name": "Vinyl Record Fair", "date": "2026-06-12",
     "start_time": "14:00", "end_time": "17:00", "location": "Exhibition Hall",
     "description": "An indoor fair with record dealers and live DJ sets.",
     "price": 5, "interests": ["music"]},
    {"activity_id": "ev-0612-05", "name": "Rooftop Sunset Concert", "date": "2026-06-12",
     "start_time": "19:00", "end_time": "21:00", "location": "Skyline Hotel Rooftop",
     "description": "An outdoor string quartet on an open rooftop as the sun sets.",
     "price": 35, "interests": ["music"]},
]


def fetch_weather(date: dt.date) -> Weather | None:
    """Simulated weather API: the forecast for one date, or None if there isn't one."""
    raw = _WEATHER.get(date.isoformat())
    if raw is None:
        return None
    return Weather.model_validate({"date": date.isoformat(), **raw})


def fetch_activities(date: dt.date) -> list[Activity]:
    """Simulated activities API: everything on offer on one date."""
    return [Activity.model_validate(a) for a in _ACTIVITIES if a["date"] == date.isoformat()]


class TripData:
    """The weather and activities for every date of one trip, fetched once up front."""

    def __init__(self, weather: dict[dt.date, Weather], activities: dict[dt.date, list[Activity]]):
        self.weather = weather
        self.activities = activities
        self._by_id = {a.activity_id: a for day in activities.values() for a in day}

    def find_activity(self, activity_id: str) -> Activity | None:
        return self._by_id.get(activity_id)


def load_trip_data(vacation: VacationInfo) -> TripData:
    """Call both APIs for every date of the trip."""
    weather: dict[dt.date, Weather] = {}
    activities: dict[dt.date, list[Activity]] = {}
    for date in vacation.dates:
        forecast = fetch_weather(date)
        if forecast is not None:
            weather[date] = forecast
        activities[date] = fetch_activities(date)
    return TripData(weather, activities)