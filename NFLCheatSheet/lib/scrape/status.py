import requests
from bs4 import BeautifulSoup
from typing import Dict


status_url = "https://www.rotowire.com/football/player.php?id={}"


def player_status_from_id(id: str) -> Dict:
    """
    Get player status from Rotowire
    :param id: Player's rotowire ID
    :return: Status Dict
    """

    global status_url
    url = status_url.format(id)

    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')

    status = soup.find("div", {"class": "p-card__injury"})

    if status:

        status = status.text.split("\n")
        status = [note for note in status if note]

        if "Covid" in status[0]:
            status_short = "Out"
            injury = "Covid-19"
        elif "Sus" in status[0]:
            status_short = "SUS"
            injury = "Suspension"
        elif "Quest" in status[0]:
            status_short = "Q"
            injury = status[1].split()[-1]
        elif status[0] in ["PUP-P", "NFI-A", "NFI-R", "IR"]:
            status_short = "Out"
            injury = status[1].split()[-1]
        else:
            status_short = status[0]
            injury = status[1].split()[-1]

        status_dict = {
            "status": status_short,
            "designation": status[0],
            "injury": injury
        }

        return status_dict

    else:

        return {}


def get_injured_list():

    url = "https://www.cbssports.com/nfl/injuries/"
    html = requests.get(url)
    soup = BeautifulSoup(html.text, 'html.parser')
    tables = soup.find_all("table")

    injured = []

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            datas = row.find_all("td")
            if datas:
                d = [data.text.strip() for data in datas if data]
                # if d[1] not in ["QB", "RB", "WR", "TE"]:
                #    continue
                injured.append(d[0].split("\n")[-1])

    return injured