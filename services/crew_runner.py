"""
services/crew_runner.py
-----------------------
Copies generated YAML files from aryaman/output/ into the crewai_project structure,
builds a Docker image, runs the crew inside a clean container, then zips the output.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    print(f"[crew_runner] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Docker discovery
# ---------------------------------------------------------------------------

def _find_docker() -> str:
    """
    Find the docker executable. Checks PATH first, then Docker Desktop
    default install locations on Windows.
    Raises RuntimeError if not found.
    """
    docker = shutil.which("docker")
    if docker:
        _log(f"docker found on PATH: {docker}")
        return docker

    candidates = [
        r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        r"C:\ProgramData\DockerDesktop\version-bin\docker.exe",
        r"C:\Program Files\Docker\Docker\resources\bin\docker",
    ]
    for path in candidates:
        if Path(path).exists():
            _log(f"docker found at hardcoded path: {path}")
            return path

    raise RuntimeError(
        "docker executable not found on PATH or in Docker Desktop default locations.\n"
        "Make sure Docker Desktop is installed and running."
    )


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _get_project_root() -> Path:
    env_root = os.environ.get("NEURAX_ROOT")
    if env_root:
        root = Path(env_root)
        _log(f"PROJECT_ROOT from NEURAX_ROOT env: {root}")
        return root
    root = Path(__file__).resolve().parent.parent
    _log(f"PROJECT_ROOT resolved from __file__: {root}")
    return root


PROJECT_ROOT   = _get_project_root()
ARYAMAN_OUTPUT = PROJECT_ROOT / "aryaman" / "output"
CREW_PROJECT   = PROJECT_ROOT / "crewai_project"
CREW_SRC       = CREW_PROJECT / "src" / "crewai_project"
CREW_CONFIG    = CREW_SRC / "config"
ZIP_OUTPUT     = PROJECT_ROOT / "aryaman" / "crew_output.zip"
DOCKER         = _find_docker()

_log(f"ARYAMAN_OUTPUT : {ARYAMAN_OUTPUT}")
_log(f"CREW_PROJECT   : {CREW_PROJECT}")
_log(f"DOCKER         : {DOCKER}")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RunResult:
    stdout:       str
    stderr:       str
    returncode:   int
    zip_path:     Path | None  = None
    copied_files: list[str]    = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def _validate_sources() -> None:
    _log(f"Validating source files in {ARYAMAN_OUTPUT}")
    sources = [ARYAMAN_OUTPUT / "agents.yaml", ARYAMAN_OUTPUT / "tasks.yaml"]
    for p in sources:
        _log(f"  {p.name} exists={p.exists()}")
    missing = [p for p in sources if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing files in {ARYAMAN_OUTPUT}: "
            + ", ".join(p.name for p in missing)
        )
    _log("Source files OK")


def _copy_files() -> list[str]:
    pairs = [
        (ARYAMAN_OUTPUT / "agents.yaml", CREW_CONFIG / "agents.yaml"),
        (ARYAMAN_OUTPUT / "tasks.yaml",  CREW_CONFIG / "tasks.yaml"),
    ]
    copied: list[str] = []
    for src, dst in pairs:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst.name)
        _log(f"Copied {src.name} → {dst}")
    return copied


def _fix_yaml_documents() -> None:
    """Strip --- separators and disable human_input."""
    for yaml_file in [CREW_CONFIG / "agents.yaml", CREW_CONFIG / "tasks.yaml"]:
        content = yaml_file.read_text(encoding="utf-8")
        content = re.sub(r'^---\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'human_input:\s*true', 'human_input: false', content, flags=re.IGNORECASE)
        yaml_file.write_text(content, encoding="utf-8")
    _log("YAML documents fixed")


def _generate_crew_py() -> None:
    import yaml

    with (CREW_CONFIG / "agents.yaml").open() as f:
        agents = yaml.safe_load(f)
    with (CREW_CONFIG / "tasks.yaml").open() as f:
        tasks = yaml.safe_load(f)

    agent_keys = list(agents.keys())
    task_keys  = list(tasks.keys())
    model      = os.environ.get("MODEL", os.environ.get("CREW_MODEL", "gemini/gemini-2.0-flash"))

    lines = [
        "import os",
        "from crewai import Agent, Task, Crew, Process, LLM",
        "from crewai.project import CrewBase, agent, crew, task",
        "",
        "@CrewBase",
        "class MyCrew:",
        '    agents_config = "config/agents.yaml"',
        '    tasks_config  = "config/tasks.yaml"',
        "",
    ]
    for key in agent_keys:
        lines += [
            "    @agent",
            f"    def {key}(self) -> Agent:",
            f'        return Agent(config=self.agents_config["{key}"], verbose=True)',
            "",
        ]
    for key in task_keys:
        lines += [
            "    @task",
            f"    def {key}(self) -> Task:",
            f'        return Task(config=self.tasks_config["{key}"])',
            "",
        ]
    lines += [
        "    @crew",
        "    def crew(self) -> Crew:",
        f'        manager_llm = LLM(model=os.environ.get("MODEL", "{model}"))',
        "        return Crew(",
        "            agents=self.agents,",
        "            tasks=self.tasks,",
        "            process=Process.hierarchical,",
        "            manager_llm=manager_llm,",
        "            verbose=True,",
        "        )",
    ]
    (CREW_SRC / "crew.py").write_text("\n".join(lines), encoding="utf-8")
    _log(f"Generated crew.py — agents={agent_keys} tasks={task_keys}")


def _generate_main_py() -> None:
    content = (
        "import os\n"
        "from crewai_project.crew import MyCrew\n"
        "\n"
        "def run():\n"
        "    os.makedirs('output', exist_ok=True)\n"
        "    result = MyCrew().crew().kickoff()\n"
        "    print(result)\n"
    )
    (CREW_SRC / "main.py").write_text(content, encoding="utf-8")
    _log("Generated main.py")


def _write_crew_env() -> None:
    model   = os.environ.get("CREW_MODEL", "gemini-2.0-flash")
    api_key = os.environ.get("CREW_API_KEY", "")
    model_lower = model.lower()

    if "gemini" in model_lower:
        provider_key = f"GEMINI_API_KEY={api_key}"
        llm_model    = f"MODEL=gemini/{model}"
    elif "claude" in model_lower:
        provider_key = f"ANTHROPIC_API_KEY={api_key}"
        llm_model    = f"MODEL=anthropic/{model}"
    elif any(model_lower.startswith(p) for p in ("gpt-", "o1", "o3")):
        provider_key = f"OPENAI_API_KEY={api_key}"
        llm_model    = f"MODEL={model}"
    else:
        provider_key = f"GROQ_API_KEY={api_key}"
        llm_model    = f"MODEL=groq/{model}"

    (CREW_PROJECT / ".env").write_text(
        f"{provider_key}\n{llm_model}\n",
        encoding="utf-8",
    )
    _log(f"Wrote crewai_project/.env → {llm_model}")


def _docker_build() -> tuple[str, str, int]:
    _log(f"Building Docker image 'crewai-runner' from {CREW_PROJECT}")
    result = subprocess.run(
        [DOCKER, "build", "-t", "crewai-runner", "."],
        cwd=str(CREW_PROJECT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
    )
    _log(f"Docker build exit code: {result.returncode}")
    if result.returncode != 0:
        _log(f"Docker build stderr:\n{result.stderr}")
    return result.stdout, result.stderr, result.returncode


def _docker_run() -> tuple[str, str, int]:
    output_dir = CREW_PROJECT / "output"
    output_dir.mkdir(exist_ok=True)

    # Forward slashes required for Docker volume mounts on Windows
    output_dir_str = str(output_dir).replace("\\", "/")
    env_file       = str(CREW_PROJECT / ".env")

    _log(f"Starting Docker container — output volume: {output_dir_str}")

    process = subprocess.Popen(
        [
            DOCKER, "run", "--rm",
            "--name", "crewai-runner-live",
            "--env-file", env_file,
            "-v", f"{output_dir_str}:/app/output",
            "crewai-runner",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    for line in process.stdout:
        print(f"[crewai:out] {line}", end="", flush=True)
        stdout_lines.append(line)

    process.wait(timeout=600)

    for line in process.stderr:
        print(f"[crewai:err] {line}", end="", flush=True)
        stderr_lines.append(line)

    _log(f"Docker run exit code: {process.returncode}")
    return (
        "".join(stdout_lines),
        "".join(stderr_lines),
        process.returncode,
    )


def _zip_output() -> Path:
    _log(f"Zipping crewai_project → {ZIP_OUTPUT}")
    ZIP_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_OUTPUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in CREW_PROJECT.rglob("*"):
            if any(part in path.parts for part in ("__pycache__", ".venv", ".git")):
                continue
            if path.is_file():
                zf.write(path, path.relative_to(CREW_PROJECT))
    _log(f"Zip written to {ZIP_OUTPUT}")
    return ZIP_OUTPUT


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_crew(*, skip_zip: bool = False) -> RunResult:
    _log("=== run_crew() started ===")

    _validate_sources()
    copied = _copy_files()
    _fix_yaml_documents()
    _write_crew_env()
    _generate_crew_py()
    _generate_main_py()

    build_stdout, build_stderr, build_code = _docker_build()
    if build_code != 0:
        raise RuntimeError(
            f"Docker build failed (code {build_code}).\n"
            f"--- stdout ---\n{build_stdout}\n"
            f"--- stderr ---\n{build_stderr}"
        )
    _log("Docker build successful")

    stdout, stderr, returncode = _docker_run()
    if returncode != 0:
        raise RuntimeError(
            f"Docker run failed (code {returncode}).\n"
            f"--- stdout ---\n{stdout}\n"
            f"--- stderr ---\n{stderr}"
        )
    _log("Docker run successful")

    zip_path = None if skip_zip else _zip_output()

    _log("=== run_crew() complete ===")
    return RunResult(
        stdout       = stdout,
        stderr       = stderr,
        returncode   = returncode,
        zip_path     = zip_path,
        copied_files = copied,
    )