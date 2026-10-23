"""Publica no canal os resultados (com autores dos gols) dos jogos da agenda de hoje que já terminaram.
Uso (cwd = pasta do projeto): python3 agenda/resultados.py [--dry]
- Lê agenda/AAAA-MM-DD.json de hoje (America/Sao_Paulo).
- Consulta a API da ESPN; acha cada jogo pelo id do time mandante (tirado da URL do escudo).
- Jogos encerrados e ainda não publicados: junta todos numa única mensagem de texto e posta.
- Registra em posts.json: {message_id, data (hoje), tipo: "resultado", jogos: [chaves]}.
Imprime um resumo. Sai com código 1 se o Telegram recusar o post.
"""
import json, sys, subprocess, datetime as dt, urllib.request
from zoneinfo import ZoneInfo

CHAT = "-1003873202735"
LIGAS = {"Premier League": "eng.1", "Championship": "eng.2", "League One": "eng.3",
         "Bundesliga": "ger.1", "2. Bundesliga": "ger.2", "Brasileirão Série A": "bra.1",
         "Brasileirão Série B": "bra.2", "La Liga": "esp.1", "La Liga 2": "esp.2",
         "Ligue 1": "fra.1", "Serie A": "ita.1", "Serie B": "ita.2",
         "Liga Portugal": "por.1", "Saudi Pro League": "ksa.1"}
dry = "--dry" in sys.argv
import os
hoje = dt.date.fromisoformat(os.environ["HOJE"]) if os.environ.get("HOJE") else dt.datetime.now(ZoneInfo("America/Sao_Paulo")).date()
try:
    agenda = json.load(open(f"agenda/{hoje}.json"))
except FileNotFoundError:
    print("sem agenda hoje"); sys.exit(0)
posts = json.load(open("posts.json"))
feitos = {k for p in posts for k in p.get("jogos", [])}
tid = lambda url: url.rsplit("/", 1)[-1].split(".")[0]

cache = {}
def eventos(cod):
    if cod not in cache:
        cache[cod] = []
        for d in (hoje, hoje + dt.timedelta(days=1)):
            u = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{cod}/scoreboard?dates={d:%Y%m%d}"
            cache[cod] += json.load(urllib.request.urlopen(u, timeout=20)).get("events", [])
    return cache[cod]

def minuto(x):
    return x.get("clock", {}).get("displayValue", "").replace("'", "") + "'"

blocos, chaves = [], []
for o in sorted(agenda, key=lambda o: o["hora"]):
    cod = LIGAS.get(o["liga"])
    if not cod:
        continue
    chave = f"{hoje}|{tid(o['lc'])}|{tid(o['lf'])}"
    if chave in feitos:
        continue
    for e in eventos(cod):
        c = e["competitions"][0]
        times = {t["homeAway"]: t for t in c["competitors"]}
        if times["home"]["team"]["id"] != tid(o["lc"]):
            continue
        st = e["status"]["type"]
        if not (st.get("completed") and st.get("state") == "post"):
            break
        h, a = times["home"], times["away"]
        gols = {h["team"]["id"]: [], a["team"]["id"]: []}
        for x in c.get("details", []):
            if not x.get("scoringPlay"):
                continue
            if "shootout" in x.get("type", {}).get("text", "").lower():
                continue
            nome = ", ".join(p["displayName"] for p in x.get("athletesInvolved", [])) or "?"
            extra = " (contra)" if x.get("ownGoal") else " (pên.)" if x.get("penaltyKick") else ""
            gols.setdefault(x.get("team", {}).get("id"), []).append(f"{nome} {minuto(x)}{extra}")
        linhas = [f"🏆 {o['liga']}", f"{o['casa']} {h.get('score','0')} x {a.get('score','0')} {o['fora']}"]
        if gols.get(h["team"]["id"]):
            linhas.append(f"⚽ {o['casa']}: " + "; ".join(gols[h['team']['id']]))
        if gols.get(a["team"]["id"]):
            linhas.append(f"⚽ {o['fora']}: " + "; ".join(gols[a['team']['id']]))
        blocos.append("\n".join(linhas)); chaves.append(chave)
        break

if not blocos:
    print("nenhum resultado novo"); sys.exit(0)
texto = "🏁 FIM DE JOGO\n\n" + "\n\n".join(blocos)
if dry:
    print(texto); sys.exit(0)
r = subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
                    "--data-urlencode", f"chat_id={CHAT}", "--data-urlencode", f"text={texto}"],
                   capture_output=True, text=True)
resp = json.loads(r.stdout or "{}")
if not resp.get("ok"):
    print("ERRO Telegram:", resp.get("description")); sys.exit(1)
posts.append({"message_id": resp["result"]["message_id"], "data": str(hoje), "tipo": "resultado", "jogos": chaves})
json.dump(posts, open("posts.json", "w"), ensure_ascii=False)
print(f"publicado message_id={resp['result']['message_id']} com {len(chaves)} jogo(s)")
