# from asyncio.events import BaseDefaultEventLoopPolicy
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

try:
    from googlesearch import search
except ImportError:
    print("No module named 'google' found")

query = input("Enter a question:\n")
headers = {}
headers['User-Agent'] = "Mozilla/5.0 (X11; Linux i686) AppleWebKit/537.17 (KHTML, like Gecko) Chrome/24.0.1312.27 Safari/537.17"
dct = {}
search_keywords = ["When", "did", "the", "Fall", "of", "Constantinople", "take", "place"]
    

for url in search(query, tld="co.in", num=10, stop=5, pause=2):
    print(url)
    req = urllib.request.Request(url, headers = headers)
    page = urllib.request.urlopen(req)
    html = page.read().decode("utf-8")
    soup = BeautifulSoup(html, 'html.parser')
    aux = ' '.join([x for x in soup.get_text().split('\n') if x != ''])
    print(aux)
    # texts = soup.reviewText.values
    # ids = soup.asin.values
    break

# best_sentences = [key for key,value in dct.items() if value == max(dct.values())]

# print("\n".join(best_sentences))
    # print(soup.get_text())
    # print(soup.prettify())
