from langchain_community.document_loaders import PyPDFLoader
from equanimus_llm_orchestrator.document_loaders.uploads_func.add_document import add_to_VDB

def PDF_to_VDB(filePath, retriever_db):
    """
    Load a document from the file system and add it to the state.
    """
    loader = PyPDFLoader(filePath)
    documents = loader.load()
    splits, retriever  = add_to_VDB(documents, retriever_db)

    return splits, retriever
