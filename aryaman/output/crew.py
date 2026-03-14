import os
from crewai import Agent, Task, Crew, Process
from crewai.project import CrewBase, agent, task

# Define the base directory for configuration files
BASE = os.path.dirname(os.path.abspath(__file__))
agents_config = os.path.join(BASE, "config", "agents.yaml")
tasks_config = os.path.join(BASE, "config", "tasks.yaml")

@CrewBase
class MyCrew:
    """
    MyCrew crew for building an ML pipeline with FastAPI.
    """
    agents_config = agents_config
    tasks_config = tasks_config

    def __init__(self):
        pass

    @agent
    def engineering_manager(self) -> Agent:
        return Agent(
            config=self.agents_config['engineering_manager'],
            verbose=True,
            allow_delegation=True
        )

    @agent
    def systems_architect(self) -> Agent:
        return Agent(
            config=self.agents_config['systems_architect'],
            verbose=True,
            allow_delegation=True
        )

    @agent
    def ml_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['ml_engineer'],
            verbose=True,
            allow_delegation=False
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config['backend_engineer'],
            verbose=True,
            allow_delegation=False
        )

    @task
    def task_31(self) -> Task:
        return Task(
            config=self.tasks_config['task_31'],
            agent=self.systems_architect()
        )

    @task
    def task_32(self) -> Task:
        return Task(
            config=self.tasks_config['task_32'],
            agent=self.ml_engineer(),
            context=[self.task_31()]
        )

    @task
    def task_33(self) -> Task:
        return Task(
            config=self.tasks_config['task_33'],
            agent=self.ml_engineer(),
            context=[self.task_31(), self.task_32()]
        )

    @task
    def task_34(self) -> Task:
        return Task(
            config=self.tasks_config['task_34'],
            agent=self.ml_engineer(),
            context=[self.task_33()]
        )

    @task
    def task_35(self) -> Task:
        return Task(
            config=self.tasks_config['task_35'],
            agent=self.ml_engineer(),
            context=[self.task_32(), self.task_34()]
        )

    @task
    def task_36(self) -> Task:
        return Task(
            config=self.tasks_config['task_36'],
            agent=self.ml_engineer(),
            context=[self.task_35()]
        )

    @task
    def task_37(self) -> Task:
        return Task(
            config=self.tasks_config['task_37'],
            agent=self.ml_engineer(),
            context=[self.task_35(), self.task_36()]
        )

    @task
    def task_38(self) -> Task:
        return Task(
            config=self.tasks_config['task_38'],
            agent=self.backend_engineer(),
            context=[self.task_36()]
        )

    @task
    def task_39(self) -> Task:
        return Task(
            config=self.tasks_config['task_39'],
            agent=self.systems_architect(),
            context=[self.task_35(), self.task_37()]
        )

    @task
    def task_40(self) -> Task:
        return Task(
            config=self.tasks_config['task_40'],
            agent=self.systems_architect(),
            context=[self.task_38(), self.task_39()]
        )

    def crew(self) -> Crew:
        """
        Creates the MyCrew crew with a hierarchical process.
        """
        return Crew(
            agents=[
                self.engineering_manager(),
                self.systems_architect(),
                self.ml_engineer(),
                self.backend_engineer()
            ],
            tasks=[
                self.task_31(),
                self.task_32(),
                self.task_33(),
                self.task_34(),
                self.task_35(),
                self.task_36(),
                self.task_37(),
                self.task_38(),
                self.task_39(),
                self.task_40()
            ],
            process=Process.hierarchical,
            manager_agent=self.engineering_manager(),
            verbose=True
        )