from langchain_community.document_loaders.html_bs import BSHTMLLoader

headers = {
    "User-Agent": "My User Agent 1.1",
    "From": "adgoch11@gmail.com",
}

# response = requests.get(
#     url="https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
#     headers=headers,
# )

# if response.status_code == 200:
#     # Get the text (HTML) from the response
#     html_content = response.text

#     # Open a file named 'content.html' in write mode ('w')
#     with open("content.html", "w", encoding="utf-8") as file:
#         # Write the HTML content to the file
#         file.write(html_content)
#     print("Content saved to 'content.html'.")
# else:
#     print(
#         f"Failed to retrieve the website content. Status code: {response.status_code}"
#     )

import requests
from bs4 import BeautifulSoup

# URL of the webpage
url = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm"

# Send a GET request to the URL
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Use BeautifulSoup to parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Write the parsed HTML to a local file
    with open("content.html", "w", encoding="utf-8") as file:
        file.write(str(soup.prettify()))
    print("HTML content saved successfully.")
else:
    print(f"Failed to retrieve the webpage: Status code {response.status_code}")


loader = BSHTMLLoader("content.html")
data = loader.load()
print(data)
