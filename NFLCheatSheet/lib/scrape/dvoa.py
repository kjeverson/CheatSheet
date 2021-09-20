import csv
from pathlib import Path

from NFLCheatSheet.lib.classes.team import Team

DVOA_PATH = Path("/Users/everson/NFLCheatSheet/data/DVOA")


def read_dvoa_file(file):

    dvoa_dict = {}
    with file.open() as dvoa_file:
        reader = csv.DictReader(dvoa_file)
        for row in reader:
            if row['Team'] == 'WAS':
                row['Team'] = 'WSH'
            dvoa_dict.update({row['Team']: row})
    return dvoa_dict


def update_dvoa_rankings():

    path = DVOA_PATH / "DVOA.csv"
    dvoa_dict = read_dvoa_file(path)

    for team in dvoa_dict.keys():
        team_obj = Team.query.filter(Team.key == team).first()
        team_stats = team_obj.get_team_stats(preseason=False)

        team_stats.DVOA = int(dvoa_dict[team]['Total DVOA Rank'])
        team_stats.OFF = int(dvoa_dict[team]['Offense DVOA Rank'])
        team_stats.DEF = int(dvoa_dict[team]['Defense DVOA Rank'])
        team_stats.ST = int(dvoa_dict[team]['Special Teams DVOA Rank'])

    path = DVOA_PATH / "OFF.csv"
    dvoa_dict = read_dvoa_file(path)

    for team in dvoa_dict.keys():
        team_obj = Team.query.filter(Team.key == team).first()
        team_stats = team_obj.get_team_stats(preseason=False)

        team_stats.OFFPASS = int(dvoa_dict[team]['Pass DVOA Rank'])
        team_stats.OFFRUSH = int(dvoa_dict[team]['Rush DVOA Rank'])

    path = DVOA_PATH / "DEF.csv"
    dvoa_dict = read_dvoa_file(path)

    for team in dvoa_dict.keys():
        team_obj = Team.query.filter(Team.key == team).first()
        team_stats = team_obj.get_team_stats(preseason=False)

        team_stats.DEFPASS = int(dvoa_dict[team]['Pass DVOA Rank'])
        team_stats.DEFRUSH = int(dvoa_dict[team]['Rush DVOA Rank'])


