import re
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs

base_url = r"https://www.sec.gov/cgi-bin/browse-edgar"
headers = {
    "User-Agent": "My User Agent 1.1",
    "From": "adgoch11@gmail.com",
}

param_dict = {
    "action": "getcompany",
    "CIK": "NVDA",
    "type": "10-k",
    "owner": "exclude",
    "output": "XML",
    "count": "10",
}

response = requests.get(url=base_url, params=param_dict, headers=headers)
print(response.url)
soup = bs(response.content, "lxml")

print("Request Successful")

# define a base url that will be used for link building.
base_url_sec = r"https://www.sec.gov"

# find the document table with our data
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
ten_k_doc_href = ten_k_soup.find_all(string=re.compile("10-K"))[0].parent.parent["href"]

fin = base_url_sec + ten_k_doc_href
print(fin)
