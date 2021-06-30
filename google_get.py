import requests
from bs4 import BeautifulSoup

if __name__ == '__main__':
    url = 'https://www.google.com/search'
    params = {"client": "opera", "q": input(">>"), "sourceid": "opera", "ie": "UTF - 8", "oe": "UTF - 8"}
    # params = {"q": input()}
    response = requests.get(url, params=params)
    print(response.status_code)
    text = response.text
    soup = BeautifulSoup(text, "html.parser")

    print(*[item.attrs for item in soup.find_all('span') if item.attrs], sep='\n')
    # print([item for item in soup.find_all('div') if "data-exchange-rate" in item.attrs])
    # elems = [item for item in soup.find_all('div', attrs={'data-exchange-rate': True})]
    # print(elems)
