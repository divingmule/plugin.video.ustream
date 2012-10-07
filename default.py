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
from pyamf import remoting

cache = StorageServer.StorageServer("ustream", 24)
addon = xbmcaddon.Addon('plugin.video.ustream')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
home = addon.getAddonInfo('path')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
fanart = os.path.join( home, 'fanart.jpg' )
filter = int(addon.getSetting('channel_filter'))
sort = int(addon.getSetting('sort_method'))


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
    USTREAM_DISCOVERY_URL = 'http://www.ustream.tv/discovery/live/'
    CATEGORIES      = [
                        { 'title' :  'On Air', 'path' : 'all'},
                        { 'title' :  'News', 'path' : 'news'},
                        { 'title' :  'Pets & Animals', 'path' : 'animals'},
                        { 'title' :  'Entertainment', 'path' : 'entertainment'},
                        { 'title' :  'Sports', 'path' : 'sports'},
                        { 'title' :  'Music', 'path' : 'music'},
                        { 'title' :  'Gaming', 'path' : 'gaming'},
                        { 'title' :  'Events', 'path' : 'events'},
                        { 'title' :  'Tech', 'path' : 'technology'}
                    ]
    for cat in CATEGORIES:
        addDir(cat['title'],USTREAM_DISCOVERY_URL + cat['path'],1,icon)

def index_category(url):
        soup = BeautifulSoup(make_request(url), convertEntities=BeautifulSoup.HTML_ENTITIES)
        for i in soup('ul',  attrs={'class' : "recordedShowThumbsV4 clearAfter"})[0]('li'):
            try:
                title = i.img['alt']
                if not title == i.h4.a.string.strip():
                    title += ' - '+i.h4.a.string.strip()
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
                continue
        try:
            next_page = 'http://www.ustream.tv'+soup('a', attrs={'class' : "pagerButton next rightSide"})[0]['href']
            addDir('Next Page', next_page, 1, icon)
        except:
            pass
            
            
def list_all_channels(user, stream_title=None):
        url = 'http://api.ustream.tv/json/user/%s/listAllChannels?key=D9B39696EF3F310EA840C3A8EFC8306D' %user
        data = json.loads(make_request(url))
        for i in data['results']:
            title = i['title']
            if not stream_title == None:
                if stream_title in title:
                    if i['status'] == 'live':
                        return resolve_url(i['id'])
                    else:
                        print '---- status key == offline ---- '
                        xbmc.executebuiltin("XBMC.Notification(Ustream,Channel Status: Offline,5000,"+icon+")")
                        return
                else: continue
            else:
                if i['status'] == 'live':
                    addLiveLink(title.encode('ascii', 'ignore'), i['id'], 4, icon, False)
            

def resolve_url(stream_id):
        def getSwf():
                req = urllib2.Request('http://www.ustream.tv/flash/viewer.swf')
                response = urllib2.urlopen(req)
                swfUrl = response.geturl()
                return swfUrl
        amf_url = 'http://cgw.ustream.tv/Viewer/getStream/1/%s.amf' % stream_id
        print "amf_url ----- "+amf_url
        amf_data = remoting.decode(make_request(amf_url)).bodies[0][1].body
        print amf_data
        print amf_data.keys()
        streams = []
        if not amf_data['status'] == 'offline':
            if 'streamVersions' in amf_data.keys():
                print '--- streamVersions: '+str(len(amf_data['streamVersions']))
                for i in amf_data['streamVersions'].keys():
                    print ' --- %s ---' %i
                    if 'streamVersionCdn' in amf_data['streamVersions'][i].keys():
                        print'--- streamVersionsCdn: '+str(len(amf_data['streamVersions'][i]['streamVersionCdn']))
                        for cdn in amf_data['streamVersions'][i]['streamVersionCdn']:
                            print amf_data['streamVersions'][i]['streamVersionCdn'][cdn]
                            cdn_url = amf_data['streamVersions'][i]['streamVersionCdn'][cdn]['cdnStreamUrl']
                            cdn_path = amf_data['streamVersions'][i]['streamVersionCdn'][cdn]['cdnStreamName']
                            streams.append((cdn_url, cdn_path))
                    else:
                        print '------ No streamVersionCdn key! ------'
            else:
                print '------ No streamVersions key! ------'
            if 'fmsUrl' in amf_data.keys():
                fms_url = amf_data['fmsUrl']
                # there may be issues with this path ???
                fms_path = amf_data['streamName']
                # if fms_path == 'streams/live':
                    # fms_path += '_1'
                    # fms_path += '_2'
                    # fms_path += '_3'
                    # fms_path += '_1_'+stream_id
                streams.append((fms_url, fms_path))
            if 'cdnUrl' in amf_data.keys():
                cdn_url = amf_data['cdnUrl']
                cdn_path = amf_data['streamName']
                stream = (cdn_url, cdn_path)
                if not stream in streams:
                    streams.append((cdn_url, cdn_path))
            if 'liveHttpUrl' in amf_data.keys():
                streams.append((amf_data['liveHttpUrl'], None))
        else:
            print '---- status key == offline ---- '
            xbmc.executebuiltin("XBMC.Notification(Ustream,Channel Status: Offline,5000,"+icon+")")
            return
            
        print '----- streams %s ------' %str(len(streams))
        print streams
        if len(streams) > 0:
            if 'rtmp://' in streams[0][0]:
                rtmp = streams[0][0]
                playpath = ' playpath=' + streams[0][1]
                app = ' app='+rtmp.split('/', 3)[-1]
                swf = ' swfUrl='+getSwf()
                try:
                    pageUrl = ' pageUrl='+amf_data['ads']['info']['url']
                except:
                    try:
                        pageUrl = ' pageUrl='+amf_data['moduleConfig']['meta']['url']
                    except:
                        print ' --- pageUrl Exception --- '
                url = rtmp + playpath + swf + pageUrl + app + ' swfVfy=1 live=true'
            else:
                print " --- not rtmp, must be m3u8? --- "
                url = streams[0][0]
            item = xbmcgui.ListItem(path=url)
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
        else:
            print '----- No Streams -----'
            return
            

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


def addLiveLink(name,url,mode,iconimage,showcontext=True):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&iconimage="+urllib.quote_plus(iconimage)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart)
        liz.setProperty('IsPlayable', 'true')
        if showcontext:
            contextMenu = [('List all channels from this user','XBMC.Container.Update(%s?url=%s&mode=3)' %(sys.argv[0], urllib.quote_plus(url)))]
            liz.addContextMenuItems(contextMenu)
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
    categories()

elif mode==1:
    index_category(url)
    
elif mode==2:
    stream_title = name.split(' - ')[0]
    list_all_channels(url, stream_title)
    
elif mode==3:
    list_all_channels(url)
    
elif mode==4:
    resolve_url(url)
   
xbmcplugin.endOfDirectory(int(sys.argv[1]))