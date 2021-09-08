from app import db


class FantasyTeam(db.Model):

    ID = db.Column(db.Integer, primary_key=True)
    league_id = db.Column(db.Integer, db.ForeignKey('fantasy_league.ID'))
    name = db.Column(db.String(30))
    players = db.Column(db.String(300))

    # Starters
    QB = db.Column(db.String(300))
    RB = db.Column(db.String(300))
    WR = db.Column(db.String(300))
    TE = db.Column(db.String(300))
    RBWR = db.Column(db.String(300))
    WRTE = db.Column(db.String(300))
    RBTE = db.Column(db.String(300))
    FLEX = db.Column(db.String(300))
    SFLEX = db.Column(db.String(300))
    DST = db.Column(db.String(300))
    K = db.Column(db.String(300))
    BENCH = db.Column(db.String(300))
    IR = db.Column(db.String(300))

    def __repr__(self):
        return "FantasyTeam({}-{})".format(self.name, self.ID)

    def add_player(self, player_id):
        if self.players:
            player_ids = self.players.split(" ")
            player_ids.append(player_id)
            self.players = " ".join(player_ids)
        else:
            self.players = player_id

    def drop_player(self, player_id):

        if self.players:
            player_ids = self.players.split(" ")
            player_ids.remove(player_id)
            self.players = " ".join(player_ids)
