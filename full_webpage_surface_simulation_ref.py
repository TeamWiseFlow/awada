"""
完整模拟网页浏览行为，包括页面滚动等
copy from https://github.com/hustzhangwenfeng/gpt-researcher/tree/master/scraping
"""

"""Selenium web scraping module."""
from __future__ import annotations

import logging
import asyncio
from pathlib import Path
from sys import platform

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.safari.options import Options as SafariOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from fastapi import WebSocket

from scraping import scrape_skills, processing as summary
from scraping.processing.html import extract_hyperlinks, format_hyperlinks

from concurrent.futures import ThreadPoolExecutor

from scraping.processing.text import summarize_text

executor = ThreadPoolExecutor()

FILE_DIR = Path(__file__).parent.parent


async def async_browse(
        selenium_web_browser: str,
        user_agent: str,
        fast_llm_model: str,
        summary_token_limit: str,
        llm_provider: str,
        url: str, question: str,
        websocket: WebSocket
) -> str:
    """Browse a website and return the answer and links to the user
    他这个项目要实现的是agent按照用户提问去搜索网页
    Args:
        selenium_web_browser (str): The web browser used for scraping
        user_agent (str): The user agent used when scraping
        url (str): The url of the website to browse
        question (str): The question asked by the user
        websocket (WebSocketManager): The websocket manager

    Returns:
        str: The answer and links to the user
    """
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=8)

    print(f"Scraping url {url} with question {question}")
    if websocket:
        await websocket.send_json(
            {
                "type": "logs",
                "output": f"🔎 Browsing the {url} for relevant about: {question}...",
            }
        )
    else:
        print(f"🔎 Browsing the {url} for relevant about: {question}...")

    try:
        driver, text = await loop.run_in_executor(
            executor, scrape_text_with_selenium, selenium_web_browser, user_agent, url
        )
        await loop.run_in_executor(executor, add_header, driver)
        summary_text = await loop.run_in_executor(
            executor, summarize_text, fast_llm_model, summary_token_limit, llm_provider, url, text, question, driver
        )
        if websocket:
            await websocket.send_json(
                {
                    "type": "logs",
                    "output": f"📝 Information gathered from url {url}: {summary_text}",
                }
            )
        else:
            print(f"📝 Information gathered from url {url}: {summary_text}")

        return f"Information gathered from url {url}: {summary_text}"
    except Exception as e:
        print(f"An error occurred while processing the url {url}: {e}")
        return f"Error processing the url {url}: {e}"


def browse_website(url: str, question: str) -> tuple[str, WebDriver]:
    """Browse a website and return the answer and links to the user

    Args:
        url (str): The url of the website to browse
        question (str): The question asked by the user

    Returns:
        Tuple[str, WebDriver]: The answer and links to the user and the webdriver
    """

    if not url:
        return "A URL was not specified, cancelling request to browse website.", None

    driver, text = scrape_text_with_selenium(url)
    add_header(driver)
    summary_text = summary.summarize_text(url, text, question, driver)

    links = scrape_links_with_selenium(driver, url)

    # Limit links to 5
    if len(links) > 5:
        links = links[:5]

    # write_to_file('research-{0}.txt'.format(url), summary_text + "\nSource Links: {0}\n\n".format(links))

    close_browser(driver)
    return f"Answer gathered from website: {summary_text} \n \n Links: {links}", driver


def scrape_text_with_selenium(selenium_web_browser: str, user_agent: str, url: str) -> tuple[WebDriver, str]:
    """Scrape text from a website using selenium

    Args:
        url (str): The url of the website to scrape
        selenium_web_browser (str): The web browser used to scrape
        user_agent (str): The user agent used when scraping

    Returns:
        Tuple[WebDriver, str]: The webdriver and the text scraped from the website
    """
    logging.getLogger("selenium").setLevel(logging.CRITICAL)

    options_available = {
        "chrome": ChromeOptions,
        "safari": SafariOptions,
        "firefox": FirefoxOptions,
    }

    options = options_available[selenium_web_browser]()
    options.add_argument(f"user-agent={user_agent}")
    options.add_argument("--headless")
    options.add_argument("--enable-javascript")

    if selenium_web_browser == "firefox":
        driver = webdriver.Firefox(options=options)
    elif selenium_web_browser == "safari":
        # Requires a bit more setup on the users end
        # See https://developer.apple.com/documentation/webkit/testing_with_webdriver_in_safari
        driver = webdriver.Safari(options=options)
    else:
        if platform == "linux" or platform == "linux2":
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--remote-debugging-port=9222")
        options.add_argument("--no-sandbox")
        options.add_experimental_option("prefs", {"download_restrictions": 3})
        driver = webdriver.Chrome(options=options)

    print(f"scraping url {url}...")
    driver.get(url)

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    # check if url is a pdf or arxiv link
    if url.endswith(".pdf"):
        text = scrape_skills.scrape_pdf_with_pymupdf(url)
    elif "arxiv" in url:
        # parse the document number from the url
        doc_num = url.split("/")[-1]
        text = scrape_skills.scrape_pdf_with_arxiv(doc_num)
    else:
        # Get the HTML content directly from the browser's DOM
        page_source = driver.execute_script("return document.body.outerHTML;")
        soup = BeautifulSoup(page_source, "html.parser")

        for script in soup(["script", "style"]):
            script.extract()

        # text = soup.get_text()
        text = get_text(soup)

    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = "\n".join(chunk for chunk in chunks if chunk)
    return driver, text


def get_text(soup):
    """Get the text from the soup

    Args:
        soup (BeautifulSoup): The soup to get the text from

    Returns:
        str: The text from the soup
    """
    text = ""
    tags = ["h1", "h2", "h3", "h4", "h5", "p"]
    for element in soup.find_all(tags):  # Find all the <p> elements
        text += element.text + "\n\n"
    return text


def scrape_links_with_selenium(driver: WebDriver, url: str) -> list[str]:
    """Scrape links from a website using selenium

    Args:
        driver (WebDriver): The webdriver to use to scrape the links

    Returns:
        List[str]: The links scraped from the website
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    hyperlinks = extract_hyperlinks(soup, url)

    return format_hyperlinks(hyperlinks)


def close_browser(driver: WebDriver) -> None:
    """Close the browser

    Args:
        driver (WebDriver): The webdriver to close

    Returns:
        None
    """
    driver.quit()


def add_header(driver: WebDriver) -> None:
    """Add a header to the website

    Args:
        driver (WebDriver): The webdriver to use to add the header

    Returns:
        None
    """
    driver.execute_script(open(f"{FILE_DIR}/js/overlay.js", "r").read())

"""
js 文件内容：
const overlay = document.createElement('div');
Object.assign(overlay.style, {
    position: 'fixed',
    zIndex: 999999,
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    background: 'rgba(0, 0, 0, 0.7)',
    color: '#fff',
    fontSize: '24px',
    fontWeight: 'bold',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
});
const textContent = document.createElement('div');
Object.assign(textContent.style, {
    textAlign: 'center',
});
textContent.textContent = 'Tavily AI: Analyzing Page';
overlay.appendChild(textContent);
document.body.append(overlay);
document.body.style.overflow = 'hidden';
let dotCount = 0;
setInterval(() => {
    textContent.textContent = 'Tavily AI: Analyzing Page' + '.'.repeat(dotCount);
    dotCount = (dotCount + 1) % 4;
}, 1000);
"""

# 如下两个skill 使用langchain，可能效果一般，而且是针对pdf和arxiv，有可能用不上
from langchain.document_loaders import PyMuPDFLoader
from langchain.retrievers import ArxivRetriever


def scrape_pdf_with_pymupdf(url) -> str:
    """Scrape a pdf with pymupdf

    Args:
        url (str): The url of the pdf to scrape

    Returns:
        str: The text scraped from the pdf
    """
    loader = PyMuPDFLoader(url)
    doc = loader.load()
    return str(doc)


def scrape_pdf_with_arxiv(query) -> str:
    """Scrape a pdf with arxiv
    default document length of 70000 about ~15 pages or None for no limit

    Args:
        query (str): The query to search for

    Returns:
        str: The text scraped from the pdf
    """
    retriever = ArxivRetriever(load_max_docs=2, doc_content_chars_max=None)
    docs = retriever.get_relevant_documents(query=query)
    return docs[0].page_content

"""Text processing functions"""
import urllib
from typing import Dict, Generator, Optional

from selenium.webdriver.remote.webdriver import WebDriver

from config import Config
from gpt_researcher_old.retriever.llm_utils import create_chat_completion
import os
from md2pdf.core import md2pdf


def split_text(text: str, max_length: int = 8192) -> Generator[str, None, None]:
    """Split text into chunks of a maximum length

    Args:
        text (str): The text to split
        max_length (int, optional): The maximum length of each chunk. Defaults to 8192.

    Yields:
        str: The next chunk of text

    Raises:
        ValueError: If the text is longer than the maximum length
    """
    paragraphs = text.split("\n")
    current_length = 0
    current_chunk = []

    for paragraph in paragraphs:
        if current_length + len(paragraph) + 1 <= max_length:
            current_chunk.append(paragraph)
            current_length += len(paragraph) + 1
        else:
            yield "\n".join(current_chunk)
            current_chunk = [paragraph]
            current_length = len(paragraph) + 1

    if current_chunk:
        yield "\n".join(current_chunk)


def summarize_text(
    fast_llm_model: str, summary_token_limit: int, llm_provider: str, url: str, text: str, question: str, driver: Optional[WebDriver] = None
) -> str:
    """Summarize text using the OpenAI API

    Args:
        fast_llm_model (str): The fast LLM model e.g gpt3.5-turbo-16k
        summary_token_limit (int): The summary token limit
        llm_provider (str): The llm provider
        url (str): The url of the text
        text (str): The text to summarize
        question (str): The question to ask the model
        driver (WebDriver): The webdriver to use to scroll the page

    Returns:
        str: The summary of the text
    """
    if not text:
        return "Error: No text to summarize"

    summaries = []
    chunks = list(split_text(text))
    scroll_ratio = 1 / len(chunks)

    print(f"Summarizing url: {url} with total chunks: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        if driver:
            scroll_to_percentage(driver, scroll_ratio * i)

        #memory_to_add = f"Source: {url}\n" f"Raw content part#{i + 1}: {chunk}"

        #MEMORY.add_documents([Document(page_content=memory_to_add)])

        messages = [create_message(chunk, question)]

        summary = create_chat_completion(
            model=fast_llm_model,
            messages=messages,
            max_tokens=summary_token_limit,
            llm_provider=llm_provider
        )
        summaries.append(summary)
        #memory_to_add = f"Source: {url}\n" f"Content summary part#{i + 1}: {summary}"

        #MEMORY.add_documents([Document(page_content=memory_to_add)])

    combined_summary = "\n".join(summaries)
    messages = [create_message(combined_summary, question)]

    final_summary = create_chat_completion(
        model=fast_llm_model,
        messages=messages,
        max_tokens=summary_token_limit,
        llm_provider=llm_provider,
    )
    print("Final summary length: ", len(combined_summary))
    print(final_summary)

    return final_summary


def scroll_to_percentage(driver: WebDriver, ratio: float) -> None:
    """Scroll to a percentage of the page

    Args:
        driver (WebDriver): The webdriver to use
        ratio (float): The percentage to scroll to

    Raises:
        ValueError: If the ratio is not between 0 and 1
    """
    if ratio < 0 or ratio > 1:
        raise ValueError("Percentage should be between 0 and 1")
    driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {ratio});")


def create_message(chunk: str, question: str) -> Dict[str, str]:
    """Create a message for the chat completion

    Args:
        chunk (str): The chunk of text to summarize
        question (str): The question to answer

    Returns:
        Dict[str, str]: The message to send to the chat completion
    """
    return {
        "role": "user",
        "content": f'"""{chunk}"""\n'
        f'Using the above text, summarize it based on the following task or query: "{question}".\n'
        f'If the query cannot be answered using the text, YOU MUST summarize the text in short.\n'
        f'Include all factual information such as numbers, stats, quotes, etc if available.',
    }

def write_to_file(filename: str, text: str) -> None:
    """Write text to a file

    Args:
        text (str): The text to write
        filename (str): The filename to write to
    """
    with open(filename, "w") as file:
        file.write(text)

async def write_md_to_pdf(task: str, path: str, text: str) -> None:
    file_path = f"{path}/{task}"
    write_to_file(f"{file_path}.md", text)
    md_to_pdf(f"{file_path}.md", f"{file_path}.pdf")
    print(f"{task} written to {file_path}.pdf")

    encoded_file_path = urllib.parse.quote(f"{file_path}.pdf")

    return encoded_file_path

def read_txt_files(directory):
    all_text = ''

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            with open(os.path.join(directory, filename), 'r') as file:
                all_text += file.read() + '\n'

    return all_text


def md_to_pdf(input_file, output_file):
    md2pdf(output_file,
           md_content=None,
           md_file_path=input_file,
           css_file_path=None,
           base_url=None)

"""HTML processing functions"""
from __future__ import annotations

from bs4 import BeautifulSoup
from requests.compat import urljoin


def extract_hyperlinks(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    """Extract hyperlinks from a BeautifulSoup object

    Args:
        soup (BeautifulSoup): The BeautifulSoup object
        base_url (str): The base URL

    Returns:
        List[Tuple[str, str]]: The extracted hyperlinks
    """
    return [
        (link.text, urljoin(base_url, link["href"]))
        for link in soup.find_all("a", href=True)
    ]


def format_hyperlinks(hyperlinks: list[tuple[str, str]]) -> list[str]:
    """Format hyperlinks to be displayed to the user

    Args:
        hyperlinks (List[Tuple[str, str]]): The hyperlinks to format

    Returns:
        List[str]: The formatted hyperlinks
    """
    return [f"{link_text} ({link_url})" for link_text, link_url in hyperlinks]