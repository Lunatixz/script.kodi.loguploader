import os
import re
import socket
from urllib import urlencode
from urllib import FancyURLopener
import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs

ADDON        = xbmcaddon.Addon()
ADDONID      = ADDON.getAddonInfo('id')
ADDONNAME    = ADDON.getAddonInfo('name')
ADDONVERSION = ADDON.getAddonInfo('version')
CWD          = ADDON.getAddonInfo('path').decode("utf-8")
LANGUAGE     = ADDON.getLocalizedString

socket.setdefaulttimeout(5)

URL      = 'https://paste.ubuntu.com/'
LOGPATH  = xbmc.translatePath('special://logpath')
LOGFILE  = os.path.join(LOGPATH, 'kodi.log')
REPLACES = (('//.+?:.+?@', '//USER:PASSWORD@'),('<user>.+?</user>', '<user>USER</user>'),('<pass>.+?</pass>', '<pass>PASSWORD</pass>'),)

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode("utf-8")
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode("utf-8"), level=xbmc.LOGDEBUG)

# Custom urlopener to set user-agent
class pasteURLopener(FancyURLopener):
    version = '%s: %s' % (ADDONID, ADDONVERSION)

class Main:
    def __init__(self):
        succes, data = self.readLog()
        if succes:
            content = self.cleanLog(data)
            succes, result = self.postLog(content)
            if succes:
                self.showResult(LANGUAGE(32005) % result)
            else:
                self.showResult(result)
        else:
            self.showResult(result)

    def readLog(self):
        try:
            lf = xbmcvfs.File(LOGFILE)
            content = lf.read()
            lf.close()
            if content:
                return True, content
            else:
                log('logfile is empty')
                return False, LANGUAGE(32001)
        except:
            log('unable to read logfile')
            return False, LANGUAGE(32002)

    def cleanLog(self, content):
        for pattern, repl in REPLACES:
            content = re.sub(pattern, repl, content)
            return content

    def postLog(self, data):
        params = {}
        params['poster'] = 'kodi'
        params['content'] = data
        params['syntax'] = 'text'
        params = urlencode(params)

        url_opener = pasteURLopener()

        try:
            page = url_opener.open(URL, params)
        except:
            log('failed to connect to the server')
            return False, LANGUAGE(32003)

        try:
            page_url = page.url.strip()
            log(page_url)
            return True, page_url
        except:
            log('unable to retrieve the paste url')
            return False, LANGUAGE(32004)

    def showResult(self, message):
        dialog = xbmcgui.Dialog()
        confirm = dialog.ok(ADDONNAME, message)

if ( __name__ == "__main__" ):
    log('script version %s started' % ADDONVERSION)
    Main()
log('script version %s ended' % ADDONVERSION)
