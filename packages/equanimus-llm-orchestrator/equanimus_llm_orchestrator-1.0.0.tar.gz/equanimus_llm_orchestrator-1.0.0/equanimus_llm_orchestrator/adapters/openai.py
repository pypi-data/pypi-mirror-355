from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings

def define_llm (
    model: str = "gpt-3.5-turbo-0125",
    temperature: float = 0.0,
):
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
      )
    return llm

def define_embedding(embedding_model = "text-embedding-3-large"):
    return OpenAIEmbeddings(model=embedding_model)
