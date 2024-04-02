from operator import itemgetter
import os

os.environ["LANGCHAIN_TRACING_V2"] = "true"
lang_endpoint = os.environ["LANGCHAIN_ENDPOINT"]
lang_apikey = os.environ["LANGCHAIN_API_KEY"]
openai_apikey = os.environ["OPENAI_API_KEY"]


import bs4
from langchain import hub
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

#### INDEXING ####
# https://lilianweng.github.io/posts/2023-06-23-agent/

# Load Documents
loader = WebBaseLoader(
    web_paths=(
        "https://www.sec.gov/ix?doc=/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
    ),
    bs_kwargs=dict(parse_only=bs4.SoupStrainer(class_=(""))),
)
docs = loader.load()

# Split
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

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
