from app import db


class FantasyLeague(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    number_teams = db.Column(db.Integer)
    teams = db.relationship('FantasyTeam', backref='league', foreign_keys="FantasyTeam.league_id", lazy=True)

    def __repr__(self):
        return "League({}-{})".format(self.name, self.ID)
