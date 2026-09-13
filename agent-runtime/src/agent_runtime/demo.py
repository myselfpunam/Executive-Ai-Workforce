"""A deterministic stand-in for the "Sales Research Agent" shown in the
dashboard mockup: retrieval -> model -> tool -> action, no real network calls.
"""

from __future__ import annotations

from .loop import DemoAgent, Step


def build_sales_research_agent() -> DemoAgent:
    return DemoAgent(
        name="Sales Research Agent",
        steps=[
            Step("retrieval", lambda: {"companies_read": 18, "source": "twenty_crm"}),
            Step("model", lambda: {"draft": "Hi {name}, following up on..."}),
            Step("tool", lambda: {"validated_email": True}),
            Step("action", lambda: {"queued_for_delivery": True}),
        ],
    )


if __name__ == "__main__":
    agent = build_sales_research_agent()
    run = agent.run()
    print(f"run_id={run.run_id} status={run.status}")
    for event in run.events:
        print(f"  {event.occurred_at}  {event.type:16s} step={event.step_id} data={event.data}")
