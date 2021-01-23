import urllib.request
import sqlite3
import json
from collections import defaultdict
import time
import os
os.chdir('/home/odessaoutage/outage/')
import login.re_schedule
os.chdir('/home/odessaoutage/outage/')
url = 'https://infoxvod.com.ua/api/repairs'
my_places = ['филатова','малиновский']
##repair_fields=r'''repair_id
##atext
##sp_time_
##sf_time_
##rp_time_
##rf_time_
##sp_time
##sf_time
##rp_time
##rf_time
##address
##location_
##locT
##type
##__address__'''.split('\n')
##sql_insert_repair=(
##    'insert into repair (%s) values (%s)'%(
##        ', '.join('"%s"'%i for i in repair_fields)),
##        ', '.join('?' for i in repair_fields)
##    )
sql_insert_reported=(
    'insert into reported (chat_id,repair_id) values (?,?)'
    )
sql_select_reported=(
    'select chat_id,repair_id from reported'
    )
chat_id=1250193677
conn = sqlite3.connect('water.db')
cursor = conn.cursor()
cursor.execute(sql_select_reported)
l=cursor.fetchall()
d=defaultdict(set)
for chat_id,repair_id in l:
    d[chat_id].add(repair_id)
def get_repairs():
    conn = sqlite3.connect('water.db')
    cursor = conn.cursor()
    with urllib.request.urlopen(url) as f:
        s=f.read()
        data=json.loads(s)
        for i in data:
            if 'places' not in i:
                continue
            for j in i['places']:
                if any(k in j.lower() for k in my_places):
                    #
                    if ('repair_id' in i 
                        and i['repair_id'] in d[chat_id]):
                        continue
                    with open('token','rt') as fp:
                        token=fp.read().strip()
                    f_statuses_responses=[]
                    send_str=str(i)
                    for k in range(len(send_str)//4000+1):
                        send_str_=send_str[k*4000:(k+1)*4000]
                        req=urllib.request.Request(
                            'https://api.telegram.org/bot%s/sendMessage'%token,
                            headers={'Content-Type':'application/json'},
                            data=(json.dumps({
                                'chat_id':chat_id,
                                'text':send_str_
                                }).encode()
                                  )
                            )
                        fs=urllib.request.urlopen(req)
                        response=fs.read()
                        response=json.loads(response)
                        f_statuses_responses.append((fs.status,response))
                    if all(f_status==200
                        and "ok" in response
                        and response["ok"]==True
                           for f_status,response in f_statuses_responses):
                        cursor.execute(sql_insert_reported,(chat_id,i['repair_id']))
                        conn.commit()
                        d[chat_id].add(i['repair_id'])
    cursor.close()
    conn.close()

##for i in range(24):
##    try:
##        get_repairs()
##    except Exception as e:
##        pass
##    if i!=23:
##        time.sleep(60*60)
get_repairs()

