"""
File that handles GET/POST Requests from FrontEnd
"""
from datetime import *
import os
import shutil
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified
from flask import Flask, jsonify, session, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt, get_jwt_identity, unset_jwt_cookies, jwt_required
from flask_cors import CORS, cross_origin
from flask_migrate import Migrate

from Account import *
from Password import *
from models import *
from config import Config
from Database import Database
from fileUtils import *
from schedules import *
from Zoom import *
from JudgeReassignment import *

def create_app(config):
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.config.from_object(config)

    # Enable Flask-Migrate commands "flask db init/migrate/upgrade" to work
    migrate = Migrate(app, db)

    init_db(app, Database.DEFAULT)
    return app


def init_db(app, db_url):
    # print(db_url)
    app.config.update(
        SQLALCHEMY_DATABASE_URI = db_url
        # SQLALCHEMY_DATABASE_URI = "postgresql+psycopg2://cs407:IBF-MTS-pwd@ibf-mst-cs407.postgres.database.azure.com/Tournament142022?sslmode=require"
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
    
app = create_app(Config)
jwt = JWTManager(app)


"""
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TSL'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEBUG'] = True
app.config['MAIL_USERNAME'] = 'CS407MTS@gmail.com'
app.config['MAIL_PASSWORD'] = 'cs407IBFMTS'
mail = Mail(app)

print("In here!")
        str = ("Thank you for wanting to administer an IBF mock trial competition.\n\n"
               "Here is your authentication code to sign up: TEMPCODE" #+ details[0] +
               "\nTo create your account please go to: localhost:300/create_account.\n"
               "Thank you,\n IBF Team")
        msg = Message("Authentication Code", sender="CS407MTS@outlook.com", body=str, recipients=["szapodeanu19@gmail.com"])
        print("2")
        mail.send(msg)
        print("3")
        return "message"

"""


# The access_token should expire if an account has been inactive for an hour
# This func will check and extend the expiration time to 1 hr if needed after each response 
# @app.after_request
def refresh_expiring_jwts(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now()
        target_timestamp = datetime.timestamp(now + timedelta(minutes=30))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            data = response.get_json()
            print(data)
            print(data["access_token"])
            data["access_token"] = access_token 
            response.data = jsonify(data)
        return response
    except (RuntimeError, KeyError):
        # Case where there is not a valid JWT. Just return the original respone
        return response
    
# Callback function to check if a JWT exists in the database blocklist
@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = db.session.query(TokenBlocklist.id).filter_by(jti=jti).scalar()
    return token is not None


@app.route("/")
def index():
    return "Welcome to our MTS!"

@app.route("/checkSession")
@jwt_required()
@cross_origin()
def checkSession():
    
    return jsonify({"code": 0})


@app.route("/getUser")
@jwt_required()
@cross_origin()
def getUser():
    accounts = [to_dict(user) for user in User.query.all()]
    id = get_jwt_identity()
    user = User.query.get(id)
    response = {"accounts": accounts}
    return jsonify(response)


# https://flask-restful.readthedocs.io/en/latest/reqparse.html
@app.route('/login', methods=["POST"])
@cross_origin()
def Login():
    if request.method == "POST":
        args = request.get_json()
        print(args)
        email = args["email"]
        pwd = args["password"]
        hashed = Password(pwd)
        pwd = hashed.password
        print(pwd)
        ### code to verify
        user = User.query.filter_by(email=email).first()
        if user is None:
            response = {"code": -1, "msg": "Email doesn't exists!"}
        else:
            if user.password != pwd:
                response = {"code": -2, "msg": "Wrong password!"}
            else:
                session["user_id"] = user.id
                access_token = create_access_token(identity=user.id)
                response = {"code": 0, "msg": "Login successfully!", "access_token": access_token, "user": user.to_dict()}
        return jsonify(response)

# Email Connection Setup
# @login_required
@app.route('/logout', methods=["GET", "POST"])
@cross_origin()
@jwt_required()
def Logout():
    if request.method == "GET":
        session.pop('uid', None)
        response = jsonify({"code": 0, "msg": "Logout Successfully"})
        unset_jwt_cookies(response)
        # revoke the access token
        jti = get_jwt()["jti"]
        db.session.add(TokenBlocklist(jti=jti, created_at=datetime.now()))
        db.session.commit()
        return response
    if request.method == "POST":
        session.pop('uid', None)
        response = jsonify({"code": 0, "msg": "Logout Successfully"})
        unset_jwt_cookies(response)
        return response



# Account Creation Related Functions:

@app.route('/sendInvite', methods=["POST"])
@cross_origin()
def sendInvite():
    if request.method == "POST":
        data = request.get_json()
        print(data['email'])
        account = Account(data['email'], "", "", "") # account = User(data['email'], "", "", "")
        unique = account.already_exists()
        
        # same thing as "unique = account.already_exists()"
        # exist_account = User.query.filter_by(email=data['email']).first()
        # if exist_account is not None:
        
        print("unique " + str(unique))
        if unique:
            return {"message": "Error: Account Already Exists", "status": 502}
        details = account.initialize_account()
        print(details)
        
        # authcode = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        # account.authCode = authcode
        # Save the account to the database
        # db.session.add(account)
        # db.session.commit()
        
        if details[1] == 1:
            return {"message": "Account Created Succesfully", "authCode": details[0], "status": 200}
        else:
            return {"message": "Error: Error creating the account", "status": 503}


@app.route('/createAccount', methods=["POST"])
@cross_origin()
def createAccount():
    if request.method == "POST":
        print("hey")
        data = request.get_json()
        print(data)
        password = Password(data['password'])
        account = Account(data['email'], password.password, data['authCode'], 'root')
        print(account)
        isValid = account.verify_account()
        if isValid == 0:
            return {"message": "Account not Found", "status": 404}
        valid_account = Account(data['email'], '', '', '')
        already_created = valid_account.already_exists()
        print(already_created[0][2])
        if already_created[0][2] != "":
            return {"message": "Error: account already created", "status": 502}

        create = account.create_account()

    return {"message": "Account created", "status": 200}



@app.route('/deleteAccount', methods=["POST"])
@cross_origin()
def deleteAccount():
    if request.method == "POST":
        data = request.get_json()
        account = Account(data['email'], "", "", "")
        response = account.delete_account()
        print(response)
        if response == 0:
            return {"message": "Account not real", "status": 502}
        return {"message": "Account deleted Successfully", "status": 200}


@app.route('/editRole', methods=["POST"])
@cross_origin()
def editRole():
    if request.method == "POST":
        data = request.get_json()
        print(data['email'])
        account = Account(data['email'], "", "", "")
        get_account = account.already_exists()
        if not get_account:
            return {"message": "Account not real", "status": 502}
        role = get_account[0][4]
        result = None
        #print(role)
        if role == 'root':
            admins = account.get_admins()
            if admins <= 3:
                return {"message": "Not enough admins remaining", "role": "root", "status": 504}
            result = account.edit_role('admin')
            if result == 1:
                return {"message": "Role changed succesfully", "role": "admin", "status": 200}
            if result == 0:
                return {"message": "Error in changing Roles", "role": "admin", "status": 503}
        else:
            result = account.edit_role('root')
            if result == 1:
                return {"message": "Role changed succesfully", "role": "root", "status": 200}
            if result == 0:
                return {"message": "Error in changing Roles", "role": "root", "status": 503}
    return("IM HERE")

@app.route('/setCode', methods=["POST"])
@cross_origin()
def setCode():
    if request.method == "POST":
        data = request.get_json()
        print(data['code'])
        account = Account("CODE", "", "", "")
        code = account.set_code(data['code'])
        if code == 1:
            return {"message": "AuthCode Changed Succesfully", "status": 200}
    return {"message": "AuthCode Changed Unsuccesfully", "status": 400}


@app.route('/updateAccount', methods=["POST"])
@cross_origin()
def UpdateAccount():
    if request.method == "POST":
        args = request.get_json()


@app.route('/uploadteam', methods=["POST"])
@cross_origin()
def uploadteam():
    tournament_id = int(request.form.get("tournament_id"))
    wild = int(request.form.get("wild"))
    tournament = Tournament.query.get(tournament_id)
    if 'File' not in request.files:
        print('No file part')
        response = {"code": -1, "msg": "no file found"}
        return jsonify(response)
    file = request.files["File"]
    print(file)
    if file.filename == '':
        print('No selected file')
        response = {"code": -2, "msg": "no selected file"}
        return jsonify(response)
    if file:
        if wild == 0:
            path = Database.getTeamFolder(tournament)
            if tournament.team_uploaded == 1:
                removeTeams(tournament, wild)
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except OSError as e:
                    print("Error: %s : %s" % (path, e.strerror))
                    return jsonify({"code": -3, "msg": "Error removing the folder"})
            path = Database.getTeamFolder(tournament)
            filename = os.path.join(path, file.filename)
        else:
            path = Database.getWildFolder(tournament)
            if tournament.wild_uploaded == 1:
                removeTeams(tournament, wild)
                try:
                    shutil.rmtree(path, ignore_errors=True)
                except OSError as e:
                    print("Error: %s : %s" % (path, e.strerror))
                    return jsonify({"code": -3, "msg": "Error removing the folder"})
            path = Database.getWildFolder(tournament)
            filename = os.path.join(path, file.filename)
        file.save(filename)
        wrong_wild_teams, missed_columns = checkInputTeams(tournament, filename, wild)
        print(tournament.to_dict())
        response = {}
        if wrong_wild_teams:
            response["wrong wild"] = 1
            response = {"code": -5, "msg": "wrong wild teams number"}
        if len(missed_columns) == 0:
            tournament.team_uploaded = 1
            db.session.commit()
            response["code"] = 0
            response["msg"] = "teams uploaded"
            return jsonify(response)
        else:
            response = {"code": -4, "msg": "incorrect file format", "missed": missed_columns}
            return jsonify(response)

@app.route('/uploadjudge', methods=["POST"])
@cross_origin()
def uploadjudge():
    tournament_id = int(request.form.get("tournament_id"))
    tournament = Tournament.query.get(tournament_id)
    print(request.files)
    if 'File' not in request.files:
        print('No file part')
        #response = {"code": -1, msg: "no file found"}
        response = {"code": -1, "msg": "no file found"}
        return jsonify(response)
    file = request.files["File"]
    print(file)
    if file.filename == '':
        print('No selected file')
        response = {"code": -2, "msg": "no selected file"}
        return jsonify(response)
    if file:
        if tournament.judge_uploaded == 1:
            removeJudges(tournament)
            path = Database.getJudgeFolder(tournament)
            try:
                shutil.rmtree(path, ignore_errors=True)
            except OSError as e:
                print("Error: %s : %s" % (path, e.strerror))
                return jsonify({"code": -3, "msg": "Error removing the folder"})
        filename = os.path.join(Database.getJudgeFolder(tournament), file.filename)
        file.save(filename)
        missed_columns = checkInputJudge(tournament, filename)
        if len(missed_columns) == 0:
            tournament.judge_uploaded = 1
            db.session.commit()
            response = {"code": 0, "msg": "file uploaded"}
            return jsonify(response)
        else:
            response = {"code": -4, "msg": "incorrect file format", "missed": missed_columns}
            return jsonify(response)

@app.route('/uploadScore', methods=["POST"])
@cross_origin()
def uploadScore():
    tournament_id = request.form.get("tournament_id")
    round_num = int(request.form.get("round_num"))
    tournament = Tournament.query.get(tournament_id)
    if 'File' not in request.files:
        print('No file part')
        #response = {"code": -1, msg: "no file found"}
        response = {"code": -1, "error": "no file found"}
        return jsonify(response)
    file = request.files["File"]
    print(file)
    if file.filename == '':
        print('No selected file')
        response = {"code": -2, "error": "no selected file"}
        return jsonify(response)
    if file:
        filename = os.path.join(Database.getRoundFolder(tournament, round_num), file.filename)
        file.save(filename)
        wrong_courtroom, missed_columns = checkInputScore(tournament, filename, round_num)
        if len(missed_columns) > 0:
            response = {"code": -4, "error": "incorrect file format", "missed": missed_columns}
            return jsonify(response)
        elif wrong_courtroom != -1:
            response = {"code": -5, "error": "courtroom not found", "wrong_courtroom": wrong_courtroom}
            return jsonify(response)
        else:
            if round_num == 5:
                tournament.complete = True
            db.session.commit()
            response = {"code": 0, "success": "file uploaded", "tournament": tournament.to_dict()}
            return jsonify(response)


@app.route('/getTournaments', methods=["POST", "GET"])
@cross_origin()
def getTournaments():
    data = request.get_json()
    uid = data["uid"]
    # uid = get_jwt_identity()
    # head admin, all tournaments - deleted: false
    user = User.query.get(uid)
    if user.role.lower() == "Head".lower() or user.role.lower() == "root".lower():
        tournaments = Tournament.query.filter(Tournament.deleted == False, Tournament.complete == False)
    else:
        # tournaments = Tournament.query.filter(Tournament.deleted == False, Tournament.region == user.region)
        tournaments = Tournament.query.filter(Tournament.creator_id == uid, Tournament.deleted == False, Tournament.complete == False, Tournament.user_region == user.region)
    response = {}
    response["tournaments"]= [tournament.to_dict() for tournament in tournaments]
    print(response["tournaments"])
    response["code"] = 0
    return jsonify(response)

@app.route('/getCompletedTournaments', methods=["POST"])
@cross_origin()
def getCompletedTournaments():
    data = request.get_json()
    uid = data["uid"]
    user = User.query.get(uid)
    if user.role.lower() == "Head".lower() or user.role.lower() == "root".lower():
        tournaments = Tournament.query.filter(Tournament.deleted == False, Tournament.complete == True)
    else:
        tournaments = Tournament.query.filter(Tournament.creator_id == uid, Tournament.deleted == False, Tournament.complete == True, Tournament.user_region == user.region)
    response = {}
    response["tournaments"] = [tournament.to_dict() for tournament in tournaments]
    response["code"] = 0
    return jsonify(response)

@app.route('/getDeletedTournaments', methods=["POST", "GET"])
@cross_origin()
def getDeltedTournaments():
    response = {}
    data = request.get_json()
    uid = data["uid"]
    # uid = get_jwt_identity()
    # head admin, all tournaments - deleted: true
    user = User.query.get(uid)
    tournaments = Tournament.query.filter(Tournament.deleted == True)
    response["tournaments"]= [tournament.to_dict() for tournament in tournaments]
    response["code"] = 0
    # if user.role.lower() == "Head".lower():
    #     tournaments = Tournament.query.filter(Tournament.deleted == True)
    #     response["tournaments"]= [tournament.to_dict() for tournament in tournaments]
    #     response["code"] = 0
    # else:
    #     response["code"] = -1
    #     response["msg"] = "Only Head Admins can retrieve deleted tournaments"
    return jsonify(response)

@app.route('/getRounds', methods=["POST"])
@cross_origin()
def getRounds():
    if request.method == "POST":
        print("Getting Rounds")
        args = request.get_json()
        print(args)
        tournament_id = args["tournament_id"]
        tournament = Tournament.query.get(tournament_id)
        engine = create_engine(tournament.db_url)
        Session = sessionmaker(engine)
        response = {}
        with Session() as session:
            rounds = session.query(Tournament).get(tournament_id).rounds
            response["current_round"] = tournament.current_round
            # rounds_dict = {}
            # for i in range(len(rounds)):
            #     rounds_dict["round"+str(rounds[i].id)] = to_dict(rounds[i])
            # response["rounds"] = rounds_dict
            rounds.sort(key=lambda r: (r.id))
            response["rounds"] = [round.to_dict() for round in rounds]
        response["code"] = 0
        response["tournament"] = tournament.to_dict()
        return jsonify(response)

@app.route('/getRegions', methods=["POST"])
@cross_origin()
def getRegions():
    print("Getting regions")
    args = request.get_json()
    print(args)
    tournament_id = args["tournament_id"]
    round_id = int(args["round_id"])
    # round_num = args["round_num"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    response = {}
    response["tournament"] = tournament.to_dict()
    if round_id >= 4:
        response["regions"] = ["StateWide"]
    else:
        response["regions"] = tournament.regions
    response["code"] = 0
    with Session() as session:
        round = session.query(Round).get(round_id)
        response["round"] = round.to_dict()
        return jsonify(response)

@app.route('/getTeams', methods=["POST"])
@cross_origin()
def getTeams():
    print("Getting Teams...")
    args = request.get_json()
    tournament_id = args["tournament_id"]
    response = {}
    # round_num = args["round_num"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        teams = session.query(Team).filter(Team.wild == 0).all()
        wild = session.query(Team).filter(Team.wild == 1).all()
        if wild:
            teams.extend(wild)
        response["teams"] = [team.to_dict() for team in teams]
    response["code"] = 0
    return jsonify(response)

@app.route('/getJudges', methods=["POST"])
@cross_origin()
def getJudges():
    print("Getting Teams...")
    args = request.get_json()
    tournament_id = args["tournament_id"]
    response = {}
    # round_num = args["round_num"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        judges = session.query(Judge).all()
        response["judges"] = [judge.to_dict() for judge in judges]
    response["code"] = 0
    return jsonify(response)

@app.route('/getScores', methods=["POST"])
@cross_origin()
def getScores():
    print("Getting Scores...")
    args = request.get_json()
    tournament_id = args["tournament_id"]
    response = {}
    # round_num = args["round_num"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        scores = session.query(Scoresheet).all()
        response["teams"] = [score.to_dict() for score in scores]
    response["code"] = 0
    return jsonify(response)

@app.route('/getScoreOverview', methods=["POST"])
@cross_origin()
def getScoreOverview():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    round_id = args["round_id"]
    response = {}
    tournament = Tournament.query.get(tournament_id)
    round = Round.query.get(round_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        matches = session.query(Match).filter(Match.round_id == round_id)
        response["matches"] = [match.to_dict() for match in matches]
    response["code"] = 0
    return jsonify(response)

@app.route('/rankTeams', methods=["POST"])
@cross_origin()
def sort_teams():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    round_num = int(args["round_num"])
    tournament = Tournament.query.get(tournament_id)
    if round_num >= 4:
        region = "StateWide"
    else:
        region = args["region"]
    response = sortTeams(tournament, round_num, region)
    response["code"] = 0
    return jsonify(response)

@app.route('/rankByRole', methods=["POST"])
@cross_origin()
def sort_teams_by_role():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    round_num = int(args["round_num"])
    tournament = Tournament.query.get(tournament_id)
    if round_num >= 4:
        region = "StateWide"
    else:
        region = args["region"]
    response = sortTeamsByRole(tournament, round_num, region)
    response["code"] = 0
    return jsonify(response)
    
@app.route('/createSchedules', methods=["POST"])
@cross_origin()
def createschedules():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    round_num = int(args["round_num"])
    tournament = Tournament.query.get(tournament_id)
    schedules = createSchedules(tournament, round_num)
    return jsonify({"code": 0, "msg": "success", "schedules": schedules})

@app.route('/getSchedule', methods=["POST"])
@cross_origin()
def getschedule():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    round_num = int(args["round_num"])
    if round_num >= 4:
        region = "StateWide"
    else:
        region = args["region"]
    tournament = Tournament.query.get(tournament_id)
    schedule = getSchedule(tournament, round_num, region)
    return jsonify({"code": 0, "msg": "success", "schedule": schedule})

@app.route('/removeT', methods=["POST", "GET"])
@cross_origin()
def RemoveTournament():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    tournament = Tournament.query.get(tournament_id)
    tournament.deleted = True
    db.session.commit()
    return jsonify({"code": 0, "msg": "tournament deleted"})

@app.route('/retrieveT', methods=["POST", "GET"])
@cross_origin()
def RetrieveTournament():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    tournament = Tournament.query.get(tournament_id)
    tournament.deleted = False
    db.session.commit()
    return jsonify({"code": 0, "msg": "tournament deleted"})

@app.route('/deleteT', methods=["POST", "GET"])
@cross_origin()
def DeleteTournament():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        matches = session.query(Match).all()
        for match in matches:
            if match.id != -1 and match.zoom_id:
                deleteMeeting(match.zoom_id)
    Database.delete_tournament_db(tournament)
    path = Database.getTournamentFolder(tournament)
    try:
        shutil.rmtree(path, ignore_errors=True)
    except OSError as e:
        print("Error: %s : %s" % (path, e.strerror))
        return jsonify({"code": -1, "msg": "Error removing the tournament folder"})
    db.session.delete(tournament)
    db.session.commit()
    return jsonify({"code": 0, "msg": "tournament deleted"})

@app.route('/changeTournamentName', methods=["POST", "GET"])
@cross_origin()
def changeName():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    new_name = args["name"]
    tournament = Tournament.query.get(tournament_id)
    tournament.name = new_name
    db.session.commit()
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        m_tournament = session.query(Tournament).get(tournament_id)
        m_tournament.name = new_name
        session.commit()
    return jsonify({"code": 0, "msg": "Rename Success"})

@app.route('/createT', methods=["POST", "GET"])
@cross_origin()
def CreateTournament():
    if request.method == "POST":
        response = {}
        args = request.get_json()
        # uid = get_jwt_identity()
        uid = args["uid"]
        name = args["name"]
        # or get token from the request header and decode to get uid
        user = User.query.get(uid)
        tournament = Tournament(creator_id=uid, name=name, user_region=user.region, complete=False)
        db.session.add(tournament)
        db.session.flush()
        tournament = Database.create_tournament_db(tournament)
        db.session.commit()
        response["tournament"] = tournament.to_dict()
        # create all tables in the new database
        print("create all tables in the new database")
        init_db(app, tournament.db_url)
        print("connect back to the default database")
        # connect back to the default database
        init_db(app, Database.DEFAULT)
        # connect to the database of the tournament
        engine = create_engine(tournament.db_url)
        Session = sessionmaker(engine)
        with Session() as session:
            new_tournament = copyTournament(tournament)
            user = copyUser(User.query.get(uid))
            # teamScore = TeamScore(id=-1)
            match = Match(id=-1)
            session.add(match)
            session.add(user)
            session.add(new_tournament)
            # session.add(teamScore)
            # session.add(current_user)
            session.commit()
        response["code"] = 0
        response["msg"] = "tournament created"
        print(response)
        return jsonify(response)
    if request.method == "POST":
        args = request.get_json(force=True)

# wip stubs
@app.route('/editTeam', methods=["POST"])
@cross_origin()
def editTeam():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    new_name = args["name"]
    new_region = args["region"]
    id = args["id"]
    new_members = list(args["members"].split(","))
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    response = {}
    with Session() as session:
        team = session.query(Team).get(id)
        name_exist = session.query(Team).filter(Team.name == new_name)
        if name_exist is None:
            team.team_name = new_name
        else:
            response["code"] = -1
            response["msg"] = "Team name already exists"
        team.region = new_region
        for i in range(len(new_members)):
            new_members[i] = new_members[i].strip()
        team.members = new_members
        session.commit()
    if "code" not in response:
        response["code"] = 0
        response["msg"] = "team successfully updated!"
    return jsonify(response)

@app.route('/getTeamRoster', methods=["POST"])
@cross_origin()
def getTeamRoster():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    match_id = args["match_id"]
    tournament = Tournament.query.get(tournament_id)
    response = {}
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
         match = session.query(Match).get(match_id)
         teamRoster = match.teamRoster[0]
         response["code"] = 0
         response["teamRoster"] = teamRoster.to_dict()
    return jsonify(response)
         

@app.route('/updateTeamRosterDefense', methods=["POST"])
@cross_origin()
def updateTeamRosterDefense():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    match_id = args["match_id"]
    defense_data = args["defenseData"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        match = session.query(Match).get(match_id)
        teamRoster = match.teamRoster[0]
        teamRoster.defense_witness1 = defense_data["DefenseWitness1"]
        teamRoster.defense_witness2 = defense_data["DefenseWitness2"]
        teamRoster.defense_witness3 = defense_data["DefenseWitness3"]
        teamRoster.defense_attorney1 = defense_data["DefenseAttorney1"]
        teamRoster.defense_attorney2 = defense_data["DefenseAttorney2"]
        teamRoster.defense_attorney2 = defense_data["DefenseAttorney3"]
        teamRoster.defense_time_keeper = defense_data["TimeKeeper"]
        session.commit()
    return jsonify({"code": 0, "msg": "success"})

@app.route('/updateTeamRosterPlaintiff', methods=["POST"])
@cross_origin()
def updateTeamRosterPlaintiff():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    match_id = args["match_id"]
    plaintiff_data = args["plaintiffData"]
    tournament = Tournament.query.get(tournament_id)
    engine = create_engine(tournament.db_url)
    Session = sessionmaker(engine)
    with Session() as session:
        match = session.query(Match).get(match_id)
        teamRoster = match.teamRoster[0]
        teamRoster.plaintiff_witness1 = plaintiff_data["PlaintiffWitness1"]
        teamRoster.plaintiff_witness2 = plaintiff_data["PlaintiffWitness2"]
        teamRoster.plaintiff_witness3 = plaintiff_data["PlaintiffWitness3"]
        teamRoster.prosecution_attorney1 = plaintiff_data["ProsecutionAttorney1"]
        teamRoster.prosecution_attorney2 = plaintiff_data["ProsecutionAttorney2"]
        teamRoster.prosecution_attorney2 = plaintiff_data["ProsecutionAttorney3"]
        teamRoster.plaintiff_time_keeper = plaintiff_data["TimeKeeper"]
        session.commit()
    return jsonify({"code": 0, "msg": "success"})

# @app.route('/updateZoom', methods=["POST"])
# @cross_origin()
# def updateZoom():
#     args = request.get_json()
#     tournament_id = args["tournament_id"]
#     schedule_id = args["schedule_id"]
#     tournament = Tournament.query.get(tournament_id)
#     time = args["time"]
#     schedule = createMeetings(tournament, schedule_id, time)
#     return jsonify({"code": 0, "msg": "success", "schedule": schedule})

@app.route('/changeJudgeAssignment', methods=["POST"])
@cross_origin()
def changeJudgeAssignment():
    args = request.get_json()
    tournament_id = args["tournament_id"]
    new_match = args["match"]
    # print(new_match)
    tournament = Tournament.query.get(tournament_id)
    response = changeJudge(tournament, new_match)
    return jsonify(response)

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)