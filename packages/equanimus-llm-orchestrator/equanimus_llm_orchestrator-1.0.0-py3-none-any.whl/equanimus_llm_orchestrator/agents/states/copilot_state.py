import operator
from typing import Annotated, List

from langgraph.graph import MessagesState
from langchain_core.language_models.chat_models import BaseChatModel


class CopilotState(MessagesState):
    summary: str
    llm: BaseChatModel
    thread_id: str
    input_split_contents: List[str]
    response: str
    message_clones: Annotated[list, operator.add]
