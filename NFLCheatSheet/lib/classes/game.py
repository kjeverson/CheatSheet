from app import db
from NFLCheatSheet.lib.scrape import boxscore
import zulu


class Game(db.Model):

    # ESPN Game ID
    ID = db.Column(db.Integer, primary_key=True)
    week = db.Column(db.Integer)
    date = db.Column(db.String(17))
    time = db.Column(db.String(15))
    preseason = db.Column(db.Boolean)

    home_team_id = db.Column(db.Integer, db.ForeignKey('team.ID'))
    home_team = db.relationship("Team", foreign_keys="Game.home_team_id", viewonly=True)
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.ID'))
    away_team = db.relationship("Team", foreign_keys="Game.away_team_id", viewonly=True)

    completed = db.Column(db.Boolean)
    overtime = db.Column(db.Boolean)

    stats = db.relationship('WeeklyStats', backref='game', lazy=True, viewonly=True)
    scraped_stats = db.Column(db.Boolean)

    away_team_score = db.Column(db.Integer)
    home_team_score = db.Column(db.Integer)
    away_team_line_score = db.Column(db.String(15))
    home_team_line_score = db.Column(db.String(15))

    winner = db.Column(db.String(3))

    passingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    rushingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    receivingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))

    awayPassingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    awayRushingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    awayReceivingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))

    homePassingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    homeRushingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    homeReceivingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))

    def __repr__(self):

        return "Game(Week {}: {} vs. {})".format(self.week,
                                                 self.home_team.name, self.away_team.name)

    def __lt__(self, other):

        if self.date not in ["TBD", "Final"]:
            if other.date not in ["TBD", "Final"]:
                return self.get_time() < other.get_time()
            else:
                return False
        else:
            return False

    def get_time(self):
        dt = zulu.parse(self.date)
        dt = dt.astimezone(tz="local")
        return dt

    def is_complete(self):

        # Check if completed if not completed...
        if not self.completed:
            result = boxscore.is_completed(self.ID)
            if result == "Final":
                self.completed = True
                self.overtime = False
            elif result == "Final/OT":
                self.completed = True
                self.overtime = True
            else:
                self.completed = False
                self.overtime = False

        return self.completed


def sort(matches):

    m_final = [match for match in matches if match.date == "Final"]
    m_TBD = [match for match in matches if match.date == "TBD"]
    m = [match for match in matches if match.date not in ["TBD", "Final"]]

    m = sorted(m)
    m_final.extend(m)
    m_final.extend(m_TBD)
    m = m_final

    return m


def get_week(games):

    now = zulu.now().datetime
    closest_game = min(games, key=lambda x: abs(x.get_time()-now))

    return closest_game.week, closest_game.preseason
