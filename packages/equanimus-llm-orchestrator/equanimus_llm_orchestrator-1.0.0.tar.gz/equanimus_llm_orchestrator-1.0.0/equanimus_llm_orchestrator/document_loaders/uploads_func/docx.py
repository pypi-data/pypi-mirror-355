from langchain_community.document_loaders.word_document import Docx2txtLoader

from equanimus_llm_orchestrator.document_loaders.uploads_func.add_document import add_to_VDB


def DOCX_to_VDB(filePath: str, retriever_db):
    """
    Load a document from the file system and add it to the state.
    """
    loader = Docx2txtLoader(filePath)
    documents = loader.load()
    splits, retriever  = add_to_VDB(documents, retriever_db)

    return splits, retriever