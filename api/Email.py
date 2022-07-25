from mailjet_rest import Client
import os

def send_email(authCode):
    api_key = 'e33b8c18ed8b016710ed0239dc629ad3'
    api_secret = '547797d4f30d950fe5bbb7e90e956ff0'
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')
    data = {
      'Messages': [
        {
          "From": {
            "Email": "cs407mts@outlook.com",
            "Name": "Stephan"
          },
          "To": [
            {
              "Email": "cs407mts@outlook.com",
              "Name": "Stephan"
            }
          ],
          "Subject": "IBF Mock Trial Invite Code",
          "TextPart": "IBF Mock Trial Code" ,
          "HTMLPart": "Dear admin,<br /> Thank you for wanting to act as an adminsitrator for IBF's mock trial competition. <br /> <br /> Here is the invite code for your account. Please use it when you create your account on localhost:3000/create_account.<br /> <br />Thank you,<br /> IBF TEAM",
          "CustomID": "AppGettingStartedTest"
        }
      ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())