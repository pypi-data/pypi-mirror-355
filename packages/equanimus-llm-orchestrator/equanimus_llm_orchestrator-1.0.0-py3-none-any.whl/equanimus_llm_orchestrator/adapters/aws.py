from langchain_aws import ChatBedrock
from langchain_aws import BedrockEmbeddings

from pathlib import Path
from transformers import GPT2TokenizerFast

def get_token_ids(text: str) -> list[int]:
    base_dir = Path(__file__).resolve().parent.parent
    tokenizer_path = base_dir / "modes_pretrained" / "GPT2TokenizerFast" / "gpt2"
    tokenizer = GPT2TokenizerFast.from_pretrained(str(tokenizer_path))

    return tokenizer.encode(text)

def define_llm (
    model: str = "us.meta.llama3-2-90b-instruct-v1:0",
    temperature: float = 0.0,
):


    llm = ChatBedrock(
        model_id=model,
        beta_use_converse_api=True,
        temperature=temperature,
        custom_get_token_ids=get_token_ids
      )
    return llm

def define_embedding(embedding_model: str = "cohere.embed-multilingual-v3", region_name: str = "us-east-1"):
    return BedrockEmbeddings(
        model_id=embedding_model,
        region_name=region_name,
    )
