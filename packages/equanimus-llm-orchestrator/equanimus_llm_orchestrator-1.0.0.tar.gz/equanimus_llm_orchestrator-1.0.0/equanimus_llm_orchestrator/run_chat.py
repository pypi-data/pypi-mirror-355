"""
Este módulo fornece uma interface simples para interagir com o agente conversacional
via a função `run_chat`. Ideal como ponto de entrada em aplicações ou bibliotecas que
dependem de interações baseadas em LLMs com suporte a múltiplos modos de operação.
"""

from enum import Enum
from typing import Optional, List
import logging

from equanimus_llm_orchestrator.core.core_chat import chat
from equanimus_llm_orchestrator.settings import validate_settings_variables


class ChatMode(Enum):
    COPILOT = 'copilot'
    CLONE = 'clone'
    RAG = 'rag'
    TRANSCRIPTION = 'transcription'


def run_chat(
        thread_id: str,
        question: Optional[str] = None,
        chat_mode: ChatMode = ChatMode.COPILOT,
        message_clones: Optional[List[str]] = None,
        sys_prompt: Optional[str] = None,
        file_path: Optional[str] = None,
        verbose: bool = False
) -> str:
    """
    Executa uma consulta ao agente conversacional.

    Parameters:
        thread_id (str): Identificador único da thread de conversa.
        question (str, optional): A pergunta a ser enviada ao agente.
        chat_mode (ChatMode, optional): O modo de operação do agente.
            Pode ser: 'copilot', 'clone', 'rag' ou 'transcription'.
        message_clones (list, optional): Lista de mensagens anteriores que o agente pode considerar.
        sys_prompt (str, optional): Prompt de sistema que define o comportamento do agente.
        file_path (str, optional): Caminho para um arquivo opcional que será utilizado pelo agente.
        verbose (bool, optional): Exibe logs no terminal para depuração.

    Returns:
        str: A resposta gerada pelo agente. Em caso de falha, retorna uma mensagem padrão.
    """
    validate_settings_variables()

    if message_clones is None:
        message_clones = []

    if not isinstance(chat_mode, ChatMode):
        raise ValueError(f"chat_mode deve ser uma instância de ChatMode. Recebido: {chat_mode}")

    try:
        response = chat(
            thread_id=thread_id,
            question=question,
            chat_mode=chat_mode,
            message_clones=message_clones,
            sys_prompt=sys_prompt,
            file_path=file_path
        )
        if verbose:
            logging.info(f"[run_chat] Resposta do agente: {response}")
        return response
    except Exception as e:
        logging.error(f"[run_chat] Erro ao executar chat: {e}")
        return "Ocorreu um erro ao processar sua solicitação. Tente novamente mais tarde."
