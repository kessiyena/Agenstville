"""AgentsVille trip planner: draft an itinerary, check it, revise it with an agent, tell the story."""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import APIError, OpenAI
from pydantic import ValidationError

from config import TRAVELER_FEEDBACK
from data import load_trip_data
from evals import WeatherJudge, all_passed, report, run_evals
from formatting import describe_plan
from models import VacationInfo
from planner import draft_itinerary, write_trip_story
from reviser import revise_itinerary

VACATION_FILE = Path(__file__).parent / "vacation.json"


def heading(text: str) -> None:
    print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")


def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found. Check your .env file.")
        return

    try:
        vacation = VacationInfo.model_validate_json(VACATION_FILE.read_text())
    except ValidationError as e:
        print(f"vacation.json isn't valid:\n{e}")
        return

    client = OpenAI(api_key=api_key)
    data = load_trip_data(vacation)
    judge = WeatherJudge(client)

    try:
        heading("1. First draft")
        draft = draft_itinerary(client, vacation, data)
        print(describe_plan(draft, vacation, data))

        heading("2. Checking the draft")
        print(report(run_evals(draft, vacation, data, judge)))

        heading("3. Revising with the travelers' feedback")
        print(f'Feedback: "{TRAVELER_FEEDBACK}"\n')
        final, results = revise_itinerary(client, vacation, data, draft, judge)

        heading("4. Final itinerary")
        print(describe_plan(final, vacation, data))
        print()
        print(report(results))
        if not all_passed(results):
            print("\nWarning: the agent ran out of turns before every check passed.")

        heading("5. The trip story")
        print(write_trip_story(client, vacation, final, data))

    except APIError as e:
        print(f"\nThe OpenAI API returned an error: {e}")


if __name__ == "__main__":
    main()
