from app import db


class FantasyTeam(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('fantasy_league.ID'))
    name = db.Column(db.String(30))
    players = db.Column(db.String(300))

    def __repr__(self):
        return "FantasyTeam({}-{})".format(self.name, self.ID)
