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

        default_headshot_path = url_for('static', filename='headshots/default.png')

        return render_template("matchups.html", teams=teams, week=week, week_string=week_string,
                               matchups=m, bye_teams=bye_teams, games_completed=games_completed,
                               Player=Player,
                               passLeader=passLeader,
                               recLeader=recLeader, rushLeader=rushLeader,
                               default_headshot_path=default_headshot_path)


@app.route('/statistics', methods=["GET"])
def stats():

    games = Game.query.all()
    current_week, preseason = get_week(games)

    teams = Team.query.all()

    player_stats = SeasonStats.query.filter_by(preseason=preseason).all()

    player_stats.sort(key=lambda player: player.passYDs, reverse=True)
    passLeaders = player_stats[0:5]
    player_stats.sort(key=lambda player: player.passTDs, reverse=True)
    passTDLeaders = player_stats[0:5]
    player_stats.sort(key=lambda player: player.rushYDs, reverse=True)
    rushLeaders = player_stats[0:5]
    player_stats.sort(key=lambda player: player.rushTDs, reverse=True)
    rushTDLeaders = player_stats[0:5]
    player_stats.sort(key=lambda player: player.recYDs, reverse=True)
    recLeaders = player_stats[0:5]
    player_stats.sort(key=lambda player: player.recTDs, reverse=True)
    recTDLeaders = player_stats[0:5]

    default_headshot_path = url_for('static', filename='headshots/default.png')

    return render_template("stats.html", preseason=preseason,
                           teams=teams,
                           Player=Player,
                           player_stats=player_stats,
                           passLeaders=passLeaders, passTDLeaders=passTDLeaders,
                           rushLeaders=rushLeaders, rushTDLeaders=rushTDLeaders,
                           recLeaders=recLeaders, recTDLeaders=recTDLeaders,
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

        team_key = request.args.get('team')
        team = Team.query.filter_by(key=team_key).first()

        players = team.get_players(preseason=preseason)

        default_headshot_path = url_for('static', filename='headshots/default.png')

        player_stats = [player.get_season_stats_by_team(preseason=preseason, team_id=team.ID) for player in players]

        injured = [player for player in players if player.date]
        injured = [player for player in injured if len(player.news) > 2]

        injured.sort(key=lambda x: x.get_injury_date(), reverse=True)

        draft_picks = Player.query.filter(Player.draft_year == 2021)\
            .filter(Player.draft_team_id == team.ID).all()

        division = Team.query.filter(
            Team.division == team.division).filter(
            Team.conference == team.conference).all()
        division.sort(key=lambda team: team.get_team_stats(preseason=preseason).pointsFor,
                      reverse=True)
        division.sort(key=lambda team: team.divisionWins, reverse=True)
        division.sort(key=lambda team: team.wins, reverse=True)

        return render_template("team.html", preseason=preseason,
                               teams=teams, players=players, team=team,
                               division=division,
                               Player=Player,
                               draft_picks=draft_picks,
                               player_stats=player_stats, injured=injured,
                               default_headshot_path=default_headshot_path)


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
    matchup = player.current_team.get_game_by_week(preseason, current_week)

    if matchup:

        if matchup.away_team.key == player.current_team.key:

            gameLocation = "@ "
            oppImgPath = url_for('static', filename='logos/{}.png'.format(matchup.home_team.key))
            oppTeam = matchup.home_team.location + ' ' + matchup.home_team.name

        else:
            gameLocation = "vs. "
            oppImgPath = url_for('static', filename='logos/{}.png'.format(matchup.away_team.key))
            oppTeam = matchup.away_team.location + ' ' + matchup.away_team.name

    else:

        gameLocation = " "
        oppImgPath = None
        oppTeam = 'Bye Week'

    player_dict.update({
        'gameLocation': gameLocation,
        'oppImg': "<img src='{}'  height='40'>".format(oppImgPath) if oppImgPath else " ",
        'oppTeam': " " + oppTeam
    })

    status = player.designation
    if status in ['Questionable', 'Doubtful']:
        if player.injury:
            status_string = '<span class="badge rounded-pill bg-warning">{} - {}</span>' \
                .format(player.designation, player.injury)
        else:
            status_string = '<span class="badge rounded-pill bg-warning">{}</span>' \
                .format(player.designation)

    elif status in ['Injured Reserve', 'Out']:
        if player.injury:
            status_string = '<span class="badge rounded-pill bg-danger">{} - {}</span>'\
                .format(player.designation, player.injury)
        else:
            status_string = '<span class="badge rounded-pill bg-danger">{}</span>'\
                .format(player.designation)
    else:
        status_string = '<span class="badge rounded-pill bg-success">Active</span>'

    if player.position == 'QB':
        labels = ["YDS", "TD", "INT", "RTG"]

    elif player.position == 'RB' or player.position == 'FB':
        labels = ["ATT", "YDS", "TD", "AVG"]

    elif player.position == 'WR' or player.position == 'TE':
        labels = ["REC", "YDS", "TD", "AVG"]

    elif player.position == 'CB' or player.position == 'S':
        labels = ["SOLO", "FF", "INT", "PD"]

    elif player.position == 'LB':
        labels = ["SOLO", "SACK", "FF", "INT"]

    elif player.position == 'DE' or player.position == 'DT':
        labels = ["SOLO", "TFL", "SACK", "QBHITS"]

    elif player.position == 'PK':
        labels = ["FG%", "XP%", "LNG", "Points"]

    elif player.position == 'P':
        labels = ["PUNTS", "AVG", "LNG", "IN20"]

    else:
        labels = ["", "", "", ""]

    recent_performance = []
    week_label = []
    week_fps = []

    recent_games = player.current_team.get_games(
        preseason=False, completed=True, home=True, away=True)[-5:]

    table_label = "<tr><th><small><small>Wk</small></small></th><th style='border-right: 1px solid white'><small><small>Opp</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th></tr>"
    if player.position == 'QB':
        table_label = "<tr><th><small><small>Wk</small></small></th><th style='border-right: 1px solid white'><small><small>Opp</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th></tr>".format("CMP/ATT", "YD", "TD", "INT", "CAR", "YD", "TD", "FPs")
    elif player.position == "RB":
        table_label = "<tr><th><small><small>Wk</small></small></th><th style='border-right: 1px solid white'><small><small>Opp</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th></tr>".format("CAR", "YD", "TD", "TGT", "REC", "YD", "TD", "FPs")
    elif player.position == "WR" or player.position == "TE":
        table_label = "<tr><th><small><small>Wk</small></small></th><th style='border-right: 1px solid white'><small><small>Opp</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th></tr>".format("TGT", "REC", "YD", "TD", "CAR", "YD", "TD", "FPs")
    else:
        table_label = "<tr><th><small><small>Wk</small></small></th><th style='border-right: 1px solid white'><small><small>Opp</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th><small><small>{}</small></small></th><th style='border-right: 1px solid white'><small><small>{}</small></small></th><th><small><small>{}</small></small></th></tr>".format("", "", "", "", "", "", "", "")

    for game in sorted(recent_games, reverse=True):
        week_label.append(game.week)
        stat = player.get_weekly_stats_by_week(preseason=preseason, week=game.week)
        table_string = "<tr><td><small><small>{}</small></small></td><td style='border-right: 1px solid white'><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td style='border-right: 1px solid white'><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td style='border-right: 1px solid white'><small><small>{}</small></small></td><td><small><small>{}</small></small></td></tr>"
        if stat:
            if game.away_team == player.current_team:
                opponent = "@ {}".format(game.home_team.key)
            else:
                opponent = "vs. {}".format(game.away_team.key)

            if player.position == 'QB':
                recent_performance.append(table_string.format(stat.week, opponent,
                                                              str(stat.passAtts) + "/" + str(
                                                                  stat.passComps), stat.passYDs,
                                                              stat.passTDs, stat.passINTs,
                                                              stat.rushAtts, stat.rushYDs,
                                                              stat.rushTDs,
                                                              '{0:.2f}'.format(stat.FPs)))
            elif player.position == "RB":
                table_string = "<tr><td><small><small>{}</small></small></td><td style='border-right: 1px solid white'><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td style='border-right: 1px solid white'><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td><small><small>{}</small></small></td><td style='border-right: 1px solid white'><small><small>{}</small></small></td><td><small><small>{}</small></small></td></tr>"
                recent_performance.append(
                    table_string.format(stat.week, opponent, stat.rushAtts, stat.rushYDs,
                                        stat.rushTDs, stat.recTGTS, stat.recs, stat.recYDs,
                                        stat.recTDs, '{0:.2f}'.format(stat.FPs)))
            elif player.position == "WR" or player.position == "TE":
                recent_performance.append(
                    table_string.format(stat.week, opponent, stat.recTGTS, stat.recs, stat.recYDs,
                                        stat.recTDs, stat.rushAtts, stat.rushYDs, stat.rushTDs,
                                        '{0:.2f}'.format(stat.FPs)))
            else:
                recent_performance.append(
                    table_string.format(stat.week, opponent, stat.passYDs, stat.passTDs,
                                        stat.passINTs, '{0:.2f}'.format(stat.FPs)))
            week_fps.append(stat.FPs)
        else:
            if game.away_team == player.current_team:
                opponent = "@ {}".format(game.home_team.key)
            else:
                opponent = "vs. {}".format(game.away_team.key)

            recent_performance.append(
                table_string.format(game.week, opponent, "-", "-", "-", "-", "-", "-", "-", '{0:.2f}'.format(0)))
            week_fps.append(0)

    week_fps.reverse()
    week_label.reverse()

    player_dict.update({'labels': labels})
    player_dict.update({'preseason': preseason})
    player_dict.update({'cutout': "<img src='{}' onerror='this.src=\"{}\"' class='img-fluid'>"
                        .format(cutout_path, default_path)})
    player_dict.update({'logo': "<img src='{}' height='30'>"
                       .format(team_logo)})
    player_dict.update({'status_string': status_string})
    player_dict.update({'team_name': player.current_team.fullname})
    player_dict.update({"recent_performance": recent_performance})
    player_dict.update({"week_label": week_label, "week_fps": week_fps})
    player_dict.update({"table_label": table_label})

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


@app.route('/compare', methods=["GET", "POST"])
def compare():

    games = Game.query.all()
    current_week, preseason = get_week(games)

    teams = Team.query.all()
    players = Player.query.filter(Player.team_id != 100).all()
    players = [player for player in players if player.position in ['QB', 'RB', 'WR', 'TE']]
    scoring = Scoring.query.filter_by(ID=0).first()

    comparing = []
    if request.method == "POST":
        if "addPlayer" in request.form:
            player_id, list = request.form.get("addPlayer").split("-")

            list = list.replace("[", "")
            list = list.replace("]", "")
            list = list.split(",") if list else []

            comparing = list if list else []
            comparing = [int(p) for p in comparing]
            comparing.append(int(player_id))

        else:
            player_id, list = request.form.get("dropPlayer").split("-")

            list = list.replace("[", "")
            list = list.replace("]", "")
            list = list.split(", ") if list else []
            list = [int(p) for p in list]
            list.remove(int(player_id))
            comparing = list

    default_headshot_path = url_for('static', filename='headshots/default.png')

    return render_template("compare.html",
                           current_week=current_week,
                           preseason=preseason,
                           teams=teams,
                           Player=Player,
                           players=players,
                           scoring=scoring,
                           comparing=comparing,
                           default_headshot_path=default_headshot_path)


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

    thread.state = "Setting Depth Charts"
    db_utils.set_depth_charts(db, thread)
    db.session.commit()

    thread.state = "Getting Team Transactions"
    db_utils.get_team_transactions(db, thread)
    db.session.commit()

    print("Updating Rosters")
    return jsonify("Done")


@app.route('/updateStats')
def update_stats():
    games = Game.query.all()
    current_week, preseason = get_week(games)

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
    db_utils.update_team_stats(db, thread, preseason)
    thread.state = "Updating Team Rankings"
    db_utils.update_rankings(db, thread, preseason)
    thread.state = "Updating DVOA Rankings"
    db_utils.update_dvoa_rankings()
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
    games = Game.query.all()
    current_week, preseason = get_week(games)

    thread_id = int(request.args.get('id'))
    global update_threads
    update_threads[thread_id].state = "STARTED"
    update_threads[thread_id].start()

    db_utils.update_db(db, update_threads[thread_id], preseason)
    db.session.commit()
    print("Updating Database")
    return jsonify("Done")


@app.route('/rebuildDatabase')
def rebuild_database():
    games = Game.query.all()
    current_week, preseason = get_week(games)
    
    thread_id = int(request.args.get('id'))
    global update_threads
    thread = update_threads[thread_id]
    thread.state = "STARTED"
    thread.start()

    thread.state = "Rebuilding Database"
    db_utils.build_db(db, thread, preseason)
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
