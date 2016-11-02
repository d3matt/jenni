import datetime
import os
import logging.handlers
import pytz


os.umask(0022)
LOGPATH = os.path.expanduser('~/.jenni/logs')
if not os.path.exists(LOGPATH):
    os.makedirs(LOGPATH)

HANDLERS = {}

def rotating_logger(logname='channel.txt'):
    fullpath = os.path.join(LOGPATH, logname)
    if fullpath in HANDLERS:
        return HANDLERS[fullpath]
    handler = logging.handlers.TimedRotatingFileHandler(fullpath, when='D', backupCount=1000)
    handler.formatter = logging.Formatter("%(message)s")
    HANDLERS[fullpath] = handler
    return handler

def timestamp():
    return pytz.timezone('US/Mountain').fromutc(datetime.datetime.utcnow())

def emit(handler, message):
    class Foo:
        def __init__(self, message):
            self.message = message
            self.exc_info = None
            self.exc_text = None
        def getMessage(self):
            return self.message
    handler.emit(Foo(message))

def logtrack(jenni, input):
    channel = input.sender
    nick = input.nick
    handler = rotating_logger(logname='%s.txt' % channel)
    line = '%s [%s] %s' % (timestamp(), nick, input.group())
    emit(handler, line)

logtrack.rule = r'.*'
logtrack.priority = 'low'

def logtrack_join(jenni, input):
    channel = input.sender
    nick = input.nick
    handler = rotating_logger(logname='%s.txt' % channel)
    line = '%s [%s] joined %s' % (timestamp(), nick, input.group())
    emit(handler, line)
    
logtrack_join.rule = r'.*'
logtrack_join.event = 'JOIN'
logtrack_join.priority = 'low'

def logtrack_part(jenni, input):
    channel = input.sender
    nick = input.nick
    handler = rotating_logger(logname='%s.txt' % channel)
    line = '%s [%s] left %s' % (timestamp(), nick, input.group())
    emit(handler, line)
    
logtrack_part.rule = r'.*'
logtrack_part.event = 'PART'
logtrack_part.priority = 'low'

def logtrack_quit(jenni, input):
    channel = input.sender
    nick = input.nick
    handler = rotating_logger(logname='%s.txt' % channel)
    line = '%s [%s] quit %s' % (timestamp(), nick, input.group())
    emit(handler, line)
    
logtrack_quit.rule = r'.*'
logtrack_quit.event = 'QUIT'
logtrack_quit.priority = 'low'
