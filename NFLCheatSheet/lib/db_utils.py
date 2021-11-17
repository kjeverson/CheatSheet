# Database Utility functions
# To Do: Remove absolute file paths

import json
from pathlib import Path
from typing import Dict, List
import re
import zulu
import operator
import requests
import time
import csv

from NFLCheatSheet.lib.classes.team import Team
from NFLCheatSheet.lib.classes.player import Player, add_player, get_player, player_url
from NFLCheatSheet.lib.classes.transactions import Transactions
from NFLCheatSheet.lib.classes import stats
from NFLCheatSheet.lib.classes.game import Game
from NFLCheatSheet.lib.classes.depth_chart import DepthChart

from NFLCheatSheet.lib.fantasy.scoring import Scoring, get_score

from NFLCheatSheet.lib.scrape.boxscore import get_game_stats, get_scores
from NFLCheatSheet.lib.scrape import schedule, transactions


DVOA_PATH = Path("/Users/everson/NFLCheatSheet/data/DVOA")

team_conference = {
    "Bengals": "AFC", "Browns": "AFC", "Steelers": "AFC", "Ravens": "AFC",
    "Bills": "AFC", "Dolphins": "AFC", "Patriots": "AFC", "Jets": "AFC",
    "Titans": "AFC", "Colts": "AFC", "Texans": "AFC", "Jaguars": "AFC",
    "Broncos": "AFC", "Chargers": "AFC", "Raiders": "AFC", "Chiefs": "AFC",
    "Bears": "NFC", "Lions": "NFC", "Vikings": "NFC", "Packers": "NFC",
    "Cowboys": "NFC", "Giants": "NFC", "Eagles": "NFC", "Football Team": "NFC",
    "Falcons": "NFC", "Saints": "NFC", "Panthers": "NFC", "Buccaneers": "NFC",
    "Rams": "NFC", "49ers": "NFC", "Cardinals": "NFC", "Seahawks": "NFC"
}

team_division = {
    "Bengals": "North", "Browns": "North", "Steelers": "North", "Ravens": "North",
    "Bills": "East", "Dolphins": "East", "Patriots": "East", "Jets": "East",
    "Titans": "South", "Colts": "South", "Texans": "South", "Jaguars": "South",
    "Broncos": "West", "Chargers": "West", "Raiders": "West", "Chiefs": "West",
    "Bears": "North", "Lions": "North", "Vikings": "North", "Packers": "North",
    "Cowboys": "East", "Giants": "East", "Eagles": "East", "Football Team": "East",
    "Falcons": "South", "Saints": "South", "Panthers": "South", "Buccaneers": "South",
    "Rams": "West", "49ers": "West", "Cardinals": "West", "Seahawks": "West"
}


def get_all_team_data() -> List[Dict]:

    print("Getting Team Data...\r", end="")
    response = requests.get("https://sports.core.api.espn.com/v2/sports/"
                            "football/leagues/nfl/seasons/2021/teams/?limit=32")
    team_data = response.json()
    team_data = team_data['items']

    teams_data = []
    for team in team_data:
        teams_data.append(requests.get(team['$ref']).json())

    print("Getting Team Data...\x1b[32mCOMPLETE!\x1b[0m")
    return teams_data


def add_teams(database, teams: List[Dict]) -> None:

    print("Adding Teams to Database...\r", end="")
    for i in range(len(teams)):
        print("Adding Teams to Database...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(teams), ((i + 1) / len(teams)) * 100),
              end="")
        team = teams[i]

        try:
            name = team['name']
        except KeyError:
            name = team['nickname']

        if name == "Washington":
            name = 'Football Team'
            team_full = 'Washington Football Team'
        else:
            name = name
            team_full = team['displayName']

        database.session.add(Team(
            ID=team['id'],
            key=team['abbreviation'],
            location=team['location'],
            name=name,
            fullname=team_full,
            primary=team['color'],
            secondary=team['alternateColor'],
            stadium=team["venue"]["fullName"],
            stadium_city=team["venue"]["address"]["city"],
            stadium_state=team["venue"]["address"]["state"],
            conference=team_conference.get(name),
            division=team_division.get(name),
            wins=0,
            loses=0,
            ties=0,
            preseason_wins=0,
            preseason_loses=0,
            preseason_ties=0,
            preseason_games_played=0,
            games_played=0
        ))

        database.session.add(stats.TeamStats(
            team_id=team['id'],
            preseason=True
        ))

        database.session.add(stats.TeamStats(
            team_id=team['id'],
            preseason=False
        ))

        database.session.add(DepthChart(
            team_id=team['id']
        ))

    database.session.add(Team(
        ID=100,
        key="FA",
        location="",
        name="Free Agent",
        fullname="Free Agent",
        wins=0,
        loses=0,
        ties=0,
        preseason_wins=0,
        preseason_loses=0,
        preseason_ties=0,
        preseason_games_played=0
    ))

    database.session.add(stats.TeamStats(
        team_id=100,
        preseason=True
    ))

    database.session.add(stats.TeamStats(
        team_id=100,
        preseason=False
    ))

    print("Adding Teams to Database...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def filter_by_position(player_data: List[Dict], position: str = 'ALL') -> List[Dict]:
    """
    Filter player data by specific position (default is 'ALL') and remove any Free Agents.
    :param player_data: List of player_data dicts
    :param position: Position to get, supports 'ALL', 'OFF', 'DEF', 'SKILL', 'REC'. Default = 'ALL'
    :return:
    """

    players = []
    for i in range(len(player_data)):
        experience_string = player_data[i]['ExperienceString']
        if experience_string:
            year = re.search(r'\d+', experience_string)
            if year:
                experience = year.group(0)
            else:
                experience = '0'
        else:
            player_data[i]['ExperienceString'] = "Rookie"
            experience = "0"

        player_data[i]['Experience'] = experience

        if position == 'ALL':
            players = [player for player in player_data]

        elif position == 'SKILL':
            players = [player for player in player_data if player['PositionCategory']
                       in ['OFF', 'ST'] and player['Position']
                       not in ['OT', 'G', 'C', 'OL', 'P', 'LS']]

        elif position == 'OFF':
            players = [player for player in player_data if player['PositionCategory']
                       in ['OFF', 'ST'] and player['Position']]

        elif position == 'DEF':
            players = [player for player in player_data if player['PositionCategory']
                       in ['DEF']]

        elif position == 'REC':
            players = [player for player in player_data if player['Position']
                       in ['RB', 'WR', 'TE']]
        else:
            players = [player for player in player_data if player['Position'] == position]

    return players


def get_all_player_data(thread, position: str = "ALL") -> List:
    """
    Get all player data from json file.
    :param position: Position to get, supports 'ALL', 'OFF', 'DEF', 'SKILL', 'REC'. Default = 'ALL'
    :return: List of Player data in dictionaries
    """

    thread.progress = 0
    thread.total = 1
    print("Getting Player Data...\r", end="")

    url = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2021/teams/{}/athletes?limit=150"

    players = []
    teams = Team.query.filter(Team.ID != 100).all()
    for team in teams:
        data = requests.get(url.format(team.ID))
        data = data.json()
        for player in data['items']:
            players.append(player['$ref'])

    print("Getting Player Data...\x1b[32mCOMPLETE!\x1b[0m")
    thread.progress = 1
    time.sleep(5)
    return players


def get_headshots(db, thread):

    players = Player.query.all()

    thread.total = len(players)
    for i in range(len(players)):
        print("{}/{} - {:0.2f}%\r".format(i + 1, len(players), ((i + 1) / len(players)) * 100),
              end="")
        thread.progress = i+1
        player = players[i]
        if player.current_team.ID != 100:
            img_path = Path("/Users/everson/NFLCheatSheet/static/headshots/{}.png"
                            .format(player.ID))
            if not img_path.exists():
                player.get_headshot()

    print("")


def add_players(database, players: List, thread) -> None:
    """
    Add players to the database
    :param players: Player data list
    :param database: Database object
    :return:
    """

    thread.state = "Adding Players to Database"
    thread.total = len(players)
    rostered_ids = []
    print("Adding Players to Database..\r", end="")
    for i in range(len(players)):
        print("Adding Players to Database...{}/{} - {:0.2f}%\r"
              .format(i+1, len(players), ((i+1)/len(players))*100), end="")
        thread.progress = i+1

        player = players[i]
        player_data = requests.get(player).json()

        player_obj = get_player(player_data['id'])

        if not player_obj:
            rostered_ids.append(int(player_data['id']))
            add_player(database, player_data)

        else:
            rostered_ids.append(player_obj.ID)
            player_obj.update_info(player_data)

    players = Player.query.all()
    for player in players:
        if player.ID not in rostered_ids:
            player.team_id = 100

    print("Adding Players to Database...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def set_depth_charts(db, thread):

    teams = Team.query.filter(Team.ID != 100).all()
    thread.total = len(teams)
    thread.state = "Updating Depth Charts"
    print("Updating Depth Charts...\r", end="")
    for i in range(len(teams)):
        print("Updating Depth Charts...{}/{} - {:0.2f}%\r"
              .format(i+1, len(teams), ((i+1)/len(teams))*100), end="")
        thread.progress = i+1

        team = teams[i]
        team.set_depth_chart()

    print("Updating Depth Charts...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def add_default_scoring(database):
    print("Adding Default Scoring to Database...\r", end="")
    database.session.add(Scoring(
        ID=0,
        fractional=True,
        passYDs=25,
        passTDs=4,
        passINTs=-2,
        pass2PTs=2,
        passSacks=0,
        passAtts=0,
        passComps=0,
        passIncs=0,
        pass40TD=0,
        pass50TD=0,
        passOver300Yards=0,
        passOver400Yards=0,
        rushYDs=10,
        rushTDs=6,
        rush2PT=2,
        rushAtts=0,
        rush40TD=0,
        rush50TD=0,
        rushOver100Yards=0,
        rushOver200Yards=0,
        recs=1,
        recYDs=10,
        recTDs=6,
        rec2PT=2,
        rec40TD=0,
        rec50TD=0,
        recOver100Yards=0,
        recOver200Yards=0,
        fumLost=-2,
        fum=0,
        fumRecTD=0
    ))

    print("Adding Default Scoring to Database...\x1b[32mCOMPLETE!\x1b[0m")


def update_player_status(database, thread):

    print("Updating Player Statuses...\r", end="")

    players = Player.query.all()
    players = [player for player in players if player.current_team.ID != 100]

    thread.total = len(players)
    for i in range(len(players)):
        print("Updating Player Statuses...{}/{} - {:0.2f}%\r"
              .format(i+1, len(players), ((i+1)/len(players))*100), end="")
        thread.progress = i+1
        player = players[i]
        player.update_status()

    print("Updating Player Statuses...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def get_schedule(database):

    print("Getting Schedule Data...\r", end="")
    sched = schedule.get_schedule()
    print("Getting Schedule Data...\x1b[32mCOMPLETE!\x1b[0m\033[K")
    preseason = sched.get("pre")
    regseason = sched.get("reg")

    print("Adding Preseason Games to Database...\r", end="")
    for i in range(len(preseason)):

        print("Adding Preseason Games to Database...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(preseason), ((i + 1) / len(preseason)) * 100), end="")

        game = preseason[i]

        home_team = Team.query.filter_by(key=game[3]).first()
        away_team = Team.query.filter_by(key=game[4]).first()

        database.session.add(Game(
            ID=game[0],
            week=game[1],
            date=game[2],
            home_team_id=home_team.ID,
            away_team_id=away_team.ID,
            preseason=True,
            completed=False,
            scraped_stats=False,
        ))

    print("Adding Preseason Games to Database...\x1b[32mCOMPLETE!\x1b[0m\033[K")
    print("Adding Regular Season Games to Database...\r", end="")

    for i in range(len(regseason)):
        print("Adding Regular Season Games to Database...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(regseason), ((i + 1) / len(regseason)) * 100), end="")

        game = regseason[i]

        home_team = Team.query.filter_by(key=game[3]).first()
        away_team = Team.query.filter_by(key=game[4]).first()

        database.session.add(Game(
            ID=game[0],
            week=game[1],
            date=game[2],
            home_team_id=home_team.ID,
            away_team_id=away_team.ID,
            preseason=False,
            completed=False,
            scraped_stats=False
        ))

    print("Adding Regular Season Games to Database...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def update_schedule(db, thread):

    print("Updating Games...\r", end="")
    # Get all unfinished games
    games = Game.query.all()
    dt_now = zulu.now().datetime
    games = [game for game in games if game.get_time() < dt_now]
    games = [game for game in games if game.is_complete() and not game.scraped_stats]

    thread.progress = 0
    thread.total = len(games)
    if len(games) == 0:
        time.sleep(5)
    for i in range(len(games)):

        print("Updating Games...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(games), ((i + 1) / len(games)) * 100), end="")

        thread.progress = i+1
        game = games[i]

        if game.completed:
            scores = get_scores(game.ID)

            away_team_scores = scores[game.away_team.key]
            home_team_scores = scores[game.home_team.key]

            game.away_team_score = int(away_team_scores.pop())
            game.home_team_score = int(home_team_scores.pop())

            game.home_team_line_score = " ".join(home_team_scores)
            game.away_team_line_score = " ".join(away_team_scores)

            if game.away_team_score > game.home_team_score:
                game.winner = game.away_team.key
                if not game.preseason:
                    game.away_team.wins += 1
                    game.home_team.loses += 1
                    game.home_team.games_played += 1
                    game.away_team.games_played += 1
                else:
                    game.away_team.preseason_wins += 1
                    game.home_team.preseason_loses += 1
                    game.home_team.preseason_games_played += 1
                    game.away_team.preseason_games_played += 1

                if game.away_team.conference == game.home_team.conference and game.away_team.division == game.home_team.division:
                    game.away_team.divisionWins += 1
                    game.home_team.divisionLosses += 1

            elif game.home_team_score > game.away_team_score:
                game.winner = game.home_team.key
                if not game.preseason:
                    game.home_team.wins += 1
                    game.away_team.loses += 1
                    game.home_team.games_played += 1
                    game.away_team.games_played += 1
                else:
                    game.home_team.preseason_wins += 1
                    game.away_team.preseason_loses += 1
                    game.home_team.preseason_games_played += 1
                    game.away_team.preseason_games_played += 1

                if game.away_team.conference == game.home_team.conference and game.away_team.division == game.home_team.division:
                    game.home_team.divisionWins += 1
                    game.away_team.divisionLosses += 1
            else:
                game.winner = "Tie"
                if not game.preseason:
                    game.away_team.ties += 1
                    game.home_team.ties += 1
                    game.home_team.games_played += 1
                    game.away_team.games_played += 1
                else:
                    game.away_team.preseason_ties += 1
                    game.home_team.preseason_ties += 1
                    game.home_team.preseason_games_played += 1
                    game.away_team.preseason_games_played += 1

                if game.away_team.conference == game.home_team.conference and game.away_team.division == game.home_team.division:
                    game.away_team.divisionTies += 1
                    game.home_team.divisionTies += 1

    print("Updating Games...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def parse_week_stats(stats):
    week_stats = {}

    for key, stat in stats.items():
        if key == "team":
            continue
        elif "/" in key:
            key1, key2 = key.split("/")
            if "/" in stat:
                stat1, stat2 = stat.split("/")
            else:
                stat1, stat2 = stat.split("-")
            week_stats.update({key1: float(stat1), key2: float(stat2)})
        else:
            try:
                week_stats.update({key: float(stat)})
            except ValueError:
                week_stats.update({key: 0})
            
    return week_stats


def add_player_week_stats(db, thread):

    games = Game.query.filter_by(completed=True).filter_by(scraped_stats=False).all()

    thread.progress = 0
    if len(games) > 0:
        thread.total = len(games)
    else:
        thread.total = 1
    for i in range(len(games)):
        game = games[i]
        thread.progress = i+1

        game_stats = get_game_stats(game.ID)
        passing = game_stats.get('passing')
        rushing = game_stats.get('rushing')
        receiving = game_stats.get('receiving')
        fumbles = game_stats.get('fumbles')
        defense = game_stats.get('defensive')
        interceptions = game_stats.get('interceptions')
        kick_returns = game_stats.get('kickReturns')
        punt_returns = game_stats.get('puntReturns')
        kicking = game_stats.get('kicking')
        punting = game_stats.get('punting')

        players = []
        away_players = []
        home_players = []

        for j in range(0, 2):

            if j == 0:
                team_id = game.away_team.ID
            else:
                team_id = game.home_team.ID

            team = Team.query.get(team_id)

            player_names = set()

            for name in passing[j].keys():
                player_names.add(name)
            for name in rushing[j].keys():
                player_names.add(name)
            for name in receiving[j].keys():
                player_names.add(name)
            if fumbles.get(j):
                for name in fumbles[j].keys():
                    player_names.add(name)
            for name in defense[j].keys():
                player_names.add(name)
            for name in interceptions[j].keys():
                player_names.add(name)
            for name in kick_returns[j].keys():
                player_names.add(name)
            for name in punt_returns[j].keys():
                player_names.add(name)
            for name in kicking[j].keys():
                player_names.add(name)
            for name in punting[j].keys():
                player_names.add(name)

            for name in player_names:
                player = Player.query.get(name)

                if not player:
                    url = player_url.format(name)
                    player_data = requests.get(url).json()
                    if player_data['fullName'] == ' Team':
                        print(name)
                        continue
                    add_player(db, player_data)
                    player = get_player(player_data['id'])

                players.append(player)

                if j == 0:
                    away_players.append(player)
                else:
                    home_players.append(player)

                week_stats = {}

                pass_stats = passing[j].get(name)
                if pass_stats:
                    week_stats.update({"passer": True})
                    week_stats.update(parse_week_stats(pass_stats))
                else:
                    week_stats.update({"passer": False})

                rush_stats = rushing[j].get(name)
                if rush_stats:
                    week_stats.update({"rusher": True})
                    week_stats.update(parse_week_stats(rush_stats))
                else:
                    week_stats.update({"rusher": False})

                rec_stats = receiving[j].get(name)
                if rec_stats:
                    week_stats.update({"receiver": True})
                    week_stats.update(parse_week_stats(rec_stats))
                else:
                    week_stats.update({"receiver": False})

                fum_stats = fumbles[j].get(name)
                if fum_stats:
                    week_stats.update(parse_week_stats(fum_stats))

                def_stats = defense[j].get(name)
                if def_stats:
                    week_stats.update({"defender": True})
                    week_stats.update(parse_week_stats(def_stats))
                else:
                    week_stats.update({"defender": False})

                int_stats = interceptions[j].get(name)
                if int_stats:
                    week_stats.update(parse_week_stats(int_stats))

                kr_stats = kick_returns[j].get(name)
                if kr_stats:
                    week_stats.update(parse_week_stats(kr_stats))
                    
                pr_stats = punt_returns[j].get(name)
                if pr_stats:
                    week_stats.update(parse_week_stats(pr_stats))
                    
                kicking_stats = kicking[j].get(name)
                if kicking_stats:
                    week_stats.update(parse_week_stats(kicking_stats))
                    
                punting_stats = punting[j].get(name)
                if punting_stats:
                    week_stats.update(parse_week_stats(punting_stats))

                db.session.add(stats.WeeklyStats(
                    player_id=int(player.ID),
                    game_id=int(game.ID),
                    week=int(game.week),
                    team_id=team.ID,
                    preseason=game.preseason,
                    counted=False,
                    passer=week_stats["passer"],
                    passComps=week_stats["passComps"] if week_stats.get("passComps") else 0,
                    passAtts=week_stats["passAtts"] if week_stats.get("passAtts") else 0,
                    passYDs=week_stats["passYDs"] if week_stats.get("passYDs") else 0,
                    passAVG=week_stats["passYDs"] / week_stats["passComps"] if week_stats.get("passComps") else 0,
                    passTDs=week_stats["passTDs"] if week_stats.get("passTDs") else 0,
                    passINTs=week_stats["passINTs"] if week_stats.get("passINTs") else 0,
                    passSacks=week_stats["passSacks"] if week_stats.get("passSacks") else 0,
                    passSackYDs=week_stats["passSackYDs"] if week_stats.get("passSackYDs") else 0,
                    passRTG=week_stats["passRTG"] if week_stats.get("passRTG") else 0,
                    rusher=week_stats["rusher"],
                    rushAtts=week_stats["rushAtts"] if week_stats.get("rushAtts") else 0,
                    rushYDs=week_stats["rushYDs"] if week_stats.get("rushYDs") else 0,
                    rushAVG=week_stats["rushYDs"] / week_stats["rushAtts"] if week_stats.get("rushAtts") else 0,
                    rushTDs=week_stats["rushTDs"] if week_stats.get("rushTDs") else 0,
                    rushLng=week_stats["rushLng"] if week_stats.get("rushLng") else 0,
                    receiver=week_stats["receiver"],
                    recs=week_stats["recs"] if week_stats.get("recs") else 0,
                    recYDs=week_stats["recYDs"] if week_stats.get("recYDs") else 0,
                    recAVG=week_stats["recYDs"] / week_stats["recs"] if week_stats.get("recs") else 0,
                    recTDs=week_stats["recTDs"] if week_stats.get("recTDs") else 0,
                    recLng=week_stats["recLng"] if week_stats.get("recLng") else 0,
                    recTGTS=week_stats["recTGTS"] if week_stats.get("recTGTS") else 0,
                    fumLost=week_stats["fumLost"] if week_stats.get("fumLost") else 0,
                    fum=week_stats["fum"] if week_stats.get("fum") else 0,
                    fumRec=week_stats["fumRec"] if week_stats.get("fumRec") else 0,
                    defender=week_stats["defender"],
                    totalTackles=week_stats["totalTackles"] if week_stats.get("totalTackles") else 0,
                    soloTackles=week_stats["soloTackles"] if week_stats.get("soloTackles") else 0,
                    sacks=week_stats["sacks"] if week_stats.get("sacks") else 0,
                    tacklesForLoss=week_stats["tacklesForLoss"] if week_stats.get("tacklesForLoss") else 0,
                    passDefensed=week_stats["passDefensed"] if week_stats.get("passDefensed") else 0,
                    qbHits=week_stats["qbHits"] if week_stats.get("qbHits") else 0,
                    defTDs=week_stats["defTDs"] if week_stats.get("defTDs") else 0,
                    defINTs=week_stats["defINTs"] if week_stats.get("defINTs") else 0,
                    defINTYDs=week_stats["defINTYDs"] if week_stats.get("defINTYDs") else 0,
                    defINTTDs=week_stats["defINTTDs"] if week_stats.get("defINTTDs") else 0,
                    krAtts=week_stats["krAtts"] if week_stats.get("krAtts") else 0,
                    krYDs=week_stats["krYDs"] if week_stats.get("krYDs") else 0, 
                    krAVG=week_stats["krAVG"] if week_stats.get("krAVG") else 0, 
                    krLng=week_stats["krLng"] if week_stats.get("krLng") else 0,
                    krTDs=week_stats["krTDs"] if week_stats.get("krTDs") else 0, 
                    prAtts=week_stats["prAtts"] if week_stats.get("prAtts") else 0, 
                    prYDs=week_stats["prYDs"] if week_stats.get("prYDs") else 0, 
                    prAVG=week_stats["prAVG"] if week_stats.get("prAVG") else 0, 
                    prLng=week_stats["prLng"] if week_stats.get("prLng") else 0, 
                    prTDs=week_stats["prTDs"] if week_stats.get("prTDs") else 0, 
                    fgMade=week_stats["fgMade"] if week_stats.get("fgMade") else 0, 
                    fgAtts=week_stats["fgAtts"] if week_stats.get("fgAtts") else 0, 
                    fgPCT=week_stats["fgPCT"] if week_stats.get("fgPCT") else 0, 
                    fgLng=week_stats["fgLng"] if week_stats.get("fgLng") else 0, 
                    xpMade=week_stats["xpMade"] if week_stats.get("xpMade") else 0, 
                    xpAtts=week_stats["xpAtts"] if week_stats.get("xpAtts") else 0, 
                    points=week_stats["points"] if week_stats.get("points") else 0, 
                    punts=week_stats["punts"] if week_stats.get("punts") else 0,
                    puntYDs=week_stats["puntYDs"] if week_stats.get("puntYDs") else 0,
                    puntAVG=week_stats["puntAVG"] if week_stats.get("puntAVG") else 0,
                    puntTB=week_stats["puntTB"] if week_stats.get("puntTB") else 0,
                    puntIn20=week_stats["puntIn20"] if week_stats.get("puntIn20") else 0,
                    puntLng=week_stats["puntLng"] if week_stats.get("puntLng") else 0,
                    FPs=0,
                ))

        pass_leader_id, rush_leader_id, rec_leader_id = stats.get_stats_leaders(
            players, game.preseason, game.week)

        game.passingLeader_id = pass_leader_id
        game.rushingLeader_id = rush_leader_id
        game.receivingLeader_id = rec_leader_id

        pass_leader_id, rush_leader_id, rec_leader_id = stats.get_stats_leaders(
            away_players, game.preseason, game.week)

        game.awayPassingLeader_id = pass_leader_id
        game.awayRushingLeader_id = rush_leader_id
        game.awayReceivingLeader_id = rec_leader_id

        pass_leader_id, rush_leader_id, rec_leader_id = stats.get_stats_leaders(
            home_players, game.preseason, game.week)

        game.homePassingLeader_id = pass_leader_id
        game.homeRushingLeader_id = rush_leader_id
        game.homeReceivingLeader_id = rec_leader_id

        game.scraped_stats = True

        thread.progress = 1

        if len(games) == 0:
            time.sleep(5)


def update_player_season_stats(db, thread):

    players = Player.query.all()

    thread.progress = 0
    thread.total = len(players)
    print("Update Season Stats...\r", end="")
    for i in range(len(players)):

        player = players[i]
        thread.progress = i+1
        print("Update Season Stats...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(players), ((i + 1) / len(players)) * 100),end="")

        preseason_week_stats = player.get_weekly_stats_list(preseason=True)
        ps = player.get_season_stats(preseason=True)
        ps.gamesPlayed = len(preseason_week_stats)
        for ws in preseason_week_stats:
            if ws.counted:
                continue
            ps.passComps = ps.passComps + int(ws.passComps) if ws.passComps else ps.passComps
            ps.passAtts = ps.passAtts + int(ws.passAtts) if ws.passAtts else ps.passAtts
            ps.passYDs = ps.passYDs + int(ws.passYDs) if ws.passYDs else ps.passYDs
            ps.passAVG = ps.passYDs / ps.passComps if ps.passComps else 0
            ps.passYDsPerGame = ps.passYDs / len(preseason_week_stats) if preseason_week_stats else 0
            ps.passTDs = ps.passTDs + int(ws.passTDs) if ws.passTDs else ps.passTDs
            ps.passINTs = ps.passINTs + int(ws.passINTs) if ws.passINTs else ps.passINTs
            ps.passSacks = ps.passSacks + int(ws.passSacks) if ws.passSacks else ps.passSacks
            ps.passSackYDs = ps.passSackYDs + int(ws.passSackYDs) if ws.passSackYDs else ps.passSackYDs
            if ws.passer:
                ps.passRTG = stats.get_passer_rating(ps.passAtts, ps.passComps, ps.passYDs, ps.passTDs, ps.passINTs)

            ps.rushAtts = ps.rushAtts + int(ws.rushAtts) if ws.rushAtts else ps.rushAtts
            ps.rushYDs = ps.rushYDs + int(ws.rushYDs) if ws.rushYDs else ps.rushYDs
            ps.rushAVG = ps.rushYDs / ps.rushAtts if ps.rushAtts else 0
            ps.rushYDsPerGame = ps.rushYDs / len(preseason_week_stats) if preseason_week_stats else 0
            ps.rushTDs = ps.rushTDs + int(ws.rushTDs) if ws.rushTDs else ps.rushTDs
            if ws.rushLng and int(ws.rushLng) > ps.rushLng:
                ps.rushLng = int(ws.rushLng)

            ps.recs = ps.recs + int(ws.recs) if ws.recs else ps.recs
            ps.recYDs = ps.recYDs + int(ws.recYDs) if ws.recYDs else ps.recYDs
            ps.recAVG = ps.recYDs / ps.recs if ps.recs else 0
            ps.recYDsPerGame = ps.recYDs / len(preseason_week_stats) if preseason_week_stats else 0
            ps.recTDs = ps.recTDs + int(ws.recTDs) if ws.recTDs else ps.recTDs
            if ws.recLng and int(ws.recLng) > ps.recLng:
                ps.recLng = int(ws.recLng)
            ps.recTGTS = ps.recTGTS + int(ws.recTGTS) if ws.recTGTS else ps.recTGTS

            ps.fumLost = ps.fumLost + int(ws.fumLost) if ws.fumLost else ps.fumLost
            ps.fum = ps.fum + int(ws.fum) if ws.fum else ps.fum
            ps.fumRec = ps.fumRec + int(ws.fumRec) if ws.fumRec else ps.fumRec

            ps.totalTackles = ps.totalTackles + int(ws.totalTackles) if ws.totalTackles else ps.totalTackles
            ps.soloTackles = ps.soloTackles + int(ws.soloTackles) if ws.soloTackles else ps.soloTackles
            ps.sacks = ps.sacks + int(ws.sacks) if ws.sacks else ps.sacks
            ps.tacklesForLoss = ps.tacklesForLoss + int(ws.tacklesForLoss) if ws.tacklesForLoss else ps.tacklesForLoss
            ps.passDefensed = ps.passDefensed + int(ws.passDefensed) if ws.passDefensed else ps.passDefensed
            ps.qbHits = ps.qbHits + int(ws.qbHits) if ws.qbHits else ps.qbHits
            ps.defTDs = ps.defTDs + int(ws.defTDs) if ws.defTDs else ps.defTDs
            ps.defINTs = ps.defINTs + int(ws.defINTs) if ws.defINTs else ps.defINTs
            ps.defINTYDs = ps.defINTYDs + int(ws.defINTYDs) if ws.defINTYDs else ps.defINTYDs
            ps.defINTTDs = ps.defINTTDs + int(ws.defINTTDs) if ws.defINTTDs else ps.defINTTDs

            ps.krAtts = ps.krAtts + int(ws.krAtts) if ws.krAtts else ps.krAtts
            ps.krYDs = ps.krYDs + int(ws.krYDs) if ws.krYDs else ps.krYDs
            ps.krAVG = ps.krYDs / ps.krAtts if ps.krAtts else 0
            if ws.krLng and int(ws.krLng) > ps.krLng:
                ps.krLng = ws.krLng
            ps.krTDs = ps.krTDs + int(ws.krTDs) if ws.krTDs else ps.krTDs

            ps.prAtts = ps.prAtts + int(ws.prAtts) if ws.prAtts else ps.prAtts
            ps.prYDs = ps.prYDs + int(ws.prYDs) if ws.prYDs else ps.prYDs
            ps.prAVG = ps.prYDs / ps.prAtts if ps.prAtts else 0
            if ws.prLng and int(ws.prLng) > ps.prLng:
                ps.prLng = ws.prLng
            ps.prTDs = ps.prTDs + int(ws.prTDs) if ws.prTDs else ps.prTDs

            ps.fgMade = ps.fgMade + int(ws.fgMade) if ws.fgMade else ps.fgMade
            ps.fgAtts = ps.fgAtts + int(ws.fgAtts) if ws.fgAtts else ps.fgAtts
            ps.fgPCT = ps.fgMade / ps.fgAtts if ps.fgAtts else 0
            if ws.fgLng and int(ws.fgLng) > ps.fgLng:
                ps.fgLng = ws.fgLng
            ps.xpMade = ps.xpMade + int(ws.xpMade) if ws.xpMade else ps.xpMade
            ps.xpAtts = ps.xpAtts + int(ws.xpAtts) if ws.xpAtts else ps.xpAtts
            ps.points = ps.points + int(ws.points) if ws.points else ps.points

            ps.punts = ps.punts + int(ws.punts) if ws.punts else ps.punts
            ps.puntYDs = ps.puntYDs + int(ws.puntYDs) if ws.puntYDs else ps.puntYDs
            ps.puntAVG = ps.puntYDs / ps.punts if ps.punts else 0
            ps.puntTB = ps.puntTB + int(ws.puntTB) if ws.puntTB else ps.puntTB
            ps.puntIn20 = ps.puntIn20 + int(ws.puntIn20) if ws.puntIn20 else ps.puntIn20
            if ws.puntLng and int(ws.puntLng) > ps.puntLng:
                ps.puntLng = ws.puntLng

            ps.FPs = ws.FPs if not ps.FPs else ps.FPs + ws.FPs

        season_week_stats = player.get_weekly_stats_list(preseason=False)
        ss = player.get_season_stats(preseason=False)
        ss.gamesPlayed = len(season_week_stats)
        for ws in season_week_stats:
            if ws.counted:
                continue
            ss.passComps = ss.passComps + int(ws.passComps) if ws.passComps else ss.passComps
            ss.passAtts = ss.passAtts + int(ws.passAtts) if ws.passAtts else ss.passAtts
            ss.passYDs = ss.passYDs + int(ws.passYDs) if ws.passYDs else ss.passYDs
            ss.passAVG = ss.passYDs / ss.passComps if ss.passComps else 0
            ss.passYDsPerGame = ss.passYDs / len(season_week_stats) if season_week_stats else 0
            ss.passTDs = ss.passTDs + int(ws.passTDs) if ws.passTDs else ss.passTDs
            ss.passINTs = ss.passINTs + int(ws.passINTs) if ws.passINTs else ss.passINTs
            ss.passSacks = ss.passSacks + int(ws.passSacks) if ws.passSacks else ss.passSacks
            ss.passSackYDs = ss.passSackYDs + int(ws.passSackYDs) if ws.passSackYDs else ss.passSackYDs
            if ws.passer:
                ss.passRTG = stats.get_passer_rating(ss.passAtts, ss.passComps, ss.passYDs, ss.passTDs, ss.passINTs)

            ss.rushAtts = ss.rushAtts + int(ws.rushAtts) if ws.rushAtts else ss.rushAtts
            ss.rushYDs = ss.rushYDs + int(ws.rushYDs) if ws.rushYDs else ss.rushYDs
            ss.rushAVG = ss.rushYDs / ss.rushAtts if ss.rushAtts else 0
            ss.rushYDsPerGame = ss.rushYDs / len(season_week_stats) if season_week_stats else 0
            ss.rushTDs = ss.rushTDs + int(ws.rushTDs) if ws.rushTDs else ss.rushTDs
            if ws.rushLng and int(ws.rushLng) > ss.rushLng:
                ss.rushLng = int(ws.rushLng)

            ss.recs = ss.recs + int(ws.recs) if ws.recs else ss.recs
            ss.recYDs = ss.recYDs + int(ws.recYDs) if ws.recYDs else ss.recYDs
            ss.recAVG = ss.recYDs / ss.recs if ss.recs else 0
            ss.recYDsPerGame = ss.recYDs / len(season_week_stats) if season_week_stats else 0
            ss.recTDs = ss.recTDs + int(ws.recTDs) if ws.recTDs else ss.recTDs
            if ws.recLng and int(ws.recLng) > ss.recLng:
                ss.recLng = int(ws.recLng)
            ss.recTGTS = ss.recTGTS + int(ws.recTGTS) if ws.recTGTS else ss.recTGTS

            ss.fumLost = ss.fumLost + int(ws.fumLost) if ws.fumLost else ss.fumLost
            ss.fum = ss.fum + int(ws.fum) if ws.fum else ss.fum
            ss.fumRec = ss.fumRec + int(ws.fumRec) if ws.fumRec else ss.fumRec

            ss.totalTackles = ss.totalTackles + int(
                ws.totalTackles) if ws.totalTackles else ss.totalTackles
            ss.soloTackles = ss.soloTackles + int(
                ws.soloTackles) if ws.soloTackles else ss.soloTackles
            ss.sacks = ss.sacks + int(ws.sacks) if ws.sacks else ss.sacks
            ss.tacklesForLoss = ss.tacklesForLoss + int(
                ws.tacklesForLoss) if ws.tacklesForLoss else ss.tacklesForLoss
            ss.passDefensed = ss.passDefensed + int(
                ws.passDefensed) if ws.passDefensed else ss.passDefensed
            ss.qbHits = ss.qbHits + int(ws.qbHits) if ws.qbHits else ss.qbHits
            ss.defTDs = ss.defTDs + int(ws.defTDs) if ws.defTDs else ss.defTDs
            ss.defINTs = ss.defINTs + int(ws.defINTs) if ws.defINTs else ss.defINTs
            ss.defINTYDs = ss.defINTYDs + int(ws.defINTYDs) if ws.defINTYDs else ss.defINTYDs
            ss.defINTTDs = ss.defINTTDs + int(ws.defINTTDs) if ws.defINTTDs else ss.defINTTDs

            ss.krAtts = ss.krAtts + int(ws.krAtts) if ws.krAtts else ss.krAtts
            ss.krYDs = ss.krYDs + int(ws.krYDs) if ws.krYDs else ss.krYDs
            ss.krAVG = ss.krYDs / ss.krAtts if ss.krAtts else 0
            if ws.krLng and int(ws.krLng) > ss.krLng:
                ss.krLng = ws.krLng
            ss.krTDs = ss.krTDs + int(ws.krTDs) if ws.krTDs else ss.krTDs

            ss.prAtts = ss.prAtts + int(ws.prAtts) if ws.prAtts else ss.prAtts
            ss.prYDs = ss.prYDs + int(ws.prYDs) if ws.prYDs else ss.prYDs
            ss.prAVG = ss.prYDs / ss.prAtts if ss.prAtts else 0
            if ws.prLng and int(ws.prLng) > ss.prLng:
                ss.prLng = ws.prLng
            ss.prTDs = ss.prTDs + int(ws.prTDs) if ws.prTDs else ss.prTDs

            ss.fgMade = ss.fgMade + int(ws.fgMade) if ws.fgMade else ss.fgMade
            ss.fgAtts = ss.fgAtts + int(ws.fgAtts) if ws.fgAtts else ss.fgAtts
            ss.fgPCT = ss.fgMade / ss.fgAtts if ss.fgAtts else 0
            if ws.fgLng and int(ws.fgLng) > ss.fgLng:
                ss.fgLng = ws.fgLng
            ss.xpMade = ss.xpMade + int(ws.xpMade) if ws.xpMade else ss.xpMade
            ss.xpAtts = ss.xpAtts + int(ws.xpAtts) if ws.xpAtts else ss.xpAtts
            ss.points = ss.points + int(ws.points) if ws.points else ss.points

            ss.punts = ss.punts + int(ws.punts) if ws.punts else ss.punts
            ss.puntYDs = ss.puntYDs + int(ws.puntYDs) if ws.puntYDs else ss.puntYDs
            ss.puntAVG = ss.puntYDs / ss.punts if ss.punts else 0
            ss.puntTB = ss.puntTB + int(ws.puntTB) if ws.puntTB else ss.puntTB
            ss.puntIn20 = ss.puntIn20 + int(ws.puntIn20) if ws.puntIn20 else ss.puntIn20
            if ws.puntLng and int(ws.puntLng) > ss.puntLng:
                ss.puntLng = ws.puntLng

            ss.FPs = ws.FPs if not ss.FPs else ss.FPs + ws.FPs

    print("Update Season Stats...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def update_team_stats(db, thread, preseason=False):

    teams = Team.query.all()

    thread.progress = 0
    thread.total = len(teams)
    for i in range(len(teams)):
        thread.progress = i+1

        team = teams[i]

        if team.ID == 100:
            continue

        team_stats = team.get_team_stats(preseason=preseason)

        if preseason:
            if not team.preseason_games_played:
                continue
        else:
            if not team.games_played:
                continue
        pass_leader_id, rush_leader_id, rec_leader_id = stats.get_stats_leaders(team.players, preseason=preseason)

        team_stats.passingLeader_id = pass_leader_id
        team_stats.rushingLeader_id = rush_leader_id
        team_stats.receivingLeader_id = rec_leader_id

        week_stats = team.get_week_stats(preseason=preseason)

        for week_stat in week_stats:

            if week_stat.counted:
                continue

            team_stats.passComps += week_stat.passComps
            team_stats.passAtts += week_stat.passAtts 
            team_stats.passYDs += week_stat.passYDs
            team_stats.passTDs += week_stat.passTDs
            team_stats.passINTs += week_stat.passINTs
            team_stats.passSacks += week_stat.passSacks
            team_stats.passSackYDs += week_stat.passSackYDs

            team_stats.rushAtts += week_stat.rushAtts
            team_stats.rushYDs += week_stat.rushYDs
            team_stats.rushTDs += week_stat.rushTDs

            team_stats.recs += week_stat.recs
            team_stats.recYDs += week_stat.recYDs
            team_stats.recTDs += week_stat.recTDs
            team_stats.recTGTS += week_stat.recTGTS

            week_stat.counted = True

        if team_stats.passComps:
            team_stats.passAVG = team_stats.passYDs / team_stats.passComps
        if team_stats.rushAtts:
            team_stats.rushAVG = team_stats.rushYDs / team_stats.rushAtts
        if team_stats.recs:
            team_stats.recAVG = team_stats.recYDs / team_stats.recs

        if team.games_played:
            team_stats.passYDsPerGame = team_stats.passYDs / team.games_played
            team_stats.rushYDsPerGame = team_stats.rushYDs / team.games_played

        team_stats.totalYards = team_stats.passYDs + team_stats.rushYDs

        team_stats.pointsFor = 0
        team_stats.pointsAgainst = 0

        for game in team.get_games(preseason=False, completed=True, home=True):
            team_stats.pointsFor += game.home_team_score
            team_stats.pointsAgainst += game.away_team_score
        for game in team.get_games(preseason=False, completed=True, away=True):
            team_stats.pointsFor += game.away_team_score
            team_stats.pointsAgainst += game.home_team_score

        if team.games_played:
            team_stats.PPG = team_stats.pointsFor / team.games_played
            team_stats.PAPG = team_stats.pointsAgainst / team.games_played


def update_fantasy_points(db, thread):

    print("Calculating Fantasy Points...\r", end="")
    scoring = Scoring.query.first()

    players = Player.query.all()
    thread.progress = 0
    thread.total = len(players)
    for i in range(len(players)):
        print("Calculating Fantasy Points...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(players), ((i + 1) / len(players)) * 100), end="")
        player = players[i]
        thread.progress = i+1
        week_stats = player.weekly_stats
        if not week_stats:
            continue
        else:
            ss = player.get_season_stats(preseason=False)
            ps = player.get_season_stats(preseason=True)
            ps.FPs = 0
            ss.FPs = 0
            for week in week_stats:
                week.FPs = get_score(scoring, week)
                if week.preseason:
                    ps.FPs += week.FPs
                else:
                    ss.FPs += week.FPs

    print("Calculating Fantasy Points...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def get_rank(stats, attribute, reverse=True):

    count = 1
    current_rank = 1
    next_rank = 1
    rank_list = []
    for i in range(len(stats)):
        if reverse:
            try:
                if float(getattr(stats[i], attribute)) > float(getattr(stats[i+1], attribute)):
                    count = 1
                    current_rank = next_rank
                    rank_list.append(current_rank)
                    next_rank = next_rank + 1
                else:
                    count += 1
                    next_rank += 1
                    rank_list.append(current_rank)

            except IndexError as err:
                rank_list.append(next_rank)
        else:
            try:
                if float(getattr(stats[i], attribute)) < float(getattr(stats[i + 1], attribute)):
                    count = 1
                    current_rank = next_rank
                    rank_list.append(current_rank)
                    next_rank = next_rank + 1
                else:
                    count += 1
                    next_rank += 1
                    rank_list.append(current_rank)

            except IndexError as err:
                rank_list.append(next_rank)

    return rank_list


def update_rankings(db, thread, preseason):

    thread.progress = 0

    teams = Team.query.filter(Team.ID != 100).all()
    s = stats.TeamStats.query.filter(stats.TeamStats.team_id != 100).filter_by(preseason=preseason).all()
    passYDsPerGame = sorted(s, key=operator.attrgetter("passYDsPerGame"), reverse=True)
    passYDsPerGameRank = get_rank(passYDsPerGame, "passYDsPerGame")

    rushYDsPerGame = sorted(s, key=operator.attrgetter("rushYDsPerGame"), reverse=True)
    rushYDsPerGameRank = get_rank(rushYDsPerGame, "rushYDsPerGame")

    passYDs = sorted(s, key=operator.attrgetter("passYDs"), reverse=True)
    passYDsRank = get_rank(passYDs, "passYDs")

    rushYDs = sorted(s, key=operator.attrgetter("rushYDs"), reverse=True)
    rushYDsRank = get_rank(rushYDs, "rushYDs")

    PPG = sorted(s, key=operator.attrgetter("PPG"), reverse=True)
    PPGRank = get_rank(PPG, "PPG")

    PAPG = sorted(s, key=operator.attrgetter("PAPG"))
    PAPGRank = get_rank(PAPG, "PAPG", reverse=False)

    thread.total = len(teams)
    for i in range(len(teams)):
        thread.progress = i+1
        team = teams[i]
        s = team.get_team_stats(preseason=preseason)
        s.passYDsPerGameRank = passYDsPerGameRank[passYDsPerGame.index(s)]
        s.rushYDsPerGameRank = rushYDsPerGameRank[rushYDsPerGame.index(s)]
        s.passYDsRank = passYDsRank[passYDs.index(s)]
        s.rushYDsRank = rushYDsRank[rushYDs.index(s)]
        s.PPGRank = PPGRank[PPG.index(s)]
        s.PAPGRank = PAPGRank[PAPG.index(s)]


def read_dvoa_file(file):

    dvoa_dict = {}
    with file.open() as dvoa_file:
        reader = csv.DictReader(dvoa_file)
        for row in reader:
            if row['Team'] == 'WAS':
                row['Team'] = 'WSH'
            dvoa_dict.update({row['Team']: row})
    return dvoa_dict


def update_dvoa_rankings():

    path = DVOA_PATH / "DVOA.csv"
    dvoa_dict = read_dvoa_file(path)

    for team in dvoa_dict.keys():
        team_obj = Team.query.filter(Team.key == team).first()
        team_stats = team_obj.get_team_stats(preseason=False)

        team_stats.DVOA = int(dvoa_dict[team]['Total DVOA Rank'])
        team_stats.OFF = int(dvoa_dict[team]['Offense DVOA Rank'])
        team_stats.DEF = int(dvoa_dict[team]['Defense DVOA Rank'])
        team_stats.ST = int(dvoa_dict[team]['Special Teams DVOA Rank'])

    path = DVOA_PATH / "OFF.csv"
    dvoa_dict = read_dvoa_file(path)

    for team in dvoa_dict.keys():
        team_obj = Team.query.filter(Team.key == team).first()
        team_stats = team_obj.get_team_stats(preseason=False)

        team_stats.OFFPASS = int(dvoa_dict[team]['Pass DVOA Rank'])
        team_stats.OFFRUSH = int(dvoa_dict[team]['Rush DVOA Rank'])

    path = DVOA_PATH / "DEF.csv"
    dvoa_dict = read_dvoa_file(path)

    for team in dvoa_dict.keys():
        team_obj = Team.query.filter(Team.key == team).first()
        team_stats = team_obj.get_team_stats(preseason=False)

        team_stats.DEFPASS = int(dvoa_dict[team]['Pass DVOA Rank'])
        team_stats.DEFRUSH = int(dvoa_dict[team]['Rush DVOA Rank'])


def get_team_transactions(db, thread):

    thread.progress = 0

    Transactions.__table__.drop(db.engine)
    Transactions.__table__.create(db.engine)

    teams = Team.query.filter(Team.ID != 100).all()
    thread.total = len(teams)
    for i in range(len(teams)):
        thread.progress = i+1
        team = teams[i]
        t = transactions.get_team_transactions(team.key)
        for transaction in t:
            db.session.add(Transactions(
                team_id=team.ID,
                date=transaction[0],
                transaction=transaction[1]
            ))


def build_db(db, thread, preseason):
    db.create_all()

    teams = get_all_team_data()
    add_teams(db, teams)

    players = get_all_player_data(thread)
    add_players(db, players, thread)
    update_player_status(db, thread)

    add_default_scoring(db)

    get_schedule(db)
    update_schedule(db, thread)

    add_player_week_stats(db, thread)
    update_fantasy_points(db, thread)
    update_player_season_stats(db, thread)

    update_team_stats(db, thread, preseason)
    update_rankings(db, thread, preseason)

    teams = Team.query.filter(Team.ID != 100).all()
    for team in teams:
        team.bye = team.get_bye()
        team.set_depth_chart()

    db.session.commit()


def update_db(db, thread, preseason):

    players = get_all_player_data(thread)
    add_players(db, players, thread)
    update_player_status(db, thread)

    update_schedule(db, thread)

    add_player_week_stats(db, thread)
    update_fantasy_points(db, thread)
    update_player_season_stats(db, thread)

    update_team_stats(db, thread, preseason)

    update_rankings(db, thread, preseason)

    db.session.commit()
