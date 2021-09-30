from app import db


class Transactions(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.ID'))

    date = db.Column(db.String(20))
    transaction = db.Column(db.String(1000))

