from app import db


class FantasyLeague(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(30))
    size = db.Column(db.Integer)
    teams = db.relationship('FantasyTeam', backref='league', foreign_keys="FantasyTeam.league_id", lazy=True)

    # Roster Information
    QB = db.Column(db.Integer, default=0)
    RB = db.Column(db.Integer, default=0)
    WR = db.Column(db.Integer, default=0)
    TE = db.Column(db.Integer, default=0)
    RBWR = db.Column(db.Integer, default=0)
    WRTE = db.Column(db.Integer, default=0)
    RBTE = db.Column(db.Integer, default=0)
    FLEX = db.Column(db.Integer, default=0)
    SFLEX = db.Column(db.Integer, default=0)
    DST = db.Column(db.Integer, default=0)
    K = db.Column(db.Integer, default=0)
    BENCH = db.Column(db.Integer, default=0)
    IR = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "League({}-{})".format(self.name, self.ID)
