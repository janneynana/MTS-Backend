from sqlalchemy import ARRAY, Float, ForeignKey, Column, Integer, PickleType, String, Boolean, MetaData, Table
meta = MetaData()


account = Table(
    "account", meta,
    Column("id", Integer, primary_key=True),
    Column("email", String(100)),
    Column("password", String(100)),
    Column("authCode", String(100)),
    Column("region", String(100)),
    Column("role", String(100), default="admin"), 
    Column("security_question", String(200)),
    Column("answer", String(100)),
)           
               
               
   


tournament = Table("tournament", meta,
        Column("id", Integer, primary_key=True),
        Column("name", String(100), default=""),
        Column("db_name", String(100)),
        Column("year", Integer),
        Column("creator_id", Integer, ForeignKey("account.id")),
        Column("current_round", Integer, default=0), # 0: haven't started; -1: Completed; 1-3: Regional Round; 4: State Final; 5: Championship Trial
        Column("regions", ARRAY(String)),
        Column("user_region", ARRAY(String)),
        Column("team_uploaded", Integer, default=0), # 0: haven't uploaded teams yet; 1: team uploaded
        Column("judge_uploaded", Integer, default=0), # 0: haven't uploaded judges yet; 1: judge uploaded
        Column("wild_uploaded", Integer, default=0), # 0: haven't uploaded wild card teams yet; 1: wild card teams uploaded
        Column("deleted", Boolean, default=False),
        Column("db_url", String(200)),
        Column("complete", Boolean, default=False),
)

round = Table(
    "round", meta,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("tournament_id", Integer, ForeignKey('tournament.id')),
    Column("status", Integer, default=0), # 0: ongoing, 1: finished
    Column("bye_teams", PickleType), # region:team_id
)


team = Table(
    "team", meta,
    Column("id", Integer, primary_key=True),
    Column("wild", Integer, default=0),
    Column("team_name", String(100)),
    Column("tournament_id", Integer, ForeignKey("tournament.id", ondelete="CASCADE")),
    Column("current_match_id", Integer, ForeignKey("match.id")),
    Column("members", ARRAY(String(100))),
    Column("region", String(100)),
    Column("role", Integer, default=-1), # 0 for Defense, 1 for Plaintiff, -1 for not played in the last round
    Column("opponent_ids", ARRAY(Integer)), # ids of the oponent teams the team has met
    Column("trial_wins", Float, default=0.0),
    Column("ballots", Float, default=0.0),
    Column("total_points", Float, default=0.0),
    Column("point_differential", Float, default=0.0),
    Column("rounds_participated", ARRAY(Integer)),
)
    
preferred = Table(
    "preferred", meta,
    Column("id", Integer, primary_key=True),
    Column("judge_id", Integer, ForeignKey("judge.id"), primary_key=True),
    Column("team_id", Integer, ForeignKey("team.id"), primary_key=True)
)


unpreferred = Table(
    "unpreferred", meta,
    Column("id", Integer, primary_key=True),
    Column("judge_id", Integer, ForeignKey("judge.id"), primary_key=True),
    Column("team_id", Integer, ForeignKey("team.id"), primary_key=True)
)

judge = Table(
    "judge", meta,
    Column("id", Integer, primary_key=True),
    Column("name", String(100)),
    Column("email", String(100), nullable=True),
    Column("hasLawDegree", Boolean),
    Column("preferredRole", String),
    Column("preferredRegions", ARRAY(String)),
    Column("preferred_teams", ARRAY(String)),
    Column("unpreferred_teams", ARRAY(String)),
    Column("assigned", Integer, default=0),
    Column("teams_met", ARRAY(Integer)),
    Column("role", PickleType),
    Column("tournament_id", Integer, ForeignKey("tournament.id", ondelete="CASCADE")),
    Column("match_id", Integer, ForeignKey("match.id")),

)

schedule = Table(
    "schedule", meta,
     Column("id", Integer, primary_key=True),
     Column("competition_name", String(100)),
     Column("region", String(100)),
     Column("round_id", Integer, ForeignKey("round.id")),
     Column("bye_team_id", Integer),
     Column("formatted", Boolean, default=False),
     Column("time", String),
)


match = Table(
    "match", meta,
    Column("id", Integer, primary_key=True),  # courtroom id
    Column("round_id", Integer, ForeignKey("round.id")),
    Column("schedule_id", Integer, ForeignKey("schedule.id", ondelete="CASCADE")),
    Column("time", String),
    Column("zoom_link", String(200), default=""),
    Column("zoom_id", String(100)),
    Column("team_ids", ARRAY(Integer)),
    Column("team_names", ARRAY(String)),
    Column("defense_team_id", Integer),
    Column("plaintiff_team_id", Integer),
    Column("winner_team", String, default=""),
    Column("presiding_judge_id", Integer),
    Column("scoring_judge_ids", ARRAY(Integer)),
    Column("presiding_judge_name", String),
    Column("scoring_judge_names", ARRAY(String)),
    Column("plaintiff_score", Float, default=0),
    Column("defense_score", Float, default=0),
    Column("bestWitness", String),
    Column("bestAttorney", String),
    Column("defense_score", Float),
    Column("plaintiff_score", Float),
)

team_roster = Table(
    "team_roster", meta,
    Column("id", Integer, primary_key=True),
    Column("match_id", Integer, ForeignKey("match.id", ondelete="CASCADE")),
    Column("defense_team", String),
    Column("plaintiff_team", String),
    Column("plaintiff_witness1", String, default=""),
    Column("plaintiff_witness2", String, default=""),
    Column("plaintiff_witness3", String, default=""),
    Column("prosecution_attorney1", String, default=""),
    Column("prosecution_attorney2", String, default=""),
    Column("prosecution_attorney3", String, default=""),
    Column("plaintiff_time_keeper", String, default=""),
    Column("plaintiff_members", ARRAY(String)),
    Column("defense_witness1", String, default=""),
    Column("defense_witness2", String, default=""),
    Column("defense_witness3", String, default=""),
    Column("defense_attorney1", String, default=""),
    Column("defense_attorney2", String, default=""),
    Column("defense_attorney3", String, default=""),
    Column("defense_time_keeper", String, default=""),
    Column("defense_members", ARRAY(String)),
)

score = Table(
    "score", meta,
    Column("id", Integer, primary_key=True),
    Column("match_id", Integer, ForeignKey("match.id", ondelete="CASCADE")),
    Column("defense_team_id", Integer, ForeignKey("team.id")),
    Column("plaintiff_team_id", Integer, ForeignKey("team.id")),
    Column("defense_team", String),
    Column("plaintiff_team", String),
    Column("defense_score", Float),
    Column("plaintiff_score", Float),
    Column("defense_result", String),
    Column("plaintiff_result", String),
    Column("ballot", Integer) # The id of the winning team,
)
