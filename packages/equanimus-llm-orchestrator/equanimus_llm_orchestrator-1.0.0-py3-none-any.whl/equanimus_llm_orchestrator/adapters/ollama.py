from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings


def define_llm(
        model: str = "llama3",
        temperature: float = 0.0
):
    llm = ChatOllama(
        model=model,
        temperature=temperature,
    )
    return llm


def define_embedding(embedding_model: str = "llama3"):
    return OllamaEmbeddings(
        model=embedding_model,
    )
