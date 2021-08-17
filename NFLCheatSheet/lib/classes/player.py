from app import db
from NFLCheatSheet.lib.scrape.status import player_status_from_id
from NFLCheatSheet.lib.scrape.stats import get_recent_stats, get_career_stats

import json


class Player(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    rotowireID = db.Column(db.Integer, unique=True)
    yahooPlayerID = db.Column(db.Integer, unique=True)

    name = db.Column(db.String(40), nullable=False)
    fname = db.Column(db.String(20), nullable=False)
    lname = db.Column(db.String(20), nullable=False)

    height = db.Column(db.String(6))
    weight = db.Column(db.Integer)
    age = db.Column(db.Integer)
    experience = db.Column(db.Integer)
    experience_string = db.Column(db.String(9))

    number = db.Column(db.Integer)
    position = db.Column(db.String(4))
    position_group = db.Column(db.String(3))

    team = db.Column(db.String(5))
    team_id = db.Column(db.Integer, db.ForeignKey('team.ID'))
    bye = db.Column(db.Integer)
    college = db.Column(db.String(20))

    status = db.Column(db.String(15))
    designation = db.Column(db.String(25))
    injury = db.Column(db.String(10))
    ret = db.Column(db.String(10))

    season_stats = db.relationship('SeasonStats', back_populates='player')
    weekly_stats = db.relationship('WeeklyStats', back_populates='player')

    def __repr__(self):

        return "Player({}-{})".format(self.name, self.position)

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    def update_status(self):

        status = player_status_from_id(self.rotowireID)
        if status:
            self.status = status.get('status')
            self.designation = status.get('designation')
            self.injury = status.get('injury')

        else:
            self.status = 'Active'

        return

    def update_stats(self, stat_type: str = "Recent"):

        if stat_type == "Recent":
            stats = get_recent_stats(self.fname, self.lname, self.position)
        else:
            stats = get_career_stats(self.fname, self.lname, self.position)

        if stats:

            stats_string = json.dumps(stats)
            self.recent_stats = stats_string

    def get_weekly_points(self, scoring, week: int):

        recent_stats = json.loads(self.recent_stats)
        week = str(week)

        week_stats = recent_stats.get(week)
        points = 0
        if week_stats:
            points = scoring.get_points(week_stats)

        return points
