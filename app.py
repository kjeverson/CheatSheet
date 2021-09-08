from flask import Flask, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
import zulu
import logging
import time
import random
from NFLCheatSheet.lib.classes.update_thread import UpdateThread
from datetime import datetime
import os


update_threads = {}
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

db = SQLAlchemy(app)

from NFLCheatSheet.lib.classes.player import Player
from NFLCheatSheet.lib.classes.team import Team
from NFLCheatSheet.lib.fantasy.scoring import Scoring
from NFLCheatSheet.lib.classes.game import Game, sort, get_week
from NFLCheatSheet.lib.classes.stats import SeasonStats, WeeklyStats, get_stats_leaders, TeamStats
from NFLCheatSheet.lib import db_utils
from NFLCheatSheet.lib.fantasy.fantasy_league import FantasyLeague
from NFLCheatSheet.lib.fantasy.fantasy_team import FantasyTeam


@app.route('/')
def matchups():

    if request.method == "GET":

        teams = Team.query.all()

        data = request.args.get('Sort')

        preseason = False
        if not data:
            games = Game.query.all()
            current_week, preseason = get_week(games)
            week = current_week
            preseason = preseason
            week_string = "pre" + str(week) if preseason else str(week)

        else:
            week_string = data.split("-")[-1]
            if "pre" in week_string:
                week = int(week_string.lstrip("pre"))
                preseason = True

            else:
                week = int(week_string)

        m = Game.query.filter_by(week=week).filter_by(preseason=preseason).all()

        bye_teams = Team.query.filter_by(bye=week).all()

        m = sort(m)

        players = []
        for match in m:
            if not match.completed:
                continue
            else:
                players.extend([match.passingLeader_id, match.rushingLeader_id,
                                match.receivingLeader_id])

        if players:
            games_completed = True
            players = [Player.query.get(player_id) for player_id in players]

            passLeader_id, rushLeader_id, receivingLeader_id = get_stats_leaders(
                players, preseason, week)

            passLeader = Player.query.get(passLeader_id)
            rushLeader = Player.query.get(rushLeader_id)
            recLeader = Player.query.get(receivingLeader_id)

        else:
            games_completed = False

            players = []
            teams = Team.query.all()
            for team in teams:
                stats = team.get_team_stats(preseason=preseason)
                if stats.passingLeader_id:
                    players.append(stats.passingLeader_id)
                if stats.rushingLeader_id:
                    players.append(stats.rushingLeader_id)
                if stats.receivingLeader_id:
                    players.append(stats.receivingLeader_id)

            if players:
                players = [Player.query.get(player_id) for player_id in players]

                passLeader_id, rushLeader_id, receivingLeader_id = get_stats_leaders(
                    players, preseason)

                passLeader = Player.query.get(passLeader_id)
                rushLeader = Player.query.get(rushLeader_id)
                recLeader = Player.query.get(receivingLeader_id)

            else:
                passLeader = None
                rushLeader = None
                recLeader = None

        # Render Times
        for match in m:
            if match.date not in ["TBD", "Final"]:
                dt = zulu.parse(match.date, '%Y-%m-%dT%H:%MZ')
                match.date = dt.format('%a %b %d, %Y %I:%M %p', 'local')

        default_headshot_path = url_for('static', filename='headshots/default.png')

        return render_template("matchups.html", teams=teams, week=week, week_string=week_string,
                               matchups=m, bye_teams=bye_teams, games_completed=games_completed,
                               passLeader=passLeader,
                               recLeader=recLeader, rushLeader=rushLeader,
                               default_headshot_path=default_headshot_path)


@app.route('/matchup', methods=["GET", "POST"])
def matchup():

    if request.method == "GET":

        ID = request.args.get('matchup')
        game = Game.query.get(ID)

        teams = Team.query.all()

        if game.completed:

            away_team_line_score = game.away_team_line_score.split(" ")
            home_team_line_score = game.home_team_line_score.split(" ")

            stats = WeeklyStats.query.filter_by(game_id=game.ID).all()

            players = []
            for stat in stats:
                players.append(stat.player)

            passLeader = Player.query.get(game.passingLeader_id)
            rushLeader = Player.query.get(game.rushingLeader_id)
            recLeader = Player.query.get(game.receivingLeader_id)

            default_headshot_path = url_for('static', filename='headshots/default.png')

            return render_template("boxscore.html", teams=teams, matchup=game, stats=stats,
                                   als=away_team_line_score,
                                   hls=home_team_line_score,
                                   passLeader=passLeader,
                                   rushLeader=rushLeader,
                                   recLeader=recLeader,
                                   default_headshot_path=default_headshot_path)

        else:
            if game.date not in ["TBD", "Final"]:
                dt = zulu.parse(game.date, '%Y-%m-%dT%H:%MZ')
                date = dt.format('%m/%d', 'local')
                time = dt.format('%I:%M %p %Z', 'local').lstrip("0")

            else:
                date = "TBD"
                time = ""

            team_stats = game.home_team.get_team_stats(preseason=game.preseason)

            homePassLeader = Player.query.get(team_stats.passingLeader_id)
            homeRushLeader = Player.query.get(team_stats.rushingLeader_id)
            homeRecLeader = Player.query.get(team_stats.receivingLeader_id)

            team_stats = game.away_team.get_team_stats(preseason=game.preseason)

            awayPassLeader = Player.query.get(team_stats.passingLeader_id)
            awayRushLeader = Player.query.get(team_stats.rushingLeader_id)
            awayRecLeader = Player.query.get(team_stats.receivingLeader_id)

            default_headshot_path = url_for('static', filename='headshots/default.png')

            home_team_games = []
            home_team_games.extend(game.home_team.away_games)
            home_team_games.extend(game.home_team.home_games)

            home_team_games = [game for game in home_team_games if game.completed]
            sorted(home_team_games)

            return render_template("matchup.html",
                                   teams=teams, matchup=game, date=date, time=time,
                                   homePassLeader=homePassLeader, homeRushLeader=homeRushLeader,
                                   homeRecLeader=homeRecLeader, awayPassLeader=awayPassLeader,
                                   awayRushLeader=awayRushLeader, awayRecLeader=awayRecLeader,
                                   default_headshot_path=default_headshot_path,
                                   home_team_games=home_team_games)


@app.route('/team', methods=["GET", "POST"])
def team():

    games = Game.query.all()
    current_week, preseason = get_week(games)

    if request.method == "GET":

        teams = Team.query.all()

        data = request.args.get('sort')
        if not data:
            team_key = request.args.get('team')
            position = 'ALL'
        else:
            team_key, position = data.split("-")

        team = Team.query.filter_by(key=team_key).first()

        players = team.players
        if position != 'ALL':
            if position == 'REC':
                players = [player for player in players if player.position in ['RB', 'WR', 'TE']]
            elif position == 'OFF':
                players = [player for player in players if player.position_group == "OFF"]
            elif position == 'DEF':
                players = [player for player in players if player.position_group == "DEF"]
            elif position == 'ST':
                players = [player for player in players if player.position_group == "ST"]
            elif position == "OL":
                players = [player for player in players if player.position in
                           ["OL", "OT", "G", "C"]]
            else:
                players = [player for player in players if player.position == position]

        schedule = list()
        schedule.extend(team.away_games)
        schedule.extend(team.home_games)

        preschedule = [game for game in schedule if game.preseason]
        preschedule = sort(preschedule)
        for game in preschedule:
            if game.date not in ["TBD", "Final"]:
                dt = zulu.parse(game.date, '%Y-%m-%dT%H:%MZ')
                game.date = dt.format('%m/%d', 'local')
                game.time = dt.format('%I:%M', 'local').lstrip("0")

        schedule = [game for game in schedule if not game.preseason]
        schedule = sort(schedule)
        for game in schedule:
            if game.date not in ["TBD", "Final"]:
                dt = zulu.parse(game.date, '%Y-%m-%dT%H:%MZ')
                game.date = dt.format('%m/%d', 'local')
                game.time = dt.format('%I:%M', 'local').lstrip("0")

        default_headshot_path = url_for('static', filename='headshots/default.png')

        stats = [stats for player in team.players for stats in player.season_stats if
                 stats.preseason]

        team_stats = TeamStats.query.filter_by(team_id=team.ID).filter_by(preseason=preseason).first()

        if team_stats.passingLeader_id:
            passLeader = Player.query.get(team_stats.passingLeader_id)
        else:
            passLeader = None

        if team_stats.rushingLeader_id:
            rushLeader = Player.query.get(team_stats.rushingLeader_id)
        else:
            rushLeader = None

        if team_stats.receivingLeader_id:
            recLeader = Player.query.get(team_stats.receivingLeader_id)
        else:
            recLeader = None

        player_stats = [player.get_season_stats(preseason=preseason) for player in players]

        injured = [player for player in players if player.date]
        injured = [player for player in injured if len(player.news) > 2]

        for player in injured:
            dt = zulu.parse(player.date, '%Y-%m-%dT%H:%MZ')
            player.date = dt.format('%B %d, %Y', 'local')
            player.date = datetime.strptime(player.date, '%B %d, %Y')

        injured.sort(key=lambda x: x.date, reverse=True)
        for player in injured:
            player.date = player.date.strftime('%B %d, %Y')

        return render_template("team.html", preseason=preseason,
                               teams=teams, players=players, team=team, stats=stats,
                               position=position, schedule=schedule, preschedule=preschedule,
                               Player=Player,
                               passLeader=passLeader,
                               rushLeader=rushLeader,
                               recLeader=recLeader,
                               player_stats=player_stats, injured=injured,
                               default_headshot_path=default_headshot_path)


@app.route('/fantasy', methods=["GET", "POST"])
def fantasy():

    teams = Team.query.all()

    if request.method == "POST":

        if "inputLeagueName" in request.form:
            name = request.form.get("inputLeagueName")
            number = request.form.get("inputLeagueSize")

            db.session.add(
                FantasyLeague(
                    name=name,
                    size=int(number),
                    QB=request.form['QB'] if request.form.get("QB") else 0,
                    RB=request.form['RB'] if request.form.get("RB") else 0,
                    WR=request.form['WR'] if request.form.get("WR") else 0,
                    TE=request.form['TE'] if request.form.get("TE") else 0,
                    RBWR=request.form['WR/RB'] if request.form.get("WR/RB") else 0,
                    WRTE=request.form['WR/TE'] if request.form.get("WR/TE") else 0,
                    RBTE=request.form['RB/TE'] if request.form.get("RB/TE") else 0,
                    FLEX=request.form['RB/WR/TE'] if request.form.get("RB/WR/TE") else 0,
                    SFLEX=request.form['QB/RB/WR/TE'] if request.form.get("QB/RB/WR/TE") else 0,
                    DST=request.form['DST'] if request.form.get("DST") else 0,
                    K=request.form['K'] if request.form.get("K") else 0,
                    BENCH=request.form['BENCH'] if request.form.get("BENCH") else 0,
                    IR=request.form['IR'] if request.form.get("IR") else 0
                )
            )
            db.session.commit()

        elif "inputTeamName" in request.form:
            name = request.form.get("inputTeamName")
            league = request.form.get("league")

            db.session.add(
                FantasyTeam(
                    league_id=int(league),
                    name=name
                )
            )
            db.session.commit()

        elif "deleteTeam" in request.form:
            team = request.form.get("deleteTeam")
            team = FantasyTeam.query.get(team)
            db.session.delete(team)
            db.session.commit()

        else:
            league = request.form.get("deleteLeague")
            league = FantasyLeague.query.get(league)

            for team in league.teams:
                db.session.delete(team)

            db.session.delete(league)
            db.session.commit()

        leagues = FantasyLeague.query.all()
        fantasy_teams = FantasyTeam.query.all()
        return render_template("fantasy.html",
                               teams=teams, fantasy_leagues=leagues, fantasy_teams=fantasy_teams)

    else:
        leagues = FantasyLeague.query.all()
        fantasy_teams = FantasyTeam.query.all()
        return render_template("fantasy.html",
                               teams=teams, fantasy_leagues=leagues, fantasy_teams=fantasy_teams)


@app.route('/fantasy_team', methods=["GET", "POST"])
def fantasy_team():

    games = Game.query.all()
    current_week, preseason = get_week(games)

    teams = Team.query.filter(Team.ID != 100).all()
    players = Player.query.filter(
        (Player.position == 'QB') | (Player.position == 'RB') | (Player.position == 'WR') |
        (Player.position == 'TE') | (Player.position == 'PK')
    ).all()

    if request.method == "GET":

        team_id = request.args.get("team")
        team = FantasyTeam.query.get(int(team_id))

    else:

        if "addPlayer" in request.form:
            team_id, player_id = request.form.get("addPlayer").split("-")
            team = FantasyTeam.query.get(int(team_id))

            team.add_player(player_id)
            db.session.commit()
        else:
            team_id, player_id = request.form.get("dropPlayer").split("-")
            team = FantasyTeam.query.get(int(team_id))

            team.drop_player(player_id)
            db.session.commit()

    if team.players:
        roster = team.players.split(" ")
    else:
        roster = []

    return render_template("fantasy_team.html", preseason=preseason, week=current_week, teams=teams, team=team, Player=Player, players=players, roster=roster)


@app.route('/player', methods=["GET", "POST"])
def player():
    games = Game.query.all()
    current_week, preseason = get_week(games)

    player_id = int(request.args.get('id'))
    player = Player.query.get(player_id)
    team = player.current_team

    player_dict = player.as_dict()
    stats = player.get_season_stats(preseason=preseason)
    player_dict.update(stats.as_dict())

    cutout_path = url_for('static', filename='headshots/{}.png'.format(player.ID))
    default_path = url_for('static', filename='headshots/default.png')

    team_logo = url_for('static', filename='logos/{}.png'.format(player.current_team.key))

    status = player.designation
    if status in ['Questionable', 'Doubtful']:
        status_string = '<span class="badge rounded-pill bg-warning">{} - {}</span>'\
            .format(player.designation, player.injury)
    elif status in ['Injured Reserve', 'Out']:
        status_string = '<span class="badge rounded-pill bg-danger">{} - {}</span>'\
            .format(player.designation, player.injury)
    else:
        status_string = '<span class="badge rounded-pill bg-success">Active</span>'

    stats = ["-", "-", "-", "-", "-"]
    if player.position == 'QB':
        labels = ["YDS", "TD", "INT", "RTG"]

    elif player.position == 'RB':
        labels = ["ATT", "YDS", "TD", "AVG"]

    else:
        labels = ["REC", "YDS", "TD", "AVG"]

    player_dict.update({'labels': labels})
    player_dict.update({'preseason': preseason})
    player_dict.update({'cutout': "<img src='{}' onerror='this.src=\"{}\"' class='img-fluid'>"
                        .format(cutout_path, default_path)})
    player_dict.update({'logo': "<img src='{}' height='100'>"
                       .format(team_logo)})
    player_dict.update({'status_string': status_string})
    player_dict.update({'team_name': player.current_team.fullname})

    return jsonify(player_dict)


@app.route('/scoring', methods=["GET", "POST"])
def scoring():

    teams = Team.query.all()

    scoring = Scoring.query.filter_by(ID=0).first()

    if request.method == "POST":
        for key, value in request.form.items():
            setattr(scoring, key, value)
        db.session.commit()

    return render_template("scoring.html", teams=teams, scoring=scoring)


@app.route('/db', methods=["GET", "POST"])
def database():

    teams = Team.query.all()

    thread_ids = []
    for i in range(0, 8):
        thread_id = random.randint(0, 10000)
        update_threads[thread_id] = UpdateThread()
        update_threads[thread_id].state = "INIT"
        thread_ids.append(thread_id)

    return render_template("db.html", teams=teams, thread_ids=thread_ids)


@app.route('/getHeadshots')
def get_headshots():
    thread_id = int(request.args.get('id'))
    global update_threads
    thread = update_threads[thread_id]
    thread.state = "STARTED"
    thread.start()

    thread.state = "Updating Player Headshots"
    db_utils.get_headshots(db, thread)
    print("Updating Headshots")
    return jsonify("Done")


@app.route('/updateRosters')
def update_rosters():
    thread_id = int(request.args.get('id'))
    global update_threads
    thread = update_threads[thread_id]
    thread.state = "STARTED"
    thread.start()

    thread.state = "Collecting Player Data"
    players = db_utils.get_all_player_data(thread)

    thread.state = "Updating Player Database"
    db_utils.add_players(db, players, thread)
    db.session.commit()
    print("Updating Rosters")
    return jsonify("Done")


@app.route('/updateStats')
def update_stats():
    thread_id = int(request.args.get('id'))
    global update_threads
    thread = update_threads[thread_id]
    thread.state = "STARTED"
    thread.start()

    thread.state = "Updating Matchups"
    db_utils.update_schedule(db, thread)
    thread.state = "Adding Weekly Stats to Database"
    db_utils.add_player_week_stats(db, thread)
    thread.state = "Updating Player Fantasy Points"
    db_utils.update_fantasy_points(db, thread)
    thread.state = "Updating Player Season Stats"
    db_utils.update_player_season_stats(db, thread)
    thread.state = "Updating Team Stats"
    db_utils.update_team_stats(db, thread)
    thread.state = "Updating Team Rankings"
    db_utils.update_rankings(db, thread)
    db.session.commit()
    print("Updating Stats")
    return jsonify("Done")


@app.route('/updateStatus')
def update_status():

    thread_id = int(request.args.get('id'))
    global update_threads
    update_threads[thread_id].state = "STARTED"
    update_threads[thread_id].start()

    update_threads[thread_id].state = "Updating Player Statuses"
    db_utils.update_player_status(db, update_threads[thread_id])
    db.session.commit()
    print("Updating Status")
    return jsonify("Done")


@app.route('/updateDatabase')
def update_database():
    thread_id = int(request.args.get('id'))
    global update_threads
    update_threads[thread_id].state = "STARTED"
    update_threads[thread_id].start()

    db_utils.update_db(db, update_threads[thread_id])
    db.session.commit()
    print("Updating Database")
    return jsonify("Done")


@app.route('/rebuildDatabase')
def rebuild_database():
    thread_id = int(request.args.get('id'))
    global update_threads
    thread = update_threads[thread_id]
    thread.state = "STARTED"
    thread.start()

    thread.state = "Rebuilding Database"
    db_utils.build_db(db, thread)
    print("Rebuilding Database")
    return jsonify("Done")


@app.route('/deleteDatabase')
def delete_database():
    os.remove("/Users/everson/NFLCheatSheet/database.db")
    print("Deleting Database")
    return jsonify("Done")


@app.route('/progress/<int:thread_id>')
def progress(thread_id):
    global update_threads

    return {"state": str(update_threads[thread_id].state),
            "progress": str(update_threads[thread_id].progress),
            "total": str(update_threads[thread_id].total)}
