from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import random
import json
import datetime
from pyppeteer import launch
import asyncio
from time import sleep
from bs4 import BeautifulSoup
import requests
import lxml

CLIENT_SECRETS_FILE='clientsecret.json'
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
with open('config.json') as config_file:
  config = json.load(config_file)
APIKEY=config.get('APIKEY')
def getchannelname(channelid):
    r=requests.get(f'https://www.youtube.com/channel/{channelid}/videos')
    soup=BeautifulSoup(r.text,'lxml')
    title=soup.find('meta', {"itemprop":"name"}).attrs['content']
    return title.strip()
def getvidoname(vidid):
    r=requests.get(f'https://www.youtube.com/watch?v={vidid}')
    soup=BeautifulSoup(r.text, 'lxml')
    title=soup.find('meta', {"property":"og:title"}).attrs['content']
    return title.strip()
class CommTask():
    def __init__(self, name, channelid, commentlist, num, acc):
        self.name=name
        self.channelid=channelid
        self.commentlist=commentlist
        self.num=num
        self.acc=acc
    
    def get_authenticated_service(self):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes="https://www.googleapis.com/auth/youtube.force-ssl")
            creds = Credentials.from_authorized_user_file(f'{self.acc}auth.json')
            return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=APIKEY, credentials=creds)
        except:
            with open('errors.json') as er:
                errors=json.load(er)                         
                errors.update({f'Could not add random comment to channel <a href="https://www.youtube.com/channel/{self.channelid}">{getchannelname(self.channelid)}</a>, account {self.acc} was deleted.':''})
                with open('errors.json', 'w') as erw:
                    json.dump(errors,erw) 

    def getvideoidlist(self):
        ytapi=self.get_authenticated_service()
        request = ytapi.search().list(
        part="snippet",
        channelId=self.channelid,
        maxResults=50
    )
        videos = request.execute()
        #videos=json.load(response)
        videoIDlist=[]
        for video in videos['items']:
            if video['id']['kind'] == 'youtube#video':
                videoIDlist.append(tuple(([video['id']['videoId'], video['snippet']['title'], video['snippet']['channelTitle']])))
        return videoIDlist
    def addcomment(self, videoID, comment):#, gid, videoid, text):
        request = self.get_authenticated_service().commentThreads().insert(
            part="snippet",
            body={
            "snippet": {
                "videoId": videoID[0],
                "topLevelComment": {
                "snippet": {
                    "textOriginal": comment
                }
                }
            }
            }
        )
        try:
            response=request.execute()
            datepublished=str(datetime.datetime.now())#response['snippet']['topLevelComment']['snippet']['publishedAt']
            commdata={videoID[0]:[videoID[1], videoID[2], comment, self.acc, datepublished, 'random comment']}
            try:
                with open('commentdata.json') as data:
                    datadict=json.load(data)
                    datadict.update(commdata)
                    with open('commentdata.json', 'w+') as data:
                        json.dump(datadict, data)       
            except:
                with open('commentdata.json', 'w+') as data:
                    json.dump(commdata, data)      
            print(commdata)
        except:
            with open('errors.json') as er:
                errors=json.load(er)                         
                errors.update({f'Could not add random comment to <a href="https://www.youtube.com/watch?v={videoID[0]}">{videoID[1]}</a> using account {self.acc}. Make sure you are using a Gmail account with a YouTube channel and have not excedeed 150 comments today':''})
                with open('errors.json', 'w') as erw:
                    json.dump(errors,erw) 

    def randomidlist(self):
        vididlist=self.getvideoidlist()
        # randlist=set()
        # size=len(vididlist)
        # for i in range(int(self.num)):
        #     rand=random.randrange(size)
        #     randlist.add(vididlist[rand])
        randlist=random.sample(vididlist, int(self.num))
        print(randlist)
        return list(randlist)

    def execute(self):
        with open('comms.json') as comms:
            commentlists=json.load(comms)
            for id in self.randomidlist():
                self.addcomment(id, random.choice(commentlists[self.commentlist]))


class Scanner():
    def __init__(self, channelid, commentlist, acc):
        self.channelid=channelid
        self.commentlist=commentlist
        self.acc=acc
        self.channelslastvid=''
    
    async def scan(self):
        browser = await launch(handleSIGINT=False, handleSIGTERM=False, handleSIGHUP=False, args=['--proxy-server= 45.76.10.181:8080','--no-sandbox'])#, headless=False)
        page = await browser.newPage()
        await page.setUserAgent("Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)")
        await page.goto(f'https://www.youtube.com/channel/{self.channelid}/videos')
        x=await page.querySelector('.yt-uix-tile-link')
        p= await x.getProperty('href')
        lastid=p.toString().split('=')[1]
        await browser.close()
        try:
            with open('channelslastvid.json') as lv:
                videodict= json.load(lv)
        except:
            videodict={}
        if self.channelid not in videodict:
            videodict[self.channelid]=lastid
            with open('channelslastvid.json', 'w+') as lv:
                json.dump(videodict, lv)
            print('first scan')
        elif videodict[self.channelid]==lastid:
            print('no new vid')
        elif videodict[self.channelid]!=lastid:
            print('has new vid')
            videodict[self.channelid]=lastid
            with open('channelslastvid.json', 'w+') as lv:
                json.dump(videodict, lv)
            self.isnewvideo(lastid)

    def get_authenticated_service(self):
        try:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes="https://www.googleapis.com/auth/youtube.force-ssl")
            creds = Credentials.from_authorized_user_file(f'{self.acc}auth.json')
            return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=APIKEY, credentials=creds)
        except:
            with open('errors.json') as er:
                errors=json.load(er)                         
                errors.update({f'Could not add scanner comment to channel <a href="https://www.youtube.com/channel/{self.channelid}">{getchannelname(self.channelid)}</a>, account {self.acc} was deleted.':''})
                with open('errors.json', 'w') as erw:
                    json.dump(errors,erw) 
    
    def addcomment(self, videoID, comment):#, gid, videoid, text):
        request = self.get_authenticated_service().commentThreads().insert(
            part="snippet",
            body={
            "snippet": {
                "videoId": videoID,
                "topLevelComment": {
                "snippet": {
                    "textOriginal": comment
                }
                }
            }
            }
        )
        try:
            response=request.execute()
            videoname=getvidoname(videoID)
            channelname=getchannelname(self.channelid)
            datepublished=str(datetime.datetime.now())#response['snippet']['topLevelComment']['snippet']['publishedAt']
            commdata={videoID:[videoname, channelname, comment, self.acc, datepublished, 'scanner comment', self.channelslastvid]}
            try:
                with open('commentdata.json') as data:
                    datadict=json.load(data)
                    datadict.update(commdata)
                    with open('commentdata.json', 'w+') as data:
                        json.dump(datadict, data)       
            except:
                with open('commentdata.json', 'w+') as data:
                    json.dump(commdata, data)      
            print(commdata)
        except:
            with open('errors.json') as er:
                errors=json.load(er)                         
                errors.update({f'Could not add scanner comment to <a href="https://www.youtube.com/watch?v={videoID[0]}">{videoID[1]}</a> using account {self.acc}. Make sure you are using a proper Gmail account and have not excedeed 150 comments today':''})
                with open('errors.json', 'w') as erw:
                    json.dump(errors,erw)

    def isnewvideo(self, videoid):
        with open('comms.json') as comms:
            commentlists=json.load(comms)
            comment=random.choice(commentlists[self.commentlist])
            self.addcomment(videoid, comment)

