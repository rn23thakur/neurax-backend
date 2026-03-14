import os
from crewai_project.crew import MyCrew

def run():
    """
    Runs the MyCrew project.
    """
    os.makedirs("output", exist_ok=True)
    result = MyCrew().crew().kickoff()
    print(result)

if __name__ == "__main__":
    run()