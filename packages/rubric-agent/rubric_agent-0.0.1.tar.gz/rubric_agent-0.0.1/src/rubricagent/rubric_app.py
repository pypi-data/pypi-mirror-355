from dotenv import load_dotenv
import os
from rubricagent.state import GraphState
from rubricagent.agent import create_agent
from rubricagent.nodes import *
from rubricagent.tools import web_search_tool
from rubricagent.chains import (
    create_rubric_chain,
    create_submission_checker,
)

from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.memory import MemorySaver

from langchain_core.runnables import RunnableConfig
from langchain_teddynote.messages import random_uuid


class RubricApp:
    def __init__(self, **data):
        load_dotenv()
        # data에 명시적으로 들어온 값이 없으면, .env의 값을 사용
        self.MODEL_TYPE = os.getenv("MODEL_TYPE", "openai")
        self.MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

        self.input = {
            "topic": data.get("topic"),
            "objective": data.get("objective"),
            "grade_level": data.get("grade_level"),
            "name": data.get("name"),
            "student_submission": data.get("student_submission"),
        }
        self.config = RunnableConfig(
            recursion_limit=3, configurable={"thread_id": random_uuid()}
        )
        self.tools = [web_search_tool(max_results=3)]
        self.rubric_generator = create_rubric_chain(self.MODEL_NAME, self.MODEL_TYPE)
        self.agent = create_agent(self.MODEL_NAME, self.tools, self.MODEL_TYPE)
        self.sub_checker = create_submission_checker(self.MODEL_NAME, self.MODEL_TYPE)
        self.app = self._build_workflow()
        self.final_state = self.app.invoke(self.input, self.config)

    def _build_workflow(self):
        workflow = StateGraph(GraphState)
        workflow.add_node("RubricGenerator", RubricGeneratorNode(self.rubric_generator))
        workflow.add_node("AgentNode", AgentNode(self.agent))

        workflow.add_edge(START, "RubricGenerator")
        workflow.add_conditional_edges(
            "RubricGenerator",
            SubmissionCheckerNode(self.sub_checker),
            {
                "submitted": "AgentNode",
                "not submitted": END,
            },
        )
        workflow.add_edge("AgentNode", END)
        return workflow.compile(checkpointer=MemorySaver())

    def __str__(self):
        return "RubricApp is available!"

    def get_rubric_standards(self) -> str:
        # Assuming the rubric standards are in the first message's content
        if (
            self.final_state
            and "messages" in self.final_state
            and len(self.final_state["messages"]) > 0
        ):
            return self.final_state["messages"][0].content
        return ""

    def get_grading_feedback(self) -> str:
        # Assuming the grading feedback is in the second message's content
        if (
            self.final_state
            and "messages" in self.final_state
            and len(self.final_state["messages"]) > 1
        ):
            return self.final_state["messages"][1].content
        return ""
