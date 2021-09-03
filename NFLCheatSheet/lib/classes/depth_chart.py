from app import db


class DepthChart(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.ID'))
    
    # Offense
    QBs = db.Column(db.String(40))
    RBs = db.Column(db.String(40))
    FBs = db.Column(db.String(40))
    WR1s = db.Column(db.String(40))
    WR2s = db.Column(db.String(40))
    WR3s = db.Column(db.String(40))
    TEs = db.Column(db.String(40))
    LTs = db.Column(db.String(40))
    LGs = db.Column(db.String(40))
    Cs = db.Column(db.String(40))
    RGs = db.Column(db.String(40))
    RTs = db.Column(db.String(40))

    # Defense
    base43 = db.Column(db.Boolean)
    base34 = db.Column(db.Boolean)

    LDEs = db.Column(db.String(40))
    LDTs = db.Column(db.String(40))
    RDTs = db.Column(db.String(40))
    RDEs = db.Column(db.String(40))
    WLBs = db.Column(db.String(40))
    MLBs = db.Column(db.String(40))
    SLBs = db.Column(db.String(40))
    LCBs = db.Column(db.String(40))
    RCBs = db.Column(db.String(40))
    SSs = db.Column(db.String(40))
    FSs = db.Column(db.String(40))

    NTs = db.Column(db.String(40))
    LILBs = db.Column(db.String(40))
    RILBs = db.Column(db.String(40))

    # Special Teams
    PKs = db.Column(db.String(40))
    Ps = db.Column(db.String(40))
    Hs = db.Column(db.String(40))
    PRs = db.Column(db.String(40))
    KRs = db.Column(db.String(40))
    LSs = db.Column(db.String(40))