"""
module2/triage_agent.py
Build Your First AI Agent — Module 2 exercise script.

Your task: fill in the SYSTEM_PROMPT and complete the run_agent() function
so the agent reads sample_log.txt, calls Claude, and returns a structured
JSON diagnosis.

Usage
-----
    python module2/triage_agent.py              # real API call
    python module2/triage_agent.py --mock       # mock mode (no API key needed)
    MOCK_MODE=1 python module2/triage_agent.py  # same as --mock via env var

What you need to fill in
------------------------
1. SYSTEM_PROMPT: define the agent's role and output schema (JSON keys).
2. run_agent(): load the sample log, call ask(), return the result dict.

Reference implementation: module2/solutions/solution.py
"""

import os
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.claude_client import ask
from shared.output import save_json, to_step_summary, to_github_issue

# ── Mock mode ────────────────────────────────────────────────────────────────
MOCK_MODE = "--mock" in sys.argv or os.environ.get("MOCK_MODE") == "1"

MOCK_RESPONSE = {
    "summary":
        "The Node.js test suite failed with 3 assertion errors in "
        "auth.test.js. Memory climbed to 87% during the run.",
    "likely_cause":
        "Test fixtures are not cleaned up between test cases, retaining heap "
        "references and causing assertion failures on retry.",
    "next_step":
        "Add explicit cleanup in the afterEach hook and reduce the fixture "
        "dataset from 10,000 to 100 records.",
    "confidence":
        "HIGH",
    "escalate":
        False,
}

# TODO: Write your system prompt here.
# Your prompt must instruct Claude to:
#   1. Take the role of a CI/CD triage agent
#   2. Analyse the build log provided by the user
#   3. Return ONLY valid JSON — no explanation, no markdown,
#      just the JSON object
#   4. Include exactly these keys:
#      - summary      (string)            one sentence describing what failed
#      - likely_cause (string)            one sentence on the root cause
#      - next_step    (string)            one concrete remediation action
#      - confidence   (HIGH|MEDIUM|LOW)   your confidence in the diagnosis
#      - escalate     (boolean)           true only if the issue needs human
#                                         intervention
#
# Hint: be explicit about when escalate should be true vs false.
# Check solutions/solution.py only after you have made your own attempt.
SYSTEM_PROMPT = """
You are a CI/CD diagnostic agent specialized in analyzing pipeline failures,
build errors, and deployment issues.

Your job is to examine logs, error messages, and contextual information to
identify the root cause of failures and recommend actionable next steps.

You MUST respond with ONLY valid JSON — no prose, no markdown, no code fences,
no explanation before or after.

Required JSON structure:
{
  "diagnosis":
    "<string: the root cause of the failure>",
  "confidence":
    "<HIGH | MEDIUM | LOW>",
  "recommended_action":
    "<string: a concrete, specific next step to resolve the issue>",
  "escalate":
    <true | false>
}

Field rules:
- diagnosis: Be specific. Name the failing step, service, or component and what
  went wrong (e.g. "Unit test 'test_auth.py::test_login' failed due to a 
  missing environment variable: DATABASE_URL").
- confidence: Set to HIGH only when the root cause is explicitly confirmed in 
  the provided logs or output. Use MEDIUM when the cause is strongly implied 
  but not directly shown. Use LOW when you are inferring from 
  limited information.
- recommended_action: Provide a concrete next step a developer can act on 
  immediately (e.g. "Add DATABASE_URL to the CI environment secrets in the 
  repository settings").
- escalate: Set to true if the failure involves a production deployment, 
  security concern, data loss risk, or any situation where a human must 
  review before taking action.

Do not include any text outside the JSON object.
"""

REQUIRED_JSON_KEYS = ["diagnosis", "confidence", "recommended_action", "escalate"]

CONFIDENCE_LEVELS = {"HIGH", "MEDIUM", "LOW"}

AGENT_CONFIG = {
    "model": "claude-opus-4-5-20251101",
    "max_tokens": 1024,
    "max_iterations": 3,
    "context_fields": [
        "log_snippet",
        "build_number",
        "repo"
    ]
}


def load_sample() -> str:
    """Load the CI failure log from sample_log.txt."""
    sample = Path(__file__).parent / "sample_log.txt"
    return sample.read_text()


def run_agent() -> dict:
    """
    TODO: Complete this function.

    Steps:
    1. Load the sample log using load_sample().
    2. If MOCK_MODE is True, return MOCK_RESPONSE directly
        (already done for you).
    3. Otherwise, call ask() with SYSTEM_PROMPT and the
        log as the user message.
    4. Return the result dict.
    """
    log_content = load_sample()

    if MOCK_MODE:
        print("[MOCK MODE] Skipping Claude API — returning "
              "pre-defined response.")
        print("[MOCK MODE] Set ANTHROPIC_API_KEY and remove "
              "--mock to call the real API.\n")
        return MOCK_RESPONSE

    return ask(
        system=SYSTEM_PROMPT,
        user=f"CI failure log:\n\n{log_content}",
        model=AGENT_CONFIG["model"],
        max_tokens=AGENT_CONFIG["max_tokens"]
    )


def main():
    result = run_agent()

    print(json.dumps(result, indent=2))
    save_json(result, module=2)
    print(to_step_summary(result, title="Module 2 Triage Agent Result"))

    if result.get("escalate"):
        print("\n🔴 ESCALATION REQUIRED — creating GitHub Issue body:")
        print(to_github_issue(result, module=2))
    else:
        print("\n✅ No escalation — agent produced a self-contained fix")

    return result


if __name__ == "__main__":
    main()
