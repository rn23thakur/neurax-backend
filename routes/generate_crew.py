"""
routes/generate_crew.py
-----------------------
FastAPI router that exposes POST /crew/generate.

The route:
  1. Delegates all heavy work to services.crew_generator.run_generation()
  2. Returns a JSON response that includes:
       - the paths of files written to disk
       - the raw YAML content of agents.yaml and tasks.yaml
         (so callers don't need a second round-trip to read the files)
       - any newly-created agent names reported by the LLM
  3. Maps all exceptions to sensible HTTP status codes.

Mount in main.py:
    from routes.generate_crew import router as crew_router
    app.include_router(crew_router)
"""

from __future__ import annotations

import traceback
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.crew_generator import run_generation

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class GenerateCrewResponse(BaseModel):
    """
    Everything the caller needs after a successful generation run.

    written_files  – filename → absolute path on disk
    agents_yaml    – raw YAML string for agents.yaml
    tasks_yaml     – raw YAML string for tasks.yaml
    new_agents     – agent names the LLM created that weren't in the input
    output_dir     – absolute path to the directory that was written
    generated_at   – UTC timestamp of this run
    """
    written_files: dict[str, str] = Field(
        description="Map of filename → absolute path on disk"
    )
    agents_yaml: str | None = Field(
        default=None,
        description="Raw content of the generated agents.yaml"
    )
    tasks_yaml: str | None = Field(
        default=None,
        description="Raw content of the generated tasks.yaml"
    )
    new_agents: list[str] = Field(
        default_factory=list,
        description="Agent names that were newly created by the LLM"
    )
    output_dir: str = Field(
        description="Absolute path to the directory where files were written"
    )
    generated_at: str = Field(
        description="UTC ISO-8601 timestamp"
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/crew-generate",
    response_model=GenerateCrewResponse,
    summary="Generate a CrewAI project from tasks + resumes",
    description=(
        "Reads tasks from .taskmaster/tasks/tasks.json and resumes from "
        "tmp/resumes/*.json, calls the configured LLM (CREW_MODEL / CREW_API_KEY), "
        "writes agents.yaml, tasks.yaml, crew.py, and main.py into "
        "aryaman/<output_subdir>/, and returns the YAML files in the response body."
    ),
)
async def generate_crew(
    output_subdir: str = Query(
        default="output",
        description=(
            "Sub-folder inside aryaman/ to write files into. "
            "Pass a unique value (e.g. a timestamp) to keep runs isolated."
        ),
    ),
) -> GenerateCrewResponse:
    """
    Trigger a full crew-generation run.

    - **output_subdir**: where inside `aryaman/` the files land (default: `output`)
    """
    try:
        result = run_generation(output_subdir=output_subdir)

    except FileNotFoundError as exc:
        # Missing tasks.json, resumes dir, or prompt.txt → 422 so the caller
        # knows it's a configuration/data problem, not a server bug.
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except EnvironmentError as exc:
        # CREW_API_KEY not set
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    except RuntimeError as exc:
        # LLM returned incomplete output (missing sections)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except Exception as exc:                        # noqa: BLE001
        # Catch-all: log full traceback server-side, return a terse 500
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during generation: {exc}",
        ) from exc

    return GenerateCrewResponse(
        written_files = {k: str(v) for k, v in result.written_files.items()},
        agents_yaml   = result.agents_yaml,
        tasks_yaml    = result.tasks_yaml,
        new_agents    = result.new_agents,
        output_dir    = str(result.output_dir),
        generated_at  = datetime.now(timezone.utc).isoformat(),
    )