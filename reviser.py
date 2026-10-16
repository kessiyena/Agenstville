"""The revision agent: a tool-calling loop that keeps going until every check passes."""

from openai import OpenAI

from config import MAX_REVISION_TURNS, MIN_ACTIVITIES_PER_DAY, REVISER_MODEL, TRAVELER_FEEDBACK
from data import TripData
from evals import EvalResult, WeatherJudge, all_passed, report, run_evals
from models import TravelPlan, VacationInfo
from prompts import REVISER_INSTRUCTIONS
from tools import TOOLS, run_tool


def as_input(item) -> dict:
    """Turn one of the model's output items back into an input item for the next call.

    responses.parse adds `parsed` fields for our convenience, but the API rejects them
    if they're sent back, so they're removed here.
    """
    data = item.model_dump(exclude_none=True)
    data.pop("parsed_arguments", None)
    for part in data.get("content") or []:
        part.pop("parsed", None)
    return data


def revise_itinerary(client: OpenAI, vacation: VacationInfo, data: TripData, draft: TravelPlan,
                     judge: WeatherJudge) -> tuple[TravelPlan, list[EvalResult]]:
    """Returns the last itinerary reached and its eval results (which may still include failures)."""
    plan = draft
    results = run_evals(plan, vacation, data, judge, MIN_ACTIVITIES_PER_DAY)
    if all_passed(results):
        return plan, results

    conversation: list = [{"role": "user", "content": f"""<vacation>
{vacation.model_dump_json(indent=2)}
</vacation>

<itinerary>
{plan.model_dump_json(indent=2)}
</itinerary>

<feedback>{TRAVELER_FEEDBACK}</feedback>

<failed_checks>
{report(results)}
</failed_checks>"""}]

    for turn in range(1, MAX_REVISION_TURNS + 1):
        response = client.responses.parse(
            model=REVISER_MODEL,
            instructions=REVISER_INSTRUCTIONS,
            input=conversation,
            tools=TOOLS,
            text_format=TravelPlan,
            reasoning={"effort": "medium"},
            store=False,
            include=["reasoning.encrypted_content"],
        )
        conversation += [as_input(item) for item in response.output]

        tool_calls = [item for item in response.output if item.type == "function_call"]
        if tool_calls:
            for call in tool_calls:
                print(f"  [turn {turn}] {call.name}({call.arguments})")
                conversation.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": run_tool(call.name, call.arguments, data),
                })
            continue

        revised = response.output_parsed
        if revised is None:
            conversation.append({"role": "user", "content": "Please return the complete revised itinerary."})
            continue

        plan = revised
        results = run_evals(plan, vacation, data, judge, MIN_ACTIVITIES_PER_DAY)
        failed = sum(not r.passed for r in results)
        print(f"  [turn {turn}] submitted an itinerary: {failed} check(s) failing")
        if all_passed(results):
            return plan, results
        conversation.append({"role": "user", "content": f"""The itinerary still fails these checks. Fix them and return it again.

<failed_checks>
{report(results)}
</failed_checks>"""})

    return plan, results