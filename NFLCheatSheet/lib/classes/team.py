from app import db
from NFLCheatSheet.lib.classes import stats
from NFLCheatSheet.lib.classes.game import Game


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

    games_played = db.Column(db.Integer)
    wins = db.Column(db.Integer)
    loses = db.Column(db.Integer)
    ties = db.Column(db.Integer)
    winPCT = db.Column(db.Integer)

    preseason_games_played = db.Column(db.Integer)
    preseason_wins = db.Column(db.Integer)
    preseason_loses = db.Column(db.Integer)
    preseason_ties = db.Column(db.Integer)
    preseasonWinPCT = db.Column(db.Integer)

    players = db.relationship('Player', backref='current_team', foreign_keys="Player.team_id", lazy=True)

    away_games = db.relationship('Game', foreign_keys="Game.away_team_id")
    home_games = db.relationship('Game', foreign_keys="Game.home_team_id")

    weekly_stats = db.relationship('WeeklyStats', back_populates='team')
    stats = db.relationship('TeamStats', back_populates='team')

    def __repr__(self):

        return "Team({})".format(self.fullname)

    def get_team_stats(self, preseason):

        return stats.TeamStats.query.filter_by(
            team_id=self.ID).filter_by(preseason=preseason).first()

    def get_week_stats(self, preseason):

        return stats.WeeklyStats.query.filter_by(
            team_id=self.ID).filter_by(preseason=preseason).all()

    def get_games(self, preseason=False, completed=True, home=False, away=False):

        games = []
        if home:
            games.extend(self.home_games)

        if away:
            games.extend(self.away_games)

        if preseason:
            games = [game for game in games if game.preseason]

        if completed:
            games = [game for game in games if game.completed]

        return games