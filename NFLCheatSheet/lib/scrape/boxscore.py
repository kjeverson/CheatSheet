import requests
from bs4 import BeautifulSoup
import re
import json


def parse_table(tables, headers):

    stat_dict = {
        0: {},  # Away
        1: {}   # Home
    }

    for i in range(len(tables)):
        table = tables[i]
        body = table.find("tbody")

        rows = body.find_all("tr")
        for row in rows:
            if "TEAM" in row.text:
                continue
            if "No" in row.text and "Fumbles" in row.text:
                continue
            if "No" in row.text and "Interceptions" in row.text:
                continue
            stats = row.find_all("td")
            #espnIDTag = stats[0].find("a")
            #espnID = espnIDTag["data-player-uid"].split(":")[-1]
            name = stats[0].find("span").text
            stats = [stat.text for stat in row.find_all("td")][1:]

            stat_dict[i].update({name: {}})
            for header in range(len(headers)):
                stat_dict[i][name].update({headers[header]: stats[header]})

            if 'AVG' in headers:
                stat_dict[i][name].pop('AVG')

    return stat_dict


def get_game_stats(game_id):
    url = "https://www.espn.com/nfl/boxscore?gameId={}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    # Passing Scrape
    passing = soup.find("div", {"id": "gamepackage-passing"})
    away_passing = passing.find("div", {"class": "col column-one gamepackage-away-wrap"})
    home_passing = passing.find("div", {"class": "col column-two gamepackage-home-wrap"})

    tables = list()
    tables.append(away_passing.find("table"))
    tables.append(home_passing.find("table"))

    headers = ['passComps/passAtts', 'passYDs', 'AVG', 'passTDs', 'passINTs',
               'passSacks/passSackYDs', 'passRTG']
    pass_stats = parse_table(tables, headers)

    # Rushing Scrape
    rushing = soup.find("div", {"id": "gamepackage-rushing"})
    away_rushing = rushing.find("div", {"class": "col column-one gamepackage-away-wrap"})
    home_rushing = rushing.find("div", {"class": "col column-two gamepackage-home-wrap"})

    tables = list()
    tables.append(away_rushing.find("table"))
    tables.append(home_rushing.find("table"))

    headers = ['rushAtts', 'rushYDs', 'AVG', 'rushTDs', 'rushLng']
    rush_stats = parse_table(tables, headers)

    # Receiving Scrape
    receiving = soup.find("div", {"id": "gamepackage-receiving"})
    away_receiving = receiving.find("div", {"class": "col column-one gamepackage-away-wrap"})
    home_receiving = receiving.find("div", {"class": "col column-two gamepackage-home-wrap"})

    tables = list()
    tables.append(away_receiving.find("table"))
    tables.append(home_receiving.find("table"))

    headers = ['recs', 'recYDs', 'AVG', 'recTDs', 'recLng', 'recTGTS']
    rec_stats = parse_table(tables, headers)

    # Fumbles Scrape
    fumbles = soup.find("div", {"id": "gamepackage-fumbles"})
    away_fumbles = fumbles.find("div", {"class": "col column-one gamepackage-away-wrap"})
    home_fumbles = fumbles.find("div", {"class": "col column-two gamepackage-home-wrap"})

    tables = list()
    tables.append(away_fumbles.find("table"))
    tables.append(home_fumbles.find("table"))

    headers = ["fum", "fumLost", "fumRec"]
    fumble_stats = parse_table(tables, headers)

    # Defense Scrape
    defense = soup.find("div", {"id": "gamepackage-defensive"})
    away_defense = defense.find("div", {"class": "col column-one gamepackage-away-wrap"})
    home_defense = defense.find("div", {"class": "col column-two gamepackage-home-wrap"})

    tables = list()
    tables.append(away_defense.find("table"))
    tables.append(home_defense.find("table"))

    headers = ["totalTackles", "soloTackles", "sacks", "tacklesForLoss", "passDefensed",
               "qbHits", "defTDs"]
    defense_stats = parse_table(tables, headers)

    return pass_stats, rush_stats, rec_stats, fumble_stats, defense_stats


def is_completed(game_id):
    url = "https://www.espn.com/nfl/boxscore?gameId={}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    result = soup.find("span", {"class": "game-time status-detail"})
    if result:
        if result.text == "Final" or result.text == "Final/OT":
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

            data[0] = data[0]
            score_dict.update({data[0]: data[1:]})

    return score_dict


def get_headers(section):
    
    if section == 'passing':
        return ['passComps/passAtts', 'passYDs', 'AVG', 'passTDs', 'passINTs',
                'passSacks/passSackYDs', 'passRTG']
    elif section == 'rushing':
        return ['rushAtts', 'rushYDs', 'AVG', 'rushTDs', 'rushLng']

    elif section == 'receiving':
        return ['recs', 'recYDs', 'AVG', 'recTDs', 'recLng', 'recTGTS']

    elif section == 'fumbles':
        return ["fum", "fumLost", "fumRec"]

    elif section == 'defensive':
        return ["totalTackles", "soloTackles", "sacks", "tacklesForLoss", "passDefensed", "qbHits",
                "defTDs"]

    elif section == 'interceptions':
        return ["defINTs", "defINTYDs", "defINTTDs"]

    elif section == 'kickReturns':
        return ["krAtts", "krYDs", "krAVG", "krLng", "krTDs"]

    elif section == 'puntReturns':
        return ["prAtts", "prYDs", "prAVG", "prLng", "prTDs"]

    elif section == 'kicking':
        return ["fgMade/fgAtts", "fgPCT", "fgLng", "xpMade/xpAtts", "points"]

    elif section == 'punting':
        return ["punts", "puntYDs", "puntAVG", "puntTB", "puntIn20", "puntLng"]

    else:
        return []


def get_game_stats_api(game_id):
    url = "http://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={}".format(
        game_id)

    data = requests.get(url)
    data = data.json()
    data = data['boxscore']['players']

    stats_dict = {
        'passing': {
            0: {},
            1: {}
        },
        'rushing': {
            0: {},
            1: {}
        },
        'receiving': {
            0: {},
            1: {}
        },
        'fumbles': {
            0: {},
            1: {}
        },
        'defensive': {
            0: {},
            1: {}
        },
        'interceptions': {
            0: {},
            1: {}
        },
        'kickReturns': {
            0: {},
            1: {}
        },
        'puntReturns': {
            0: {},
            1: {}
        },
        'kicking': {
            0: {},
            1: {}
        },
        'punting': {
            0: {},
            1: {}
        },
    }

    for i in range(0, 2):
        stats = data[i]['statistics']
        for section in stats:
            section_name = section['name']
            players = section['athletes']
            headers = get_headers(section_name)
            if not headers:
                continue
            for player in players:
                name = player['athlete']['id']
                player_stats = player['stats']
                stats_dict[section_name][i].update({name: {}})
                for j in range(len(headers)):
                    stats_dict[section_name][i][name].update({headers[j]: player_stats[j]})

    return stats_dict
