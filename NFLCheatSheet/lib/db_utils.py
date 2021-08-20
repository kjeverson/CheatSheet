# Database Utility functions
# To Do: Remove absolute file paths

import json
from pathlib import Path
from typing import Dict, List
import re
import zulu
import operator
import requests

from NFLCheatSheet.lib.classes.team import Team
from NFLCheatSheet.lib.classes.player import Player
from NFLCheatSheet.lib.classes import stats
from NFLCheatSheet.lib.classes.game import Game

from NFLCheatSheet.lib.fantasy.scoring import Scoring, get_score

from NFLCheatSheet.lib.scrape.status import get_injured_list
from NFLCheatSheet.lib.scrape.images import get_headshot
from NFLCheatSheet.lib.scrape.boxscore import get_game_stats, get_scores
from NFLCheatSheet.lib.scrape import schedule


def get_all_team_data() -> List[Dict]:

    print("Getting Team Data...\r", end="")
    #response = requests.get(
    # 'https://fly.sportsdata.io/v3/nfl/scores/json/Teams?key=2810c12201be4499bff03931c186f9f5')
    #team_data = response.json()

    with open("/Users/everson/flask/data/teams.json", "r") as teams_file:
        teams_data = json.load(teams_file)

    print("Getting Team Data...\x1b[32mCOMPLETE!\x1b[0m")
    return teams_data


def add_teams(database, teams: List[Dict]) -> None:

    print("Adding Teams to Database...\r", end="")
    for i in range(len(teams)):
        print("Adding Teams to Database...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(teams), ((i + 1) / len(teams)) * 100),
              end="")
        team = teams[i]

        database.session.add(Team(
            ID=team['TeamID'],
            key=team['Key'],
            location=team['City'],
            name=team['Name'],
            fullname=team['FullName'],
            conference=team['Conference'],
            division=team['Division'],
            bye=team['ByeWeek'],
            hc=team['HeadCoach'],
            dc=team['DefensiveCoordinator'],
            oc=team['OffensiveCoordinator'],
            primary=team['PrimaryColor'],
            secondary=team['SecondaryColor'],
            tertiary=team['TertiaryColor'],
            wordmark=team["WikipediaWordMarkUrl"],
            stadium=team["StadiumDetails"]["Name"],
            stadium_city=team["StadiumDetails"]["City"],
            stadium_state=team["StadiumDetails"]["State"],
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
            team_id=team['TeamID'],
            preseason=True
        ))

        database.session.add(stats.TeamStats(
            team_id=team['TeamID'],
            preseason=False
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

    # Only get rostered players
    # player_data = [player for player in player_data if player['Team'] is not None]

    for i in range(len(player_data)):
        experience_string = player_data[i]['ExperienceString']
        if experience_string:
            year = re.search(r'\d+', experience_string.split('0')[0])
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


def get_all_player_data(position: str = "ALL") -> List[Dict]:
    """
    Get all player data from json file.
    :param position: Position to get, supports 'ALL', 'OFF', 'DEF', 'SKILL', 'REC'. Default = 'ALL'
    :return: List of Player data in dictionaries
    """

    print("Getting Player Data...\r", end="")

    # API CAll for all Player data
    #response = requests.get("https://api.sportsdata.io/v3/nfl/scores/json/Players?"
    #                        "key=2810c12201be4499bff03931c186f9f5")
    #player_data = response.json()

    player_file_path = Path("/Users/everson/NFLCheatSheet/data/players.json")
    #with player_file_path.open("w") as player_file:
    #    json.dump(player_data, player_file)

    with player_file_path.open("r") as player_file:
        player_data = json.load(player_file)

    players = filter_by_position(player_data, position)

    print("Getting Player Data...\x1b[32mCOMPLETE!\x1b[0m")
    return players


def get_headshots(db):

    players = Player.query.all()

    for i in range(len(players)):
        print("{}/{} - {:0.2f}%\r".format(i + 1, len(players), ((i + 1) / len(players)) * 100),
              end="")
        player = players[i]
        if player.current_team.ID != 100:
            img_path = Path("/Users/everson/NFLCheatSheet/static/headshots/{}.png"
                            .format(player.ID))
            if not img_path.exists():
                get_headshot(player.ID, player.yahooPlayerID)
    print("")


def add_players(database, players: List[Dict]) -> None:
    """
    Add players to the database
    :param players: Player data list
    :param database: Database object
    :return:
    """

    print("Adding Players to Database..\r", end="")
    for i in range(len(players)):
        print("Adding Players to Database...{}/{} - {:0.2f}%\r"
              .format(i+1, len(players), ((i+1)/len(players))*100), end="")

        player = players[i]
        player_obj = Player.query.get(player['PlayerID'])

        # Player doesn't exist in the database.
        if not player_obj:

            database.session.add(Player(
                ID=player['PlayerID'],
                rotowireID=player['RotoWirePlayerID'],
                yahooPlayerID=player['YahooPlayerID'],
                name=player['Name'],
                fname=player['FirstName'],
                lname=player['LastName'],
                height=player['Height'],
                weight=player['Weight'],
                age=player['Age'],
                experience=player['Experience'],
                experience_string=player['ExperienceString'],
                number=player['Number'],
                position=player['Position'],
                position_group=player['PositionCategory'],
                team=player['Team'],
                team_id=player['TeamID'] if player['TeamID'] else 100,
                prev_team_id=None,
                bye=player['ByeWeek'],
                college=player['College'],
                status="Active",
                designation="",
                injury="",
                ret="",
            ))

            database.session.add(stats.SeasonStats(
                player_id=player['PlayerID'],
                preseason=False,
                passComps=0,
                passAtts=0,
                passYDs=0,
                passTDs=0,
                passINTs=0,
                passSacks=0,
                passSackYDs=0,
                passRTG=0,
                rushAtts=0,
                rushYDs=0,
                rushTDs=0,
                rushLng=0,
                recs=0,
                recYDs=0,
                recTDs=0,
                recLng=0,
                recTGTS=0
            ))

            database.session.add(stats.SeasonStats(
                player_id=player['PlayerID'],
                preseason=True,
                passComps=0,
                passAtts=0,
                passYDs=0,
                passTDs=0,
                passINTs=0,
                passSacks=0,
                passSackYDs=0,
                passRTG=0,
                rushAtts=0,
                rushYDs=0,
                rushTDs=0,
                rushLng=0,
                recs=0,
                recYDs=0,
                recTDs=0,
                recLng=0,
                recTGTS=0
            ))

        # Player exists in the database.
        else:

            player_obj.rotowireID = player['RotoWirePlayerID']
            player_obj.yahooPlayerID = player['YahooPlayerID']
            player_obj.name = player['Name']
            player_obj.fname = player['FirstName']
            player_obj.lname = player['LastName']
            player_obj.height = player['Height']
            player_obj.weight = player['Weight']
            player_obj.age = player['Age']
            player_obj.experience = player['Experience']
            player_obj.experience_string = player['ExperienceString']
            player_obj.number = player['Number']
            player_obj.position = player['Position']
            player_obj.position_group = player['PositionCategory']
            player_obj.team = player['Team']
            if player['TeamID']:
                player_obj.prev_team_id = player_obj.prev_team_id if player_obj.prev_team_id else None
            else:
                player_obj.prev_team_id = player_obj.prev_team_id if player_obj.prev_team_id else player_obj.team_id
            player_obj.team_id = player['TeamID'] if player['TeamID'] else 100
            player_obj.bye = player['ByeWeek']
            player_obj.college = player['College']
            player_obj.status = "Active"
            player_obj.designation = ""
            player_obj.injury = ""
            player_obj.ret = ""
            player_obj.recent_stats = ""
            player_obj.career_stats = ""

    print("Adding Players to Database...\x1b[32mCOMPLETE!\x1b[0m\033[K")


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


def update_player_status(database):

    print("Updating Player Statuses...\r", end="")

    injured = get_injured_list()

    players = Player.query.all()
    for i in range(len(players)):
        print("Updating Player Statuses...{}/{} - {:0.2f}%\r"
              .format(i+1, len(players), ((i+1)/len(players))*100), end="")
        player = players[i]
        if player.current_team.ID == 100:
            continue
        if player.name in injured:
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


def update_schedule(db):

    print("Updating Games...\r", end="")
    # Get all unfinished games
    games = Game.query.all()
    dt_now = zulu.now().datetime
    games = [game for game in games if game.get_time() < dt_now]
    games = [game for game in games if game.is_complete() and not game.scraped_stats]

    for i in range(len(games)):

        print("Updating Games...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(games), ((i + 1) / len(games)) * 100), end="")
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

    print("Updating Games...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def get_player_from_list(players, name):

    for player in players:
        if player.name == name:
            return player

    return None


def get_player(game, players, name):

    player = get_player_from_list(players, name)
    if player:
        return player
    else:
        player = Player.query.filter_by(name=name).all()
        if len(player) == 1:
            return player[-1]
        else:
            fname, lname = name.split(" ", 1)

            player = Player.query.filter(
                (Player.lname.contains(lname)) & (Player.team_id == game.home_team.ID) |
                (Player.lname.contains(lname)) & (Player.team_id == game.away_team.ID)).all()

            if len(player) == 1:
                return player[-1]

            elif len(player) > 1:

                player = Player.query.filter(
                    (Player.fname.like(fname)) & (Player.lname.contains(lname)) & (Player.team_id == game.home_team.ID) |
                    (Player.fname.like(fname)) & (Player.lname.contains(lname)) & (Player.team_id == game.away_team.ID)).all()

                return player[-1]

            else:
                player = Player.query.filter(
                    (Player.fname == fname) & (Player.team_id == game.home_team.ID) |
                    (Player.fname == fname) & (Player.team_id == game.away_team.ID)).all()

                if len(player) == 1:
                    return player[-1]

                else:
                    print(name, player)
                    return None


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
            week_stats.update({key: float(stat)})
            
    return week_stats


def add_player_week_stats(db):

    games = Game.query.filter_by(completed=True).filter_by(scraped_stats=False).all()

    for game in games:
        passing, rushing, receiving = get_game_stats(game.ID)

        players = []

        for i in range(0, 2):

            if i == 0:
                team_id = game.away_team.ID
            else:
                team_id = game.home_team.ID

            team = Team.query.get(team_id)
            team_stats = team.get_team_stats(preseason=game.preseason)

            player_names = set()

            for name in passing[i].keys():
                player_names.add(name)
            for name in rushing[i].keys():
                player_names.add(name)
            for name in receiving[i].keys():
                player_names.add(name)

            for name in player_names:
                player = get_player(game, players, name)

                if not player:
                    print(name)
                    continue

                players.append(player)

                week_stats = {"preseason": game.preseason}

                pass_stats = passing[i].get(name)
                if pass_stats:
                    week_stats.update({"passer": True})
                    week_stats.update(parse_week_stats(pass_stats))
                else:
                    week_stats.update({"passer": False})

                rush_stats = rushing[i].get(name)
                if rush_stats:
                    week_stats.update({"rusher": True})
                    week_stats.update(parse_week_stats(rush_stats))
                else:
                    week_stats.update({"rusher": False})

                rec_stats = receiving[i].get(name)
                if rec_stats:
                    week_stats.update({"receiver": True})
                    week_stats.update(parse_week_stats(rec_stats))
                else:
                    week_stats.update({"receiver": False})

                db.session.add(stats.WeeklyStats(
                    player_id=int(player.ID),
                    game_id=int(game.ID),
                    week=int(game.week),
                    team_id=team.ID,
                    preseason=week_stats["preseason"],
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
                    fumLost=0,
                    fum=0,
                    FPs=0,
                ))

        pass_leader_id, rush_leader_id, rec_leader_id = stats.get_stats_leaders(players, game.week)

        game.passingLeader_id = pass_leader_id
        game.rushingLeader_id = rush_leader_id
        game.receivingLeader_id = rec_leader_id

        game.scraped_stats = True


def update_player_season_stats(db):

    players = Player.query.all()

    print("Update Season Stats...\r", end="")
    for i in range(len(players)):

        player = players[i]
        print("Update Season Stats...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(players), ((i + 1) / len(players)) * 100),end="")

        preseason_week_stats = player.get_weekly_stats_list(preseason=True)
        ps = player.get_season_stats(preseason=True)
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
                ps.passRTG = ((((ps.passComps/ps.passAtts)-0.3)*5+((ps.passYDs/ps.passAtts)-3)*0.25+(ps.passTDs/ps.passAtts)*20+2.375-((ps.passINTs/ps.passAtts)*25))/6)*100

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

            ps.FPs = ws.FPs if not ps.FPs else ps.FPs + ws.FPs

        season_week_stats = player.get_weekly_stats_list(preseason=False)
        ss = player.get_season_stats(preseason=False)
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
                ss.passRTG = ((((ss.passComps/ss.passAtts)-0.3)*5+((ss.passYDs/ss.passAtts)-3)*0.25+(ss.passTDs/ss.passAtts)*20+2.375-((ss.passINTs/ss.passAtts)*25))/6)*100

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

            ss.FPs = ws.FPs if not ss.FPs else ss.FPs + ws.FPs

    print("Update Season Stats...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def update_team_stats(db):

    teams = Team.query.all()

    for i in range(len(teams)):
        team = teams[i]

        team_stats = team.get_team_stats(preseason=True)

        pass_leader_id, rush_leader_id, rec_leader_id = stats.get_stats_leaders(team.players)

        team_stats.passingLeader_id = pass_leader_id
        team_stats.rushingLeader_id = rush_leader_id
        team_stats.receivingLeader_id = rec_leader_id

        week_stats = team.get_week_stats(preseason=True)
        
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

        if team.preseason_games_played > 0:
            team_stats.passYDsPerGame = team_stats.passYDs / team.preseason_games_played
            team_stats.rushYDsPerGame = team_stats.rushYDs / team.preseason_games_played

        team_stats.totalYards = team_stats.passYDs + team_stats.rushYDs

        for game in team.get_games(preseason=True, completed=True, home=True):
            team_stats.pointsFor += game.home_team_score
            team_stats.pointsAgainst += game.away_team_score
        for game in team.get_games(preseason=True, completed=True, away=True):
            team_stats.pointsFor += game.away_team_score
            team_stats.pointsAgainst += game.home_team_score

        if team.preseason_games_played:
            team_stats.PPG = team_stats.pointsFor / team.preseason_games_played
            team_stats.PAPG = team_stats.pointsAgainst / team.preseason_games_played


def update_fantasy_points(db):

    print("Calculating Fantasy Points...\r", end="")
    scoring = Scoring.query.first()

    players = Player.query.all()
    for i in range(len(players)):
        print("Calculating Fantasy Points...{}/{} - {:0.2f}%\r"
              .format(i + 1, len(players), ((i + 1) / len(players)) * 100), end="")
        player = players[i]
        week_stats = player.weekly_stats
        if not week_stats:
            continue
        else:
            for week in week_stats:
                week.FPs = get_score(scoring, week)
    print("Calculating Fantasy Points...\x1b[32mCOMPLETE!\x1b[0m\033[K")


def update_rankings(db):

    teams = Team.query.filter(Team.ID != 100).all()
    s = stats.TeamStats.query.filter(stats.TeamStats.team_id != 100).filter_by(preseason=True).all()
    passYDsPerGameRank = sorted(s, key=operator.attrgetter("passYDsPerGame"), reverse=True)
    rushYDsPerGameRank = sorted(s, key=operator.attrgetter("rushYDsPerGame"), reverse=True)
    passYDsRank = sorted(s, key=operator.attrgetter("passYDs"), reverse=True)
    rushYDsRank = sorted(s, key=operator.attrgetter("passYDs"), reverse=True)
    PPGRank = sorted(s, key=operator.attrgetter("PPG"), reverse=True)
    PAPGRank = sorted(s, key=operator.attrgetter("PAPG"))

    for team in teams:
        s = team.get_team_stats(preseason=True)
        s.passYDsPerGameRank = passYDsPerGameRank.index(s)+1
        s.rushYDsPerGameRank = rushYDsPerGameRank.index(s)+1
        s.passYDsRank = passYDsRank.index(s)+1
        s.rushYDsRank = rushYDsRank.index(s)+1
        s.PPGRank = PPGRank.index(s)+1
        s.PAPGRank = PAPGRank.index(s)+1


def build_db(db):
    db.create_all()

    teams = get_all_team_data()
    add_teams(db, teams)

    players = get_all_player_data()
    add_players(db, players)
    update_player_status(db)

    add_default_scoring(db)

    get_schedule(db)
    update_schedule(db)

    add_player_week_stats(db)
    update_fantasy_points(db)
    update_player_season_stats(db)

    update_team_stats(db)
    update_rankings(db)

    db.session.commit()


def update_db(db):

    players = get_all_player_data()
    add_players(db, players)
    update_player_status(db)

    update_schedule(db)

    add_player_week_stats(db)
    update_fantasy_points(db)
    update_player_season_stats(db)

    update_team_stats(db)

    update_rankings(db)

    db.session.commit()
