import json
import os
import time

import requests


BASE_URL = "http://127.0.0.1:8000"


SCENARIOS = [
    {
        "name": "Scenario 1: Plan a 3 day trip to Goa",
        "message": (
            "Plan a 3 day trip to Goa. "
            "Find me a flight and hotel."
        ),
    },
    {
        "name": "Scenario 2: Find a flight to Goa",
        "message": (
            "Find me the best flight to Goa."
        ),
    },
    {
        "name": "Scenario 3: Find a hotel in Goa",
        "message": (
            "Find me a good hotel in Goa "
            "for a 3 day trip."
        ),
    },
]


def save_report(scenario_number: int, payload: dict):
    os.makedirs("reports",exist_ok=True)

    filename = (
        f"reports/scenario"
        f"{scenario_number}-0.html"
    )

    pretty_json = json.dumps(payload, indent=2, ensure_ascii=False)

    html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Travel Agent Report</title>

            <style>
                body {{
                    font-family: Arial;
                    background: #f5f7fa;
                    padding: 30px;
                }}

                pre {{
                    background: #111827;
                    color: #e5e7eb;
                    padding: 20px;
                    border-radius: 8px;
                    overflow-x: auto;
                }}

                h1 {{
                    color: #111827;
                }}
            </style>
        </head>

        <body>

        <h1>Travel Agent Report</h1>

        <pre>{pretty_json}</pre>

        </body>
        </html>
    """

    with open(filename,"w",encoding="utf-8") as file:
        file.write(html)

    return filename


def run_scenario(scenario_number: int, scenario: dict):
    print()
    print("=" * 40)
    print(scenario["name"])
    print("=" * 40)
    print()

    started = time.perf_counter()

    response = requests.post(f"{BASE_URL}/plan", json={"message": scenario["message"]}, timeout=120)

    latency_ms = int((time.perf_counter() - started)* 1000)

    response.raise_for_status()

    payload = response.json()

    print(
        f"Status: "
        f"{payload.get('status', 'completed')}"
    )

    print(f"Latency: {latency_ms} ms")

    print("Agent says:")

    print(
        json.dumps(
            payload.get("travel_plan"),
            indent=2,
            ensure_ascii=False,
        )
    )

    print()

    print(
        "Agents called:",
        payload.get(
            "agents_called",
            [],
        ),
    )

    print(
        "Tools called:",
        payload.get(
            "tools_called",
            [],
        ),
    )

    report = save_report(
        scenario_number,
        payload,
    )

    print(
        f"Report saved: {report}"
    )


def main():

    for index, scenario in enumerate(
        SCENARIOS,
        start=1,
    ):

        run_scenario(
            index,
            scenario,
        )


if __name__ == "__main__":

    main()
