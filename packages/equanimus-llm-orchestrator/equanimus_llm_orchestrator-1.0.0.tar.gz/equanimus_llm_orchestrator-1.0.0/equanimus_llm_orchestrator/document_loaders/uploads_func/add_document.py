from langchain_text_splitters import RecursiveCharacterTextSplitter

def add_to_VDB (documents, retriever, chunk_size=500, chunk_overlap=20):

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    splits = text_splitter.split_documents(documents)

    retriever.add_documents(splits)

    return splits, retriever
