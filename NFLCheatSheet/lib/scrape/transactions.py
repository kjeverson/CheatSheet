import requests
from bs4 import BeautifulSoup
from datetime import datetime

URL = "https://www.espn.com/nfl/team/transactions/_/name/{}"


def convert_to_datetime(date_string):

    date = datetime.strptime(date_string, "%B %d, %Y")
    return date


def get_team_transactions(key):
    url = URL.format(key)
    html = requests.get(url)

    soup = BeautifulSoup(html.text, "html.parser")
    rows = soup.find_all("tr")
    rows = [row for row in rows if row.text != "DATETRANSACTION"]

    transactions = []
    for row in rows:
        data = row.find_all("td")
        data = [d.text for d in data]
        #data[0] = convert_to_datetime(data[0])
        transactions.append(data)

    return transactions

