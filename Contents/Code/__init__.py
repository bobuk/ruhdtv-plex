# -*- coding: utf-8 -*-
# Writen by me, yeah! Grigory Bakunov <thebobuk@ya.ru>
# Please leave my copyrights here cause as you can notice
# "Copyright" always means "absolutely right copying".
# Illegal copying of this code prohibited by real patsan's law!

import re
from copy import deepcopy

VERSION = 1.4

PREFIX = "/video/hdouttv"

SITE = "http://hdout.tv/"
S_SERIES = SITE + "List/"
S_SERIES_XML = S_SERIES + "all/XML/"
S_MY_SERIES_XML = S_SERIES + "my/XML/"
S_EPISODES = SITE +"Series/"
S_EPISODES_XML = S_EPISODES + "%s/XML/"
S_FULLPATH = SITE + 'EpisodeLink/'
S_FULLPATH_XML = S_FULLPATH + '%s/XML/'
S_RSS_PATH = SITE + "RSS/"
NAME = L('Title')
TITLE = "HDOut.tv"

ART           = 'art.png'
ICON          = 'icon.png'

####################################################################################################

authed = False
token  = False

def Start():
    ObjectContainer.art = R(ART)
    ObjectContainer.title1 = TITLE
    DirectoryObject.thumb = R(ICON)

    HTTP.CacheTime = CACHE_1HOUR


def ValidatePrefs():
    u = Prefs['username']
    p = Prefs['password']
    if( u and p ):
        return True if Authentificate() else MessageContainer("Error", "Wrong username or password")
    else:
        return MessageContainer( "Error",   "You need to provide both a user and password" )

def Authentificate(cacheTime=CACHE_1WEEK):
    if Prefs['username'] and Prefs['password']:
        req = HTTP.Request(SITE, values = {
            'login' : Prefs["username"],
            'password' : Prefs["password"]}, cacheTime=CACHE_1WEEK)
        if 'search' not in str(req.content):
            if cacheTime != 0:
                return Authentificate(cacheTime=0)
            Log("Oooops, wrong pass or no creds")
            return False
        else:
            Log("Ok, i'm in!")
            cookies = HTTP.CookiesForURL(SITE)
            if cookies != None:
                Dict['Cookies'] = cookies
                Dict['SID'] = cookies.split('=', 1)[1]
                authed = True
            else:
                Log('Cached: ' + Dict['Cookies'])
        return True
    Log('No prefs')
    return False


@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(Serials, title2='List of all shows on this site', filter='all'), title='All shows'))
    oc.add(DirectoryObject(key=Callback(Serials, title2='List of your favorite shows', filter='favorites'), title='Favorites'))
    oc.add(PrefsObject(title="Preferences"))
    oc.add(DirectoryObject(key=Callback(Serials, title2='List of new or updated series', filter='updated'), title='Updates'))

    return oc


@route(PREFIX+'/serials/{filter}')
def Serials(title2, filter):
    if not Authentificate():
        return MessageContainer( "Error",   "You need to provide both a user and password" )

    dir = ObjectContainer(title2=title2)
    
    if filter == 'all':
        xml = XML.ElementFromURL(S_SERIES_XML)
    elif filter == 'favorites':
        xml = XML.ElementFromURL(S_MY_SERIES_XML)

    if filter in ['all', 'favorites']:
        for item in xml.xpath('//serieslist/item'):
            title = item.xpath('./title')[0].text
            summary = item.xpath('./info')[0].text
            mark = item.xpath('./mark')[0].text

            poster = SITE + "static/c/b/" + mark + ".jpg"
            thumb = SITE + "static/c/s/" + mark + ".jpg"

            sid   = item.xpath('./id_series')[0].text
            dir.add(TVShowObject(key=Callback(
                                                Serial,
                                                sid = sid,
                                                title = title, 
                                                mark = mark
                                            ),
                                 rating_key = sid,
                                 title = title, 
                                 summary = summary, 
                                 art = poster, thumb = poster))
        return dir
    else:
        rss = XML.ElementFromURL(S_RSS_PATH, headers = {'Cookie': Dict['Cookies']})
        for item in rss.xpath('//item'):
            title = item.xpath('./title')[0].text.strip()
            thumb = item.xpath('./image')[0].text
            eid = item.xpath('./link')[0].text.split('/')[4]
            dir.add(EpisodeObject(
                key=Callback(Episode, eid = eid),
                rating_key='hdouttv' + '.' + str(eid),
                title=title,
                thumb=thumb,
                items=[
                    MediaObject(
                        parts=[
                            PartObject(
                                key=Callback(Episode, eid=eid))])]
                ))
        return dir


@route(PREFIX+'/serial/{sid}')
def Serial(sid, title, mark):

    dir = ObjectContainer()
    HTTP.Headers['Cookie'] = Dict['Cookies']
    seasons = XML.ElementFromURL(S_EPISODES_XML % sid, cacheTime=0)

    for season in seasons.xpath('//season'):
        for item in season.xpath('./item'):
            season_num = int(item.xpath('./snum')[0].text)
            episode_num = int(item.xpath('./enum')[0].text)
            title = item.xpath('./title')[0].text
            eid = item.xpath('./id_episodes')[0].text
            server = item.xpath('./server')[0].text
            full_title = "%02d-%02d. %s" % (season_num, episode_num, title)
            
            if server and len(server) > 0:
                turl = "http://msk1.hdout.tv/"
            else:
                turl = "http://msk.hdout.tv/"
            thumb = turl + ("hd/%s/sc/%02d-%02d.jpg" % (mark, season_num, episode_num))

            dir.add(EpisodeObject(
                key=Callback(Episode, eid = eid),
                rating_key='hdouttv' + '.' + str(eid),
                title=full_title,
                thumb=thumb,
                items=[
                    MediaObject(
                        parts=[
                            PartObject(
                                key=Callback(episode_url, eid=eid))])]
                ))

    return dir

@route(PREFIX+'/episode/{eid}')
def Episode(eid):
    oc = ObjectContainer()
    oc.add(EpisodeObject(
        key=Callback(Episode, eid = eid),
        rating_key='hdouttv' + '.' + str(eid),
        items=[MediaObject(
            # video_resolution = 720 if row['quality'].encode('utf-8')=='720p' else 400,
            video_codec = VideoCodec.H264,
            audio_codec = AudioCodec.AAC,
            container = Container.MP4,
            optimized_for_streaming = True,
            audio_channels = 2,
            parts = [PartObject(key=Callback(episode_url, eid=eid))]
        )]
    ))
    return oc

def episode_url(eid):
    Log(S_FULLPATH_XML % eid)
    HTTP.Headers['Cookie'] = Dict['Cookies']
    video = XML.ElementFromURL(S_FULLPATH_XML % eid, cacheTime=0)
    video_url = video.xpath("//videourl")[0].text
    return Redirect(video_url)

