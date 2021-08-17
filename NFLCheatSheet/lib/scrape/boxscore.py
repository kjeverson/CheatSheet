import requests
from bs4 import BeautifulSoup
import re


def parse_table(tables, headers):

    stat_dict = {}

    for table in tables:
        head = table.find("thead")
        body = table.find("tbody")

        rows = body.find_all("tr")
        for row in rows:
            if "TEAM" in row.text:
                continue
            stats = row.find_all("td")
            name = stats[0].find("span").text
            stats = [stat.text for stat in row.find_all("td")][1:]

            stat_dict.update({name: {}})
            for i in range(len(headers)):
                stat_dict[name].update({headers[i]: stats[i]})

    return stat_dict


def get_game_stats(game_id):
    url = "https://www.espn.com/nfl/boxscore?gameId={}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    # Passing Scrape
    passing = soup.find("div", {"id": "gamepackage-passing"})
    tables = passing.find_all("table")
    headers = ['passComps/passAtts', 'passYDs', 'AVG', 'passTDs', 'passINTs',
               'passSacks/passSackYDs', 'passRTG']
    pass_stats = parse_table(tables, headers)

    # Rushing Scrape
    rushing = soup.find("div", {"id": "gamepackage-rushing"})
    tables = rushing.find_all("table")
    headers = ['rushAtts', 'rushYDs', 'AVG', 'rushTDs', 'rushLng']
    rush_stats = parse_table(tables, headers)

    # Receiving Scrape
    receiving = soup.find("div", {"id": "gamepackage-receiving"})
    tables = receiving.find_all("table")
    headers = ['recs', 'recYDs', 'AVG', 'recTDs', 'recLng', 'recTGTS']
    rec_stats = parse_table(tables, headers)

    return pass_stats, rush_stats, rec_stats


def is_completed(game_id):
    url = "https://www.espn.com/nfl/boxscore?gameId={}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    result = soup.find("span", {"class": "game-time status-detail"})
    if result:
        if result.text == "Final":
            return True

    return False


def get_scores(game_id):
    url = "https://www.espn.com/nfl/boxscore?gameId={}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    score_dict = {}
    linescore = soup.find("table", {"id": "linescore"})
    if linescore:
        rows = linescore.find_all("tr")
        for row in rows:
            raw_data = row.find_all("td")
            data = [data.text for data in raw_data]
            if not data:
                continue

            data[0] = "WAS" if data[0] == "WSH" else data[0]
            score_dict.update({data[0]: data[1:]})

    return score_dict
