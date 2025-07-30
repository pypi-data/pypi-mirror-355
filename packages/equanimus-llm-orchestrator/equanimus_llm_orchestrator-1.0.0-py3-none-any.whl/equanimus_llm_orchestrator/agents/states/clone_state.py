from typing import  TypedDict

from langchain_core.language_models.chat_models import BaseChatModel


class CloneChatState(TypedDict):
    new_message: str
    llm: BaseChatModel
