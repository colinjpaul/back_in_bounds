"""
==============================================================================
BACK IN BOUNDS - AUTONOMOUS AI QA AGENT
==============================================================================
Framework: Claude API (manual tool-use loop) + Playwright (Python sync API)
Target: Running Dash Web Application (http://127.0.0.1:8050)

This is a ReAct-style agent: on every turn Claude sees a system prompt, the
running transcript, and a fixed set of Playwright tools; it picks one tool,
we execute it for real against the live browser, feed the result back as a
`tool_result`, and repeat until Claude calls `finish` (or --max-steps runs
out). There is no scripted list of steps - the loop and the tool set are the
only fixed part.

Self-healing locators: the agent is never given a hardcoded map of element
IDs. It calls `snapshot` to read the live DOM (every visible element with an
id, role, button, link or input, plus its text) and chooses selectors from
that, the same way a human tester would look at the page before clicking.
If an ID changes between app versions, the agent adapts instead of failing.

To run on your local Mac:
  1. pip install anthropic
  2. export ANTHROPIC_API_KEY=sk-ant-...
  3. playwright install chromium   (if not already installed)
  4. python golf_app_v8.py                     (in Terminal 1)
  5. python qa_agent.py                        (in Terminal 2)

Each run writes a Markdown defect report + screenshots to
reports/qa_agent_run_<timestamp>/.
==============================================================================
"""

import argparse
import os
import sys
from datetime import datetime

import anthropic
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8050"
DEFAULT_MODEL = "claude-opus-5"
DEFAULT_MAX_STEPS = 20

DEFAULT_GOAL = (
    "Explore the Back in Bounds golf analytics app. Visit both tabs "
    "('Round Analysis' and 'Range Sessions'), interact with the course "
    "selector, hole selector and club selector dropdowns, and check that "
    "the page updates in a way that makes sense (numbers change, no tab or "
    "dropdown leaves the page blank, no stale data left over from the "
    "previous selection). Report any defect you actually observe - do not "
    "report anything you have not personally seen with a tool call."
)

SYSTEM_PROMPT = """You are an autonomous QA agent testing a live Dash web app at {base_url}.

You interact with the app exclusively through the tools provided - you have no other way to see or act on the page. You have already been given a `snapshot` of the page as it loaded, in the first message.

Rules:
- Before clicking anything you have not already seen in a snapshot, call `snapshot` to read the current DOM rather than guessing a selector.
- `click` and `get_text` accept a CSS selector, or Playwright's `text=exact visible text` syntax for elements without a stable id (e.g. a dropdown option).
- Take a `screenshot` whenever you see something that looks wrong, before calling `report_defect` - the screenshot is the evidence a human reviewer will check.
- Only call `report_defect` for something you actually observed via a tool result in this conversation. Do not report a defect you are merely suspicious of.
- You have a budget of {max_steps} tool calls for this entire run. When you have covered the goal (or decided it's unreachable), call `finish` with a short summary - do not keep exploring past the point of diminishing returns.
"""

TOOLS = [
    {
        "name": "navigate",
        "description": "Navigate the browser to a URL.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
            "additionalProperties": False,
        },
    },
    {
        "name": "snapshot",
        "description": (
            "Read the current page: returns every visible element that has an id, "
            "or is a button/link/input/tab, along with its tag, id, role and text. "
            "Call this before clicking a selector you are not already sure of."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "click",
        "description": "Click the first element matching a Playwright selector (CSS or 'text=...').",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": ["selector"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_text",
        "description": "Return the visible text content of the first element matching a selector.",
        "input_schema": {
            "type": "object",
            "properties": {"selector": {"type": "string"}},
            "required": ["selector"],
            "additionalProperties": False,
        },
    },
    {
        "name": "screenshot",
        "description": "Save a screenshot of the current page and return its file path.",
        "input_schema": {
            "type": "object",
            "properties": {"label": {"type": "string", "description": "Short slug for the filename, e.g. 'blank-club-selector'."}},
            "required": ["label"],
            "additionalProperties": False,
        },
    },
    {
        "name": "report_defect",
        "description": "Log a defect you have personally observed via a prior tool result.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                "description": {"type": "string", "description": "What you did, what you expected, what you saw instead."},
            },
            "required": ["title", "severity", "description"],
            "additionalProperties": False,
        },
    },
    {
        "name": "finish",
        "description": "End the run. Call this once the goal has been covered or is unreachable.",
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
            "additionalProperties": False,
        },
    },
]

SETTLE_MS = 400  # let a Dash callback re-render before the next snapshot/click

# Anthropic first-party API pricing, $ per 1M tokens (input, output). Used only
# for the rough cost estimate this script prints/writes - not billing-accurate
# (ignores prompt-cache discounts), but close enough to sanity-check a run.
MODEL_PRICING = {
    "claude-opus-5": (5.00, 25.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-haiku-4-5": (1.00, 5.00),
}


def estimate_cost(model, input_tokens, output_tokens):
    pricing = MODEL_PRICING.get(model)
    if pricing is None:
        return None
    in_rate, out_rate = pricing
    return (input_tokens / 1_000_000) * in_rate + (output_tokens / 1_000_000) * out_rate


def slugify(text):
    keep = [c if c.isalnum() else "-" for c in text.strip().lower()]
    slug = "".join(keep).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug[:60] or "screenshot"


class ToolExecutionError(Exception):
    pass


class QAAgentSession:
    """Owns the live browser page and the transcript/defect log for one run."""

    def __init__(self, page, run_dir):
        self.page = page
        self.run_dir = run_dir
        self.transcript = []
        self.defects = []
        self.shot_count = 0

    def navigate(self, tool_input):
        url = tool_input["url"]
        self.page.goto(url, timeout=15000)
        self.page.wait_for_timeout(SETTLE_MS)
        return f"Navigated to {url}. Title: {self.page.title()!r}"

    def snapshot(self, tool_input):
        elements = self.page.evaluate(
            """
            () => {
                const out = [];
                const seen = new Set();
                const nodes = document.querySelectorAll(
                    '[id], button, a, input, select, [role="button"], [role="tab"], h1, h2, h3'
                );
                for (const el of nodes) {
                    if (out.length >= 80) break;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') continue;
                    const rect = el.getBoundingClientRect();
                    if (rect.width === 0 && rect.height === 0) continue;
                    const id = el.id || '';
                    if (id) {
                        if (seen.has(id)) continue;
                        seen.add(id);
                    }
                    const text = (el.innerText || el.value || '')
                        .trim().slice(0, 80).replace(/\\s+/g, ' ');
                    out.push({
                        tag: el.tagName.toLowerCase(),
                        id: id,
                        role: el.getAttribute('role') || '',
                        text: text,
                    });
                }
                return out;
            }
            """
        )
        if not elements:
            return "No visible interactive elements found on the page."
        lines = [f"{e['tag']}#{e['id'] or '(no id)'} role={e['role'] or '-'} text={e['text']!r}" for e in elements]
        return "\n".join(lines)

    def click(self, tool_input):
        selector = tool_input["selector"]
        self.page.click(selector, timeout=5000)
        self.page.wait_for_timeout(SETTLE_MS)
        return f"Clicked {selector!r}."

    def get_text(self, tool_input):
        selector = tool_input["selector"]
        text = self.page.locator(selector).inner_text(timeout=5000)
        return text.strip()

    def screenshot(self, tool_input):
        self.shot_count += 1
        filename = f"{self.shot_count:02d}-{slugify(tool_input['label'])}.png"
        path = os.path.join(self.run_dir, filename)
        self.page.screenshot(path=path)
        return f"Saved screenshot to {filename}"

    def report_defect(self, tool_input):
        self.defects.append(dict(tool_input))
        return f"Defect logged: {tool_input['title']}"


def build_tool_result(block_id, content, is_error=False):
    result = {"type": "tool_result", "tool_use_id": block_id, "content": content}
    if is_error:
        result["is_error"] = True
    return result


def run_agent(goal, base_url, model, max_steps, headless, effort):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set. Export it before running this agent.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic()
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = os.path.join("reports", f"qa_agent_run_{run_id}")
    os.makedirs(run_dir, exist_ok=True)

    system_prompt = SYSTEM_PROMPT.format(base_url=base_url, max_steps=max_steps)
    finish_summary = None

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        session = QAAgentSession(page, run_dir)
        handlers = {
            "navigate": session.navigate,
            "snapshot": session.snapshot,
            "click": session.click,
            "get_text": session.get_text,
            "screenshot": session.screenshot,
            "report_defect": session.report_defect,
        }

        try:
            opening = session.navigate({"url": base_url})
            initial_snapshot = session.snapshot({})
            first_message = (
                f"Goal: {goal}\n\n"
                f"{opening}\n\nInitial page snapshot:\n{initial_snapshot}"
            )
            messages = [{"role": "user", "content": first_message}]
            total_input_tokens = 0
            total_output_tokens = 0

            for step in range(1, max_steps + 1):
                response = client.messages.create(
                    model=model,
                    max_tokens=4096,
                    system=system_prompt,
                    tools=TOOLS,
                    output_config={"effort": effort},
                    messages=messages,
                )
                messages.append({"role": "assistant", "content": response.content})

                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens
                print(
                    f"[step {step}] tokens: in={response.usage.input_tokens} "
                    f"out={response.usage.output_tokens} "
                    f"(running total: in={total_input_tokens} out={total_output_tokens})"
                )

                for block in response.content:
                    if block.type == "text" and block.text.strip():
                        print(f"[step {step}] Claude: {block.text.strip()}")

                tool_uses = [b for b in response.content if b.type == "tool_use"]
                if not tool_uses:
                    break

                tool_results = []
                stop_requested = False
                for block in tool_uses:
                    if block.name == "finish":
                        finish_summary = block.input.get("summary", "")
                        print(f"[step {step}] finish: {finish_summary}")
                        tool_results.append(build_tool_result(block.id, "Run finished."))
                        stop_requested = True
                        continue

                    handler = handlers.get(block.name)
                    print(f"[step {step}] {block.name}({block.input})")
                    try:
                        if handler is None:
                            raise ToolExecutionError(f"Unknown tool: {block.name}")
                        result_text = handler(block.input)
                        session.transcript.append({"step": step, "tool": block.name, "input": block.input, "result": result_text})
                        tool_results.append(build_tool_result(block.id, result_text))
                    except Exception as exc:
                        error_text = f"{type(exc).__name__}: {exc}"
                        session.transcript.append({"step": step, "tool": block.name, "input": block.input, "result": f"ERROR: {error_text}"})
                        tool_results.append(build_tool_result(block.id, error_text, is_error=True))

                messages.append({"role": "user", "content": tool_results})
                if stop_requested:
                    break
            else:
                finish_summary = finish_summary or f"Reached the {max_steps}-step budget before the agent called finish."
        finally:
            browser.close()

    cost = estimate_cost(model, total_input_tokens, total_output_tokens)
    cost_line = f"${cost:.4f}" if cost is not None else "unknown (model not in MODEL_PRICING)"
    print(
        f"\nTotal tokens: in={total_input_tokens} out={total_output_tokens} "
        f"| estimated cost: {cost_line}"
    )

    write_report(
        run_dir, run_id, goal, base_url, model, session.transcript, session.defects,
        finish_summary, total_input_tokens, total_output_tokens, cost,
    )
    print(f"Report written to {os.path.join(run_dir, 'report.md')}")
    return session.defects


def write_report(run_dir, run_id, goal, base_url, model, transcript, defects, summary,
                  total_input_tokens, total_output_tokens, cost):
    cost_line = f"${cost:.4f}" if cost is not None else "unknown (model not in MODEL_PRICING)"
    lines = [
        "# QA Agent Run Report",
        "",
        f"- **Run ID:** {run_id}",
        f"- **Target:** {base_url}",
        f"- **Model:** {model}",
        f"- **Goal:** {goal}",
        f"- **Steps executed:** {len(transcript)}",
        f"- **Defects found:** {len(defects)}",
        f"- **Tokens:** in={total_input_tokens} out={total_output_tokens}",
        f"- **Estimated cost:** {cost_line}",
        "",
        "## Summary",
        "",
        summary or "(agent did not provide a closing summary)",
        "",
        "## Defects",
        "",
    ]

    if not defects:
        lines.append("No defects reported.")
    else:
        for i, d in enumerate(defects, 1):
            lines += [
                f"### {i}. {d['title']} ({d['severity']})",
                "",
                d["description"],
                "",
            ]

    lines += ["", "## Full Tool Call Transcript", ""]
    for entry in transcript:
        lines.append(f"**Step {entry['step']} - `{entry['tool']}`** `{entry['input']}`")
        lines.append("")
        lines.append(f"> {entry['result']}")
        lines.append("")

    with open(os.path.join(run_dir, "report.md"), "w") as f:
        f.write("\n".join(lines))


def parse_args():
    parser = argparse.ArgumentParser(description="Autonomous AI QA agent for the Back in Bounds Dash app.")
    parser.add_argument("--goal", default=DEFAULT_GOAL, help="Natural-language exploration goal for the agent.")
    parser.add_argument("--base-url", default=BASE_URL, help="URL of the running Dash app.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Claude model ID to use.")
    parser.add_argument("--max-steps", type=int, default=DEFAULT_MAX_STEPS, help="Maximum tool calls before the run is cut off.")
    parser.add_argument("--effort", default="low", choices=["low", "medium", "high", "xhigh", "max"], help="Reasoning effort per turn.")
    parser.add_argument("--headed", action="store_true", help="Show the browser window instead of running headless.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_agent(
        goal=args.goal,
        base_url=args.base_url,
        model=args.model,
        max_steps=args.max_steps,
        headless=not args.headed,
        effort=args.effort,
    )
