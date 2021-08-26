from app import db


class SeasonStats(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.ID'), nullable=False)
    player = db.relationship('Player', back_populates='season_stats', uselist=False)

    preseason = db.Column(db.Boolean)

    gamesPlayed = db.Column(db.Integer, default=0)

    # Passing
    passComps = db.Column(db.Integer, default=0)
    passAtts = db.Column(db.Integer, default=0)
    passYDs = db.Column(db.Integer, default=0)
    passYDsPerGame = db.Column(db.Integer, default=0)
    passAVG = db.Column(db.Integer, default=0)
    passTDs = db.Column(db.Integer, default=0)
    passINTs = db.Column(db.Integer, default=0)
    passSacks = db.Column(db.Integer, default=0)
    passSackYDs = db.Column(db.Integer, default=0)
    passRTG = db.Column(db.Integer, default=0)

    # Rushing
    rushAtts = db.Column(db.Integer, default=0)
    rushYDs = db.Column(db.Integer, default=0)
    rushYDsPerGame = db.Column(db.Integer, default=0)
    rushAVG = db.Column(db.Integer, default=0)
    rushTDs = db.Column(db.Integer, default=0)
    rushLng = db.Column(db.Integer, default=0)

    # Receiving
    recs = db.Column(db.Integer, default=0)
    recYDs = db.Column(db.Integer, default=0)
    recYDsPerGame = db.Column(db.Integer, default=0)
    recAVG = db.Column(db.Integer, default=0)
    recTDs = db.Column(db.Integer, default=0)
    recLng = db.Column(db.Integer, default=0)
    recTGTS = db.Column(db.Integer, default=0)

    # Fumbles
    fumLost = db.Column(db.Integer, default=0)
    fum = db.Column(db.Integer, default=0)

    # Fantasy
    FPs = db.Column(db.Integer, default=0)

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}


class WeeklyStats(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.ID'), nullable=False)
    player = db.relationship('Player', back_populates='weekly_stats', uselist=False)
    game_id = db.Column(db.Integer, db.ForeignKey('game.ID'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.ID'), nullable=False)
    team = db.relationship('Team', back_populates='weekly_stats')

    week = db.Column(db.Integer)
    preseason = db.Column(db.Boolean)
    counted = db.Column(db.Boolean)

    # Passing
    passer = db.Column(db.Boolean)
    passComps = db.Column(db.Integer, default=0)
    passAtts = db.Column(db.Integer, default=0)
    passYDs = db.Column(db.Integer, default=0)
    passAVG = db.Column(db.Integer, default=0)
    passTDs = db.Column(db.Integer, default=0)
    passINTs = db.Column(db.Integer, default=0)
    passSacks = db.Column(db.Integer, default=0)
    passSackYDs = db.Column(db.Integer, default=0)
    passRTG = db.Column(db.Integer, default=0)

    # Rushing
    rusher = db.Column(db.Boolean)
    rushAtts = db.Column(db.Integer, default=0)
    rushYDs = db.Column(db.Integer, default=0)
    rushAVG = db.Column(db.Integer, default=0)
    rushTDs = db.Column(db.Integer, default=0)
    rushLng = db.Column(db.Integer, default=0)

    # Receiving
    receiver = db.Column(db.Boolean)
    recs = db.Column(db.Integer, default=0)
    recYDs = db.Column(db.Integer, default=0)
    recAVG = db.Column(db.Integer, default=0)
    recTDs = db.Column(db.Integer, default=0)
    recLng = db.Column(db.Integer, default=0)
    recTGTS = db.Column(db.Integer, default=0)

    # Fumbles
    fumLost = db.Column(db.Integer, default=0)
    fum = db.Column(db.Integer, default=0)
    fumRec = db.Column(db.Integer, default=0)

    # Defense
    defender = db.Column(db.Boolean)
    totalTackles = db.Column(db.Integer, default=0)
    soloTackles = db.Column(db.Integer, default=0)
    sacks = db.Column(db.Integer, default=0)
    tacklesForLoss = db.Column(db.Integer, default=0)
    passDefensed = db.Column(db.Integer, default=0)
    qbHits = db.Column(db.Integer, default=0)
    defTDs = db.Column(db.Integer, default=0)
    defINTs = db.Column(db.Integer, default=0)
    defINTYDs = db.Column(db.Integer, default=0)

    # Kick Returns
    krAtts = db.Column(db.Integer, default=0)
    krYDs = db.Column(db.Integer, default=0)
    krAVG = db.Column(db.Integer, default=0)
    krLng = db.Column(db.Integer, default=0)
    krTDs = db.Column(db.Integer, default=0)

    # Punt Returns
    prAtts = db.Column(db.Integer, default=0)
    prYDs = db.Column(db.Integer, default=0)
    prAVG = db.Column(db.Integer, default=0)
    prLng = db.Column(db.Integer, default=0)
    prTDs = db.Column(db.Integer, default=0)

    # Kicking
    fgMade = db.Column(db.Integer, default=0)
    fgAtts = db.Column(db.Integer, default=0)
    fgPCT = db.Column(db.Integer, default=0)
    xpMade = db.Column(db.Integer, default=0)
    xpAtts = db.Column(db.Integer, default=0)
    points = db.Column(db.Integer, default=0)

    # Punting
    punts = db.Column(db.Integer, default=0)
    puntYDs = db.Column(db.Integer, default=0)
    puntAVG = db.Column(db.Integer, default=0)
    puntTB = db.Column(db.Integer, default=0)
    puntIn20 = db.Column(db.Integer, default=0)
    puntLng = db.Column(db.Integer, default=0)

    # Fantasy Points
    FPs = db.Column(db.Integer, default=0)

    def as_dict(self):
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    def __lt__(self, other):

        if self.passer and other.passer:
            return self.passYDs < other.passYDs

        elif self.rusher and other.rusher:
            return self.rushYDs < other.rushYDs

        elif self.receiver and other.receiver:
            return self.recYDs < other.recYDs

        else:
            return self.FPs < other.FPs


class TeamStats(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.ID'), nullable=False)
    team = db.relationship('Team', back_populates='stats', uselist=False)

    preseason = db.Column(db.Boolean)

    DVOA = db.Column(db.Integer, default=0)
    OFF = db.Column(db.Integer, default=0)
    DEF = db.Column(db.Integer, default=0)
    ST = db.Column(db.Integer, default=0)

    PPG = db.Column(db.Integer, default=0)
    pointsFor = db.Column(db.Integer, default=0)
    PAPG = db.Column(db.Integer, default=0)
    pointsAgainst = db.Column(db.Integer, default=0)
    totalYards = db.Column(db.Integer, default=0)

    passComps = db.Column(db.Integer, default=0)
    passAtts = db.Column(db.Integer, default=0)
    passYDs = db.Column(db.Integer, default=0)
    passTDs = db.Column(db.Integer, default=0)
    passINTs = db.Column(db.Integer, default=0)
    passSacks = db.Column(db.Integer, default=0)
    passSackYDs = db.Column(db.Integer, default=0)

    rushAtts = db.Column(db.Integer, default=0)
    rushYDs = db.Column(db.Integer, default=0)
    rushTDs = db.Column(db.Integer, default=0)

    recs = db.Column(db.Integer, default=0)
    recYDs = db.Column(db.Integer, default=0)
    recTDs = db.Column(db.Integer, default=0)
    recTGTS = db.Column(db.Integer, default=0)

    passingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    rushingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))
    receivingLeader_id = db.Column(db.Integer, db.ForeignKey('player.ID'))

    passAVG = db.Column(db.Integer, default=0)
    passYDsPerGame = db.Column(db.Integer, default=0)
    rushAVG = db.Column(db.Integer, default=0)
    rushYDsPerGame = db.Column(db.Integer, default=0)
    recAVG = db.Column(db.Integer, default=0)

    PPGRank = db.Column(db.Integer, default=0)
    PAPGRank = db.Column(db.Integer, default=0)
    passYDsPerGameRank = db.Column(db.Integer, default=0)
    rushYDsPerGameRank = db.Column(db.Integer, default=0)
    passYDsRank = db.Column(db.Integer, default=0)
    rushYDsRank = db.Column(db.Integer, default=0)


def get_stats_leaders(players, week=None):

    if not players:
        return None

    passYDs_leader = None
    passYDs_leader_stats = None
    passYDs = 0
    rushYDs_leader = None
    rushYDs_leader_stats = None
    rushYDs = 0
    recYDs_leader = None
    recYDs_leader_stats = None
    recYDs = 0

    for player in players:

        if week:
            stats = WeeklyStats.query.filter_by(player_id=player.ID).filter_by(preseason=True).all()
            stats = [stat for stat in stats if stat.game.week == week]
            if not stats:
                continue
            else:
                stats = stats[-1]
        else:
            stats = SeasonStats.query.filter_by(player_id=player.ID)\
                .filter_by(preseason=True).first()

        if not passYDs_leader:
            passYDs_leader = player
            passYDs_leader_stats = stats
            passYDs = stats.passYDs

        else:
            if stats.passYDs > passYDs_leader_stats.passYDs:
                passYDs_leader = player
                passYDs_leader_stats = stats
                passYDs = stats.passYDs

        if not rushYDs_leader:
            rushYDs_leader = player
            rushYDs_leader_stats = stats
            rushYDs = stats.rushYDs

        else:
            if stats.rushYDs > rushYDs_leader_stats.rushYDs:
                rushYDs_leader = player
                rushYDs_leader_stats = stats
                rushYDs = stats.rushYDs

        if not recYDs_leader:
            recYDs_leader = player
            recYDs_leader_stats = stats
            recYDs = stats.recYDs

        else:
            if stats.recYDs > recYDs_leader_stats.recYDs:
                recYDs_leader = player
                recYDs_leader_stats = stats
                recYDs = stats.recYDs

    if passYDs == 0:
        passYDs_leader = None

    if rushYDs == 0:
        rushYDs_leader = None

    if recYDs == 0:
        recYDs_leader = None

    return passYDs_leader.ID, rushYDs_leader.ID, recYDs_leader.ID


def get_passer_rating(passAtts, passComps, passYDs, passTDs, passINTs):

    a = passComps/passAtts - 0.3 * 5
    b = passYDs / passAtts - 3 * 0.25
    c = passTDs/passAtts * 20
    d = 2.375 - passINTs/passAtts * 25

    if a > 2.375:
        a = 2.375

    if a < 0:
        a = 0

    if b > 2.375:
        b = 2.375

    if b < 0:
        b = 0

    if c > 2.375:
        c = 2.375

    if c < 0:
        c = 0

    if d > 2.375:
        d = 2.375

    if d < 0:
        d = 0

    return a + b + c + d /6 * 100
