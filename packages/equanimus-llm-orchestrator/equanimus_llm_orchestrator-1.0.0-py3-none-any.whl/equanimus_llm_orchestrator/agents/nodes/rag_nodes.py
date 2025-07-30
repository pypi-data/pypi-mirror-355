from equanimus_llm_orchestrator.agents.states.rag_state import RagState
from equanimus_llm_orchestrator.document_loaders.loader import loader
from equanimus_llm_orchestrator.chat_prompts.templates_prompts import system_rag_map_prompt
from equanimus_llm_orchestrator.document_loaders.utils.utils import format_docs
from equanimus_llm_orchestrator.connectVDB.connectCroma import vector_store_as_retriever

from equanimus_llm_orchestrator.agents.summarization_workflow import create_summarization_workflow


def load_file_node(state: RagState):
    """
    Load the file.
    """
    splits = []
    file_path = state.get("file_path")
    thread_id = state.get("thread_id")
    embedding = state.get("embedding")
    try:
        splits = loader(thread_id, file_path, embedding)
    except Exception:
        return {"response": "Error ao carregar arquivo", "documents": []}

    return {"documents": splits}


def find_documents_vector_db_node(state: RagState):
    """
    Find documents in the vector database.
    """
    thread_id = state.get("thread_id")
    embedding = state.get("embedding")
    question = state.get("question")

    retriever = vector_store_as_retriever(
        thread_id = thread_id,
        embeddings = embedding,
    )

    documents = retriever.invoke(question)

    return {"documents": documents}


def summarize_documents_node(state: RagState):
    """
    Summarize documents.
    """
    llm = state.get("llm")
    documents = state.get("documents")
    graph = create_summarization_workflow()
    app = graph.compile()
    result = app.invoke(
        {
            "contents": [doc.page_content for doc in documents],
            "llm": llm,
        }
    )
    context = result.get("final_summary")
    return {"context": context}


def load_documents_to_context_node(state: RagState):
    """
    Load documents to context.
    """
    documents = state.get("documents")
    llm = state.get("llm")
    thread_id = state.get("thread_id")
    documents_formatted = format_docs(documents)
    map_prompt = system_rag_map_prompt()
    prompt = map_prompt.format(context=documents_formatted)

    return {"sys_prompt_start": prompt, "llm": llm,"thread_id": thread_id,  "context": documents_formatted}


def load_summary_to_context_node(state: RagState):
    """
    Load summary to context.
    """
    context = state.get("context")
    llm = state.get("llm")
    thread_id = state.get("thread_id")
    map_prompt = system_rag_map_prompt()
    prompt = map_prompt.format(context=context)

    return {"sys_prompt_start": prompt, "llm": llm,"thread_id": thread_id}

def check_documents_node(state: RagState):
    """
    Check documents.
    """
    if not state.get("documents"):
        return {"response": "Error ao carregar documento",  "documents": []}
    documents = state.get("documents", [])
    print(f"Found {len(documents)} documents")
    return {"documents": documents}

def not_loaded_file_node(state: RagState):
    """
    Not loaded file.
    """
    return {"response": f"Desculpe não consegui ler o arquivo"}