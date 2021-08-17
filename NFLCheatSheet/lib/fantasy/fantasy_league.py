from typing import Type
from fantasy_team import FantasyTeam


class FantasyLeague:

    def __init__(self, name):

        self.name = name
        self.teams = []
        self.players = []

    def addTeam(self, team: Type[FantasyTeam]) -> None:

        self.teams.append(team)

    def removeTeam(self, team: Type[FantasyTeam]) -> None:

        self.teams.remove(team)


    def getTeamFromEmail(self, email: str) -> Type[FantasyTeam]:

        for team in self.teams:
            if team.owner.email == email:
                return team
