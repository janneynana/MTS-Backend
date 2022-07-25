import jwt
from numpy import mat
import requests
import json
from time import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import flag_modified

# from .models import *
# from .Database import *
from models import *
from Database import *

# Enter your API key and your API secret
API_KEY = 'I3L5b4rMSgWRkLH9gEwxNA'
API_SEC = 'XBB3jOruq8TXxtXN7yMmbyEwOL5PLvhByYKg'

# create a function to generate a token
# using the pyjwt library


def generateToken():
	token = jwt.encode(

		# Create a payload of the token containing
		# API Key & expiration time
		{'iss': API_KEY, 'exp': time() + 5000},

		# Secret used to generate token signature
		API_SEC,

		# Specify the hashing alg
		algorithm='HS256'
	)
	return token



# send a request with headers including
# a token and meeting details

# def createMeetings(tournament, schedule_id):
#     engine = create_engine(tournament.db_url)
#     Session = sessionmaker(engine)
#     with Session() as session:
#         schedule = session.query(Schedule).get(schedule_id)
#         matches = schedule.matches
#         for match in matches:
#             if match.zoom_id:
#                 deleteMeeting(match.zoom_id)
#             id, link, pwd = createMeeting(match)
#             match.zoom_id = id
#             match.zoom_link = link
#         session.commit()
#         formatted_schedule = getSchedule(tournament, schedule.round_id, schedule.region)
#     return formatted_schedule
            
    

def createMeeting(match):
    # create json data for post requests
    meetingdetails = {"topic": "MockTrial Courtroom " + str(match.id),
				"type": 2,
				"start_time": match.time,
				"duration": "120",
				"timezone": "UTC",
				"agenda": "test",
				"recurrence": {"type": 1,
								"repeat_interval": 1
								},
				"settings": {"host_video": "true",
                 			# "alternative_hosts": "jchill@example.com;thill@example.com",
							# "alternative_hosts_email_notification": "True",
							"participant_video": "true",
							"email_notification": "true",
							"join_before_host": "True",
							"mute_upon_entry": "False",
							"watermark": "true",
							"audio": "voip",
							"auto_recording": "cloud"
							}
				}
    
    headers = {'authorization': 'Bearer ' + generateToken(),
			'content-type': 'application/json'}
    
    r = requests.post(
		f'https://api.zoom.us/v2/users/me/meetings',
		headers=headers, data=json.dumps(meetingdetails))
    
    # print("\n creating zoom meeting ... \n")
    y = json.loads(r.text)
    # print(y)
    join_URL = y["join_url"]
    meeting_id = y["id"]
    meetingPassword = y["password"]
    # print(
	# 	f'\nzoom meeting link {join_URL}\
	# 	\npassword: "{meetingPassword}"\n')
    
    return meeting_id, join_URL
 
def deleteMeeting(id):
    headers = {'authorization': 'Bearer ' + generateToken(),
			'content-type': 'application/json'}
    response = requests.delete(
		f'https://api.zoom.us/v2/meetings/{id}',
		headers=headers)
	

# run the create meeting function
# my_time = "2022-07-22T8: 15: 00"
# meeting_id, join_URL, meetingPassword = createMeeting(my_time)


