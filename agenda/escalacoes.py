"""Publica no canal as escalações dos jogos da agenda de hoje assim que a ESPN as divulga (antes do apito inicial).
Uso (cwd = raiz do repo): python3 agenda/escalacoes.py [--dry]   (HOJE=AAAA-MM-DD para testar outro dia)
- Lê agenda/AAAA-MM-DD.json, acha cada jogo na ESPN pelo id do mandante.
- Jogo ainda não encerrado e com titulares divulgados nos dois times -> entra no post.
- Junta numa única mensagem os jogos novos e registra em posts.json (tipo "escalacao", jogos: [chaves]).
"""
import json, os, sys, html, subprocess, datetime as dt, urllib.request
from zoneinfo import ZoneInfo

CHAT = "-1003873202735"
LIGAS = {"Premier League": "eng.1", "Championship": "eng.2", "League One": "eng.3",
         "Bundesliga": "ger.1", "2. Bundesliga": "ger.2", "Brasileirão Série A": "bra.1",
         "Brasileirão Série B": "bra.2", "La Liga": "esp.1", "La Liga 2": "esp.2",
         "Ligue 1": "fra.1", "Serie A": "ita.1", "Serie B": "ita.2",
         "Liga Portugal": "por.1", "Saudi Pro League": "ksa.1"}
dry = "--dry" in sys.argv
teste = bool(os.environ.get("HOJE"))
hoje = dt.date.fromisoformat(os.environ["HOJE"]) if teste else dt.datetime.now(ZoneInfo("America/Sao_Paulo")).date()
try:
    agenda = json.load(open(f"agenda/{hoje}.json"))
except FileNotFoundError:
    print("sem agenda hoje"); sys.exit(0)

posts = json.load(open("posts.json"))
feitos = {k for p in posts if p.get("tipo") == "escalacao" for k in p.get("jogos", [])}
tid = lambda url: url.rsplit("/", 1)[-1].split(".")[0]
get = lambda u: json.load(urllib.request.urlopen(u, timeout=20))
e = html.escape

cache = {}
def eventos(cod):
    if cod not in cache:
        cache[cod] = []
        for d in (hoje, hoje + dt.timedelta(days=1)):
            cache[cod] += get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{cod}/scoreboard?dates={d:%Y%m%d}").get("events", [])
    return cache[cod]

blocos, chaves = [], []
for o in sorted(agenda, key=lambda o: o["hora"]):
    cod = LIGAS.get(o["liga"])
    chave = f"{hoje}|{tid(o['lc'])}|{tid(o['lf'])}"
    if not cod or chave in feitos:
        continue
    for ev in eventos(cod):
        c = ev["competitions"][0]
        times = {t["homeAway"]: t for t in c["competitors"]}
        if times["home"]["team"]["id"] != tid(o["lc"]):
            continue
        if ev["status"]["type"].get("state") == "post" and not teste:
            break
        try:
            s = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{cod}/summary?event={ev['id']}")
        except Exception:
            break
        ros = {r["homeAway"]: r for r in s.get("rosters", []) if r.get("homeAway")}
        linhas = [f"🏆 <b>{e(o['liga'])}</b> · {o['hora']}"]
        ok = True
        for lado, nome in (("home", o["casa"]), ("away", o["fora"])):
            r = ros.get(lado, {})
            tit = [a["athlete"]["displayName"] for a in r.get("roster", []) if a.get("starter")]
            if len(tit) < 11:
                ok = False; break
            form = f" ({r['formation']})" if r.get("formation") else ""
            linhas.append(f"<b>{e(nome)}</b>{e(form)}: " + e(", ".join(tit)))
        if ok:
            blocos.append("\n".join(linhas)); chaves.append(chave)
        break

if not blocos:
    print("nenhuma escalação nova"); sys.exit(0)
texto = "📋 ESCALAÇÕES\n\n" + "\n\n".join(blocos)
if dry:
    print(texto); sys.exit(0)
token = os.environ.get("TELEGRAM_TOKEN") or "__SAVED_KEY__"
r = subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{token}/sendMessage",
                    "-d", f"chat_id={CHAT}", "-d", "parse_mode=HTML", "-d", "disable_web_page_preview=true",
                    "--data-urlencode", f"text={texto}"], capture_output=True, text=True)
resp = json.loads(r.stdout or "{}")
if not resp.get("ok"):
    sys.exit(f"ERRO Telegram: {resp.get('description')}")
posts.append({"message_id": resp["result"]["message_id"], "data": str(hoje), "tipo": "escalacao", "jogos": chaves})
json.dump(posts, open("posts.json", "w"), ensure_ascii=False)
print("publicado", resp["result"]["message_id"], len(chaves), "jogos")
