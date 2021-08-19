from app import db


class Team(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(3), unique=True)

    location = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    fullname = db.Column(db.String(40), nullable=False)

    conference = db.Column(db.String(3))
    division = db.Column(db.String(5))

    bye = db.Column(db.Integer)

    hc = db.Column(db.String(30))
    dc = db.Column(db.String(30))
    oc = db.Column(db.String(30))

    primary = db.Column(db.String(6))
    secondary = db.Column(db.String(6))
    tertiary = db.Column(db.String(6))

    logo = db.Column(db.String(100))
    wordmark = db.Column(db.String(100))

    stadium = db.Column(db.String(30))
    stadium_city = db.Column(db.String(30))
    stadium_state = db.Column(db.String(2))

    wins = db.Column(db.Integer)
    loses = db.Column(db.Integer)
    ties = db.Column(db.Integer)
    winPCT = db.Column(db.Integer)

    preseason_wins = db.Column(db.Integer)
    preseason_loses = db.Column(db.Integer)
    preseason_ties = db.Column(db.Integer)

    players = db.relationship('Player', backref='current_team', foreign_keys="Player.team_id", lazy=True)
    prev_players = db.relationship('Player', backref='previous_team', foreign_keys="Player.prev_team_id", lazy=True)

    away_games = db.relationship('Game', foreign_keys="Game.away_team_id")
    home_games = db.relationship('Game', foreign_keys="Game.home_team_id")

    weekly_stats = db.relationship('WeeklyStats', back_populates='team')
    stats = db.relationship('TeamStats', back_populates='team')

    def __repr__(self):

        return "Team({})".format(self.fullname)
