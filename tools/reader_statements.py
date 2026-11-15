"""Reader-facing projections of the two checked historical results."""
from __future__ import annotations

from typing import Any

FORMS = {"R01": ("window_cohort", "revocation-windows-v1"),
         "R04": ("event_order", "bridge-opener-log-v1")}


def render_statement(case_id: str, result: dict[str, Any]) -> str:
    if case_id == "R04":
        times = result["opener_timing"]
        return ("The bridge logged that it treated the still-running helper as the browser. "
                f"It reported success {times['running_to_success_ms']} ms later. "
                f"The bridge logged helper exit {times['exit_code']} another "
                f"{times['success_to_exit_ms']} ms after success.")
    if case_id != "R01":
        raise ValueError("Unknown reader statement form")
    selection = {"retrospective": "retrospectively selected",
                 "before_measurement": "predeclared"}[result["selection"]]
    confirmed, total = result["confirmed"], result["declared"]
    unknown, contradicted = result["unknown"], result["contradicted"]
    routes = result["profiles_by_route"]
    profile_counts = {len(profiles) for profiles in routes.values()}
    scope = f"across {len(routes)} routes"
    if len(profile_counts) == 1:
        scope += f" with {next(iter(profile_counts))} authentication profiles per route"
    sentences = [f"Absence of a provider revocation request was confirmed in {confirmed} of "
                 f"{total} {selection} base windows {scope}.",
                 f"Confirmation requires at least {result['minimum_seconds']} seconds of observation "
                 "after the operation acknowledgement."]
    if unknown:
        sentences.append(f"{unknown} window remains unknown." if unknown == 1
                         else f"{unknown} windows remain unknown.")
    if contradicted:
        noun = "window" if contradicted == 1 else "windows"
        sentences.append(f"The provider received a revocation request in {contradicted} {noun}.")
    return " ".join(sentences)


def reader_intro(statements: dict[str, str]) -> str:
    """The checked page prefix ends immediately before the reproduction instructions."""
    return ("# Evidence for two historical observations\n\n"
            "## R01: provider revocation windows\n\n" + statements["R01"] + "\n\n"
            "[Declared run IDs and computed counts](R01.json) · "
            "[Base windows and control](../disconnect/bench/RESULTS.json) · "
            "[Recorded excerpts](../disconnect/bench/receipts/R01.json)\n\n"
            "## R04: bridge log order\n\n" + statements["R04"] + "\n\n"
            "[Messages, line numbers and intervals](R04.json) · "
            "[Reviewed capture](r04-timing.json) · "
            "[Recorded excerpts](../matrix/receipts/R04.json)\n\n")
