from enum import Enum

from equanimus_llm_orchestrator.adapters.setup import setup
from equanimus_llm_orchestrator.agents.main_workflow import create_main_workflow
from django.conf import settings


llm, embedding = setup(
    llm_type=settings.LLM_TYPE,
    model_name=settings.LLM_MODEL_NAME,
    embedding_model=settings.LLM_EMBEDDING_MODEL_NAME,
    region_name=settings.AWS_DEFAULT_REGION,
)


class ChatMode(Enum):
    COPILOT = 'copilot'
    CLONE = "clone"
    RAG = "rag"
    TRANSCRIPTION = "transcription"


def run(thread_id: str, question=None, chat_mode: ChatMode = "copilot", message_clones=[], sys_prompt=None,
        file_path=None):
    graph = create_main_workflow()
    app = graph.compile()
    return app.invoke(
        {
            "question": question,
            "llm": llm,
            "chat_mode": chat_mode,
            "message_clones": message_clones,
            "thread_id": thread_id,
            "sys_prompt_start": sys_prompt,
            "file_path": file_path,
        }
    )


def chat(thread_id, question=None, chat_mode: ChatMode = "copilot", message_clones=[], sys_prompt=None, file_path=None):
    response = run(thread_id, question, chat_mode, message_clones, sys_prompt, file_path)
    return response.get("response") or "Desculpe não consigo responder a sua pergunta no momento."
