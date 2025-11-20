import streamlit as st
# from openai import OpenAI
from langchain_openai.chat_models import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from summary import generate_pdf_summary_prompt
from citation import generate_pdf_citation_prompt
from upload import upload_pdf
# from rag import generate_rag_runnable_chain
from function_tools import get_fosrc_answer

@st.dialog("Ask FOSRC")
def ask_fosrc():
    st.write(f"Ask a question.  Generated answers will reference scientific materials stored in the Federal Open Science Repository of Canada.")
    user_question = st.text_area(
        label="Question:",
        height=200,
        max_chars=400
    )
    if st.button("Submit"):

        with st.spinner("Processing"):

            response = get_fosrc_answer(user_question)

            # Append the assistant's full response to the 'messages' list
            st.session_state.messages.append({"role": "assistant", "content": response})

            st.rerun()

@st.dialog("Summarize a PDF File")
def summarize_pdf():
    st.write(f"Upload a PDF file to summarize.")

    language_options = ["English", "Français"]
    selected_language = st.selectbox("Select a language for the summary:", language_options, index=0)
    
    uploaded_pdf_file = st.file_uploader("Choose a file:", type=["pdf"])

    if uploaded_pdf_file is not None:
        st.write("File uploaded successfully!")
        st.write(f"File Name: {uploaded_pdf_file.name}")
        st.write(f"File Type: {uploaded_pdf_file.type}")
        st.write(f"File Size: {uploaded_pdf_file.size} bytes")

    else:
        st.info("Please upload a PDF file.")
    
    if st.button("Submit"):

        with st.spinner("Processing"):

            response = get_open_ai_client().invoke([SystemMessage(generate_pdf_summary_prompt(uploaded_pdf_file, selected_language))])

            # Append the assistant's full response to the 'messages' list
            st.session_state.messages.append({"role": "assistant", "content": response.content})

            st.rerun()

@st.dialog("Generate a Citation")
def generate_citation():
    st.write(f"Generate a citation from a PDF document.")

    citation_style_options = ["APA", "MLA"]
    selected_citation_style = st.selectbox("Select a language for the summary:", citation_style_options, index=0)
    
    uploaded_pdf_file = st.file_uploader("Choose a file:", type=["pdf"])

    if uploaded_pdf_file is not None:
        st.write("File uploaded successfully!")
        st.write(f"File Name: {uploaded_pdf_file.name}")
        st.write(f"File Type: {uploaded_pdf_file.type}")
        st.write(f"File Size: {uploaded_pdf_file.size} bytes")

    else:
        st.info("Please upload a PDF file.")
    
    if st.button("Submit"):

        with st.spinner("Processing"):

            response = get_open_ai_client().invoke([SystemMessage(generate_pdf_citation_prompt(uploaded_pdf_file, selected_citation_style))])

            # Append the assistant's full response to the 'messages' list
            st.session_state.messages.append({"role": "assistant", "content": response.content})

            st.rerun()

@st.dialog("Upload PDF(s)")
def upload():
    st.write(f"Upload PDF(s) to a vector database.")

    uploaded_pdf_files = st.file_uploader("Choose a file:", type=["pdf"], accept_multiple_files=True)

    if uploaded_pdf_files is not None:
        st.write("File(s) uploaded successfully!")
        for file in uploaded_pdf_files:
            st.write(f"File Name: {file.name}")
            st.write(f"File Type: {file.type}")
            st.write(f"File Size: {file.size} bytes")

    else:
        st.info("Please upload a PDF file.")
    
    if st.button("Submit"):

        with st.spinner("Processing"):

            for file in uploaded_pdf_files:
                response = get_open_ai_client().invoke([SystemMessage(generate_pdf_citation_prompt(file, "APA"))])
                upload_pdf(file, response.content)

            # Append the assistant's full response to the 'messages' list
            st.session_state.messages.append({"role": "assistant", "content": "Upload to vector database complete."})

            st.rerun()

def get_open_ai_client():
    
    # Initializing the OpenAI client
    client = ChatOpenAI(
    model = st.session_state["openai_model"], 
    # Set the seed value to get repeatable/predictable results
    # seed = 100, 

    # Optional setting for temperature; default is 1; temperature
            # can be set up to 2 for more answer randomness/creativity
    temperature = 1, 
    max_tokens = 1000,

    # Optional api_key parameter if you prefer to pass api key in 
    # directly instead of loading environment variables
    # Fetching the OPENAI_API_KEY environment variable from the secrets.toml file
    api_key=st.secrets["OPENAI_API_KEY"],  
    )

    return client

def initialize_session_state():

    # Setting up the OpenAI model in session state if it is not already defined
    if "openai_model" not in st.session_state:
        st.session_state["openai_model"] = st.secrets["GPT_MODEL"]

    # Initializing the 'chat_history_summary' key in the session state 
    if "chat_history_summary" not in st.session_state:
        st.session_state.chat_history_summary = ""

    # Initializing the 'messages' list 
    if "messages" not in st.session_state:
        st.session_state.messages = []

        # Appending the user's input to the 'messages' list in session state
        st.session_state.messages.append({"role": "assistant", "content": "Hello.  How can I help you today?"})

def reset_conversation(): 
    st.session_state.messages = None 
    st.session_state.messages = []
    # Appending the user's input to the 'messages' list in session state
    st.session_state.messages.append({"role": "assistant", "content": "Hello.  How can I help you today?"})
    st.session_state.chat_history_summary = ""
    
def run_app():
    # Setting up the Streamlit page configuration; the page
    # title has been modified, and an icon has been added to the title
    st.set_page_config(
        page_title="FOSRC Chatbot", 
        page_icon="💬")

    # Setting the page title
    # st.title("Chatbot Prototype")

    # Setting the side bar
    with st.sidebar:
        st.button("Ask FOSRC", type="tertiary", on_click=ask_fosrc)
        st.button("Summarize a PDF", type="tertiary", on_click=summarize_pdf)
        st.button("Generate a Citation", type="tertiary", on_click=generate_citation)
        st.button("Upload PDF(s)", type="tertiary", on_click=upload)

    initialize_session_state()
        
    # Looping through the 'messages' list to display each message except system messages
    for message in st.session_state.messages:

        # Do not show system messages in the chat UI, 
        # only human messages and AI messages
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Input field for the user to send a new message
    if prompt := st.chat_input("Ask a question or enter a response."):

        # Appending the user's input to the 'messages' list in session state
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display the user's message in a chat bubble
        with st.chat_message("user"):
            st.markdown(prompt)
    
        # Assistant's response
        with st.chat_message("assistant"):

            # Only ever include the last 5 non-system messages
            # (4 historic messages and 1 new user message) in the chat prompt
            # because the previous chat history summary is 
            # provided in the system message (to optimize token usage
            # in the case of long conversations); keeping the last
            # 5 messages is needed for better user experience
            chat_prompt = [
                    HumanMessage(message["content"]) if message["role"] == "user" else AIMessage(message["content"]) for message in st.session_state.messages[-5:]
                ]
            
            system_message_text=f'''You are a scientific expert that can communicate simply, clearly, and concisely.

Use the following chat history summary if present to answer questions if needed:
{st.session_state.chat_history_summary}
'''

            streaming_response = get_open_ai_client().stream([SystemMessage(system_message_text)] + chat_prompt)

            # Display the assistant's response as it streams
            streaming_response_text = st.write_stream(streaming_response)

            # Append the assistant's full response to the 'messages' list
            st.session_state.messages.append({"role": "assistant", "content": streaming_response_text})
            
            # If there are more than 5 non-system messages,
            # then create a chat history summary to optimize token usage
            if len(st.session_state.messages) > 5:
                new_chat_history = ""

                # If the chat_history_summary value is an empty string, then create one
                # using all the historic messages; otherwise; use the previous
                # chat history summary and the 2 newests chat messages to create a new
                # chat history summary
                if st.session_state.chat_history_summary == "":
                    for message in st.session_state.messages:
                        new_chat_history += f"{message["role"]}: {message["content"]}\n\n"

                else:
                    new_chat_history = f"user: {prompt}\n\nassistant: {streaming_response_text}\n\n"

                summary_instructions = f'''Create a chat history summary as an ordered list of past user questions with the summarized assistant responses.  The chat history summary should repeat the previous chat history summary below if present, and new list items should be added according to the new chat history below.  Do not include headings.

Previous Chat History Summary:
{st.session_state.chat_history_summary}

New chat history:
{new_chat_history}
'''
                
                # Create a new chat history summary using the summary instructions
                summary = get_open_ai_client().invoke([HumanMessage(summary_instructions)])

                st.session_state.chat_history_summary = summary.content

                # print("********************")
                # print(st.session_state.chat_history_summary)
                

    if len(st.session_state.messages) > 1:

        st.divider()

        # Button to restart the chat session
        st.button("Reset Chat", on_click=reset_conversation)

if __name__== '__main__':
    run_app()
