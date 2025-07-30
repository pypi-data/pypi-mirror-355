from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from equanimus_llm_orchestrator.agents.states.main_state import MainState
from equanimus_llm_orchestrator.core.clone_chat import run_clone
from equanimus_llm_orchestrator.core.copilot import run_copilot
from equanimus_llm_orchestrator.core.rag import run_rag

from django.conf import settings

def copilot_agent_node(state: MainState):
    question = state.get("question")
    sys_prompt_start = state.get("sys_prompt_start") if state.get("sys_prompt_start") else "Você é um assistente de perguntas e respostas. um co-piloto para tarefas de linguagem natural. Responda sempre de forma e concisa e direta."

    messages = [
        ("system", sys_prompt_start),
        ("human", question)
    ]
    copilot_graph = run_copilot(
        thread_id=state.get("thread_id"),
        messages=messages,
    )

    return { "response": copilot_graph.get("response")}

def rag_agent_node(state: MainState):
    question = state.get("question")
    file_path = state.get("file_path")
    thread_id = state.get("thread_id")
    rag_graph = run_rag(
        thread_id=thread_id,
        question=question,
        file_path=file_path,
    )
    return { "response": rag_graph.get("response")}

def clone_agent_node(state: MainState):
    start_messages = state.get("message_clones")
    llm = state.get("llm")
    history = []
    for message in start_messages:
        num_tokens = llm.get_num_tokens(message.content)
        if num_tokens > settings.LLM_MAX_INPUT_TOKENS:
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                chunk_size=settings.LLM_MAX_INPUT_TOKENS,
                chunk_overlap=0,
            )
            input_split_contents = text_splitter.split_text(message.content)
            for content in input_split_contents:
                if message.type == "human":
                    input_message = HumanMessage(content=content)
                elif message.type == "ai":
                    input_message = AIMessage(content=content)
                elif message.type == "system":
                    input_message = SystemMessage(content=content)
                else:
                    input_message = HumanMessage(content=content)
                history.append(input_message)
        else:
            history.append(message)

    if history[-1].type != "human":
        history.append(HumanMessage(content="Resuma a conversa acima:"))
    clone_graph = run_clone(
        thread_id=state.get("thread_id"),
        messages=history,
    )
    return { "response": clone_graph.get("response")}

def get_response_node(state: MainState):
    return {"response": state.get("response")}