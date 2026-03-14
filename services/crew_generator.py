"""
services/crew_generator.py
--------------------------
Service layer that wraps the core generation logic.

Responsibilities:
  - Load tasks from  .taskmaster/tasks/tasks.json
  - Walk tmp/resumes/ and collect all *.json files into a list of dicts
  - Read CREW_MODEL and CREW_API_KEY from environment / .env
  - Build the LangChain LLM (Groq by default, swap freely)
  - Call generate_crew_project() and return a GenerationResult
  - Sanitise raw LLM output (strip fences, normalise paths)
  - Write files to  aryaman/<output_subdir>/
  - Return YAML content in the result so the route can send it back

Directory layout assumed (relative to project root):
    .taskmaster/tasks/tasks.json   – task breakdown
    tmp/resumes/<name>.json        – one file per engineer resume
    aryaman/prompt.txt             – system prompt
    aryaman/<subdir>/              – generated output lands here
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from langchain_core.language_models import BaseChatModel, BaseLLM
from langchain_core.messages import HumanMessage, SystemMessage

# ---------------------------------------------------------------------------
# Project root – everything is resolved relative to this so the service works
# regardless of where uvicorn / the test runner is invoked from.
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent   # neurax/

TASKS_PATH   = PROJECT_ROOT / ".taskmaster" / "tasks" / "tasks.json"
RESUMES_DIR  = PROJECT_ROOT / "tmp" / "resumes"
PROMPT_PATH  = PROJECT_ROOT / "aryaman" / "prompt.txt"
OUTPUT_BASE  = PROJECT_ROOT / "aryaman"

# XML tags the LLM is expected to wrap each file in
_SECTIONS: list[tuple[str, str]] = [
    ("agents.yaml", "agents.yaml"),
    ("tasks.yaml",  "tasks.yaml"),
    ("crew.py",     "crew.py"),
    ("main.py",     "main.py"),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class GenerationResult:
    """Carries everything the route needs to build its response."""

    def __init__(
        self,
        output_dir: Path,
        written_files: dict[str, Path],
        agents_yaml: str | None,
        tasks_yaml: str | None,
        new_agents: list[str],
    ):
        self.output_dir    = output_dir
        self.written_files = written_files   # filename → absolute Path
        self.agents_yaml   = agents_yaml     # raw YAML string (or None)
        self.tasks_yaml    = tasks_yaml      # raw YAML string (or None)
        self.new_agents    = new_agents      # list of newly created agent names


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _load_tasks() -> dict[str, Any]:
    if not TASKS_PATH.exists():
        raise FileNotFoundError(f"tasks.json not found at {TASKS_PATH}")
    with TASKS_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_resumes() -> list[dict[str, Any]]:
    """
    Walk tmp/resumes/ recursively and parse every *.json file.
    Returns a list of dicts – one per resume file.
    """
    if not RESUMES_DIR.exists():
        raise FileNotFoundError(f"Resumes directory not found at {RESUMES_DIR}")

    resumes: list[dict[str, Any]] = []
    for path in sorted(RESUMES_DIR.rglob("*.json")):
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        # Attach the stem name so the LLM knows who it belongs to
        if isinstance(data, dict):
            data.setdefault("_source_file", path.stem)
        resumes.append(data)

    if not resumes:
        raise ValueError(f"No resume JSON files found under {RESUMES_DIR}")

    return resumes


def _load_prompt() -> str:
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"prompt.txt not found at {PROMPT_PATH}")
    return PROMPT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# LLM factory  (reads CREW_MODEL + CREW_API_KEY from env)
# ---------------------------------------------------------------------------

def _build_llm() -> BaseChatModel:
    """
    Build a LangChain chat model driven entirely by env vars.

    CREW_MODEL   – e.g. "llama-3.3-70b-versatile" (Groq) or "gpt-4o" (OpenAI)
    CREW_API_KEY – the provider API key

    Provider is inferred from the model name prefix:
      • starts with "gpt-"  or "o1"  → OpenAI
      • starts with "claude"          → Anthropic
      • starts with "gemini"          → Google
      • everything else               → Groq  (default)
    """
    model   = os.environ.get("CREW_MODEL",   "llama-3.3-70b-versatile")
    api_key = os.environ.get("CREW_API_KEY", "")

    if not api_key:
        raise EnvironmentError(
            "CREW_API_KEY is not set. Add it to your .env file."
        )

    model_lower = model.lower()

    if model_lower.startswith(("gpt-", "o1", "o3")):
        from langchain_openai import ChatOpenAI          # type: ignore
        return ChatOpenAI(model=model, temperature=0.2, api_key=api_key)

    if model_lower.startswith("claude"):
        from langchain_anthropic import ChatAnthropic   # type: ignore
        return ChatAnthropic(model=model, temperature=0.2, api_key=api_key)

    if model_lower.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI  # type: ignore
        return ChatGoogleGenerativeAI(model=model, temperature=0.2, google_api_key=api_key)

    # Default → Groq
    from langchain_groq import ChatGroq                 # type: ignore
    return ChatGroq(model=model, temperature=0.2, api_key=api_key)


# ---------------------------------------------------------------------------
# Output sanitisation helpers
# ---------------------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """Remove ```yaml / ```python / ``` fences models sometimes add."""
    text = re.sub(r"^```[a-zA-Z]*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"^```\s*$",        "", text, flags=re.MULTILINE)
    return text.strip()


def _extract_section(raw: str, tag: str) -> str | None:
    """Pull content from <tag>…</tag> in the LLM response."""
    pattern = rf"<{re.escape(tag)}>(.*?)</{re.escape(tag)}>"
    match   = re.search(pattern, raw, re.DOTALL)
    if match:
        return match.group(1).strip("\n")
    return None


def _rewrite_output_paths(content: str, output_dir: Path) -> str:
    """
    TODO: if crew.py or main.py hardcode relative paths like
    "output/agents.yaml" we can rewrite them here to point at the
    actual aryaman/<subdir>/ location.  Implement per-project as needed.
    """
    # Example (uncomment and adjust pattern when you know the exact strings):
    # content = content.replace('output/', str(output_dir) + '/')
    return content


def _write_file(directory: Path, filename: str, content: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / filename
    target.write_text(content, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Core generation call  (thin wrapper so routes stay clean)
# ---------------------------------------------------------------------------

def run_generation(output_subdir: str = "output") -> GenerationResult:
    """
    Orchestrate the full pipeline and return a GenerationResult.

    Parameters
    ----------
    output_subdir : sub-folder inside aryaman/ where files are written.
                    Defaults to "output".  You could pass a timestamp or
                    job-id from the route to keep runs isolated.
    """
    tasks   = _load_tasks()
    resumes = _load_resumes()
    prompt  = _load_prompt()
    llm     = _build_llm()

    output_dir = OUTPUT_BASE / output_subdir

    # --- Resolve prompt placeholders ---
    tasks_str   = json.dumps(tasks,   indent=2)
    resumes_str = json.dumps(resumes, indent=2)

    resolved_prompt = (
        prompt
        .replace("{tasks_json}",  tasks_str)
        .replace("{resume_json}", resumes_str)
    )

    # --- Invoke LLM ---
    messages = [
        SystemMessage(content=resolved_prompt),
        HumanMessage(
            content=(
                "Generate the four CrewAI project files now. "
                "Return ONLY the tagged sections as specified. "
                "Do NOT include any explanations outside the tags."
            )
        ),
    ]
    response   = llm.invoke(messages)
    raw_output: str = response.content  # type: ignore[attr-defined]

    # --- Parse sections ---
    written:    dict[str, Path] = {}
    missing:    list[str]       = []
    agents_yaml: str | None     = None
    tasks_yaml:  str | None     = None

    for xml_tag, filename in _SECTIONS:
        content = _extract_section(raw_output, xml_tag)
        if content is None:
            missing.append(xml_tag)
            continue

        clean = _strip_code_fences(content)
        clean = _rewrite_output_paths(clean, output_dir)

        dest = _write_file(output_dir, filename, clean)
        written[filename] = dest

        # Stash YAML strings so the route can return them directly
        if filename == "agents.yaml":
            agents_yaml = clean
        elif filename == "tasks.yaml":
            tasks_yaml = clean

    if missing:
        raise RuntimeError(
            f"The following sections were missing from the LLM response: {missing}.\n"
            f"Raw output (first 2 000 chars):\n{raw_output[:2000]}"
        )

    # --- Capture new_agents_created metadata ---
    new_agents_raw = _extract_section(raw_output, "new_agents_created")
    new_agents: list[str] = []
    if new_agents_raw:
        new_agents = [
            line.strip()
            for line in new_agents_raw.splitlines()
            if line.strip() and line.strip().lower() != "none"
        ]

    return GenerationResult(
        output_dir    = output_dir,
        written_files = written,
        agents_yaml   = agents_yaml,
        tasks_yaml    = tasks_yaml,
        new_agents    = new_agents,
    )