import json,urllib.request,sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timedelta,timezone
HOJE=sys.argv[1]
L=[("Premier League","eng.1"),("Championship","eng.2"),("League One","eng.3"),("Bundesliga","ger.1"),("2. Bundesliga","ger.2"),("Brasileirão Série A","bra.1"),("Brasileirão Série B","bra.2"),("La Liga","esp.1"),("La Liga 2","esp.2"),("Ligue 1","fra.1"),("Serie A","ita.1"),("Serie B","ita.2"),("Liga Portugal","por.1"),("Saudi Pro League","ksa.1"),("Libertadores","conmebol.libertadores"),("Sul-Americana","conmebol.sudamericana"),("Copa do Brasil","bra.copa_do_brazil"),("Champions League","uefa.champions"),("Europa League","uefa.europa"),("Conference League","uefa.europa.conf"),("Paulistão","bra.camp.paulista"),("Carioca","bra.camp.carioca"),("Gauchão","bra.camp.gaucho"),("Mineiro","bra.camp.mineiro"),("Eliminatórias","fifa.worldq.conmebol"),("Argentino","arg.1"),("MLS","usa.1"),("Eredivisie","ned.1"),("Copa da Liga Inglesa","eng.league_cup"),("Colombiano","col.1"),("Mexicano","mex.1")]
COPAS={"Libertadores","Sul-Americana","Copa do Brasil","Champions League","Europa League","Conference League","Eliminatórias","Paulistão","Carioca","Gauchão","Mineiro","Copa da Liga Inglesa"}
d0=datetime.strptime(HOJE,"%Y-%m-%d");ds=[d0.strftime("%Y%m%d"),(d0+timedelta(days=1)).strftime("%Y%m%d")]
def get(a):
    (n,c),d=a
    try:return n,json.load(urllib.request.urlopen(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{c}/scoreboard?dates={d}",timeout=30)),None
    except Exception as e:return n,None,str(e)
jobs=[(l,d) for l in L for d in ds]
out={};errs=[]
with ThreadPoolExecutor(20) as ex:
    for n,j,e in ex.map(get,jobs):
        if e:errs.append((n,e));continue
        for ev in j.get('events',[]):
            t=datetime.strptime(ev['date'],"%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)-timedelta(hours=3)
            if t.strftime("%Y-%m-%d")!=HOJE:continue
            comp=ev['competitions'][0];cs=comp['competitors']
            h=[c for c in cs if c['homeAway']=='home'][0];a=[c for c in cs if c['homeAway']=='away'][0]
            def gp(c):
                try:return sum(int(x) for x in c['records'][0]['summary'].split('-'))
                except:return None
            g=[x for x in (gp(h),gp(a)) if x is not None]
            out[ev['id']]=dict(id=ev['id'],liga=n,hora=t.strftime("%H:%M"),casa=h['team']['displayName'],fora=a['team']['displayName'],lc=h['team'].get('logo',''),lf=a['team'].get('logo',''),hid=h['team']['id'],aid=a['team']['id'],gp=(max(g)+1 if g else None),status=ev['status']['type']['name'])
G=list(out.values())
for n in set(x['liga'] for x in G):
    if n in COPAS:
        for x in G:
            if x['liga']==n:x['gp']=None
        continue
    m=max([x['gp'] for x in G if x['liga']==n and x['gp']] or [0])
    for x in G:
        if x['liga']==n and m:x['gp']=m
G.sort(key=lambda x:(x['hora'],x['liga']))
json.dump(G,open('/workspace/work/espn_hoje.json','w'),ensure_ascii=False,indent=1)
print("ERRS",errs)
for x in G:print(x['hora'],x['liga'],x['gp'],'|',x['casa'],'x',x['fora'],x['status'])
print(len(G))
