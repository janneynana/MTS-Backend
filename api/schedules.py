from pydoc import plain
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

from models import *
from Database import *
from Zoom import *

Round4_MATCH_SIZE = 14

def createSchedules(tournament, next_round):
    if next_round == 1:
        schedules = createRound1(tournament)
    elif next_round == 2:
        schedules = createRound2(tournament)
    elif next_round == 3:
        schedules = createRound3(tournament)
    elif next_round == 4:
        schedules = createStateFinal(tournament)
    elif next_round == 5:
        schedules = createChampionshipTrial(tournament)
    
    # update the tournament in the default database
    tournament.current_round = next_round
    db.session.commit()
    return schedules

def haveMet(team1, team2):
    if team1.id in team2.opponent_ids:
        return True
    else:
        return False
    
def pairTeamsRound3(team1, team2, bye_team_ids, schedule):
    # The two exceptions to this are for the teams that had byes in Rounds 1 and 2,
    # The Round 1 bye team will automatically present whichever side it did not present in Round 2.
    # The Round 2 bye team will automatically present whichever side it did not present in Round 1
    if team1.id in bye_team_ids:
        team2.role = team1.role
        team1.role = 1 - team2.role
    elif team2.id in bye_team_ids:
        team1.role = team2.role
        team2.role = 1- team1.role
    else:
        team1.role = random.choice([0, 1])
        team2.role = 1 - team1.role
    if team1.opponent_ids:
        team1.opponent_ids.append(team2.id)
    else:
        team1.opponent_ids = [team2.id]
    if team2.opponent_ids:
        team2.opponent_ids.append(team1.id)
    else:
        team2.opponent_ids = [team1.id]
    flag_modified(team1, "opponent_ids")
    flag_modified(team2, "opponent_ids")
    match = Match(round_id=3, schedule_id=schedule.id, team_ids=[team1.id, team2.id])
    if team1.role == 0:
        match.team_names = [team1.team_name, team2.team_name]
        match.defense_team_id = team1.id
        match.plaintiff_team_id = team2.id
        match.teams = [team1, team2]
    else:
        match.team_names = [team2.team_name, team1.team_name]
        match.defense_team_id = team2.id
        match.plaintiff_team_id = team1.id
        match.teams = [team2, team1]
    if team1.role == 0:
         match.defense_team_id = team1.id
         match.plaintiff_team_id = team2.id
    else:
        match.defense_team_id = team2.id
        match.plaintiff_team_id = team1.id
    return match

def handleRound3Exceptions(matches, team1, team2, bye_team_ids, schedule):
    print("handling exception")
    j = len(matches) - 1
    while j >= 0:
        match = matches[j]
        paired_team_ids = match.team_ids
        union1 = set(team1.opponent_ids) & set(paired_team_ids)
        union2 = set(team2.opponent_ids) & set(paired_team_ids)
        # print("union1", union1)
        # print("union2", union2)
        if len(union1) > 0 and len(union2) > 0 and union1 == union2 :
            # unable to match
            j -= 1
        else:
            # break the match and repair the teams
            team3 = match.teams[0]  # match.teams is assigned at line #83
            team4 = match.teams[1]
            team3.opponent_ids.pop()
            team4.opponent_ids.pop()
            if team3.id not in team1.opponent_ids:
                matches[j] = pairTeamsRound3(team1, team3, bye_team_ids, schedule)
                matches.append(pairTeamsRound3(team2, team4, bye_team_ids, schedule))
            else:
                matches[j] = pairTeamsRound3(team1, team4, bye_team_ids, schedule)
                matches.append(pairTeamsRound3(team2, team3, bye_team_ids, schedule))
            return 0
    if j < 0:
       return -1
                
def getRound4Teams(teams, round3, round4, regions):
    round3_teams = []
    wild_teams = []
    round3_bye_teams = {} # dictionary: region:team
    # exclude the bye teams in round 3
    for team in teams:
        if team.wild == 1:
            wild_teams.append(team)
        elif team.id not in list(round3.bye_teams.values()):
            round3_teams.append(team)
        else:
            round3_bye_teams[team.region] = team
    round3_teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
    round4.bye_teams = {} # dictionary - region:team_id
    round4_bye_teams = [] # list of teams
    for region in regions:
        if region not in round3.bye_teams.keys():
            continue
        region_teams = [team for team in teams if team.region == region]
        # bye_team3 = [team for team in region_teams if team.id == round3.bye_teams[region]][0] # round 3 bye team of that region
        size = len(region_teams)
        # need to select a bye team for round4
        bye_team4 = region_teams[size//2]
        print("bye_team4:", bye_team4.id, bye_team4.team_name)
        round4.bye_teams[region] = bye_team4.id
        # round3_bye_teams[region] = bye_team3
    round4_defense_teams = [team for team in round3_teams if team.role == 1]
    round4_plaintiff_teams = [team for team in round3_teams if team.role == 0]
    end = min(len(round4_defense_teams), 12)
    round4_defense_teams = round4_defense_teams[:end]
    end = min(len(round4_plaintiff_teams), 12)
    round4_plaintiff_teams = round4_plaintiff_teams[:end]
    # for t in round4_defense_teams:
    #     print("defense", t.id, t.team_name)
    # for t in round4_plaintiff_teams:
    #     print("plaintiff", t.id, t.team_name)
    # The team that had a bye in Round3 will take the place of the team that has a bye in Round 4 (if there's any).
    end = min(min(len(round4_defense_teams), len(round4_plaintiff_teams)), 12)
    for i in range(end):
        # print("1. i:", i)
        defense_team = round4_defense_teams[i]
        plaintiff_team = round4_plaintiff_teams[i]
        if defense_team.id in round4.bye_teams.values():
            round4_bye_teams.append((round4_defense_teams[i]))
            round4_defense_teams[i] = round3_bye_teams[defense_team.region]
        if plaintiff_team.id in round4.bye_teams.values():
            round4_bye_teams.append((round4_plaintiff_teams[i]))
            round4_plaintiff_teams[i] = round3_bye_teams[plaintiff_team.region]
    # append wild card teams
    round4_defense_teams.append(wild_teams[0])
    round4_defense_teams.append(wild_teams[1])
    round4_plaintiff_teams.append(wild_teams[2])
    round4_plaintiff_teams.append(wild_teams[3])
    round4.bye_teams = {}
    for t in round4_bye_teams:
        print("round4_bye_team:", t.id, t.team_name)
        round4.bye_teams[t.region] = t.id
    return round4_defense_teams, round4_plaintiff_teams, round4_bye_teams

def rotateTeams(teams, start_index, end_index):
    end_team = teams[end_index]
    while end_index > start_index:
        teams[end_index] = teams[end_index-1]
        end_index -= 1
    teams[start_index] = end_team
    
def findViablePlaintiff(defense_teams, plaintiff_teams, current_index):
    # print("findViablePlaintiff, i =", current_index)
    defense_team = defense_teams[current_index]
    plaintiff_team = plaintiff_teams[current_index]
    # print("defense", defense_team.team_name)
    # print("plaintiff", plaintiff_team.team_name)
    i = current_index-1
    while i >= 0:
        temp_defense = defense_teams[i]
        temp_plaintiff= plaintiff_teams[i]
        # print("temp_defense", temp_defense.team_name)
        # print("temp_plaintiff", temp_plaintiff.team_name)
        if (not haveMet(temp_defense, plaintiff_team)) and (not haveMet(temp_plaintiff, defense_team)):
            plaintiff_teams[current_index] = plaintiff_teams[i]
            plaintiff_teams[i] = plaintiff_team
            return
        i -= 1
    if i == -1:
        print("Unable to create Schedules")
        return "Unable to create Schedules"      

def calculate_round4_bye_teams_scores(bye_teams, session):
    for team in bye_teams:
        if 4 in team.rounds_participated:
            continue
        round_count = 0
        if 1 in team.rounds_participated:
            round_count += 1
        if 2 in team.rounds_participated:
            round_count += 1
        if 3 in team.rounds_participated:
            round_count += 1
        team.trial_wins += team.trial_wins/round_count 
        team.ballots += team.ballots/round_count 
        team.total_points += team.total_points/round_count 
        team.point_differential += team.point_differential/round_count 

def testing(tournament):
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges = divideJudges(session)
        matches = session.query(Match).filter(Match.id != 1)
        for match in matches:
            match.teams = [session.query(Team).get(match.defense_team_id), session.query(Team).get(match.plaintiff_team_id)]
            assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match)
        session.commit()

def createRound1(tournament):
    regions = tournament.regions
    schedules = {}
    # connect to the database of the tournament
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        m_tournament = session.query(Tournament).get(tournament.id)
        presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges = divideJudges(session)
        m_tournament.current_round = 1
        round = Round(id=1, name="Round1", tournament_id=tournament.id)
        session.add(round)
        session.commit()
        bye_teams = {}
        matches = []
        for region in regions:
            schedule = Schedule(competition_name=region+" Regional Competition", region=region, round_id=1)
            session.add(schedule)
            teams = session.query(Team).filter_by(region=region).all()
            size = len(teams)
            if size % 2 != 0:
                # odd number of teams, will have a bye team
                bye_team = teams[size-1]
                schedule.bye_team_id = bye_team.id
                bye_teams[region] = bye_team.id
                teams = teams[:-1]
                size -= 1
            for i in range(size//2):
                team1 = teams[i]
                team2 = teams[size-1-i]
                team1.role = random.choice([0, 1])
                team2.role = 1 - team1.role
                team1.opponent_ids = [team2.id]
                team2.opponent_ids = [team1.id]
                match = Match(round_id=1, schedule_id=schedule.id, team_ids=[team1.id, team2.id])
                if team1.role == 0:
                    match.defense_team_id = team1.id
                    match.plaintiff_team_id = team2.id
                    match.team_names = [team1.team_name, team2.team_name]
                    match.teams = [team1, team2]
                else:
                    match.defense_team_id = team2.id
                    match.plaintiff_team_id = team1.id
                    match.team_names = [team2.team_name, team1.team_name]
                    match.teams = [team2, team1]
                assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match)
                session.add(match)
                matches.append(match)
            # schedules[region] = formatSchedule(schedule, matches, session)
        session.commit()
        round.bye_teams = bye_teams
        for match in matches:
            if match.zoom_id:
                deleteMeeting(match.zoom_id)
            created, id, link = createMeeting(match)
            if created:
                match.zoom_id = id
                match.zoom_link = link
            teamRoster = TeamRoster(match_id=match.id, defense_team=match.team_names[0], plaintiff_team=match.team_names[1],
                                    defense_members=match.teams[0].members, plaintiff_members=match.teams[1].members)
            session.add(teamRoster)
        session.commit()
    return schedules

def createRound2(tournament):
    regions = tournament.regions
    schedules = {}
    # connect to the database of the tournament
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges = divideJudges(session)
        m_tournament = session.query(Tournament).get(tournament.id)
        m_tournament.current_round = 2
        round = Round(id=2, name="Round2", tournament_id=tournament.id)
        session.add(round)
        bye_teams = {}
        round1 = session.query(Round).get(1)
        matches = []
        for region in regions:
            schedule = Schedule(competition_name=region+" Regional Competition", region=region, round_id=2)
            session.add(schedule)
            session.commit()
            bye_team = None
            replace_team = None
            # teams = session.query(Team).filter(Team.region == region).order_by(
            #     Team.trial_wins.desc(),
            #     Team.ballots.desc(),
            #     Team.total_points.desc(),
            #     Team.point_differential.desc()).all()
            if region in round1.bye_teams:
                replace_team_id = round1.bye_teams[region]
                replace_team = session.query(Team).filter(Team.region == region, Team.id == replace_team_id).first()
                teams = session.query(Team).filter(Team.region == region, Team.id != replace_team_id).all()
            else: 
                teams = session.query(Team).filter(Team.region == region).all()
            
            teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
            # print(teams)
            size = len(teams)
            if replace_team is not None:
                # The team that is ranked in the lower half of the median will have a bye in Round 2.
                bye_team = teams[size//2]
                replace_team.role = bye_team.role
                schedule.bye_team_id = bye_team.id
                bye_teams[region] = bye_team.id
                teams[size//2] = replace_team
            defense_teams = []
            plaintiff_teams = []
            for team in teams:
                if team.role == 1:
                    defense_teams.append(team)
                else:
                    plaintiff_teams.append(team)
            k = len(defense_teams)
            # rotate the teams or modify the team sequence until each pair is valid
            i = 0
            while i < k:
                # print("rotate", i)
                team1 = defense_teams[i]
                team2 = plaintiff_teams[i]
                # check if the two teams have played with each other before
                if haveMet(team1, team2):
                    if i < k - 1: 
                        rotateTeams(plaintiff_teams, i, i+1)
                    else:
                        findViablePlaintiff(defense_teams, plaintiff_teams, i)
                i += 1
            # pair up the teams
            i = 0
            while i < k:
                # print("pair", i)
                team1 = defense_teams[i]
                team2 = plaintiff_teams[i]
                team1.role = 0
                team2.role = 1
                if team1.opponent_ids:
                    team1.opponent_ids.append(team2.id)
                else:
                    team1.opponent_ids = [team2.id]
                if team2.opponent_ids:
                    team2.opponent_ids.append(team1.id)
                else:
                    team2.opponent_ids = [team1.id]
                flag_modified(team1, "opponent_ids")
                flag_modified(team2, "opponent_ids")
                match = Match(round_id=2, schedule_id=schedule.id, team_ids=[team1.id, team2.id], 
                              team_names = [team1.team_name, team2.team_name],
                              defense_team_id=team1.id, plaintiff_team_id=team2.id)
                match.teams = [team1, team2]
                matches.append(match)
                assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match)
                session.add(match)
                # print(to_dict(match))
                i += 1
            # schedules[region] = formatSchedule(schedule, matches, session)
        session.commit()
        for match in matches:
            if match.zoom_id:
                deleteMeeting(match.zoom_id)
            created, id, link = createMeeting(match)
            if created:
                match.zoom_id = id
                match.zoom_link = link
            teamRoster = TeamRoster(match_id=match.id, defense_team=match.team_names[0], plaintiff_team=match.team_names[1],
                                    defense_members=match.teams[0].members, plaintiff_members=match.teams[1].members)
            session.add(teamRoster)
        round.bye_teams = bye_teams    
        session.commit()
    return schedules

def createRound3(tournament):
    regions = tournament.regions
    schedules = {}
    # connect to the database of the tournament
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges = divideJudges(session)
        m_tournament = session.query(Tournament).get(tournament.id)
        m_tournament.current_round = 3
        round = Round(id=3, name="Round3", tournament_id=tournament.id)
        session.add(round)
        bye_teams = {}
        round1 = session.query(Round).get(1)
        round2 = session.query(Round).get(2)
        all_matches = []
        for region in regions:
            matches = []
            schedule = Schedule(competition_name=region+" Regional Competition", region=region, round_id=3)
            session.add(schedule)
            session.commit()
            teams = session.query(Team).filter(Team.region == region).all()
            size = len(teams)
            bye_team1 = None
            bye_team2 = None
            bye_team_ids = []
            # remove if block if the score has been duplicated
            if size % 2 != 0:
                bye_team1 = session.query(Team).get(round1.bye_teams[region]) # bye_team in Round 1
                bye_team2 = [team for team in teams if team.id == round2.bye_teams[region]][0] # bye_team in Round 2
                bye_team_ids = [bye_team1.id, bye_team2.id]
                # Not Sure
            teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
            
            if size % 2 != 0:
                bye_team = teams.pop() # The team in last place will have a bye in Round 3.
                schedule.bye_team_id = bye_team.id
                size -= 1
                bye_teams[region] = bye_team.id
            i = 0
            while i < size-1:
                # print("i =", i)
                team1 = teams[i]
                team2 = teams[i+1]
                # check if the two teams have played with each other before
                if haveMet(team1, team2):
                    if i == size - 2:
                        # the last pair has played each other before
                        # if so, go back to the previous matchup to find a valid solution
                        handleRound3Exceptions(matches, team1, team2, bye_team_ids, schedule)
                        break
                    elif haveMet(team1, teams[i+2]):
                        # teams[i] has played teams[i+1] and teams[i+2]
                        teams[i+1] = teams[i+3]
                        teams[i+3] = team2
                    else:
                        # teams[i] has played teams[i+1] but not teams[i+2]
                        teams[i+1] = teams[i+2]
                        teams[i+2] = team2
                    continue
                match = pairTeamsRound3(team1, team2, bye_team_ids, schedule)
                matches.append(match)
                # print(len(matches))
                i += 2
            for match in matches:
                assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match)
                session.add(match)
            all_matches.extend(matches)
            session.commit()
            # schedules[region] = formatSchedule(schedule, matches, session)
        round.bye_teams = bye_teams
        for match in all_matches:
            if match.zoom_id:
                deleteMeeting(match.zoom_id)
            created, id, link = createMeeting(match)
            if created:
                match.zoom_id = id
                match.zoom_link = link
            teamRoster = TeamRoster(match_id=match.id, defense_team=match.team_names[0], plaintiff_team=match.team_names[1],
                                    defense_members=match.teams[0].members, plaintiff_members=match.teams[1].members)
            session.add(teamRoster)   
        session.commit()  
    return schedules

def createStateFinal(tournament):
    regions = tournament.regions
    schedules = {}
    # connect to the database of the tournament
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges = divideJudges(session)
        m_tournament = session.query(Tournament).get(tournament.id)
        m_tournament.current_round = 4
        round4 = Round(id=4, name="Round4", tournament_id=tournament.id)
        session.add(round4)
        schedule = Schedule(competition_name="State Finals", region="StateWide", round_id=4)
        session.add(schedule)
        session.commit()
        round3 = session.query(Round).get(3)
        all_teams = session.query(Team).all()
        round4_defense_teams, round4_plaintiff_teams, round4_bye_teams = getRound4Teams(all_teams, round3, round4, regions)
        calculate_round4_bye_teams_scores(round4_bye_teams, session)
        match_size = min(min(len(round4_defense_teams), len(round4_plaintiff_teams)), Round4_MATCH_SIZE)
        # rotate the teams or modify the team sequence until each pair is valid
        for i in range(match_size):
            # print("2. i:", i)
            defense_team = round4_defense_teams[i]
            plaintiff_team = round4_plaintiff_teams[i]
            if haveMet(defense_team, plaintiff_team):
                # the defense_team i has played plaintiff_team i in the previous round
                if i + 1 == match_size: 
                    # edge case: defense_team 12 can't be paired with plaintiff_team 12
                    # go up to find a viable plaintiff_team to pair
                    findViablePlaintiff(round4_defense_teams, round4_plaintiff_teams, i)
                elif haveMet(defense_team, round4_plaintiff_teams[i+1]):
                    # the defense_team i has played plaintiff_team i and i+1 in the previous round
                    if i + 2 == match_size: 
                        # edge case: defense_team 11 cannot be paired with plaintiff_team 11 nor 12
                        findViablePlaintiff(round4_defense_teams, round4_plaintiff_teams, i)
                    elif haveMet(defense_team, round4_plaintiff_teams[i+2]):
                        # the defense_team i has played plaintiff_team i, i+1, and i+2 in the previous round
                        if i + 3 == match_size: 
                            # edge case: defense_team 11 cannot be paired with plaintiff_team 11, 12 nor 13
                            findViablePlaintiff(round4_defense_teams, round4_plaintiff_teams, i)
                        else:
                            rotateTeams(round4_plaintiff_teams, i, i+3)
                    else:
                        rotateTeams(round4_plaintiff_teams, i, i+2)
                else:
                    rotateTeams(round4_plaintiff_teams, i, i+1)
        
        # pair teams
        matches = []
        for i in range(match_size):
            defense_team = round4_defense_teams[i]
            plaintiff_team = round4_plaintiff_teams[i]
            defense_team.role = 0
            plaintiff_team.role = 1
            if defense_team.opponent_ids:
                defense_team.opponent_ids.append(plaintiff_team.id)
            else:
                defense_team.opponent_ids = [plaintiff_team.id]
            if plaintiff_team.opponent_ids:
                plaintiff_team.opponent_ids.append(defense_team.id)
            else:
                plaintiff_team.opponent_ids = [defense_team.id]
            flag_modified(defense_team, "opponent_ids")
            flag_modified(plaintiff_team, "opponent_ids")
            match = Match(round_id=4, schedule_id=schedule.id, 
                          team_ids=[defense_team.id, plaintiff_team.id], 
                          team_names = [defense_team.team_name, plaintiff_team.team_name],
                          defense_team_id=defense_team.id, 
                          plaintiff_team_id=plaintiff_team.id)
            session.add(match)
            match.teams = [plaintiff_team, defense_team]
            matches.append(match)
            i += 1
        # schedules[schedule.region] = formatSchedule(schedule, matches, session)
        session.commit()
        for match in matches:
            if match.zoom_id:
                deleteMeeting(match.zoom_id)
            created, id, link = createMeeting(match)
            if created:
                match.zoom_id = id
                match.zoom_link = link
            assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match)
            teamRoster = TeamRoster(match_id=match.id, defense_team=match.team_names[0], plaintiff_team=match.team_names[1],
                                    defense_members=match.teams[0].members, plaintiff_members=match.teams[1].members)
            session.add(teamRoster)
        session.commit()
    return schedules

def createChampionshipTrial(tournament):
    schedules = {}
    # connect to the database of the tournament
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges = divideJudges(session)
        m_tournament = session.query(Tournament).get(tournament.id)
        m_tournament.current_round = 5
        round4 = session.query(Round).get(4)
        round5 = Round(id=5, name="Round5", tournament_id=tournament.id)
        session.add(round5)
        schedule = Schedule(competition_name="Championship Trial", region="StateWide", round_id=5)
        session.add(schedule)
        round4_teams = []
        all_teams = session.query(Team).all()
        for team in all_teams:
            if team.rounds_participated and 4 in team.rounds_participated:
                round4_teams.append(team)
            elif round4.bye_teams and team.id in round4.bye_teams.values():
                round4_teams.append(team)
        round4_teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        # for t in round4_teams:
        #     print(repr(t))
        team1 = round4_teams[0]
        team2 = round4_teams[1]
        team1.role = random.choice([0, 1])
        team2.role = 1 - team1.role
        # team1.opponent_ids.append(team2.id)
        # team2.opponent_ids.append(team1.id)
        # flag_modified(team1, "opponent_ids")
        # flag_modified(team2, "opponent_ids")
        match = Match(round_id=5, schedule_id=schedule.id, team_ids=[team1.id, team2.id])
        if team1.role == 0:
            match.defense_team_id = team1.id
            match.plaintiff_team_id = team2.id
            match.team_names = [team1.team_name, team2.team_name]
            match.teams = [team1, team2]
        else:
            match.defense_team_id = team2.id
            match.plaintiff_team_id = team1.id
            match.team_names = [team2.team_name, team1.team_name]
            match.teams = [team2, team1]
        session.add(match)
        assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match)
        # flag_modified(match, "scoring_judge_ids")
        # flag_modified(match, "scoring_judge_names")
        session.commit()
        if match.zoom_id:
                deleteMeeting(match.zoom_id)
        created, id, link = createMeeting(match)
        if created:
            match.zoom_id = id
            match.zoom_link = link
        teamRoster = TeamRoster(match_id=match.id, defense_team=match.team_names[0], plaintiff_team=match.team_names[1],
                                    defense_members=match.teams[0].members, plaintiff_members=match.teams[1].members)
        session.add(teamRoster)
        session.commit()
        # schedules[schedule.region] = formatSchedule(schedule, [match], session)
    return schedules

def formatSchedule(schedule, schedule_matches, session):
    response = {}
    matches = []
    bye_teams = []
    round = session.query(Round).get(schedule.round_id)
    if schedule.region == "StateWide":
        if round.bye_teams:
            bye_teams = session.query(Team).filter(Team.id.in_(round.bye_teams.values())).all()
            response["bye_teams"] = "; ".join([team.team_name for team in bye_teams])
        else:
            response["bye_teams"] = "None"
    elif schedule.bye_team_id:
        bye_teams = session.query(Team).filter(Team.id==schedule.bye_team_id)
    if schedule.formatted:
        response["matches"] = schedule.formattedMatches
    else:
        for match in schedule_matches:
            match_dict = {}
            match_dict["courtroom"] = match.id
            match_dict["teams"] = {}
            match_dict["sides"] = {}
            # if round.id in [1, 3, 5]:
            #     # to be determined before the trial starts
            #     match_dict["teams"]["first"] = match.team_names[0]
            #     match_dict["sides"]["first"] = "Undecided"
            #     match_dict["sides"]["second"] = "Undecided"
            #     match_dict["teams"]["second"] = match.team_names[1]
            # else:
            # match_dict["teams"]["first"] = session.query(Team).get(match.plaintiff_team_id).team_name
            match_dict["teams"]["first"] = match.team_names[1]
            match_dict["sides"]["first"] = "Plaintiff"
            match_dict["sides"]["second"] = "Defense"
            # match_dict["teams"]["second"] = session.query(Team).get(match.defense_team_id).team_name
            match_dict["teams"]["second"] = match.team_names[0]
            match_dict["winner_team"] = match.winner_team
            match_dict["presidingJudge"] = ""
            match_dict["scoringJudgeFirst"] = ""
            match_dict["scoringJudgeSecond"] = ""
            match_dict["scoringJudgeThird"] = ""
            match_dict["zoomLink"] = ""
            match_dict["teamRosterLink"] = ""
            if match.presiding_judge_id:
                match_dict["presidingJudge"] = match.presiding_judge_name
            if match.scoring_judge_ids:
                scoring_judges = match.scoring_judge_names
                match_dict["scoringJudgeFirst"] = scoring_judges[0]
                match_dict["scoringJudgeSecond"] = scoring_judges[1]
                try:
                    match_dict["scoringJudgeThird"] = scoring_judges[2]
                except Exception:
                    match_dict["scoringJudgeThird"] = ""
            if match.zoom_link:
                match_dict["zoomLink"] = match.zoom_link
            if match.bestWitness:
                match_dict["bestWitness"] = match.bestWitness
            if match.bestAttorney:
                match_dict["bestAttorney"] = match.bestAttorney
            # formatted = FormattedMatch(courtroom=match.id, teams=match_dict["teams"], sides=match_dict["sides"],
            #                            winner_team=match.winner_team)
            # session.add(formatted)
            matches.append(match_dict)
        response["matches"] = matches
        # schedule.formatted = True
    response["schedule"] =schedule.to_dict()
    response["bye_teams"] = [team.team_name for team in bye_teams]
    return response
    
def getSchedule(tournament, round_num, region):
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        schedule = session.query(Schedule).filter(Schedule.round_id == round_num, Schedule.region == region).first()
        response = formatSchedule(schedule, schedule.matches, session)   
        session.commit()        
    return response

# Sort teams by region
def sortTeams(tournament, round_num, region):
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        bye_teams = []
        if round_num == 4:
            round = session.query(Round).get(round_num)
            if round.bye_teams:
                bye_teams = session.query(Team).filter(Team.id.in_(round.bye_teams.values())).all()
            teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
            teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        elif round_num == 5:
            teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
            teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        else:
            schedule = session.query(Schedule).filter(Schedule.round_id == round_num, Schedule.region == region).first()
            if schedule.bye_team_id:
                bye_teams = session.query(Team).filter(Team.id==schedule.bye_team_id)
            if round_num == 1:
                teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
                teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
            if round_num == 2:
                teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
                teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
            if round_num == 3:
                teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
                teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        response = {}
        response["teams"] = [team.to_dict() for team in teams]
        response["bye_teams"] = [team.to_dict() for team in bye_teams]
    return response

# Sort plaintiff teams and defense by region
def sortTeamsByRole(tournament, round_num, region):
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        bye_teams = []
        if round_num == 4:
            round = session.query(Round).get(round_num)
            if round.bye_teams:
                bye_teams = session.query(Team).filter(Team.id.in_(round.bye_teams.values())).all()
            teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
            teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        elif round_num == 5:
            teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
            teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        else:
            schedule = session.query(Schedule).filter(Schedule.round_id == round_num, Schedule.region == region).first()
            if schedule.bye_team_id:
                bye_teams = session.query(Team).filter(Team.id==schedule.bye_team_id)
            if round_num == 1:
                teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
                teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
            if round_num == 2:
                teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
                teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
            if round_num == 3:
                teams = session.query(Team).filter(round_num.in_(Team.rounds_participated)).all()
                teams.sort(key=lambda t: (t.trial_wins, 
                                      t.ballots,
                                      t.total_points,
                                      t.point_differential), reverse=True)
        defense_teams = []
        plaintiff_teams = []
        for team in teams:
            if team.role == 0:
                defense_teams.append(team)
            elif team.role == 1:
                plaintiff_teams.append(team)
        response = {}
        response["defense_teams"] = [team.to_dict() for team in defense_teams]
        response["plaintiff_teams"] = [team.to_dict() for team in plaintiff_teams]
        response["bye_teams"] = [team.to_dict() for team in bye_teams]
    return response

def divideJudges(session):
    judges = session.query(Judge).order_by(Judge.assigned)
    presiding_judges = set()
    presiding_preferred = set()
    presiding_uppreferred = set()
    scoring_judges = set()
    for j in judges:
        # clear match ids
        j.match_id = -1
        if j.hasLawDegree:
            if j.preferredRole and j.preferredRole == "Presiding":
                presiding_preferred.add(j)
            elif j.preferredRole and j.preferredRole == "Scoring":
                presiding_uppreferred.add(j)
            else:
                presiding_judges.add(j)
        else:
            scoring_judges.add(j)
    print(len(presiding_preferred), len(presiding_judges), len(presiding_uppreferred), len(scoring_judges))
    return presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges

def isUnPreferred(judge_id, judges):
    if judges is None or len(judges) == 0:
        return False
    for judge in judges:
        if judge_id == judge.id:
            return True
    return False

def hasMet(team1, team2, judge):
    if judge.teams_met and team1.id not in judge.teams_met and team2.id not in judge.teams_met:
        return True
    return False

def addMetTeam(team1, team2, judge):
    if judge.teams_met:
        judge.teams_met.append(team1.id)
        judge.teams_met.append()(team2.id)
    else:
        judge.teams_met = [team1.id, team2.id]
        flag_modified(judge, "teams_met")

def assign(match, j, judges, role):
    if role == 0:
        match.presiding_judge_id = j.id
        match.presiding_judge_name = j.name
    else:
        if match.scoring_judge_ids:
            match.scoring_judge_ids.append(j.id)
            match.scoring_judge_names.append(j.name)
            flag_modified(match, "scoring_judge_ids")
            flag_modified(match, "scoring_judge_names")
        else:
            match.scoring_judge_ids = [j.id]
            match.scoring_judge_names = [j.name]
    j.assigned += 1
    j.match_id = match.id
    # print(len(judges))
    # print(j.name)
    judges.remove(j) 
    
def assignJugesByTeamPreference(match, team1, team2, team1_unpreferred, team2_unpreferred, team1_preferred, team2_preferred, judges, role):
    assigned = 0
    if team1_preferred is not None:
        candidate = []
        for j in judges:
            if j.preferred_teams and team1.team_name in j.preferred_teams:
                candidate.append(j)  
        for j in candidate:
            if not isUnPreferred(j.id, team2_unpreferred) and not hasMet(team1, team2, j):
                assign(match, j, judges, role)
                assigned = 1
                break
    
    if not assigned and team2_preferred is not None:
        candidate = []
        for j in judges:
            if j.preferred_teams and team2.team_name in j.preferred_teams:
                candidate.append(j) 
        for j in candidate:
            if not isUnPreferred(j.id, team1_unpreferred) and not hasMet(team1, team2, j):
                assign(match, j, judges, role)
                assigned = 1
                break
    return assigned

def assignJudgesByRegionPreference(match, team1, team2, team1_unpreferred, team2_unpreferred, judges, role):
    assigned = 0
    candidate = []
    for j in judges:
        if j.preferred_teams and team1.region in j.preferred_regions:
            candidate.append(j) 
    for j in candidate:
        if not isUnPreferred(j.id, team1_unpreferred) and not isUnPreferred(j.id, team2_unpreferred) and not hasMet(team1, team2, j):
            assign(match, j, judges, role)
            assigned = 1
            break     
    return assigned

def assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, team1_preferred, team2_preferred, judges, role):
    # find judge who  prefers one of the team
    assigned = assignJugesByTeamPreference(match, team1, team2, team1_unpreferred, 
                          team2_unpreferred, team1_preferred, team2_preferred, judges, role)
    if not assigned:
        # find judge who prefers the region of the match
        assigned = assignJudgesByRegionPreference(match, team1, team2, team1_unpreferred, 
                                                    team2_unpreferred, judges, role) 
    if not assigned:
        for j in judges:
            if not isUnPreferred(j.id, team1_unpreferred) and not isUnPreferred(j.id, team2_unpreferred) and not hasMet(team1, team2, j):
                assign(match, j, judges, role)
                assigned = 1
                break
    return assigned
    
    
def assignJudge(presiding_judges, presiding_preferred, presiding_uppreferred, scoring_judges, match):
    team1 = match.teams[0]
    team2 = match.teams[1] 
    # if team1.preferred_by is not None:
    #     team1_preferred = [j.id for j in team1.preferred_by]
    # if team1.unpreferred_by is not None:
    #     team1_unpreferred = [j.id for j in team1.unpreferred_by]
    # if team2.preferred_by is not None:
    #     team2_preferred = [j.id for j in team2.preferred_by]
    # if team2.unpreferred_by is not None:
    #     team2_unpreferred = [j.id for j in team2.unpreferred_by]
    team1_preferred = team1.preferred_by
    team1_unpreferred = team1.unpreferred_by
    team2_preferred = team2.preferred_by
    team2_unpreferred = team2.unpreferred_by
    # assign Presiding judge
    # find judge who has law degree and wanna be a presiding judge
    assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
                    team1_preferred, team2_preferred, presiding_preferred, 0)
    
    # find judge who has law degree and doesn't care about their roles
    if not assigned:
        assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
                    team1_preferred, team2_preferred, presiding_judges, 0)
        
    # find judge who has law degree and doesn't wanna be a presiding judge
    if not assigned:
        assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
                    team1_preferred, team2_preferred, presiding_uppreferred, 0)
    
    if not assigned:
        print("Couldn't find residing judge for this match")

    # assign Scoring judge1
    assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
                    team1_preferred, team2_preferred, scoring_judges, 1)
    if not assigned:
        assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
                    team1_preferred, team2_preferred, presiding_uppreferred, 1)
        
    if not assigned:
        print("Couldn't find a scoring judge for this match")
    else:
        # assign Scoring judge2
        assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
            team1_preferred, team2_preferred, scoring_judges, 1)
        if not assigned:
            assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
            team1_preferred, team2_preferred, presiding_uppreferred, 1)
        
        if not assigned:
            match.scoring_judge_ids.append(match.presiding_judge_id)
            match.scoring_judge_names.append(match.presiding_judge_name)
            flag_modified(match, "scoring_judge_ids")
            flag_modified(match, "scoring_judge_names")
            print("Couldn't find a second scoring judge for this match")
        else:
            # assign Scoring judge3
            assigned = assignJudgesByRolePreference(match, team1, team2, team1_unpreferred, team2_unpreferred, 
            team1_preferred, team2_preferred, scoring_judges, 1)
    
    return
   

        

    
if __name__ == "__main__":
    pass