from app import db
from NFLCheatSheet.lib.classes import stats
import requests
import re


class Team(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(3), unique=True)

    location = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    fullname = db.Column(db.String(40), nullable=False)

    conference = db.Column(db.String(3))
    division = db.Column(db.String(5))

    bye = db.Column(db.Integer, default=0)

    primary = db.Column(db.String(6))
    secondary = db.Column(db.String(6))

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
    depth_chart = db.relationship('DepthChart', backref='team', foreign_keys="DepthChart.team_id", lazy=True, uselist=False)

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
        else:
            games = [game for game in games if not game.preseason]

        if completed:
            games = [game for game in games if game.completed]

        return games

    def get_bye(self):

        games = self.get_games(completed=False, home=True, away=True)
        weeks = [game.week for game in games]
        bye = [week for week in range(1, 19) if week not in weeks]
        return bye[-1]

    def set_depth_chart(self):

        o = {"qb": [], "rb": [], "fb": [], "wr1": [], "wr2": [], "wr3": [], "te": [], "lt": [],
             "lg": [], "c": [], "rg": [], "rt": []}

        d = {"lde": [], "ldt": [], "rdt": [], "rde": [], "wlb": [], "mlb": [], "slb": [],
             "lcb": [], "rcb": [], "ss": [], "fs": [], "nt": [], "lilb": [], "rilb": []}

        st = {"pk": [], "p": [], "h": [], "pr": [], "kr": [], "ls": []}

        url = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2021/teams/{}/depthcharts?lang=en&region=us".format(self.ID)
        data = requests.get(url).json()

        data = data['items']

        offense = []
        defense = []
        special = []
        for unit in data:
            if unit['name'] == "Special Teams":
                special = unit
            elif unit['name'] == "3WR 1TE":
                offense = unit
            elif unit['name'] == "Base 3-4 D" or unit['name'] == "Base 4-3 D":
                defense = unit

        if offense:
            for position, info in offense['positions'].items():
                if position == "wr":
                    athletes = info['athletes']
                    for athlete in athletes:
                        slot = athlete['slot']
                        slot = 3 if slot > 3 else slot
                        ID = re.search(r'athletes\/(\d+)', athlete['athlete']['$ref']).groups()[0]
                        o[position+str(slot)].append(ID)
                else:
                    athletes = info['athletes']
                    for athlete in athletes:
                        ID = re.search(r'athletes\/(\d+)', athlete['athlete']['$ref']).groups()[0]
                        o[position].append(ID)

        if defense:
            for position, info in defense['positions'].items():
                athletes = info['athletes']
                for athlete in athletes:
                    ID = re.search(r'athletes\/(\d+)', athlete['athlete']['$ref']).groups()[0]
                    d[position].append(ID)

        if special:
            for position, info in special['positions'].items():
                athletes = info['athletes']
                for athlete in athletes:
                    ID = re.search(r'athletes\/(\d+)', athlete['athlete']['$ref']).groups()[0]
                    st[position].append(ID)

        depth_chart = self.depth_chart
        depth_chart.QBs = " ".join(o["qb"])
        depth_chart.RBs = " ".join(o["rb"])
        depth_chart.FBs = " ".join(o["fb"])
        depth_chart.WR1s = " ".join(o["wr1"])
        depth_chart.WR2s = " ".join(o["wr2"])
        depth_chart.WR3s = " ".join(o["wr3"])
        depth_chart.TEs = " ".join(o["te"])
        depth_chart.LTs = " ".join(o["lt"])
        depth_chart.LGs = " ".join(o["lg"])
        depth_chart.Cs = " ".join(o["c"])
        depth_chart.RGs = " ".join(o["rg"])
        depth_chart.RTs = " ".join(o["rt"])
        depth_chart.LDEs = " ".join(d["lde"])
        depth_chart.LDTs = " ".join(d["ldt"])
        depth_chart.RDTs = " ".join(d["rdt"])
        depth_chart.RDEs = " ".join(d["rde"])
        depth_chart.WLBs = " ".join(d["wlb"])
        depth_chart.MLBs = " ".join(d["mlb"])
        depth_chart.SLBs = " ".join(d["slb"])
        depth_chart.LCBs = " ".join(d["lcb"])
        depth_chart.RCBs = " ".join(d["rcb"])
        depth_chart.SSs = " ".join(d["ss"])
        depth_chart.FSs = " ".join(d["fs"])
        depth_chart.NTs = " ".join(d["nt"])
        depth_chart.LILBs = " ".join(d["lilb"])
        depth_chart.RILBs = " ".join(d["rilb"])
        depth_chart.PKs = " ".join(st["pk"])
        depth_chart.Ps = " ".join(st["p"])
        depth_chart.Hs = " ".join(st["h"])
        depth_chart.PRs = " ".join(st["pr"])
        depth_chart.KRs = " ".join(st["kr"])
        depth_chart.LSs = " ".join(st["ls"])
