from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    retrieved_entries: List[dict]
    user_goals: List[dict]
    recent_entries: List[dict]
