from flask import Flask, render_template, request, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import os
import zulu
import logging

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
from NFLCheatSheet.lib.classes.stats import SeasonStats, WeeklyStats, get_stats_leaders


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

        m = Game.query.filter_by(week=week)

        if preseason:
            m = [matchup for matchup in m if matchup.preseason]
        else:
            m = [matchup for matchup in m if not matchup.preseason]

        bye_teams = Team.query.filter_by(bye=week).all()

        m = sort(m)

        # Render Times
        for match in m:
            if match.date not in ["TBD", "Final"]:
                dt = zulu.parse(match.date, '%Y-%m-%dT%H:%MZ')
                match.date = dt.format('%a %b %d, %Y %I:%M %p', 'local')

        return render_template("matchups.html", teams=teams, week=week, week_string=week_string,
                               matchups=m, bye_teams=bye_teams)


@app.route('/matchup', methods=["GET", "POST"])
def matchup():

    if request.method == "GET":

        ID = request.args.get('matchup')
        game = Game.query.get(ID)

        teams = Team.query.all()

        if game.completed:

            away_team_line_score = game.away_team_line_score.split(" ")
            home_team_line_score = game.home_team_line_score.split(" ")

            pass_stats = sorted([stats for stats in game.stats if stats.passer], reverse=True)
            rush_stats = sorted([stats for stats in game.stats if stats.rusher], reverse=True)
            rec_stats = sorted([stats for stats in game.stats if stats.receiver], reverse=True)

            players = []
            for stats in game.stats:
                players.append(stats.player)

            week_leaders = get_stats_leaders(players, game.week)
            default_headshot_path = url_for('static', filename='headshots/default.png')

            return render_template("boxscore.html", teams=teams, matchup=game,
                                   pass_stats=pass_stats, rush_stats=rush_stats,
                                   rec_stats=rec_stats, als=away_team_line_score,
                                   hls=home_team_line_score, week_leaders=week_leaders,
                                   default_headshot_path=default_headshot_path)

        else:
            if game.date not in ["TBD", "Final"]:
                dt = zulu.parse(game.date, '%Y-%m-%dT%H:%MZ')
                date = dt.format('%m/%d', 'local')
                time = dt.format('%I:%M %p %Z', 'local').lstrip("0")

            else:
                if game.completed:
                    date = "Final"
                    time = ""
                else:
                    date = "TBD"
                    time = ""

            home_leaders = get_stats_leaders(game.home_team.players)
            away_leaders = get_stats_leaders(game.away_team.players)

            default_headshot_path = url_for('static', filename='headshots/default.png')

            return render_template("matchup.html", teams=teams, matchup=game, date=date, time=time,
                                   home_leaders=home_leaders, away_leaders=away_leaders,
                                   default_headshot_path=default_headshot_path)


@app.route('/team', methods=["GET", "POST"])
def team():

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

        team_leaders = get_stats_leaders(team.players)

        default_headshot_path = url_for('static', filename='headshots/default.png')

        stats = [stats for player in team.players for stats in player.season_stats if
                 stats.preseason]

        return render_template("team.html", teams=teams, players=players, team=team, stats=stats,
                               position=position, schedule=schedule, preschedule=preschedule,
                               team_leaders=team_leaders,
                               default_headshot_path=default_headshot_path)


@app.route('/player', methods=["GET", "POST"])
def player():
    player_id = int(request.args.get('id'))
    player = Player.query.get(player_id)
    team = player.current_team

    player_dict = player.as_dict()
    ps = [stats for stats in player.season_stats if stats.preseason][0]
    player_dict.update(ps.as_dict())

    cutout_path = url_for('static', filename='headshots/{}.png'.format(player.ID))
    default_path = url_for('static', filename='headshots/default.png')

    team_logo = url_for('static', filename='logos/{}.png'.format(player.current_team.key))
    status = player.designation
    if status:
        if status in ['Questionable', 'Doubtful']:
            status_string = '<span class="badge rounded-pill bg-warning">{} - {}</span>'\
                .format(player.designation, player.injury)
        else:
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
