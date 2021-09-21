import requests
from bs4 import BeautifulSoup


def is_completed(game_id):
    url = "https://www.espn.com/nfl/boxscore?gameId={}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    result = soup.find("span", {"class": "game-time status-detail"})
    if result:
        if result.text == "Final":
            return result.text
        
        if result.text == "Final/OT":
            return result.text

    return None


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


def get_game_stats(game_id):
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
