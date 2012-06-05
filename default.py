import urllib
import urllib2
import re
import os
import xbmcplugin
import xbmcgui
import xbmcaddon
from BeautifulSoup import BeautifulSoup
try:
    import json
except:
    import simplejson as json

addon = xbmcaddon.Addon('plugin.video.ustream')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
home = addon.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
fanart = os.path.join( home, 'fanart.jpg' )


def categories():
        # addDir('Entertainment','http://www.ustream.tv/entertainment',1,'')
        # addDir('Sports','http://www.ustream.tv/sports',1,'')
        # addDir('News','http://www.ustream.tv/discovery/live/news',1,'')
        # addDir('Tech','http://www.ustream.tv/technology',1,'')
        # addDir('Gaming','http://www.ustream.tv/gaming',1,'')
        # addDir('Music','http://www.ustream.tv/music',1,'')
        # addDir('Animals','http://www.ustream.tv/pets-animals',1,'')
        # addDir('Election 2012','http://www.ustream.tv/election2012',1,'')
        addDir('All Live','http://www.ustream.tv/discovery/live/all',1,'')


def index_categorie(url):
        headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = urllib2.Request(url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        soup = soup = BeautifulSoup(link, convertEntities=BeautifulSoup.HTML_ENTITIES)
        for i in soup('ul',  attrs={'class' : "recordedShowThumbsV4 clearAfter"})[0]('li'):
            try:
                title = i.img['alt']
                thumb = i.img['src']
                if 'blank' in thumb:
                    thumb = i.img['rel']
                url = i('a')[-1]['href']
                print 'URL: '+url
                try: live = i.strong.string
                except: live = ''
                if live == 'LIVE':
                    addLiveLink(title.encode('ascii', 'ignore'), url.split('/')[-1], 2, thumb)
            except:
                pass
            

def resolve_url(url):
        def getSwf():
                req = urllib2.Request('http://www.ustream.tv/flash/viewer.swf')
                response = urllib2.urlopen(req)
                swfUrl = response.geturl()
                return swfUrl

        url = 'http://api.ustream.tv/json/user/%s/listAllChannels?key=D9B39696EF3F310EA840C3A8EFC8306D' % url
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        link=response.read()
        print response.geturl()
        print response.info()
        response.close()
        data = json.loads(link)
        try:
            channel_id = data['results'][0]['id']
        except: print data
        amf_url = 'http://cgw.ustream.tv/Viewer/getStream/1/%s.amf' % channel_id
        print "amf_url ----- "+amf_url
        headers = {'User-agent' : 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.13) Gecko/20080311 Firefox/2.0.0.13'}
        req = urllib2.Request(amf_url,None,headers)
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match = re.compile('.*(rtmp://.+?)\x00.*').findall(link)
        rtmp = match[0]
        playpath = ' playpath='+re.compile('.*streamName\W\W\W(.+?)[/]*\x00.*').findall(link)[0]
        swf = ' swfUrl='+getSwf()
        pageUrl = ' pageUrl='+data['results'][0]['url']
        url = rtmp + playpath + swf + pageUrl + ' swfVfy=1 live=true'
        item = xbmcgui.ListItem(path=url)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
            params=sys.argv[2]
            cleanedparams=params.replace('?','')
            if (params[len(params)-1]=='/'):
                params=params[0:len(params)-2]
            pairsofparams=cleanedparams.split('&')
            param={}
            for i in range(len(pairsofparams)):
                splitparams={}
                splitparams=pairsofparams[i].split('=')
                if (len(splitparams))==2:
                    param[splitparams[0]]=splitparams[1]

        return param

        
def addDir(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
        return ok

        
def addLink(name,url,iconimage):
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name })
        liz.setProperty( "Fanart_Image", fanart)
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=liz)
        return ok


def addLiveLink(name,url,mode,iconimage):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart)
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok


params=get_params()

try:
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_UNSORTED)
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL)
except:
    pass

url=None
name=None
mode=None

try:
    url=urllib.unquote_plus(params["url"])
except:
    pass
try:
    name=urllib.unquote_plus(params["name"])
except:
    pass
try:
    catId=urllib.unquote_plus(params["catId"])
except:
    pass
try:
    iconimage=urllib.unquote_plus(params["iconimage"])
except:
    pass
try:
    mode=int(params["mode"])
except:
    pass

print "Mode: "+str(mode)
print "URL: "+str(url)
print "Name: "+str(name)

if mode==None:
    print ""
    categories()

elif mode==1:
    print ""
    index_categorie(url)
    
elif mode==2:
    print ""
    resolve_url(url)
   
xbmcplugin.endOfDirectory(int(sys.argv[1]))