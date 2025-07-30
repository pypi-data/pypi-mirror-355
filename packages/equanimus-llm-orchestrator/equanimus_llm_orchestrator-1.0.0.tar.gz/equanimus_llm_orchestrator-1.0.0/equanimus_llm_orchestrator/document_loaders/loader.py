import os
import requests
import tempfile

from urllib.parse import urlparse

from langchain_core.embeddings import Embeddings

from equanimus_llm_orchestrator.connectVDB.connectCroma import vector_store_as_retriever

from equanimus_llm_orchestrator.document_loaders.uploads_func.docx import DOCX_to_VDB
from equanimus_llm_orchestrator.document_loaders.uploads_func.pdf import PDF_to_VDB


def download_file(url: str) -> str:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(urlparse(url).path)[1])
    with open(temp_file.name, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return temp_file.name

def get_file_extension(path: str) -> str:
    parsed_url = urlparse(path)
    if parsed_url.scheme in ("http", "https"):
        return os.path.splitext(parsed_url.path)[1]
    else:
        return os.path.splitext(path)[1]
def loader(thread_id: str, file_path: str,embedding: Embeddings):
    """
    Load the file.
    """
    retriever = vector_store_as_retriever(
        thread_id = thread_id,
        embeddings = embedding,
    )
    splits = None

    loaders = {
        ".pdf": PDF_to_VDB,
        ".docx": DOCX_to_VDB
    }

    try:
        if file_path:
            is_url = urlparse(file_path).scheme in ("http", "https")
            temp_file_path = file_path
            if is_url:
                temp_file_path = download_file(file_path)
        file_extension = get_file_extension(temp_file_path)
        if file_extension in loaders:
            splits, _ = loaders[file_extension](temp_file_path, retriever)
        else:
            raise ValueError("Formato inválido")
    except Exception as e:
        print(f"Error loading file: {e}")
    finally:
        if is_url and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    return splits