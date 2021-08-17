import requests
from bs4 import BeautifulSoup
from PIL import Image
from pathlib import Path
from datetime import date


def get_headshot(PlayerID, YahooPlayerID):

    # Checks to see if me have already saved the player's headshot, if not try to download.
    img_path = Path("/Users/everson/NFLCheatSheet/static/headshots/{}.png".format(PlayerID))

    if img_path.exists():
        return None

    url = "https://sports.yahoo.com/nfl/players/{}/".format(YahooPlayerID)
    html = requests.get(url)
    soup = BeautifulSoup(html.text, "html.parser")
    img = soup.find("img", {"class": "Pos(a) B(0) M(a) H(100%) T(10%) H(90%)! Start(-15%)"})

    if img:
        if 'default' in img:
            return None

        else:
            img = img['src'][102:]

            if img:
                image_data = requests.get(img, stream=True)
                #if image_data.ok:
                with img_path.open('wb') as image_file:
                    image = Image.open(image_data.raw)
                    image.save(image_file)
