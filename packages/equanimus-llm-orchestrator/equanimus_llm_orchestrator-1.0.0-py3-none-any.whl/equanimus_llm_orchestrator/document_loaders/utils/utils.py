from typing import List
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.documents import Document
from equanimus_llm_orchestrator.chat_prompts.templates_prompts import reduce_prompt


def reduce(input: dict, llm: BaseChatModel) -> str:
    prompt = reduce_prompt().invoke(input)
    response = llm.invoke(prompt)
    return response.content


def count_token_in_documents(documents: List[Document], llm: BaseChatModel) -> int:
    """Get number of tokens for input contents."""
    return sum(llm.get_num_tokens(doc.page_content) for doc in documents)


def format_docs(documents: List[Document]):
    return "\n\n".join(doc.page_content for doc in documents)