#encoding=utf-8
import locale
import sys
import pdb
from multiprocessing.connection import Client
from conf import LISTENERHOST, LISTENERPORT

lang, charset = locale.getdefaultlocale()

address = (LISTENERHOST, LISTENERPORT)

msg = u'这是一个美丽的世界'
if sys.argv[1]:
    msg = '\n'.join(sys.argv[1:]).replace('<br>', '\n')
    print msg
conn = Client(address)
conn.send(msg.decode(charset))
print conn.recv_bytes().decode('utf-8').encode(charset)

conn.close()
