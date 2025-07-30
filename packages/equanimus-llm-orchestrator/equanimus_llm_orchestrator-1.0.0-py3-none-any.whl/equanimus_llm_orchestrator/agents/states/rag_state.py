import operator
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings


class RagState(TypedDict):
    question: str
    llm: BaseChatModel
    response: str
    thread_id: str
    context: str
    documents: List[Document] = []
    file_path: str
    embedding: Embeddings

