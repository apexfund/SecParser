# One function to configure the ticker and fetch link
def get_latest_link(ticker: str) -> str:
    import re
    import requests
    import pandas as pd
    from bs4 import BeautifulSoup as bs

    # Set default headers/parameters
    base_url = r"https://www.sec.gov/cgi-bin/browse-edgar"
    headers = {
        "User-Agent": "Apex User Agent",
        "From": "apexfund@gmail.com",
    }

    param_dict = {
        "action": "getcompany",
        "CIK": ticker,
        "type": "10-k",
        "owner": "exclude",
        "output": "XML",
        "count": "10",
    }

    # Fetch response from EDGAR
    response = requests.get(url=base_url, params=param_dict, headers=headers)
    print(response.url)
    soup = bs(response.content, "lxml")

    print("Request Successful")

    # Define a base url that will be used for link building.
    base_url_sec = r"https://www.sec.gov"

    # Find the document table with our data
    doc_table = soup("table")[2]
    doc_table = bs(str(doc_table), "html.parser")

    # Locating the 10-k file links
    strink = ""
    for item in doc_table.find_all(string=re.compile("10-K")):
        strink += str(item.parent.parent.prettify())

    ten_k_rows = bs(strink, "html.parser")
    with open("row.txt", "w") as file:
        file.write(str(ten_k_rows.prettify()))

    file_dict = {}
    file_dict["file_type"] = param_dict["type"]
    file_dict["ticker"] = param_dict["CIK"]
    file_dict["links"] = {}
    if len(ten_k_rows) != 0:

        for row in ten_k_rows.find_all("tr"):
            filing_date = str(
                row.find_all("td")[3].text
            ).strip()  # Extract date from the HTML directly
            date = str(filing_date).replace("-", "")
            file_dict["links"][date] = {}

            filing_doc_href = row.find("a", {"id": "documentsbutton"})
            if filing_doc_href is not None:
                file_dict["links"][date]["documents"] = (
                    base_url_sec + filing_doc_href["href"]
                )

            filing_int_href = row.find("a", {"id": "interactiveDataBtn"})
            if filing_int_href is not None:
                file_dict["links"][date]["interactive_data"] = (
                    base_url_sec + filing_int_href["href"]
                )

    # print(file_dict)

    ten_k = requests.get(
        url=file_dict["links"][next(iter(file_dict["links"]))]["interactive_data"],
        headers=headers,
    )
    ten_k_soup = bs(ten_k.content, "lxml")
    ten_k_doc_href = ten_k_soup.find_all(string=re.compile("10-K"))[0].parent.parent[
        "href"
    ]

    fin = base_url_sec + ten_k_doc_href
    fin = fin[:20] + fin[28:]
    return fin


# One function to parse html and store in DB
def fetch_parse_store(url: str) -> None:
    import os
    import requests
    from langchain import hub
    from bs4 import BeautifulSoup as bs
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders.html_bs import BSHTMLLoader
    from langchain_community.vectorstores.chroma import Chroma
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    #### INDEXING ####

    headers = {
        "User-Agent": "Apex User Agent",
        "From": "apexfundquant@gmail.com",
    }

    # Send a GET request to the URL
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Use BeautifulSoup to parse the HTML content
        soup = bs(response.text, "html.parser")

        # Write the parsed HTML to a local file
        with open("/tmp/content.html", "w", encoding="utf-8") as file:
            file.write(str(soup.prettify()))
        print("HTML content saved successfully.")
    else:
        print(f"Failed to retrieve the webpage: Status code {response.status_code}")


# One function for actual operation
def fetch_completions(prompt: str) -> str:
    import os
    import requests
    from langchain import hub
    from bs4 import BeautifulSoup as bs
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_community.document_loaders.html_bs import BSHTMLLoader
    from langchain_community.vectorstores.chroma import Chroma
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
    os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    loader = BSHTMLLoader("/tmp/content.html")
    data = loader.load()

    # Split
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(data)

    # Embed
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY),
    )

    retriever = vectorstore.as_retriever()
    # print(retriever)

    #### RETRIEVAL and GENERATION ####

    # Prompt
    prompt = hub.pull("rlm/rag-prompt")

    # LLM
    llm = ChatOpenAI(model_name="gpt-4-turbo", temperature=0)

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
    return rag_chain.invoke(prompt)


def lambda_handler(event, context):
    return event
