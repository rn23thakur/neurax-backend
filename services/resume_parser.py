import httpx
from fastapi import UploadFile
from loguru import logger

RESUME_PARSER_URL = "http://127.0.0.1:8001/api/v1/resume/parse"


async def call_resume_parser(file: UploadFile) -> dict:
    """
    Forward the uploaded PDF to resume_parser_api and return the parsed response.

    Args:
        file: The uploaded PDF file from the neurax route.

    Returns:
        Parsed response dict from resume_parser_api.

    Raises:
        RuntimeError: If the upstream API call fails.
    """
    file_bytes = await file.read()

    async with httpx.AsyncClient(timeout=60.0) as client:
        logger.info(f"Forwarding '{file.filename}' to resume_parser_api")

        response = await client.post(
            RESUME_PARSER_URL,
            files={"file": (file.filename, file_bytes, "application/pdf")},
        )

        if response.status_code != 200:
            logger.error(
                f"resume_parser_api returned {response.status_code}: {response.text}"
            )
            raise RuntimeError(
                f"resume_parser_api failed with status {response.status_code}: {response.text}"
            )

        logger.info("resume_parser_api responded successfully")
        return response.json()