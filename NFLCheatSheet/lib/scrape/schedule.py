import requests
from bs4 import BeautifulSoup


def get_schedule():

    schedule = {}

    # 1-4
    preseason_url = "https://www.espn.com/nfl/schedule/_/week/{}/seasontype/1"
    # 1-18
    regular_url = "https://www.espn.com/nfl/schedule/_/week/{}/seasontype/2"

    # Populate Preseason
    matchups = []
    for i in range(1, 5):

        url = preseason_url.format(i)
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')

        tables = soup.find_all("table")
        for table in tables:
            body = table.find("tbody")
            if body:
                for row in body.find_all("tr"):
                    game_id = row.find_all("a")[4]['href'].split("/")[-1]

                    if "=" in game_id:
                        game_id = game_id.split("=")[-1]

                    date = [date["data-date"] for date in row.find_all("td")
                            if "data-date" in date.attrs]

                    if not date:
                        date = final_datetime_scrape(game_id)

                    date = date[-1] if date else "TBD"

                    d = [data.text for data in row.find_all("td")]
                    
                    home_team_key = d[1][-3:].split(" ")[-1]
                    away_team_key = d[0][-3:].split(" ")[-1]
                    #home_team_key = "WAS" if home_team_key == "WSH" else home_team_key
                    #away_team_key = "WAS" if away_team_key == "WSH" else away_team_key

                    matchups.append([game_id, i, date, home_team_key, away_team_key])

    schedule.update({"pre": matchups})

    # Populate Regular Season
    matchups = []
    for i in range(1, 19):

        url = regular_url.format(i)
        html = requests.get(url)
        soup = BeautifulSoup(html.text, 'html.parser')

        tables = soup.find_all("table")
        for table in tables:
            body = table.find("tbody")
            if body:
                for row in body.find_all("tr"):
                    game_id = row.find_all("a")[4]['href'].split("/")[-1]

                    if "=" in game_id:
                        game_id = game_id.split("=")[-1]

                    date = [date["data-date"] for date in row.find_all("td")
                            if "data-date" in date.attrs]

                    if not date:
                        date = final_datetime_scrape(game_id)

                    date = date[-1] if date else "TBD"

                    d = [data.text for data in row.find_all("td")]

                    home_team_key = d[1][-3:].split(" ")[-1]
                    away_team_key = d[0][-3:].split(" ")[-1]
                    #home_team_key = "WAS" if home_team_key == "WSH" else home_team_key
                    #away_team_key = "WAS" if away_team_key == "WSH" else away_team_key

                    matchups.append([game_id, i, date, home_team_key, away_team_key])

    schedule.update({"reg": matchups})

    return schedule


def final_datetime_scrape(game_id):

    url = "https://www.espn.com/nfl/game/_/gameId/{}".format(game_id)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    game_info = soup.find("article", {"class": "sub-module game-information"})
    date = game_info.find("div", {"class": "game-date-time"})
    date = date.find("span")
    date = date["data-date"]

    return [date]
