from pinecone import Pinecone, ServerlessSpec
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import time
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
# import streamlit as st
import os
from dotenv import load_dotenv

if os.getenv("DEPLOYMENT_ENVIRONMENT", "development") != "production":
    load_dotenv()

def generate_rag_runnable_chain():

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


    embedding = OpenAIEmbeddings(model = "text-embedding-3-small", openai_api_key=os.getenv("OPENAI_API_KEY"))

    index = pc.Index(index_name)

    pc_vector_store = PineconeVectorStore(index=index, embedding=embedding)

    retriever = pc_vector_store.as_retriever(

        # The maximum marginal relevance (mmr) search is like the similarity search
        # except that it make sure that duplicate/overly-similar/redundant
        # results are not returned from the database; result diversity can be
        # improved with maximum marginal relevance search (compared with
        # plain similarity searching)
        search_type = 'mmr', 

        # The lambda multiplication factor controls the diversity of results;
        # the scale goes from 0 to 1; 0 is most diverse; 1 is least diverse;
        # setting to 1 would be equivalent to a similarity search
        search_kwargs = {

            # Number of Documents to return. Defaults to 4.
            'k':4, 

            # The lambda multiplication factor controls the diversity of results;
            # the scale goes from 0 to 1; 0 is most diverse; 1 is least diverse;
            # setting to 1 would be equivalent to a similarity search
            'lambda_mult':0.7

            # optonal filter parameter to filter by a metadata value
            # filter = {"metadata key": "metadata value"}
            }
        )

    TEMPLATE = '''You are a scientific expert that can communicate simply, clearly, and concisely.

Provide a detailed answer for the following question:
{question}

To answer the question, only use the following context if relevant; otherwise, say "The information is not available in FOSRC":
{context}

If any resource in the context is used, then at the end of the response, specify the full citation for the resource in the format:

FOSRC References:

*Citations*

where *Citations* should be substituted with the citations as an alphabetically ordered list.

If no resource in the context is used, then do not include the "FOSRC References" section.
'''

    prompt_template = PromptTemplate.from_template(TEMPLATE)

    chain = ({'context': retriever, 
            'question': RunnablePassthrough()} 
            | prompt_template)

    return chain