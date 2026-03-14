"""
routes/run_crew.py
------------------
FastAPI router:
  POST /crew-run          → copy files, docker build+run, return logs + zip url
  GET  /crew-download     → stream crew_output.zip
"""

from __future__ import annotations

import json
import subprocess
import traceback

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from services.crew_runner import ZIP_OUTPUT, run_crew, run_crew_streaming

router = APIRouter(tags=["Crew"])


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class RunCrewResponse(BaseModel):
    copied_files: list[str]  = Field(description="YAML files copied into crewai_project/config/")
    returncode:   int        = Field(description="Docker run exit code (0 = success)")
    stdout:       str        = Field(description="Captured stdout from the crew run")
    stderr:       str        = Field(description="Captured stderr from the crew run")
    zip_url:      str | None = Field(default=None, description="Hit GET /crew-download to grab the zip")


# ---------------------------------------------------------------------------
# POST /crew-run
# ---------------------------------------------------------------------------

@router.post(
    "/crew-run",
    response_model=RunCrewResponse,
    summary="Run the CrewAI project inside Docker",
    description=(
        "Copies agents.yaml + tasks.yaml from aryaman/output/ into crewai_project/, "
        "generates crew.py + main.py deterministically, builds a Docker image, "
        "runs the crew inside the container, zips the output, and returns logs."
    ),
)
async def run_crew_endpoint(
    skip_zip: bool = Query(default=False, description="Skip zipping the output"),
) -> RunCrewResponse:
    try:
        result = run_crew(skip_zip=skip_zip)

    except FileNotFoundError as exc:
        print(f"[run_crew] FileNotFoundError: {exc}", flush=True)
        traceback.print_exc()
        raise HTTPException(
            status_code=422,
            detail=f"Source files not ready: {exc}. Run POST /crew-generate first.",
        ) from exc

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Crew run timed out after 10 minutes.")

    except RuntimeError as exc:
        print(f"[run_crew] RuntimeError: {exc}", flush=True)
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except Exception as exc:
        print(f"[run_crew] Unexpected error: {exc}", flush=True)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}") from exc

    return RunCrewResponse(
        copied_files = result.copied_files,
        returncode   = result.returncode,
        stdout       = result.stdout,
        stderr       = result.stderr,
        zip_url      = "/crew-download" if result.zip_path else None,
    )


# ---------------------------------------------------------------------------
# POST /crew-run-stream  (Server-Sent Events — real-time Docker logs)
# ---------------------------------------------------------------------------

@router.post(
    "/crew-run-stream",
    summary="Run CrewAI in Docker and stream logs via SSE",
    description=(
        "Same pipeline as POST /crew-run but streams each log line as a "
        "Server-Sent Event so the browser can display output in real time."
    ),
)
def run_crew_stream_endpoint(
    skip_zip: bool = Query(default=False),
) -> StreamingResponse:

    def event_generator():
        try:
            for evt_type, stream, line in run_crew_streaming(skip_zip=skip_zip):
                payload = json.dumps({"type": evt_type, "stream": stream, "line": line})
                yield f"data: {payload}\n\n"
        except Exception as exc:
            payload = json.dumps({"type": "error", "stream": "", "line": str(exc)})
            yield f"data: {payload}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if proxied
        },
    )


# ---------------------------------------------------------------------------
# GET /crew-download
# ---------------------------------------------------------------------------

@router.get(
    "/crew-download",
    summary="Download the generated crewai_project as a zip",
    description="Streams crew_output.zip. Call POST /crew-run first.",
    response_class=FileResponse,
)
async def download_zip() -> FileResponse:
    if not ZIP_OUTPUT.exists():
        raise HTTPException(
            status_code=404,
            detail="No zip found. Run POST /crew-run first.",
        )
    return FileResponse(
        path       = str(ZIP_OUTPUT),
        media_type = "application/zip",
        filename   = "crew_output.zip",
    )