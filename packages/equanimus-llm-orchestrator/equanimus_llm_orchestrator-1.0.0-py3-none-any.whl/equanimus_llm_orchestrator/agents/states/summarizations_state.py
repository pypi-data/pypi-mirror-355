import operator
from typing import Annotated, List, TypedDict
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel


class OverallSummaryState(TypedDict):
    contents: List[str]
    summaries: Annotated[list, operator.add]
    collapsed_summaries: List[Document]
    final_summary: str
    llm: BaseChatModel


class SummaryState(TypedDict):
    content: str
    llm: BaseChatModel