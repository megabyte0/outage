import urllib.request
import json
import zlib
from html.parser import HTMLParser
import urllib.parse
import urllib.error
import re
import time
##har=[]
##for i in ['www.pythonanywhere.com_Archive [21-01-20 13-20-39].har',
##          'www.pythonanywhere.com_Archive [21-01-20 13-22-18].har',
##          'www.pythonanywhere.com_Archive [21-01-23 08-04-37].har'
##    ]:
##    with open(i,'rt') as fp:
##        har.append(json.load(fp))
##f=lambda x:(
##    f(x[0]) if isinstance(x,list) else
##    [(k,type(v)) for k,v in x.items()]
##    if isinstance(x,dict)
##    else None
##    )
with open('har.json','rt') as fp:
    har=json.load(fp)
har=[{'log':{'entries':[i]}} for i in har]
copy_headers=lambda x:({
    i['name']:i['value']
    for i in x['request']['headers']
    if i['name'] not in ['Host','Connection','Content-Length']
    })
#har[0]['log']['entries'][0]['request']['headers']
copy_request=lambda x:(
    [x['request']['url'],
     {'headers':copy_headers(x),
      'method':x['request']['method']}
     ]
    )
req_from_copied=(
    lambda request:urllib.request.Request(request[0],**(request[1]))
    )
req=copy_request(har[0]['log']['entries'][0])

#https://stackoverflow.com/a/52086806
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
opener = urllib.request.build_opener(NoRedirect)
urllib.request.install_opener(opener)    
#

cookies=dict()

def myurlopen(req):
    global cookies
    try:
        fr = urllib.request.urlopen(req)
    except urllib.error.HTTPError as e:
        fr = e
    print(fr.status,fr.headers)
    data=fr.read()
    if fr.headers['Content-Encoding']=='gzip':
        data=zlib.decompress(data,wbits=zlib.MAX_WBITS+16)
    cookies.update(dict(
        tuple(i.split(';',1)[0].split('='))
        for i in fr.headers.get_all('Set-Cookie',[])
    ))
    fr.close()
    return (fr,data)

fr,_=myurlopen(req_from_copied(req))
assert fr.status==302
assert 'Location' in fr.headers
def update_cookies(req):
    global cookies
    req[1]['headers']['Cookie']='; '.join('='.join(i) for i in cookies.items())

def follow_redirect(req,location):
    update_cookies(req)
    req[0]=urllib.parse.urljoin(req[0],location)
    req[1]['method']='GET'
    return myurlopen(req_from_copied(req))

fr,data=follow_redirect(req,fr.headers['Location'])

class MyHTMLParser(HTMLParser):
    def __init__(self, *args, **kwargs):
        self.tags = []
        super().__init__(*args, **kwargs)

    def handle_starttag(self, tag, attrs):
        self.tags.append(('start',tag,attrs))

    def handle_endtag(self, tag):
        self.tags.append(('end',tag))

    def handle_data(self, data):
        self.tags.append(('data',data))

parser = MyHTMLParser()
parser.feed(data.decode())
start,end=[n for n,i in enumerate(parser.tags) if i[1]=='form']
params=(
    (lambda d:tuple(
        d[j] if j in d else None
        for j in ['name','value']
        ))(dict(i[2]))
    for i in parser.tags[start+1:end]
    if i[0]=='start' and i[1]=='input'
    )
params=dict(i for i in params if i[0])
with open('.env','rt') as fp:
    for i in fp.read().split('\n'):
        if '=' in i:
            i=i.split('=')
            params[i[0]]=i[1]
postData='&'.join('='.join(urllib.parse.quote(j) for j in i)
                  for i in params.items())
req=copy_request(har[1]['log']['entries'][0])
update_cookies(req)
req[1]['data']=postData.encode()
fr,data=myurlopen(req_from_copied(req))
assert fr.status==302
assert 'Location' in fr.headers
fr,data=follow_redirect(req,fr.headers['Location'])

matcher=re.compile('csrfToken(?:\s*\=\s*|\:\s*)\"([a-zA-Z0-9]+)\"')
csrf=matcher.findall(data.decode())
assert len(csrf)==3 and len(set(csrf))==1

req=copy_request(har[2]['log']['entries'][0])
update_cookies(req)
req[1]['headers']['X-CSRFToken']=csrf[0]
hour,minute=time.gmtime(time.time()+60*60)[3:5]
req[1]['data']=json.dumps({
    "interval":"daily",
    "hour":str(hour),
    "minute":str(minute),
    "command":"python3.8 /home/odessaoutage/outage/water_outage_kiss_yagni.py"
    }).encode()

fr,data=myurlopen(req_from_copied(req))
assert fr.status==200

#copy_har_part=lambda x,e:{e[0]:x[e[0]]} if len(e)==1 else {e[0]:copy_har_part(x[e[0]],e[1:])}
#copy_har=lambda x:{'request':{i:x['request'][i] for i in ['url','headers','method']}}
#har0=[copy_har(har[i]['log']['entries'][0]) for i in range(3)]
