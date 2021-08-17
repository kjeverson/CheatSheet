import re
import requests
from bs4 import BeautifulSoup
from typing import Dict


def get_recent_stats(firstname: str, lastname: str, position: str) -> Dict:
    """
    Get Player's Recent Game Stats (Usually in season)
    :param firstname: Player's First Name
    :param lastname: Player's Last Name
    :return: Dict of recent game stats
    """

    url = "https://www.nfl.com/players/{}-{}/stats/".format(firstname, lastname)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    recent_games = {}
    table = soup.find("table", {"summary": "Recent Games"})
    if table:
        if position == "QB":
            headers = ["OPP", "RESULT", "passComps", "passAtts", "passYDs", "passAVG", "passTDs",
                       "passINTs", "passSacks", "SCKY", "RATE", "rushAtts", "rushYDs", "rushAVG",
                       "rushTDs", "fum", "fumLost"]
        elif position == "RB":
            headers = ["OPP", "RESULT", "passComps", "rushAtts", "rushYDs", "rushAVG", "rushLNG",
                       "rushTDs", "rec", "recYDs", "recAVG", "recLNG", "recTDs", "fum", "fumLost"]
        else:
            headers = ["OPP", "RESULT", "rec", "recYDs", "recAVG", "recLNG", "recTDs", "rushAtts",
                       "rushYDs", "rushAVG", "rushLNG", "rushTDs", "fum", "fumLost"]

        #headers = [re.sub(r'\s+', '', header.text) for header in table.find_all("th")][1:]

        tbody = table.find("tbody")
        for week in tbody.find_all("tr"):
            wk = week.find("td", {"class": None}).text
            recent_games.update({wk: {}})
            i = 0
            for col in week.find_all("td", {"class": not None}):
                key = headers[i]
                data = "0" if not col.text else re.sub(r'\s+', '', col.text)
                recent_games[wk].update({key: data})
                i += 1

    return recent_games


def get_career_stats(firstname: str, lastname: str, position: str) -> Dict:
    """
    Get Player's Career Stats from NFL.com
    :param firstname: Player's First Name
    :param lastname: Player's Last Name
    :return: Dict of career stats
    """

    url = "https://www.nfl.com/players/{}-{}/stats/".format(firstname, lastname)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    table = soup.find("table", {"summary": "Career Stats"})
    headers = [re.sub(r'\s+', '', header.text) for header in table.find_all("th")][1:]

    career_stats = {}

    tbody = table.find("tbody")
    for season in tbody.find_all("tr"):
        year = season.find("td", {"class": None}).text
        career_stats.update({year: {}})
        i = 0
        for col in season.find_all("td", {"class": not None}):
            key = headers[i]
            data = "0" if not col.text else re.sub(r'\s+', '', col.text)
            career_stats[year].update({key: data})
            i += 1

    return career_stats
