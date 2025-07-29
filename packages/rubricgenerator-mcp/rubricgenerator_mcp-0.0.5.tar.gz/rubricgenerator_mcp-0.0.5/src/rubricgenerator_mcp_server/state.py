from typing import Annotated, Sequence, TypedDict, NotRequired
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class GraphState(TypedDict):
    topic: Annotated[
        str, "Detailed tasks (e.g., essay writing, graph interpretation, etc.)"
    ]
    objective: Annotated[
        str, "Assessment purpose (e.g., essay writing, graph interpretation, etc.)"
    ]
    grade_level: Annotated[str, "Grade level"]

    name: NotRequired[Annotated[str, "Student name"]]
    student_submission: NotRequired[Annotated[str, "Submitted assignment"]]

    messages: Annotated[Sequence[BaseMessage], add_messages]
