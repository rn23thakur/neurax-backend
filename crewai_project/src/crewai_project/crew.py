import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def engineering_manager(self) -> Agent:
        return Agent(config=self.agents_config["engineering_manager"], verbose=True)

    @agent
    def systems_architect(self) -> Agent:
        return Agent(config=self.agents_config["systems_architect"], verbose=True)

    @agent
    def ml_engineer(self) -> Agent:
        return Agent(config=self.agents_config["ml_engineer"], verbose=True)

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(config=self.agents_config["backend_engineer"], verbose=True)

    @task
    def task_31(self) -> Task:
        return Task(config=self.tasks_config["task_31"])

    @task
    def task_32(self) -> Task:
        return Task(config=self.tasks_config["task_32"])

    @task
    def task_33(self) -> Task:
        return Task(config=self.tasks_config["task_33"])

    @task
    def task_34(self) -> Task:
        return Task(config=self.tasks_config["task_34"])

    @task
    def task_35(self) -> Task:
        return Task(config=self.tasks_config["task_35"])

    @task
    def task_36(self) -> Task:
        return Task(config=self.tasks_config["task_36"])

    @task
    def task_37(self) -> Task:
        return Task(config=self.tasks_config["task_37"])

    @task
    def task_38(self) -> Task:
        return Task(config=self.tasks_config["task_38"])

    @task
    def task_39(self) -> Task:
        return Task(config=self.tasks_config["task_39"])

    @task
    def task_40(self) -> Task:
        return Task(config=self.tasks_config["task_40"])

    @crew
    def crew(self) -> Crew:
        manager_llm = LLM(model=os.environ.get("MODEL", "gemini-2.5-flash"))
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm=manager_llm,
            verbose=True,
        )