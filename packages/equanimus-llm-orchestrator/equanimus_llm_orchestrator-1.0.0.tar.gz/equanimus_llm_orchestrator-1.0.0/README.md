# LLM Orchestrator

Orquestrador de fluxos conversacionais com Modelos de Linguagem (LLMs) em múltiplos modos, incluindo **copiloto**, **clone**, **RAG (Geração Aumentada por Recuperação)** e **transcrição**.

## 🚀 Visão Geral

`llm_orchestrator` é uma biblioteca que gerencia interações com LLMs através de uma interface unificada. Ele carrega e configura modelos de linguagem e de embedding, define modos conversacionais e executa fluxos usando pipelines baseados em agentes inteligentes.

## ✨ Funcionalidades

- ✅ Integração fácil com diversos provedores de LLM  
- 🧠 Suporte a múltiplos modos de conversa:
  - `copilot`: respostas assistivas  
  - `clone`: simula histórico de mensagens anterior  
  - `rag`: gera respostas com base em documentos recuperados  
  - `transcription`: processa e responde a áudios/textos transcritos  
- ⚙️ Orquestração de workflows com agentes  
- 🧩 Suporte a embeddings para casos de uso avançados  

## 🧰 Instalação

```bash
pip install llm_orchestrator
```

## 🧠 Modos de Conversa
| Modo            | Descrição                                        |
| --------------- | ------------------------------------------------ |
| `copilot`       | Comportamento assistivo geral                    |
| `clone`         | Responde com base no histórico de mensagens      |
| `rag`           | Usa documentos externos para melhorar a resposta |
| `transcription` | Projetado para lidar com entrada de áudio        |

## 📂 Estrutura do Projeto
```
llm_orchestrator/
├── init.py # Inicialização do pacote
├── README.md # Documentação principal do projeto
├── requirements.txt # Dependências do projeto
├── config.py # Configurações globais e carregamento de env
├── run_chat.py # Script principal para executar conversas
├── adapters/ # Integrações com LLMs e embeddings
├── agents/ # Agentes e definição dos fluxos principais
├── chat_prompts/ # Templates de prompts para os modos de chat
├── connectVDB/ # Conexões com banco de dados vetorial (VDB)
├── core/ # Utilitários centrais, constantes e helpers
├── document_loaders/ # Carregadores de documentos (PDFs, textos, etc.)
├── engine.tldr/ # Engine principal (ex: fluxo de TLDR)
├── modes_pretrained/ # Modos de comportamento pré-treinados
```
## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir uma issue ou enviar um pull request com melhorias.

## 📄 Licença
Licença MIT
