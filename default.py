import os
import uuid
import re
import socket
import pyqrcode
import sys
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
CWD          = ADDON.getAddonInfo('path').decode('utf-8')
LANGUAGE     = ADDON.getLocalizedString

socket.setdefaulttimeout(5)

URL      = 'https://paste.ubuntu.com/'
LOGPATH  = xbmc.translatePath('special://logpath')
LOGFILE  = os.path.join(LOGPATH, 'kodi.log')
OLDLOG   = os.path.join(LOGPATH, 'kodi.old.log')
REPLACES = (('//.+?:.+?@', '//USER:PASSWORD@'),('<user>.+?</user>', '<user>USER</user>'),('<pass>.+?</pass>', '<pass>PASSWORD</pass>'),)
IMAGEFILE = os.path.join(xbmc.translatePath(CWD),'temp-uuid=%s.png'%str(uuid.uuid4()))
ALL_PROPERTIES = []

def log(txt):
    if isinstance (txt,str):
        txt = txt.decode('utf-8')
    message = u'%s: %s' % (ADDONID, txt)
    xbmc.log(msg=message.encode('utf-8'), level=xbmc.LOGDEBUG)

class QRCode(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        url = pyqrcode.create(xbmcgui.Window(10000).getProperty("logouploader.qr.url"))
        url.png(IMAGEFILE, scale=10)

# Custom urlopener to set user-agent
class pasteURLopener(FancyURLopener):
    version = '%s: %s' % (ADDONID, ADDONVERSION)

class Main:
    def __init__(self):
        self.getSettings()
        files = self.getFiles()
        for item in files:
            filetype = item[0]
            if filetype == 'log':
                error = LANGUAGE(32011)
                name = LANGUAGE(32031)
            elif filetype == 'oldlog':
                error = LANGUAGE(32012)
                name = LANGUAGE(32032)
            elif filetype == 'crashlog':
                error = LANGUAGE(32013)
                name = LANGUAGE(32033)
            succes, data = self.readLog(item[1])
            if succes:
                content = self.cleanLog(data)
                succes, result = self.postLog(content)
                if succes:
                    self.showResult(LANGUAGE(32006) % (name, result), result)
                else:
                    self.showResult('%s[CR]%s' % (error, result))
            else:
                self.showResult('%s[CR]%s' % (error, result))

    def getProperty(self, str):
        return xbmcgui.Window(10000).getProperty(str)

    def setProperty(self, str1, str2):
        ALL_PROPERTIES.append(str1)
        xbmcgui.Window(10000).setProperty(str1, str2)
            
    def clearProperty(self, str):
        xbmcgui.Window(10000).clearProperty(str)
        
    def cleanProperty(self):
        for property in ALL_PROPERTIES:
            self.clearProperty(property)
        try:
            xbmcvfs.delete(IMAGEFILE)
        except:
            pass
            
    def getSettings(self):
        self.oldlog = ADDON.getSetting('oldlog') == 'true'
        self.crashlog = ADDON.getSetting('crashlog') == 'true'

    def getFiles(self):
        logfiles = []
        logfiles.append(['log', LOGFILE])
        if self.oldlog:
            if xbmcvfs.exists(OLDLOG):
                logfiles.append(['oldlog', OLDLOG])
            else:
                self.showResult(LANGUAGE(32021))
        if self.crashlog:
            crashlog_path = ''
            items = []
            if xbmc.getCondVisibility('system.platform.osx'):
                crashlog_path = os.path.join(os.path.expanduser('~'), 'Library/Logs/DiagnosticReports/')
                filematch = 'Kodi'
            elif xbmc.getCondVisibility('system.platform.ios'):
                crashlog_path = '/var/mobile/Library/Logs/CrashReporter/'
                filematch = 'Kodi'
            elif xbmc.getCondVisibility('system.platform.linux'):
                crashlog_path = os.path.expanduser('~') # not 100% accurate (crashlogs can be created in the dir kodi was started from as well)
                filematch = 'kodi_crashlog'
            elif xbmc.getCondVisibility('system.platform.windows'):
                self.showResult(LANGUAGE(32023))
            elif xbmc.getCondVisibility('system.platform.android'):
                self.showResult(LANGUAGE(32024))
            if crashlog_path and os.path.isdir(crashlog_path):
                lastcrash = None
                dirs, files = xbmcvfs.listdir(crashlog_path)
                for item in files:
                    if filematch in item and os.path.isfile(os.path.join(crashlog_path, item)):
                        items.append(os.path.join(crashlog_path, item))
                        items.sort(key=lambda f: os.path.getmtime(f))
                        lastcrash = items[-1]
                if lastcrash:
                    logfiles.append(['crashlog', lastcrash])
            if len(items) == 0:
                self.showResult(LANGUAGE(32022))
        return logfiles

    def readLog(self, path):
        try:
            lf = xbmcvfs.File(path)
            content = lf.read()
            lf.close()
            if content:
                return True, content
            else:
                log('file is empty')
                return False, LANGUAGE(32001)
        except:
            log('unable to read file')
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
        return True, 'http://test'#TEST
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

    def showResult(self, message, url=None):
        if url:
            self.setProperty("logouploader.qr.image", IMAGEFILE)
            self.setProperty("logouploader.qr.message", message)
            self.setProperty("logouploader.qr.url", url)
            qr = QRCode( "script-loguploader-main.xml" , CWD, "default")
            qr.doModal()
            self.cleanProperty()
            del qr
        else:
            dialog = xbmcgui.Dialog()
            confirm = dialog.ok(ADDONNAME, message)
if ( __name__ == '__main__' ):
    log('script version %s started' % ADDONVERSION)
    Main()
log('script version %s ended' % ADDONVERSION)
