import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from loguru import logger

from services.resume_parser import call_resume_parser

router = APIRouter()

RESUMES_DIR = Path(__file__).resolve().parent.parent / "tmp" / "resumes"


def _resolve_filename(extracted_info: dict) -> str:
    """
    Derive a filename from the parsed response.
    Uses extracted_info.name if available, otherwise finds the next
    missing employee_N slot in RESUMES_DIR.
    """
    raw_name: str = extracted_info.get("name", "").strip()

    if raw_name and raw_name.lower() != "not available":
        # e.g. "Aryan Thakur" -> "Aryan_Thakur"
        safe = re.sub(r"\s+", "_", raw_name)
        safe = re.sub(r"[^\w\-]", "", safe)
        return safe

    # Fallback: find the lowest missing employee_N
    existing = {
        int(m.group(1))
        for f in RESUMES_DIR.glob("employee_*.json")
        if (m := re.fullmatch(r"employee_(\d+)", f.stem))
    }
    n = 1
    while n in existing:
        n += 1
    return f"employee_{n}"


@router.post("/parse-resume")
async def parse_resume(file: UploadFile = File(...)) -> JSONResponse:
    """
    Accept a PDF resume, forward it to resume_parser_api,
    and persist the structured response under tmp/resumes/<name>.json.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Call upstream parser
    try:
        parsed = await call_resume_parser(file)
    except RuntimeError as e:
        logger.error(f"Resume parser service error: {e}")
        raise HTTPException(status_code=502, detail=str(e))

    # Resolve filename and persist
    extracted_info = parsed.get("extracted_info", {})
    filename = _resolve_filename(extracted_info)

    RESUMES_DIR.mkdir(parents=True, exist_ok=True)
    dest = RESUMES_DIR / f"{filename}.json"

    with open(dest, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved resume to {dest}")

    return JSONResponse(
        content={
            "message": "Resume parsed and saved successfully.",
            "saved_as": str(dest),
            "data": parsed,
        }
    )