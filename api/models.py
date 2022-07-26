import json
from math import fabs
from multiprocessing.dummy import Array
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ARRAY, Float, ForeignKey, Column, Integer, PickleType, String, Boolean, DateTime, Table
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.declarative import DeclarativeMeta

db = SQLAlchemy()
Base = declarative_base()


class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False)

class User(db.Model):
    # __bind__key__ = "default"
    __tablename__ = "account"
    id = Column(Integer, primary_key=True)
    email = Column(String(100))
    password = Column(String(100))
    authCode = Column(String(100))
    region = Column(String(100))
    role = Column(String(100), default="admin") 
    # tournaments = Column(ARRAY(String(100))) 

    # relationship
    tournaments = relationship("Tournament", backref="creator")
    
    def to_dict(self):
        fields = {}
        fields['id'] = self.id
        fields['email'] = self.email
        fields['role'] = self.role
        return fields

class Tournament(db.Model):
    __tablename__ = "tournament"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), default="")
    db_name = Column(String(100))
    year = Column(Integer)
    creator_id = Column(Integer, ForeignKey("account.id"))
    current_round = Column(Integer, default=0) # 0: haven't started; -1: Completed; 1-3: Regional Round; 4: State Final; 5: Championship Trial
    regions = Column(ARRAY(String))
    team_uploaded = Column(Integer, default=0) # 0: haven't uploaded teams yet; 1: team uploaded
    judge_uploaded = Column(Integer, default=0) # 0: haven't uploaded judges yet; 1: judge uploaded
    wild_uploaded = Column(Integer, default=0) # 0: haven't uploaded wild card teams yet; 1: wild card teams uploaded
    deleted = Column(Boolean, default=False)
    db_url = Column(String(200))

    #relationships
    # creator = relationship("User", back_populates="tournaments", foreign_keys=[creator_id])
    teams = relationship("Team", backref="tournament")
    judges = relationship("Judge", backref="tournament")
    rounds = relationship("Round", backref="tournament")
    
    def to_dict(self):
        fields = {}
        fields["id"] = self.id
        fields["name"] = self.name
        fields["year"] = self.year
        fields["regions"] = self.regions
        fields["team_uploaded"] = self.team_uploaded
        fields["judge_uploaded"] = self.judge_uploaded
        fields["wild_uploaded"] = self.wild_uploaded
        fields["current_round"] = self.current_round
        return fields
        
    def __repr__(self):
        return '<Tournament %r>' % str(self.id) + " created by " + str(self.creator_id)
    
class Round(db.Model):
    __tablename__ = "round"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    tournament_id = Column(Integer, ForeignKey('tournament.id'))
    status = Column(Integer, default=0) # 0: ongoing, 1: finished
    bye_teams = Column(PickleType) # region:team_id
    
    # relationship
    schedules = relationship("Schedule", back_populates="round")
    matches = relationship("Match", back_populates="round")
    
    def to_dict(self):
        fields = {}
        fields["id"] = self.id
        fields["name"] = self.name
        fields["tournament_id"] = self.tournament_id
        fields["status"] = self.status
        return fields
    
class Team(db.Model):
    __tablename__ = "team"
    id = Column(Integer, primary_key=True)
    wild = Column(Integer, default=0)
    team_name =  Column(String(100))
    tournament_id = Column(Integer, ForeignKey("tournament.id", ondelete="CASCADE"))
    current_match_id = Column(Integer, ForeignKey("match.id"))
    members = Column(ARRAY(String(100)))
    region = Column(String(100))
    role = Column(Integer, default=-1) # 0 for Defense, 1 for Plaintiff, -1 for not played in the last round
    opponent_ids = Column(ARRAY(Integer)) # ids of the oponent teams the team has met
    # preferred_judge_ids = Column(ARRAY(Integer))
    # preferred_judge_ids = Column(ARRAY(Integer))
    trial_wins = Column(Float, default=0.0)
    ballots = Column(Float, default=0.0)
    total_points = Column(Float, default=0.0)
    point_differential = Column(Float, default=0.0)
    rounds_participated = Column(ARRAY(Integer))
    # round1_score_id = Column(Integer, ForeignKey("team_score.id"), default=-1) # -1 means no score yet
    # round2_score_id = Column(Integer, ForeignKey("team_score.id"), default=-1)
    # round3_score_id = Column(Integer, ForeignKey("team_score.id"), default=-1)
    # round4_score_id = Column(Integer, ForeignKey("team_score.id"), default=-1)
    # round5_score_id = Column(Integer, ForeignKey("team_score.id"), default=-1)
    
    # relationship
    # defense_match = relationship('Match', foreign_keys='Match.defense_team_id', backref='defense_team', lazy=True)
    # plaintiff_match = relationship('Match', foreign_keys='Match.plaintiff_team_id', backref='plaintiff_team', lazy=True)
    preferred_by = relationship('Judge', secondary="preferred", back_populates="preferredTeams")
    unpreferred_by = relationship('Judge', secondary="unpreferred", back_populates="unpreferredTeams")
    # defense_score = relationship('Scoresheet', foreign_keys='Scoresheet.defense_team_id', backref='defense_team', lazy=True)
    # plaintiff_score = relationship('Scoresheet', foreign_keys='Scoresheet.plaintiff_team_id', backref='plaintiff_team', lazy=True)

    def __repr__(self):
        return '<Team %r>' % str(self.id) + ' ' + self.team_name
    
    def to_dict(self):
        fields = {}
        fields["id"] = self.id
        fields["name"] = self.team_name
        fields["region"] = self.region
        if self.role == 0:
            fields["role"] = "Defense"
        elif self.role == 1:
            fields["role"] = "Plaintiff"
        fields["members"] = self.members
        return fields

class TeamScore(db.Model):
    __tablename__ = "team_score"
    id = Column(Integer, primary_key=True)
    team_id = Column(Integer)
    trial_wins = Column(Float, default=0.0)
    ballots = Column(Float, default=0.0)
    total_points = Column(Float, default=0.0)
    point_differential = Column(Float, default=0.0)
    
    # relationship
    # round1 = relationship('Team', foreign_keys='Team.round1_score_id', backref='round1_score', lazy=True)
    # round2 = relationship('Team', foreign_keys='Team.round2_score_id', backref='round2_score', lazy=True)
    # round3 = relationship('Team', foreign_keys='Team.round3_score_id', backref='round3_score', lazy=True)
    # round4 = relationship('Team', foreign_keys='Team.round4_score_id', backref='round4_score', lazy=True)
    # round5 = relationship('Team', foreign_keys='Team.round5_score_id', backref='round5_score', lazy=True)
    
    def add(self, score):
        self.trial_wins += score.trial_wins
        self.ballots += score.ballots
        self.total_points += score.total_points
        self.point_differential  += score.point_differential

class Preferred(db.Model):
    __tablename__ = "preferred"
    id = db.Column(db.Integer, primary_key=True)
    judge_id = Column(Integer, ForeignKey("judge.id"), primary_key=True)
    team_id = Column(Integer, ForeignKey("team.id"), primary_key=True)


class Unpreferred(db.Model):
    __tablename__ = "unpreferred"
    id = db.Column(db.Integer, primary_key=True)
    judge_id = Column(Integer, ForeignKey("judge.id"), primary_key=True)
    team_id = Column(Integer, ForeignKey("team.id"), primary_key=True)

class Judge(db.Model):
    __tablename__ = "judge"
    id = Column(Integer, primary_key=True)
    name =  Column(String(100))
    email = Column(String(100), nullable=True)
    hasLawDegree = Column(Boolean)
    preferredRole = Column(String)
    preferredRegions = Column(ARRAY(String))
    preferred_teams = Column(ARRAY(String))
    unpreferred_teams = Column(ARRAY(String))
    assigned = Column(Integer, default=0)
    teams_met = Column(ARRAY(Integer))
    role = Column(PickleType)
    # How to use it?
    # judge = Judge(name="judge1")
    # judge.role['1'] = 'sth'
    tournament_id = Column(Integer, ForeignKey("tournament.id", ondelete="CASCADE"))
    match_id = Column(Integer, ForeignKey("match.id"))

    # relationship
    # tournament = relationship("Tournament", back_populates="judges", foreign_keys=[tournament_id])
    preferredTeams = relationship("Team", secondary="preferred", back_populates="preferred_by")
    unpreferredTeams = relationship("Team", secondary="unpreferred", back_populates="unpreferred_by")
    
    def to_dict(self):
        fields = {}
        fields["id"] = self.id
        fields["name"] = self.name
        fields["email"] = self.email
        fields["hasLawDegree"] = self.hasLawDegree
        fields["preferredRole"] = self.preferredRole
        fields["preferredRegions"] = self.preferredRegions
        fields["preferred teams"] = self.preferred_teams
        fields["unpreferred teams"] = self.unpreferred_teams
        return fields

    def __repr__(self):
        return '<Judge %r>' % self.name + ' ' + self.email

class Schedule(db.Model):
    __tablename__ = "schedule"
    id = Column(Integer, primary_key=True)
    competition_name = Column(String(100))
    region = Column(String(100))
    round_id = Column(Integer, ForeignKey("round.id"))
    bye_team_id = Column(Integer)
    formatted = Column(Boolean, default=False)
    time = Column(String)

    # relationship
    matches = relationship("Match", back_populates="schedule", lazy='subquery')
    formattedMatches = relationship("FormattedMatch", back_populates="schedule")
    round = relationship("Round", back_populates="schedules")
    # tournament = relationship("Tournament", back_populates="schedules")
    
    def to_dict(self):
        fields = {}
        fields["id"] = self.id
        fields["time"] = self.time
        fields["region"] = self.region
        fields["round_id"] = self.round_id
        fields["competition_name"] = self.competition_name
        return fields

    def __repr__(self):
        return '<Schedule %r>' % str(self.id) + ' ' + self.competition_name

class FormattedMatch(db.Model):
    __tablename__ = "formatted_match"
    schedule_id = Column(Integer, ForeignKey("schedule.id", ondelete="CASCADE"))
    courtroom = Column(Integer, primary_key=True)  # match id
    teams = Column(PickleType)
    sides = Column(PickleType)
    winner_team = Column(String, default="")
    presidingJudge = Column(String, default="")
    scoringJudgeFirst = Column(String, default="")
    scoringJudgeSecond = Column(String, default="")
    scoringJudgeThird = Column(String, default="")
    zoomLink = Column(String, default="")
    bestWitness = Column(String, default="")
    bestAttorney = Column(String, default="")
    
    # relationship
    schedule = relationship("Schedule", back_populates="formattedMatches")

class Match(db.Model):
    __tablename__ = "match"
    id = Column(Integer, primary_key=True)  # courtroom id
    round_id = Column(Integer, ForeignKey("round.id"))
    schedule_id = Column(Integer, ForeignKey("schedule.id", ondelete="CASCADE"))
    time = Column(String)
    zoom_link = Column(String(200), default="")
    zoom_id = Column(String(100))
    team_ids = Column(ARRAY(Integer))
    team_names = Column(ARRAY(String))
    defense_team_id = Column(Integer)
    plaintiff_team_id = Column(Integer)
    winner_team = Column(String, default="")
    presiding_judge_id = Column(Integer)
    scoring_judge_ids = Column(ARRAY(Integer))
    presiding_judge_name = Column(String)
    scoring_judge_names = Column(ARRAY(String))
    bestWitness = Column(String)
    bestAttorney = Column(String)

    # relationship
    scores = relationship("Scoresheet", back_populates="match")
    round = relationship("Round", back_populates="matches")
    schedule = relationship("Schedule", back_populates="matches", lazy='subquery')
    teamRoster = relationship("TeamRoster", back_populates="match")
    

    def __repr__(self):
        return '<Match %r>' % str(self.id)

class TeamRoster(db.Model):
    __tablename__ = "team_roster"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("match.id", ondelete="CASCADE"))
    defense_team = Column(String)
    plaintiff_team = Column(String)
    plaintiff_witness1 = Column(String, default="")
    plaintiff_witness2 = Column(String, default="")
    plaintiff_witness3 = Column(String, default="")
    prosecution_attorney1 = Column(String, default="")
    prosecution_attorney2 = Column(String, default="")
    prosecution_attorney3 = Column(String, default="")
    plaintiff_time_keeper = Column(String, default="")
    plaintiff_members = Column(ARRAY(String))
    defense_witness1 = Column(String, default="")
    defense_witness2 = Column(String, default="")
    defense_witness3 = Column(String, default="")
    defense_attorney1 = Column(String, default="")
    defense_attorney2 = Column(String, default="")
    defense_attorney3 = Column(String, default="")
    defense_time_keeper = Column(String, default="")
    defense_members = Column(ARRAY(String))
    
    
    # relationship
    match = relationship("Match", back_populates="teamRoster")
    
    def to_dict(self):
        fields = {}
        defenseData = {}
        plaintiffData = {}
        defenseData["teamName"] = self.defense_team
        defenseData["DefenseWitness1"] = self.defense_witness1
        defenseData["DefenseWitness2"] = self.defense_witness2
        defenseData["DefenseWitness3"] = self.defense_witness3
        defenseData["DefenseAttorney1"] = self.defense_attorney1
        defenseData["DefenseAttorney2"] = self.defense_attorney2
        defenseData["DefenseAttorney3"] = self.defense_attorney3
        defenseData["TimeKeeper"] = self.defense_time_keeper
        defenseData["members"] = self.defense_members
        plaintiffData["PlaintiffWitness1"] = self.plaintiff_witness1
        plaintiffData["PlaintiffWitness2"] = self.plaintiff_witness2
        plaintiffData["PlaintiffWitness3"] = self.plaintiff_witness3
        plaintiffData["ProsecutionAttorney1"] = self.prosecution_attorney1
        plaintiffData["ProsecutionAttorney2"] = self.prosecution_attorney2
        plaintiffData["ProsecutionAttorney3"] = self.prosecution_attorney3
        plaintiffData["TimeKeeper"] = self.plaintiff_time_keeper
        plaintiffData["members"] = self.plaintiff_members
        plaintiffData["teamName"] = self.plaintiff_team
        fields["defenseData"] = defenseData
        fields["plaintiffData"] = plaintiffData
        return fields

class Scoresheet(db.Model):
    __tablename__ = "score"
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey("match.id", ondelete="CASCADE"))
    defense_team_id = Column(Integer, ForeignKey("team.id"))
    plaintiff_team_id = Column(Integer, ForeignKey("team.id"))
    defense_team = Column(String)
    plaintiff_team = Column(String)
    defense_score = Column(Float)
    plaintiff_score = Column(Float)
    defense_result = Column(String)
    plaintiff_result = Column(String)
    ballot = Column(Integer) # The id of the winning team

    # relationship
    match = relationship("Match", back_populates="scores")
    
    def to_dict(self):
        fields = {}
        fields["id"] = self.id
        fields["courtroom"] = self.match_id
        fields["defense"] = self.defense_team
        fields["plaintiff"] = self.plaintiff_team
        fields["defense score"] = self.defense_score
        fields["plaintiff score"] = self.plaintiff_score
        fields["defense result"] = self.defense_result
        fields["plaintiff result"] = self.plaintiff_result
        fields["ballot"] = self.ballot
        return fields

    def __repr__(self):
        return '<Scoresheet %r>' % str(self.id)


def to_dict(obj):
    if isinstance(obj.__class__, DeclarativeMeta):
        # an SQLAlchemy class
        fields = {}
        for field in [x for x in dir(obj) if not x.startswith('_') and x != 'metadata']:
            data = obj.__getattribute__(field)
            try:
                json.dumps(data)  # this will fail on non-encodable values, like other classes
                if data is not None:
                    fields[field] = data
            except TypeError:
                pass
        # a json-encodable dict
        return fields

def copyUser(user):
    return User(id=user.id, email=user.email, password=user.password, role=user.role)

def copyTournament(tournament):
    return Tournament(id=tournament.id, creator_id=tournament.creator_id, db_name=tournament.db_name,
                      name=tournament.name, year=tournament.year, db_url=tournament.db_url)