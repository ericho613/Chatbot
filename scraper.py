
import requests
from pinecone import Pinecone, ServerlessSpec
from langchain_text_splitters.character import CharacterTextSplitter
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
# import streamlit as st
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
from dotenv import load_dotenv
import asyncio
from concurrent.futures import ThreadPoolExecutor

# from selenium.webdriver.edge.service import Service as EdgeService
# from webdriver_manager.microsoft import EdgeChromiumDriverManager

from bs4 import BeautifulSoup

load_dotenv()

class ScrapedWebPage:
    def __init__(self, url):

        self.url = url

        # Configure headless Chrome
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        # Use webdriver-manager to manage ChromeDriver
        service = Service(ChromeDriverManager().install())

        # Initialize the Chrome WebDriver with the service and options
        driver = webdriver.Chrome(service=service, options=options)

        print(f"Start scraping URL: {self.url}")

        # Start Selenium WebDriver
        driver.get(self.url)

        # Wait for JS to load (adjust as needed)
        time.sleep(2)

        # Fetch the page source after JS execution
        page_source = driver.page_source
        driver.quit()

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(page_source, 'html.parser')

        # Extract title
        self.title = soup.find('h1').get_text() if soup.find('h1') else soup.title.string if soup.title else "No title"

        # Remove all trailing and leading whitespaces, and new line
        # characters from p elements
        for paragraph_elem in soup.find_all('p'):
            modified_paragraph_text = paragraph_elem.get_text(separator=" ", strip=True)
            paragraph_elem.replace_with(modified_paragraph_text)

        # Remove unnecessary elements
        for irrelevant in soup.body(["script", "style", "img", "input", "footer", "header", "nav", "ds-search-results"]):
            irrelevant.decompose()

        # Extract the main text
        self.text = soup.body.get_text(separator="\n", strip=True)

        print(f"Finished scraping URL: {self.url}")

def scrape_web_page_sync(url: str):
    return ScrapedWebPage(url)

async def scrape_web_page_async(url, loop):
        
    executor = ThreadPoolExecutor(max_workers=5) # Adjust max_workers as needed

    """Asynchronously schedules a synchronous Selenium scraping task."""
    return await loop.run_in_executor(executor, scrape_web_page_sync, url)

async def upload_all_scraped_webpages(scraped_web_pages_list: list[ScrapedWebPage]):

    print(f"Starting upload to Pinecone.")

    pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

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

    # Initializing the character splitter, and defining how you want
    #  split text up in a document
    char_splitter = CharacterTextSplitter(
        # Setting the separator to "." to separate at the end of a sentence, and
        # to not end the chunk before a sentence finishes
        separator = ".",
        chunk_size = 10000,
        chunk_overlap  = 0
    )

    embedding = OpenAIEmbeddings(model = "text-embedding-3-small", openai_api_key=os.environ.get("OPENAI_API_KEY"))

    index = pc.Index(index_name)
    
    tasks = []

    for scraped_web_page in scraped_web_pages_list:

        pc_vector_store = PineconeVectorStore(index=index, embedding=embedding)

        # Splitting the original web page text into chunks of text
        char_split_text = char_splitter.split_text(scraped_web_page.text)

        print(f"Uploading the following to Pinecone: {scraped_web_page.title}")

        tasks.append(pc_vector_store.aadd_texts(
            texts=char_split_text,
            metadatas=[{"url": scraped_web_page.url, "title": scraped_web_page.title} for _ in range(len(char_split_text))]
        ))

    await asyncio.gather(*tasks)
    print(f"All scraped webpages uploaded to Pinecone.")

async def main():

    parent_sitemap_response = requests.get(os.environ.get("FOSRC_SERVER_LINK") + '/sitemap_index.html')

    #BeautifulSoup allows us to parse html; in other words, 
    # we can use beautiful soup to convert a html string value
    # to html objects (contained within a BeautifulSoup
    # instance)

    # Passing the html string value and 'html.parser' to the 
    # BeautifulSoup() class to create a BeautifulSoup instance
    # with the parsed html
    # Note that 'html.parser' is one of many different parsers
    # you can use with BeautifulSoup
    parent_soup = BeautifulSoup(parent_sitemap_response.content, 'html.parser')

    # Fetching all the href attribute values from every anchor element on the
    # parent sitemap page, and storing the href values in a list
    sitemap_parent_href_list = [link.get("href") for link in parent_soup.find_all("a")]
    sitemap_children_href_list = []

    # Fetching all the href attribute values from every anchor element on
    # every child sitemap page, and storing the href values in a list
    for href in sitemap_parent_href_list:
        child_sitemap_response = requests.get(href)
        child_soup = BeautifulSoup(child_sitemap_response.content, 'html.parser')
        for a in child_soup.find_all('a'):
            sitemap_children_href_list.append(a.get("href"))


    # Only scrape the last 50 sitemap children web pages for testing purposes;
    # set -50 to 0 in production environment
    sitemap_children_href_list_sample = sitemap_children_href_list[-50:]

    loop = asyncio.get_running_loop()

    chunk_size = 5

    scraped_web_pages_list = []

    # Only process 5 at a time to avoid overloading memory
    for i in range(0, len(sitemap_children_href_list_sample), chunk_size):
        chunk = sitemap_children_href_list_sample[i:i + chunk_size]
        tasks = [scrape_web_page_async(href, loop) for href in chunk]
        scraped_web_pages_chunk_list = await asyncio.gather(*tasks)
        scraped_web_pages_list.extend(scraped_web_pages_chunk_list)
        print(f"Completed {i + chunk_size} of {len(sitemap_children_href_list_sample)} web pages.")

    await upload_all_scraped_webpages(scraped_web_pages_list)

if __name__ == "__main__":
    asyncio.run(main())