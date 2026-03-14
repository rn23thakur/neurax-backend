import os
from crewai import Agent, Task, Crew, Process

BASE = os.path.dirname(os.path.abspath(__file__))
agents_config = os.path.join(BASE, "config", "agents.yaml")
tasks_config  = os.path.join(BASE, "config", "tasks.yaml")

@Agent(agents_config)
class MyAgent:
    pass

@Task(tasks_config)
class MyTask:
    pass

class MyCrew(Crew):
    def __init__(self):
        super().__init__(process=Process.hierarchical)

    def crew(self):
        return self

my_crew = MyCrew()