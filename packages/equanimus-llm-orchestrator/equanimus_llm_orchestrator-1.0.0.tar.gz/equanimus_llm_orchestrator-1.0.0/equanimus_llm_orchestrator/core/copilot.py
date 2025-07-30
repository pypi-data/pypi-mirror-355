from langgraph.checkpoint.postgres import PostgresSaver

from equanimus_llm_orchestrator.adapters.setup import setup
from equanimus_llm_orchestrator.agents.copilot_workflow import create_copilot_workflow
from django.conf import settings

DB_URI = settings.DB_URL.replace("postgres://", "postgresql://")

llm, embedding = setup(
    llm_type=settings.LLM_TYPE,
    model_name=settings.LLM_MODEL_NAME,
    embedding_model=settings.LLM_EMBEDDING_MODEL_NAME,
    region_name=settings.AWS_DEFAULT_REGION,
)


def run_copilot(thread_id: str, messages):
    with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        checkpointer.setup()
        graph = create_copilot_workflow()
        app = graph.compile(checkpointer=checkpointer)

        return app.invoke(
            {
                "messages": messages,
                "llm": llm,
                "thread_id": thread_id,
            },
            config={
                "configurable": {
                    "thread_id": thread_id,
                },
            },
        )
