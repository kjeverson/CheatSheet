from app import db
from NFLCheatSheet.lib.classes import stats

import zulu
import json
import requests
from pathlib import Path
from PIL import Image, UnidentifiedImageError
import re


player_url = ("http://sports.core.api.espn.com/v2/sports/football/leagues/"
              "nfl/seasons/2021/athletes/{}?lang=en&region=us")


class Player(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    rotowireID = db.Column(db.Integer, unique=True)
    yahooPlayerID = db.Column(db.Integer, unique=True)

    name = db.Column(db.String(40), nullable=False)
    fname = db.Column(db.String(20), nullable=False)
    lname = db.Column(db.String(20), nullable=False)
    shortname = db.Column(db.String(25), nullable=False)

    height = db.Column(db.String(6))
    weight = db.Column(db.Integer)
    age = db.Column(db.Integer)
    experience = db.Column(db.Integer)
    experience_string = db.Column(db.String(9))

    number = db.Column(db.Integer)
    position = db.Column(db.String(4))

    team_id = db.Column(db.Integer, db.ForeignKey('team.ID'))
    practice_squad = db.Column(db.Boolean)
    college = db.Column(db.String(20))

    status = db.Column(db.String(15))
    designation = db.Column(db.String(25))
    injury = db.Column(db.String(10))
    ret = db.Column(db.String(10))
    news = db.Column(db.String(250))
    analysis = db.Column(db.String(2000))
    date = db.Column(db.String(25))

    draft_year = db.Column(db.Integer, default=0)
    draft_round = db.Column(db.Integer, default=0)
    draft_pick = db.Column(db.Integer, default=0)
    draft_team_id = db.Column(db.Integer)
    undrafted = db.Column(db.Boolean)

    season_stats = db.relationship('SeasonStats', back_populates='player')
    weekly_stats = db.relationship('WeeklyStats', back_populates='player')

    def __repr__(self):

        return "Player({}-{})".format(self.name, self.position)

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    def get_season_stats(self, preseason):

        return stats.SeasonStats.query.filter_by(
            player_id=self.ID).filter_by(preseason=preseason).first()

    def get_weekly_stats(self, game):

        return stats.WeeklyStats.query.filter_by(
            player_id=self.ID).filter_by(game_id=game.ID).first()

    def get_weekly_stats_by_week(self, preseason=False, week=None):
        return stats.WeeklyStats.query.filter_by(player_id=self.ID).filter_by(preseason=preseason).filter_by(week=str(week)).first()

    def get_weekly_stats_list(self, preseason):

        return stats.WeeklyStats.query.filter_by(
            player_id=self.ID).filter_by(preseason=preseason).all()

    def update_info(self, player_data):
        
        if player_data['status']['abbreviation'] == "FA":
            team_id = 100
        else:
            team_id = int(re.search(r'teams\/(\d+)', player_data['team']['$ref']).groups()[0])

        if player_data['status']['name'] == "Practice Squad":
            practice_squad = True
        else:
            practice_squad = False

        self.name = player_data['fullName']
        self.fname = player_data['firstName']
        self.lname = player_data['lastName']
        self.shortname = player_data['shortName']
        self.height = player_data['displayHeight']
        self.weight = player_data['weight']
        self.age = player_data['age'] if player_data.get('age') else 0
        self.experience = player_data['experience']['years']
        self.experience_string = get_experience_string(self.experience)
        self.number = player_data['jersey'] if player_data.get('jersey') else 0
        self.position = player_data['position']['abbreviation']
        self.team_id = team_id
        self.practice_squad = practice_squad

    def update_status(self):

        url = player_url.format(self.ID)

        data = requests.get(url).json()
        injuries = data.get('injuries')
        if injuries:

            description = injuries[0]['type']['description']
            if description == "questionable":
                self.status = "Q"
                self.designation = "Questionable"
            elif description == "Injured Reserve":
                self.status = "IR"
                self.designation = "Injured Reserve"
            elif description == "out":
                self.status = "O"
                self.designation = "Out"
            elif description == "Suspension":
                self.status = "SUS"
                self.designation = "Suspension"
            else:
                self.status = "O"
                self.designation = "Out"

            try:
                self.injury = injuries[0]['details']['type']
            except KeyError:
                self.injury = ""

            self.date = injuries[0]['date']
            if len(injuries[0]['shortComment'].split()) == 1:
                self.news = "{} was listed as {} on {}."\
                    .format(self.name, self.designation,
                            self.get_injury_date().strftime('%B %d'))
                self.analysis = self.news
            else:
                self.news = injuries[0]['shortComment']
                self.analysis = injuries[0]['longComment']

            try:
                self.ret = injuries[0]['details']['returnDate']
            except KeyError:
                self.ret = ""

        else:
            self.status = 'Active'
            self.designation = 'Active'
            self.news = ""
            self.analysis = ""
            self.ret = ""

        return

    def get_weekly_points(self, scoring, week: int):

        recent_stats = json.loads(self.recent_stats)
        week = str(week)

        week_stats = recent_stats.get(week)
        points = 0
        if week_stats:
            points = scoring.get_points(week_stats)

        return points

    def get_headshot(self):

        url = player_url.format(self.ID)

        data = requests.get(url).json()
        image = data.get('headshot')
        if image:
            image = image['href']

            img_path = Path("/Users/everson/NFLCheatSheet/static/headshots/{}.png".format(self.ID))
            if img_path.exists():
                return

            image_data = requests.get(image, stream=True)
            with img_path.open('wb') as image_file:
                try:
                    image = Image.open(image_data.raw)
                    image.save(image_file)
                except UnidentifiedImageError:
                    pass

    def get_injury_date(self):
        dt = zulu.parse(self.date)
        dt = dt.astimezone(tz="local")
        return dt


def get_experience_string(experience):

    if experience == 0:
        return "Rookie Season"

    experience = str(experience)

    if experience[-1] == '1' and experience != '11':
        return experience + "st Season"

    elif experience[-1] == '2' and experience != '12':
        return experience + "nd Season"

    elif experience[-1] == '3' and experience != '13':
        return experience + "rd Season"

    else:
        return experience + "th Season"


def get_player(player_id):

    return Player.query.get(player_id)


def add_player(db, player_data):

    if player_data.get('draft'):
        undrafted = False
        draftYear = player_data['draft']['year']
        draftRound = player_data['draft']['round']
        draftPick = player_data['draft']['selection']
        draft_team_id = int(re.search(r'teams\/(\d+)', player_data['draft']['team']['$ref']).groups()[0])
    else:
        undrafted = True
        draftYear = ""
        draftRound = ""
        draftPick = ""
        draft_team_id = ""

    if player_data['status']['abbreviation'] == "FA":
        team_id = 100
    else:
        try:
            team_id = int(re.search(r'teams\/(\d+)', player_data['team']['$ref']).groups()[0])
        except KeyError as error:
            print(player_data['fullName'])
            team_id = 100
    try:
        college = requests.get(player_data['college']['$ref']).json()['name']
    except KeyError:
        college = ""

    if player_data['status']['name'] == "Practice Squad":
        practice_squad = True
    else:
        practice_squad = False

    db.session.add(Player(
        ID=player_data['id'],
        name=player_data['fullName'],
        fname=player_data['firstName'],
        lname=player_data['lastName'],
        shortname=player_data['shortName'],
        height=player_data['displayHeight'],
        weight=player_data['weight'],
        age=player_data['age'] if player_data.get('age') else 0,
        experience=player_data['experience']['years'],
        experience_string=get_experience_string(player_data['experience']['years']),
        number=player_data['jersey'] if player_data.get('jersey') else 0,
        position=player_data['position']['abbreviation'],
        team_id=team_id,
        college=college,
        status="",
        designation="",
        injury="",
        ret="",
        undrafted=undrafted,
        draft_year=draftYear if draftYear else 0,
        draft_round=draftRound if draftRound else 0,
        draft_pick=draftPick if draftPick else 0,
        draft_team_id=draft_team_id if draft_team_id else 0,
        practice_squad=practice_squad
    ))

    db.session.add(stats.SeasonStats(
        player_id=player_data['id'],
        preseason=False,
    ))

    db.session.add(stats.SeasonStats(
        player_id=player_data['id'],
        preseason=True,
    ))

    db.session.commit()
