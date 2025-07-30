from abc import ABC, abstractmethod
from rubricagent.state import GraphState


class BaseNode(ABC):
    def __init__(self, **kwargs):
        self.name = "BaseNode"
        self.verbose = False
        if "verbose" in kwargs:
            self.verbose = kwargs["verbose"]

    @abstractmethod
    def execute(self, state: GraphState) -> GraphState:
        pass

    def logging(self, method_name, **kwargs):
        if self.verbose:
            print(f"[{self.name}] {method_name}")
            for key, value in kwargs.items():
                print(f"{key}: {value}")

    def __call__(self, state: GraphState):
        return self.execute(state)


class RubricGeneratorNode(BaseNode):
    def __init__(self, rubric_generator, **kwargs):
        super().__init__(**kwargs)
        self.name = "RubricGeneratorNode"
        self.rubric_generator_chain = rubric_generator

    def execute(self, state: GraphState) -> GraphState:
        topic = state["topic"]
        objective = state["objective"]
        grade_level = state["grade_level"]

        generated_rubric = self.rubric_generator_chain.invoke(
            {
                "topic": topic,
                "objective": objective,
                "grade_level": grade_level,
            }
        )

        return GraphState(messages=[generated_rubric])


class AgentNode(BaseNode):
    def __init__(self, agent, **kwargs):
        super().__init__(**kwargs)
        self.name = "AgentNode"
        self.agent = agent

    def execute(self, state: GraphState) -> GraphState:
        # 프롬프트에서 사용하는 변수명과 일치하게 입력값 준비
        agent_input = {
            "rubric": state["messages"],
            "topic": state["topic"],
            "objective": state["objective"],
            "grade_level": state["grade_level"],
            "name": state["name"],
            "student_submission": state["student_submission"],
        }
        result = self.agent.invoke(agent_input)

        # 결과를 state에 병합
        return GraphState(messages=[result["output"]])


class SubmissionCheckerNode(BaseNode):
    def __init__(self, submission_checker, **kwargs):
        super().__init__(**kwargs)
        self.name = "SubmissionCheckerNode"
        self.submission_checker = submission_checker

    def execute(self, state: GraphState) -> GraphState:
        # 프롬프트에서 사용하는 변수명과 일치하게 입력값 준비
        agent_input = {"student_submission": state["student_submission"]}
        result = self.submission_checker.invoke(agent_input)

        if result.binary_score == "yes":
            print("==== [Student assignment has been submitted] ====")
            print("==== [Generating Rubric, Evaluation and Feedback] ====")
            return "submitted"
        else:
            print("==== [Student assignment has't been submitted] ====")
            print("==== [Generating Only Rubric] ====")
            return "not submitted"
