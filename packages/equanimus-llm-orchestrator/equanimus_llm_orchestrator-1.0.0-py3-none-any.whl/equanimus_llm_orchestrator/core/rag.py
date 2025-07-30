from typing import Optional

from equanimus_llm_orchestrator.adapters.setup import setup
from equanimus_llm_orchestrator.agents.rag_workflow import create_rag_workflow
from django.conf import settings

llm, embedding = setup(
    llm_type=settings.LLM_TYPE,
    model_name=settings.LLM_MODEL_NAME,
    embedding_model=settings.LLM_EMBEDDING_MODEL_NAME,
    region_name=settings.AWS_DEFAULT_REGION,
)


def run_rag(thread_id: str, question: str, file_path: Optional[str]):
    graph = create_rag_workflow()
    app = graph.compile()
    return app.invoke(
        {
            "question": question,
            "llm": llm,
            "thread_id": thread_id,
            "file_path": file_path,
            "embedding": embedding,
        }
    )
