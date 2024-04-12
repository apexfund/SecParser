from operator import itemgetter
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
# lang_endpoint = os.environ["LANGCHAIN_ENDPOINT"]
lang_apikey = os.environ["LANGCHAIN_API_KEY"]
openai_apikey = os.environ["OPENAI_API_KEY"]


import requests
from langchain import hub
from bs4 import BeautifulSoup as bs
from bs4 import SoupStrainer
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_community.document_loaders.html_bs import BSHTMLLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

#### INDEXING ####
# https://lilianweng.github.io/posts/2023-06-23-agent/

headers = {
    "User-Agent": "My User Agent 1.1",
    "From": "adgoch11@gmail.com",
}

# URL of the webpage
url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"

# Send a GET request to the URL
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Use BeautifulSoup to parse the HTML content
    soup = bs(response.text, "html.parser")

    # Write the parsed HTML to a local file
    with open("content.html", "w", encoding="utf-8") as file:
        file.write(str(soup.prettify()))
    print("HTML content saved successfully.")
else:
    print(f"Failed to retrieve the webpage: Status code {response.status_code}")


loader = BSHTMLLoader("content.html")
data = loader.load()

# Split
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(data)

# Embed
vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())

retriever = vectorstore.as_retriever()
print(retriever)

#### RETRIEVAL and GENERATION ####

# Prompt
prompt = hub.pull("rlm/rag-prompt")

# LLM
llm = ChatOpenAI(model_name="gpt-4-turbo-preview", temperature=0)


# Post-processing
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# print(format_docs(docs))

# Chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# Question
print(rag_chain.invoke("What are the general risks taken by the company?"))
