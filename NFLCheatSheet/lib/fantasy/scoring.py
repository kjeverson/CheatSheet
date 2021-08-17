from app import db


class Scoring(db.Model):

    ID = db.Column(db.Integer, primary_key=True)

    # Allow Fractional Points
    fractional = db.Column(db.Boolean)

    # Standard Passing Scoring
    passYDs = db.Column(db.Integer)
    passTDs = db.Column(db.Integer)
    passINTs = db.Column(db.Integer)
    pass2PTs = db.Column(db.Integer)
    passSacks = db.Column(db.Integer)
    passAtts = db.Column(db.Integer)
    passComps = db.Column(db.Integer)
    passIncs = db.Column(db.Integer)

    # Bonus Passing Scoring
    pass40TD = db.Column(db.Integer)
    pass50TD = db.Column(db.Integer)
    passOver300Yards = db.Column(db.Integer)
    passOver400Yards = db.Column(db.Integer)

    # Standard Rushing Scoring
    rushYDs = db.Column(db.Integer)
    rushTDs = db.Column(db.Integer)
    rush2PT = db.Column(db.Integer)
    rushAtts = db.Column(db.Integer)

    # Bonus Rushing Scoring
    rush40TD = db.Column(db.Integer)
    rush50TD = db.Column(db.Integer)
    rushOver100Yards = db.Column(db.Integer)
    rushOver200Yards = db.Column(db.Integer)

    # Standard Receiving Scoring
    recs = db.Column(db.Integer)
    recYDs = db.Column(db.Integer)
    recTDs = db.Column(db.Integer)
    rec2PT = db.Column(db.Integer)

    # Bonus Receiving Scoring
    rec40TD = db.Column(db.Integer)
    rec50TD = db.Column(db.Integer)
    recOver100Yards = db.Column(db.Integer)
    recOver200Yards = db.Column(db.Integer)

    # Fumble Scoring
    fumLost = db.Column(db.Integer)
    fum = db.Column(db.Integer)
    fumRecTD = db.Column(db.Integer)


def get_score(scoring, week_stats):

    score = 0
    if week_stats.passer:
        score += week_stats.passYDs / scoring.passYDs
        score += week_stats.passTDs * scoring.passTDs
        score += week_stats.passINTs * scoring.passINTs
        #score += week_stats.pass2PTs * scoring.pass2PTs
        score += week_stats.passSacks * scoring.passSacks
        score += week_stats.passAtts * scoring.passAtts
        score += week_stats.passComps * scoring.passComps
        score += (week_stats.passComps - week_stats.passAtts) * scoring.passIncs

        if 300 < week_stats.passYDs < 400:
            score += scoring.passOver300Yards

        if week_stats.passYDs > 400:
            score += scoring.passOver400Yards

    if week_stats.rusher:
        score += week_stats.rushYDs / scoring.rushYDs
        score += week_stats.rushTDs * scoring.rushTDs
        score += week_stats.rushAtts * scoring.rushAtts

        if 100 < week_stats.rushYDs < 200:
            score += scoring.rushOver100Yards

        if week_stats.rushYDs > 200:
            score += scoring.rushOver200Yards

    if week_stats.receiver:
        score += week_stats.recs * scoring.recs
        score += week_stats.recYDs / scoring.recYDs
        score += week_stats.recTDs * scoring.recTDs

        if 100 < week_stats.recYDs < 200:
            score += scoring.recOver100Yards

        if week_stats.recYDs > 200:
            score += scoring.recOver200Yards

    return score
