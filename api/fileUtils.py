from cmath import nan
import numpy as np
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from models import *
from Database import *


def checkInputJudge(tournament, filename):
    dataset = pd.read_csv(filename, sep=',', header=0)
    dataset.columns = dataset.columns.str.lower()
    required_columns = ['prefix', 'first name', 'last name', "email", "i prefer the role of", "do you have a law degree?", 
                        "preferred regions", "preferred teams", "unpreferred teams"]
    missed_colums = []
    for col in required_columns:
        if col not in dataset.columns:
            missed_colums.append(col)
    if len(missed_colums) == 0:
        # save the teams
        saveJudges(tournament, dataset)
        tournament.judge_uploaded = 1
    return missed_colums
            
def checkInputTeams(tournament, filename, wild):
    missed_colums = []
    wrong_wild_teams = False
    dataset = pd.read_csv(filename, sep=',', header=0)
    dataset.columns = dataset.columns.str.lower()
    required_columns = ['team', 'region', 'members']
    for col in required_columns:
        if col not in dataset.columns:
            missed_colums.append(col)
    if wild == 1 and dataset.shape[0] != 4:
        wrong_wild_teams = True
    elif len(missed_colums) == 0:
        # save the teams
        saveTeams(tournament, dataset, wild)
        tournament.team_uploaded = 1
        if wild == 1:
            tournament.wild_uploaded = 1
    return wrong_wild_teams, missed_colums

def checkInputScore(tournament, filename, round_num):
    missed_colums = []
    wrong_courtroom = -1
    dataset = pd.read_csv(filename, sep=',', header=0)
    dataset.columns = dataset.columns.str.lower()
    required_colums = ['courtroom', 'plaintiff school', "defense school", "plaintiff total", "defense total",
                        'plaintiff result', 'defense result']
    for col in required_colums:
        if col not in dataset.columns:
            missed_colums.append(col)
    
    if len(missed_colums) == 0:
        # save the scores
        wrong_courtroom = saveScores(tournament, dataset, round_num)
        if wrong_courtroom != -1:
            return wrong_courtroom, missed_colums
        tournament.score_uploaded = 1
    return wrong_courtroom, missed_colums

def saveTeams(tournament, data, wild):
    # regions, counts = np.unique(data["region"], return_counts=True)
    regions = set(data["region"])
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        m_tournament = session.query(Tournament).get(tournament.id)
        if wild == 0:
            m_tournament.regions = regions
            tournament.regions = regions # save to default database
        # flag_modified(tournament, "regions")
        for index, row in data.iterrows():
            team_name = row["team"]
            region = row["region"]
            team = Team(team_name=team_name, region=region, wild=wild)
            members = list(row["members"].split(","))
            for i in range(len(members)):
                members[i] = members[i].strip()
            team.members = members
            session.add(team)
        session.commit()
        

def saveJudges(tournament, data):
    data = data.fillna('')
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        for index, row in data.iterrows():
            # print(row)
            judge = Judge()
            judge.name = row["first name"] + " " + row["last name"]
            judge.email = row["email"]
            law_degree = row["do you have a law degree?"]
            if "y" in law_degree.lower():
                judge.hasLawDegree = True
            else:
                judge.hasLawDegree = False
            preferredRole = row["i prefer the role of"]
            if preferredRole:
                if "score" in preferredRole.lower():
                    judge.preferredRole = "Scoring"
                elif "presid" in preferredRole.lower():
                    judge.preferredRole = "Presiding"
                    
            if row["preferred regions"]:
                preferredRegions = list(row["preferred regions"].split(","))
                for i in range(len(preferredRegions)):
                    preferredRegions[i] = preferredRegions[i].strip()
                judge.preferredRegions = preferredRegions
            session.add(judge) 
            preferred_teams = row["preferred teams"]
            if preferred_teams:
                judge.preferred_teams = list(preferred_teams.split(","))
                for i in range(len(judge.preferred_teams)):
                    t = judge.preferred_teams[i]
                    judge.preferred_teams[i] = t.strip()
                    team = session.query(Team).filter(Team.team_name == t).all()
                    if team:
                        judge.preferredTeams.append(team[0])
            
            unpreferred_teams = row["unpreferred teams"]
            if unpreferred_teams: 
                judge.preferred_teams = list(unpreferred_teams.replace(" ", "").split(","))
                judge.unpreferred_teams = unpreferred_teams
                for i in range(len(judge.unpreferred_teams)):
                    t = unpreferred_teams[i]
                    judge.unpreferred_teams[i] = t.strip()
                    team = session.query(Team).filter(Team.team_name == t).all()
                    if team:
                        judge.unpreferredTeams.append(team[0])
        session.commit()
        
def duplicateScore(team):
    team.trial_wins *= 2
    team.ballots *= 2
    team.total_points *= 2
    team.point_differential *= 2

def calculate_round4_bye_teams_scores(bye_teams):
    for team in bye_teams:
        if team.rounds_participated and 4 in team.rounds_participated:
            continue
        round_count = 0
        if team.rounds_participated and 1 in team.rounds_participated:
            round_count += 1
        if team.rounds_participated and 2 in team.rounds_participated:
            round_count += 1
        if team.rounds_participated and 3 in team.rounds_participated:
            round_count += 1
        team.trial_wins += team.trial_wins/round_count 
        team.ballots += team.ballots/round_count 
        team.total_points += team.total_points/round_count 
        team.point_differential += team.point_differential/round_count 
        
def saveScores(tournament, data, round_num):
    print(round_num, type(round_num))
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        m_round = session.query(Round).get(round_num)
        bye_team_ids = None
        bye_teams = []
        if m_round.bye_teams:
            bye_team_ids = m_round.bye_teams.values()
        teams = session.query(Team).all()
        team_dict = {}
        team_score_dic = {}
        all_matches = session.query(Match).filter(Match.round_id == round_num)
        matches = {}
        for match in all_matches:
            match.scoreSheets = []
            matches[match.id] = match
            match.teams = []
        for team in teams:
            team_dict[team.team_name.lower()] = team
            if bye_team_ids and team.id in bye_team_ids:
                bye_teams.append(team)
                if round_num == 2:
                    # round2 bye teams
                    duplicateScore(team)
            if round_num == 2 and team.rounds_participated is None:
                duplicateScore(team)
            teamScore = TeamScore(team_id=team.id, trial_wins=0, ballots=0, total_points=0, point_differential=0)
            # session.add(teamScore)
            team_score_dic[team.id] = teamScore
        # session.commit()
        # for team in teams:
        #     if team.id not in bye_team_ids:
        #         assignScore(team, team_score_dic[team.id], round_num)
        for index, row in data.iterrows():
            match_id = row["courtroom"]
            try:
                match = matches[match_id]
            except:
                return match_id
            plaintiff = team_dict[row["plaintiff school"].lower()]
            defense = team_dict[row["defense school"].lower()]
            plaintiff_total = row["plaintiff total"]
            defense_total = row["defense total"]
            plaintiff_result = row["plaintiff result"]
            defense_result = row["defense result"]
            defense.role = 0
            plaintiff.role = 1
            match.defense_team_id = defense.id
            match.plaintiff_team_id = plaintiff.id
            if len(match.teams) == 0:
                match.teams = [defense, plaintiff]
                match.team_names = [defense.team_name, plaintiff.team_name]
            scoreSheet = Scoresheet(match_id=match_id, defense_team_id=defense.id, plaintiff_team_id=plaintiff.id,
                                    defense_team=defense.team_name, plaintiff_team=plaintiff.team_name,
                                    defense_score=defense_total, plaintiff_score=plaintiff_total,
                                    defense_result=defense_result, plaintiff_result=plaintiff_result)
            match.scoreSheets.append(scoreSheet)
            plaintiff_score = team_score_dic[plaintiff.id]
            defense_score = team_score_dic[defense.id]
            plaintiff.total_points += plaintiff_total
            defense.total_points += defense_total
            plaintiff_score.total_points += plaintiff_total
            defense_score.total_points += defense_total
            if defense_result.lower() == "Win".lower():
                defense.ballots += 1
                defense_score.ballots += 1
                scoreSheet.ballot = defense.id
            else:
                plaintiff.ballots += 1
                plaintiff_score.ballots += 1
                scoreSheet.ballot = plaintiff.id
            session.add(scoreSheet)
        for match in all_matches:
            # print(match.id, match.plaintiff_team_id, match.defense_team_id)
            plaintiff_score = team_score_dic[match.plaintiff_team_id]
            defense_score = team_score_dic[match.defense_team_id]
            team1 = team_dict.pop(match.teams[0].team_name)
            team2 = team_dict.pop(match.teams[1].team_name)
            # Two Judge Panel
            scoreSheets = match.scoreSheets
            if len(scoreSheets) == 2:
                plaintiff_new_score = round((scoreSheets[0].plaintiff_score + scoreSheets[1].plaintiff_score)/2)
                defense_new_score = round((scoreSheets[0].defense_score + scoreSheets[1].defense_score)/2)
                plaintiff_score.total_points += plaintiff_new_score
                defense_score.total_points += defense_new_score
                if plaintiff_new_score > defense_new_score:
                    plaintiff_score.ballots += 1
                    plaintiff.ballots += 1
                else:
                    defense.ballots += 1
                    defense_score.ballots += 1
            match.defense_score = defense_score.total_points
            match.plaintiff_score = plaintiff_score.total_points
            plaintiff_score.point_differential = plaintiff_score.total_points - defense_score.total_points
            defense_score.point_differential = defense_score.total_points - plaintiff_score.total_points
            team1.point_differential = defense_score.point_differential
            team2.point_differential = plaintiff_score.point_differential
            if plaintiff_score.ballots > defense_score.ballots:
                team2.trial_wins += 1
                plaintiff_score.trial_wins += 1
                match.winner_team = match.team_names[1]
            else:
                team1.trial_wins += 1
                defense_score.trial_wins += 1
                match.winner_team = match.team_names[0]
             
            if team1.rounds_participated:
                team1.rounds_participated.append(round_num)
            else:
                team1.rounds_participated = [round_num]
            if team2.rounds_participated:
                team2.rounds_participated.append(round_num)
            else:
                team2.rounds_participated = [round_num]
            
            if team1.opponent_ids:
                team1.opponent_ids.append(team1.id)
                flag_modified(team1, "opponent_ids")
            else:
                team1.opponent_ids = [team2.id]
                
            if team2.opponent_ids:
                team2.opponent_ids.append(team1.id)
                flag_modified(team2, "opponent_ids")
            else:
                team2.opponent_ids = [team1.id]
            
            # if bye_team_ids and team1.id in bye_team_ids:
            #     m_round.bye_teams.pop(team1.region)
            #     flag_modified(m_round, "bye_teams")
            # if bye_team_ids and team2.id in bye_team_ids:
            #     m_round.bye_teams.pop(team2.region)
            #     flag_modified(m_round, "bye_teams")
                
            flag_modified(team1, "rounds_participated")
            flag_modified(team2, "rounds_participated")
            flag_modified(match, "team_names")
        new_bye_teams = []
        new_bye_teams_dict = {}
        for team in team_dict.values():
            new_bye_teams.append(team)
            new_bye_teams_dict[team.region] = team.id
        if round_num == 4:
            calculate_round4_bye_teams_scores(new_bye_teams)
        m_round.status = 1
        session.commit()
    return -1

    
# def assignScore(team, score, round_num):
#     if round_num == 1:
#         team.round1_score_id = score.id
#     elif round_num == 2:
#         team.round2_score_id = score.id
#         # if team.round1_score_id != -1:
#         #     return team.round1_score
#         # else:
#         #     return None
#     elif round_num == 3:
#         team.round3_score_id = score.id
#         # return team.round2_score
#         # team.round3_score = score
#         # print(team.team_name, team.round3_score_id)
#     elif round_num == 4:
#         team.round4_score_id = score.id
#         # return team.round3_score
#         # team.round4_score = score
#     elif round_num == 5:
#         # team.round5_score = score
#         team.round5_score_id = score.id
#         # return team.round4_score
        
def removeTeams(tournament, wild):
    print("remove teams", wild)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        session.query(Team).filter(Team.wild == wild).delete()
        session.commit()
    
    
def removeJudges(tournament):
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        session.query(Team).delete()
        session.commit()

if __name__ == "__main__":
    if checkInputJudge("../static/titanic.csv"):
        print("Here we go!")
    