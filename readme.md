Perform the following steps to run the application on a Windows operating system:

1.  In the command prompt, navigate inside the project folder by running the following command: cd [absolute path of the project folder]

2. Create a python virtual environment for the project.  In the terminal, run the following command: python -m venv venv

3. In the terminal, activate the virtual environment by running the following command: venv\Scripts\activate

4. In the terminal, install all required 3rd party packages/dependencies by running the following command: pip3 install -r requirements.txt

5. Create a ".env" file in the root folder/directory.  You can copy the ".env-example" file in the directory, and rename it to ".env".

5. Obtain an API key from OpenAI (https://openai.com/) and Pinecone (https://www.pinecone.io/).  Then, in the .env file, create a key named "OPENAI_API_KEY", and assign to it the value of the OpenAI API key using an "=".  Also, create a key named "PINECONE_API_KEY", and assign to it the value of the Pinecone API key using an "=".

6. To start the application using streamlit, run the following command in the terminal: streamlit run app.py

To run the web scraping program, perform the following steps:

1. Create a ".env" file in the root folder/directory.  You can copy the ".env-example" file in the directory, and rename it to ".env".

2. To start the application using streamlit, run the following command in the terminal: streamlit run app.py