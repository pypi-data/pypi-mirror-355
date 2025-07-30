import chromadb
import chromadb.auth
from chromadb.config import DEFAULT_TENANT, DEFAULT_DATABASE, Settings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from django.conf import settings


def connectClient():
  try:
    chromaClient = chromadb.HttpClient(
      host=settings.CHROMA_HOST,
      port=settings.CHROMA_PORT,
      ssl=True,
      headers=None,
      settings=Settings(
        chroma_client_auth_provider=settings.CHROMA_AUTH_PROVIDER,
        chroma_client_auth_credentials=f"{settings.CHROMA_USER}:{settings.CHROMA_PASSWORD}",
      ),
      tenant=DEFAULT_TENANT,
      database=DEFAULT_DATABASE,
    )
    return chromaClient
  except Exception as e:
    print(f"Erro ao conectar ao ChromaDB: {e}")


def get_collection(collection_name, connect_client = connectClient()):
  try:
    collection = connect_client.get_or_create_collection(collection_name)
    return collection
  except Exception as e:
    print(f"Erro ao conectar a collection: {collection_name} ChromaDB: {e}")
    return None


def connectVDB (collection_name, embeddings: Embeddings, connect_client = connectClient(), refresh=False):
  if refresh:
    collection = get_collection(collection_name, connect_client)
    if collection:
      connect_client.delete_collection(collection_name)

  vector_store = Chroma(
    client=connect_client,
    collection_name=collection_name,
    embedding_function=embeddings,
  )
  return vector_store


def vector_store_as_retriever(thread_id: str, embeddings: Embeddings, refresh=False):
  connect = connectClient()
  vector_store = connectVDB(
    collection_name = thread_id,
    embeddings=embeddings,
    connect_client=connect,
    refresh=refresh
  )

  retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5},
  )
  return retriever
