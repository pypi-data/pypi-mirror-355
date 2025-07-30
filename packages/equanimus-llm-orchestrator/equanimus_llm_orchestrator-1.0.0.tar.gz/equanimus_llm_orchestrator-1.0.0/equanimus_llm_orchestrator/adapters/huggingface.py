from langchain_huggingface import HuggingFaceEndpoint

from langchain_huggingface import HuggingFaceEmbeddings

def define_llm (
    model: str =  "mistralai/Mistral-7B-Instruct-v0.2",
    temperature: float = 0.0,
):
  """HuggingFace Endpoint. To use this class, you should have installed the huggingface_hub package, and the environment variable HUGGINGFACEHUB_API_TOKEN set with your API token, or given as a named parameter to the constructor."""

  llm = HuggingFaceEndpoint(
    repo_id=model,
    temperature=temperature,
  )
  return llm

def define_embedding(embedding_model: str = "sentence-transformers/all-mpnet-base-v2"):
    model_kwargs = {'device': 'cpu'}
    encode_kwargs = {'normalize_embeddings': False}
    hf = HuggingFaceEmbeddings(
      model_name=embedding_model,
      model_kwargs=model_kwargs,
      encode_kwargs=encode_kwargs
    )
    return hf
