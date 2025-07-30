from equanimus_llm_orchestrator.adapters import aws, ollama, openai
from equanimus_llm_orchestrator.adapters import huggingface


def setup(llm_type, model_name=None, embedding_model=None, temperature=None, region_name=None):

    temperature = 0.0

    llm_definitions = {
        "openai": lambda: (openai.define_llm(
            model=model_name,
            temperature=temperature
        ), openai.define_embedding(
            embedding_model=embedding_model
        )),
        "aws": lambda: (aws.define_llm(
            model=model_name,
            temperature=temperature
            ), aws.define_embedding(
                embedding_model=embedding_model
            )),
        'ollama': lambda: (ollama.define_llm(
            model=model_name,
              temperature=temperature),
                           ollama.define_embedding(
                  embedding_model=embedding_model
                  )),
        'huggingface': lambda: (huggingface.define_llm(
            model=model_name,
            temperature=temperature,
        ), huggingface.define_embedding(
            embedding_model=embedding_model,
            region_name=region_name
        ))
    }

    if llm_type in llm_definitions:
        return llm_definitions[llm_type]()
    else:
        raise ValueError("Invalid LLM name")