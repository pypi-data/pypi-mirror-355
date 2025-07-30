import operator
from typing import Annotated, List, TypedDict, Optional
from langchain_core.documents import Document


from langchain_core.language_models.chat_models import BaseChatModel


class MainState(TypedDict):
    question: str
    chat_mode: str
    llm: BaseChatModel
    response: str
    thread_id: str
    message_clones: Annotated[list, operator.add]
    summaries: Annotated[list, operator.add]
    collapsed_summaries: List[Document]
    final_summary: str
    contents: List[str]
    summary: str
    sys_prompt_start: str
    file_path: str