from owner import Owner
from player_orig import Player
from typing import Type


class FantasyTeam:

    def __init__(self, name: str, owner: Type[Owner]):

        self.id = 0 # TBD how to implement unique ID
        self.name = name
        self.owner = owner
        self.roster = []
        self.reserve = []

    def getRosterSize(self) -> int:

        return len(self.roster)

    def getNumberOfPos(self, position) -> int:

        count = 0
        for player in self.roster:
            if player.Position == position:
                count += count

        return count

    def addPlayer(self, player: Type[Player]):

        self.roster.append(player)

    def dropPlayer(self, player: Type[Player]):

        self.roster.remove(player)
