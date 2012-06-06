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
try:
    import StorageServer
except:
    import storageserverdummy as StorageServer

cache = StorageServer.StorageServer("ustream", 24)
addon = xbmcaddon.Addon('plugin.video.ustream')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
home = addon.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
fanart = os.path.join( home, 'fanart.jpg' )



def make_request(url):
        try:
            headers = {'User-agent' : 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0',
                       'Referer' : 'http://www.ustream.tv'}
            req = urllib2.Request(url,None,headers)
            response = urllib2.urlopen(req)
            data = response.read()
            response.close()
            return data
        except urllib2.URLError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
                xbmc.executebuiltin("XBMC.Notification(Ustream,HTTP ERROR: "+str(e.code)+",5000,"+icon+")")
                
                
def get_cats():
        url = 'http://www.ustream.tv'
        return(make_request(url))


def categories():
        data = cache.cacheFunction(get_cats)
        soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES)
        items = soup('ul', attrs={'class' : "categories"})[0]('li')
        for i in items:
            try:
                name = i.a.span.string.replace('\n','').replace('\t','')
                if name == 'Campaign 2012': continue
                if name == 'More': continue
                href = i.a['href']
                if name == 'Pets & Animals':
                    href = '/animals'
                if name == 'Education':
                    href = '/how-to'
                if name == 'Spirituality':
                    href = '/religion'
                if not '/discovery/live' in href:
                    href = '/discovery/live'+href
                url = 'http://www.ustream.tv'+href
                if name == 'On Air':
                    name = 'All Live'
                addDir(name, url, 1, icon)
            except:
                continue


def index_categorie(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
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
        try:
            next_page = 'http://www.ustream.tv'+soup('a', attrs={'class' : "pagerButton next rightSide"})[0]['href']
            addDir('Next Page', next_page, 1, icon)
        except:
            pass
            

def resolve_url(url):
        def getSwf():
                req = urllib2.Request('http://www.ustream.tv/flash/viewer.swf')
                response = urllib2.urlopen(req)
                swfUrl = response.geturl()
                return swfUrl

        url = 'http://api.ustream.tv/json/user/%s/listAllChannels?key=D9B39696EF3F310EA840C3A8EFC8306D' % url
        data = json.loads(make_request(url))
        try:
            channel_id = data['results'][0]['id']
        except: print data
        amf_url = 'http://cgw.ustream.tv/Viewer/getStream/1/%s.amf' % channel_id
        print "amf_url ----- "+amf_url
        amf_data = make_request(amf_url)
        match = re.compile('.*(rtmp://.+?)\x00.*').findall(amf_data)
        rtmp = match[0]
        playpath = ' playpath='+re.compile('.*streamName\W\W\W(.+?)[/]*\x00.*').findall(amf_data)[0]
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