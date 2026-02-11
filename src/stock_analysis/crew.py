import os

from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task
from dotenv import load_dotenv

try:
    from .tools.calculator_tool import CalculatorTool
    from .tools.sec_tools import SEC10KTool, SEC10QTool
    from .tools.web_tools import BraveSearchAliasTool
except ImportError:
    from tools.calculator_tool import CalculatorTool
    from tools.sec_tools import SEC10KTool, SEC10QTool
    from tools.web_tools import BraveSearchAliasTool

load_dotenv()


@CrewBase
class StockAnalysisCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def _llm(self) -> LLM:
        model = os.getenv("MODEL", "llama-3.1-8b-instant")
        max_tokens = int(os.getenv("MAX_TOKENS", "280"))
        temperature = float(os.getenv("TEMPERATURE", "0.2"))
        groq_api_key = os.getenv("GROQ_API_KEY")
        if groq_api_key:
            return LLM(
                model=model,
                api_key=groq_api_key,
                base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
                max_tokens=max_tokens,
                temperature=temperature,
            )

        xai_api_key = os.getenv("XAI_API_KEY")
        if xai_api_key:
            return LLM(
                model=os.getenv("XAI_MODEL", "grok-2-latest"),
                api_key=xai_api_key,
                base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
                max_tokens=max_tokens,
                temperature=temperature,
            )

        raise ValueError("Set GROQ_API_KEY or XAI_API_KEY in .env before running.")

    def _agent_max_iter(self) -> int:
        return int(os.getenv("AGENT_MAX_ITER", "4"))

    @agent
    def research_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["research_analyst"],
            verbose=True,
            llm=self._llm(),
            tools=[
                BraveSearchAliasTool(),
            ],
            max_iter=self._agent_max_iter(),
            max_retry_limit=1,
        )

    @task
    def research(self) -> Task:
        return Task(
            config=self.tasks_config["research"],
            agent=self.research_analyst_agent(),
        )

    @agent
    def financial_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],
            verbose=True,
            llm=self._llm(),
            tools=[
                CalculatorTool(),
                BraveSearchAliasTool(),
            ],
            max_iter=self._agent_max_iter(),
            max_retry_limit=1,
        )

    @agent
    def filings_analyst_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["financial_analyst"],
            verbose=True,
            llm=self._llm(),
            tools=[
                BraveSearchAliasTool(),
                SEC10QTool(),
                SEC10KTool(),
            ],
            max_iter=self._agent_max_iter(),
            max_retry_limit=1,
        )

    @task
    def financial_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["financial_analysis"],
            agent=self.financial_analyst_agent(),
        )

    @task
    def filings_analysis(self) -> Task:
        return Task(
            config=self.tasks_config["filings_analysis"],
            agent=self.filings_analyst_agent(),
        )

    @agent
    def investment_advisor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["investment_advisor"],
            verbose=True,
            llm=self._llm(),
            tools=[
                CalculatorTool(),
            ],
            max_iter=self._agent_max_iter(),
            max_retry_limit=1,
        )

    @task
    def recommend(self) -> Task:
        return Task(
            config=self.tasks_config["recommend"],
            agent=self.investment_advisor_agent(),
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
