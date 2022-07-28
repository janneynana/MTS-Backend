from zoneinfo import available_timezones
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from models import *
from Database import *
from schedules import *


def addJudge(tournament, judge):
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    response = {}
    with Session() as session:
        judge = Judge(name=judge.name, email=judge.email, hasLawDegree=judge.hasLawDegree)
        session.add(judge)
        session.commit()
        response["code"] = 0
        response["msg"] = "new judge has successfully added"
    return response

def removeMetTeam(team1, team2, judge):
    if judge.teams_met:
        if team1.id in judge.teams_met:
            judge.teams_met.remove(team1.id)
        if team2.id in judge.teams_met:
            judge.teams_met.remove(team2.id)
            
def findAvailableResidingJudge(team1, team2, session):
    judges = session.query(Judge).filter(Judge.match_id == -1, Judge.hasLawDegree == True).order_by(Judge.assigned)
    available = []
    for judge in judges:
        if not hasMet(team1, team2, judge):
            available.append(judge.name)
    return available

def findAvailableScoringJudge(team1, team2, session):
    judges = session.query(Judge).filter(Judge.match_id == -1).order_by(Judge.assigned)
    available = []
    for judge in judges:
        if not hasMet(team1, team2, judge):
            available.append(judge.name)
    return available

def changeJudge(tournament, new_match):
    # Not Completed
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        match = session.query(Match).get(new_match.id)
        team1 = session.query(Team).get(match.defense_team_id)
        team2 = session.query(Team).get(match.plaintiff_team_id)
        if match.presiding_judge_name.lower() != new_match.presidingJudge.lower():
            new_presiding = session.query(Judge).filter(Judge.name.ilike(new_match.presiding_judge))
            if new_presiding is None:
                return {"code": -1, "msg": "The new residing judge doesn't match any existing judge names"}
            elif -1 != new_presiding.match_id != match.id:
                m = session.query(Match).get(new_presiding.match_id)
                recommend = findAvailableResidingJudge(team1, team2, session)
                return {"code": -2, "msg": "The new residing judge is already assigned to another match",
                            "match_id": m.id, "competition": m.schedule[0].competition_name, "recommend": recommend}
            elif hasMet(team1, team2, new_presiding):
                recommend = findAvailableResidingJudge(team1, team2, session)
                return {"code": -3, "msg": "The new residing judge has met one of the teams before",
                        "recommend": recommend}
            else:
                old_presiding = session.query(Judge).get(match.presiding_judge_id)
                old_presiding.match_id = -1
                new_presiding.match_id = match.id
                match.presiding_judge_name = new_presiding.name
                match.presiding_judge_id = new_presiding.id
                removeMetTeam(team1, team2, old_presiding)
                addMetTeam(team1, team2, new_presiding)
        new_scoring_judges = [new_match.scoringJudgeFirst, new_match.scoringJudgeSecond]
        old_scoring_judges = match.scoring_judges_names
        if new_match.scoringJudgeThird:
            new_scoring_judges.append(new_match.scoringJudgeThrid)
        
        match.scoring_judge_names = []
        match.scoring_judge_ids = []
        for i in range(len(new_scoring_judges)):
            new_scoring = new_scoring_judges[i]
            new_scoring_judge = session.query(Judge).filter(Judge.name.ilike(new_scoring_judge))
            old_scoring_judge = session.query(Judge).get(match.scoring_judge_ids[i])
            if new_scoring in old_scoring_judges:
                old_scoring_judge.match_id = -1
                new_scoring_judge.match_id = match.id
                match.scoring_judge_names.append[new_scoring]
                match.scoring_judge_ids.append[new_scoring_judge.id]
                removeMetTeam(team1, team2, old_scoring_judge)
            if new_scoring.lower() != match.scoring_judges_names[i].lower():
                if new_scoring_judge is None:
                    response = {"code": -1, "msg": "The new scoring judge 1 doesn't match any existing judge names"}
                    return response
                elif -1 != new_scoring_judge.match_id != match.id:
                    m = session.query(Match).get(new_scoring.match_id)
                    recommend = findAvailableResidingJudge(team1, team2, session)
                    return {"code": -2, "msg": "The scoring judge" + str(i) + " is already assigned to another match",
                                "match_id": m.id, "competition": m.schedule[0].competition_name, "recommend": recommend}
                elif hasMet(team1, team2, new_scoring_judge):
                    recommend = findAvailableResidingJudge(team1, team2, session)
                    return {"code": -3, "msg": "The new scoring judge" + str(i) + " has met one of the teams before",
                            "recommend": recommend}
                else:
                    old_scoring_judge.match_id = -1
                    new_scoring_judge.match_id = match.id
                    match.scoring_judge_names.append[new_scoring]
                    match.scoring_judge_ids.append[new_scoring_judge.id]
                    removeMetTeam(team1, team2, old_scoring_judge)
                    addMetTeam(team1, team2, new_scoring_judge)
        
        return {"code": 0, "msg": "judge reassignment success"}