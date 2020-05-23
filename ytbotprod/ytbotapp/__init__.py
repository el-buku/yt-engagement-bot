from flask import Flask
import asyncio
from ytbotapp.classes import Scanner
import json


# def scanscanscan():
#     try:
#         with open('scanners.json') as scanrs:
#             scanners=json.load(scanrs)
#     except:
#         scanners={}
#     for scanner in scanners:
#         activ=Scanner(scanner, scanners[scanner][0], scanners[scanner][1])
#         #future=executor.submit(target=asyncio.run(activ.scan()))
#         #procproc.start()
#         asyncio.run(activ.scan())

app=Flask(__name__)
with open('config.json') as config_file:
  config = json.load(config_file)
app.config['SECRET_KEY']=config.get('SECRET_KEY')
#CLIENT_SECRETS_FILE = "clientsecret.json"
#YOUTUBE_READ_WRITE_SSL_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"#, https://www.googleapis.com/auth/userinfo.profile"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
# app.config['MONGO_URI']='mongodb+srv://dbuser:dbpass@cluster0-ek49r.mongodb.net/test?retryWrites=true&w=majority'
# mongo=PyMongo(app)
# comments=mongo.db.comments
# comments.insert_one({'usr':{'listapulii':['comentariupulii','fuckss..////ssd@##', 'comentariupulii2'], 'lisstapooli':['randomcomm', 'randomstr']}})
# print(dict(comments.distinct('usr')[0]))
#scanscanscan()
from ytbotapp import routes