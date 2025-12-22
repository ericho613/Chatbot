from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import time
# import streamlit as st
from pypdf import PdfReader
import os
from dotenv import load_dotenv

if os.getenv("DEPLOYMENT_ENVIRONMENT", "development") != "production":
    load_dotenv()

def upload_pdf(pdf_file, citation):

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    index_name = "pdf-index"

    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name,
            # Dimension has been set to 1536 to match OpenAI's "text-embedding-3-small" embedding algorithm
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        while not pc.describe_index(index_name).status["ready"]:
            time.sleep(1)

    pdf_reader = PdfReader(pdf_file)

    full_pdf_text = ""

    # Iterate through all the PDF pages and remove all the new 
    # line characters to save tokens
    for i in range(len(pdf_reader.pages)):
        full_pdf_text += ' '.join(pdf_reader.pages[i].extract_text().split())

    # Initializing the character splitter, and defining how you want
    #  split text up in a document
    char_splitter = CharacterTextSplitter(
        # Setting the separator to "." to separate at the end of a sentence, and
        # to not end the chunk before a sentence finishes
        separator = ".",
        chunk_size = 1000,
        chunk_overlap  = 20
    )

    # Splitting the original PDF file into chunks of text
    char_split_text = char_splitter.split_text(full_pdf_text)

    embedding = OpenAIEmbeddings(model = "text-embedding-3-small", openai_api_key=os.getenv("OPENAI_API_KEY"))

    index = pc.Index(index_name)

    pc_vector_store = PineconeVectorStore(index=index, embedding=embedding)

    pc_vector_store.add_texts(
        texts=char_split_text,
        metadatas=[{"citation": citation} for _ in range(len(char_split_text))]
    )