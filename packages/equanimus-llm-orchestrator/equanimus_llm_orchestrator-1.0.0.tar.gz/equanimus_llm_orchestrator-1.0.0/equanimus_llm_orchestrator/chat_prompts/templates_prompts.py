from langchain_core.prompts import ChatPromptTemplate


def map_prompt():
  map_prompt = ChatPromptTemplate.from_messages(
    [("human", "Escreva um resumo conciso do seguinte conteúdo:\\n\\n{context}")]
  )
  return map_prompt

def system_rag_map_prompt():
    system_rag_map_prompt =  ChatPromptTemplate.from_messages(
    [
       ("system", "Você é um assistente para tarefas de resposta a perguntas. Use os seguintes pedaços de contexto recuperado para responder à pergunta. Se você não sabe a resposta, responda como um agente de copilot. Mantenha a resposta concisa.\\n\\n Context: {context}")
     ]
  )
    return system_rag_map_prompt


def reduce_prompt ():
    reduce_template = """
    A seguir, um conjunto de resumos:
    {docs}
    Pegue isso e destile em um resumo final e consolidado dos temas principais.
    """

    reduce_prompt = ChatPromptTemplate([("human", reduce_template)])

    return reduce_prompt
