import os
from crewai import Agent, Task, Crew, Process, LLM
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class MyCrew:
    agents_config = "config/agents.yaml"
    tasks_config  = "config/tasks.yaml"

    @agent
    def agent_one(self) -> Agent:
        return Agent(config=self.agents_config["agent_one"], verbose=True)

    @agent
    def agent_two(self) -> Agent:
        return Agent(config=self.agents_config["agent_two"], verbose=True)

    @agent
    def agent_three(self) -> Agent:
        return Agent(config=self.agents_config["agent_three"], verbose=True)

    @task
    def task_1(self) -> Task:
        return Task(config=self.tasks_config["task_1"])

    @task
    def task_2(self) -> Task:
        return Task(config=self.tasks_config["task_2"])

    @task
    def task_3(self) -> Task:
        return Task(config=self.tasks_config["task_3"])

    @task
    def task_4(self) -> Task:
        return Task(config=self.tasks_config["task_4"])

    @task
    def task_5(self) -> Task:
        return Task(config=self.tasks_config["task_5"])

    @task
    def task_6(self) -> Task:
        return Task(config=self.tasks_config["task_6"])

    @task
    def task_7(self) -> Task:
        return Task(config=self.tasks_config["task_7"])

    @task
    def task_8(self) -> Task:
        return Task(config=self.tasks_config["task_8"])

    @task
    def task_9(self) -> Task:
        return Task(config=self.tasks_config["task_9"])

    @task
    def task_10(self) -> Task:
        return Task(config=self.tasks_config["task_10"])

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