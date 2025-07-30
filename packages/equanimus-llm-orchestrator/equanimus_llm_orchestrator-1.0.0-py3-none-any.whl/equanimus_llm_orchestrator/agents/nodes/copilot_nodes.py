from langchain_core.messages import RemoveMessage, HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from django.conf import settings


from equanimus_llm_orchestrator.agents.states.copilot_state import CopilotState


def generate_response_node(state: CopilotState):
    llm = state.get("llm")
    messages = state.get("messages")
    response = llm.invoke(messages)
    new_messages = [response]
    return {"response": response.content, "messages": new_messages}


def summarize_conversation_node(state: CopilotState):
    summary = state.get("summary")
    if summary:
        summary_message = (
            f"Aqui é um resumo da conversa até o momento: {summary}\n\n"
            "Amplie o resumo levando em consideração as novas mensagens acima::"
        )
    else:
        summary_message = "Crie um resumo da conversa acima:"
    llm = state.get("llm")
    messages = state.get("messages") + [("human", summary_message)]
    response = llm.invoke(messages)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}


def map_inputs_note (state: CopilotState):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=settings.LLM_MAX_INPUT_TOKENS,
        chunk_overlap=0,
    )
    messages = state.get("messages")
    last_message = messages[-1]
    input_split_contents = text_splitter.split_text(last_message.content)
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][-1:]]

    return {"input_split_contents": input_split_contents, "messages": delete_messages}


def add_input_to_context_node(state: CopilotState):
    messages = state.get("messages")
    input_split_contents = state.get("input_split_contents")
    input_messages = [HumanMessage(content=content) for content in input_split_contents]
    messages = messages + input_messages
    return {"messages": messages, "input_split_contents": []}


def should_summarize_conversation(state: CopilotState):
    llm = state.get("llm")
    messages = state.get("messages")
    num_tokens = sum([llm.get_num_tokens(m.content) for m in messages])
    if num_tokens > settings.LLM_MAX_CONTEXT_TOKENS:
        return "summarize_conversation"
    else:
        return "generate_response"

def add_message_to_context_node(state: CopilotState):
    messages = state.get("messages")
    return {"messages": messages}