from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import health, parse_prd, parse_resume, generate_crew, run_crew

app = FastAPI(
    title="cofounder.ai API",
    description="Backend services powering cofounder.ai",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "cofounder.ai",
        "status": "running",
        "message": "Welcome to the cofounder.ai backend"
    }


# Register routers
def register_routes():
    app.include_router(
        health.router,
        prefix="/health",
        tags=["health"]
    )
    app.include_router(parse_prd.router, tags=["PRD"])
    app.include_router(parse_resume.router, tags=["Resume"])
    app.include_router(generate_crew.router, tags=["Crew"])
    app.include_router(run_crew.router, tags=["Crew"])


register_routes()