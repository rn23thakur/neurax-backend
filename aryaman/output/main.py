import os
from crewai_project.crew import MyCrew

def run():
    os.makedirs("output", exist_ok=True)
    result = MyCrew().crew().kickoff()
    print(result)