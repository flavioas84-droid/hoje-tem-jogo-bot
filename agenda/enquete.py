"""Enquete "Quem vence?" do jogo do dia (só opinião do público, nada de apostas).
Uso (cwd = raiz do repo): python3 agenda/enquete.py [--dry]   (HOJE=AAAA-MM-DD / AGORA=HH:MM para testar)
- A partir das 10h (Brasília), escolhe o jogo do dia na agenda (clubes grandes + peso da liga),
  posta uma enquete anônima com mandante / Empate / visitante e registra em posts.json (tipo "enquete").
- Quando o jogo começa, encerra a enquete (stopPoll) e marca "encerrada": true.
- No máximo 1 enquete por dia; jogo que começa em menos de 30 min não é escolhido.
"""
import json, os, sys, datetime as dt, urllib.request
from zoneinfo import ZoneInfo

CHAT = "-1003873202735"
TZ = ZoneInfo("America/Sao_Paulo")
PESO_LIGA = {"Libertadores": 8, "Champions League": 8, "Eliminatórias": 8, "Copa do Brasil": 7,
             "Sul-Americana": 5, "Europa League": 4, "Paulistão": 4, "Carioca": 4, "Gauchão": 3, "Mineiro": 3,
             "Conference League": 2, "Argentino": 2, "Eredivisie": 1, "MLS": 1,
             "Brasileirão Série A": 6, "Premier League": 5, "La Liga": 4, "Serie A": 3,
             "Bundesliga": 3, "Ligue 1": 2, "Liga Portugal": 2, "Brasileirão Série B": 2,
             "Saudi Pro League": 1}
GRANDES = ["flamengo", "palmeiras", "corinthians", "são paulo", "sao paulo", "santos", "vasco",
           "fluminense", "botafogo", "grêmio", "gremio", "internacional", "atlético-mg", "atletico-mg",
           "atlético mineiro", "atletico mineiro", "cruzeiro", "bahia", "fortaleza",
           "real madrid", "barcelona", "atlético madrid", "atletico madrid", "manchester city",
           "manchester united", "liverpool", "arsenal", "chelsea", "tottenham", "bayern",
           "dortmund", "paris saint-germain", "psg", "juventus", "internazionale", "inter milan",
           "ac milan", "napoli", "roma", "brasil", "argentina", "boca juniors", "river plate", "benfica", "porto", "sporting", "al-hilal", "al-nassr"]
dry = "--dry" in sys.argv
agora = dt.datetime.now(TZ)
hoje = dt.date.fromisoformat(os.environ["HOJE"]) if os.environ.get("HOJE") else agora.date()
if os.environ.get("AGORA"):
    h, m = map(int, os.environ["AGORA"].split(":"))
    agora = dt.datetime(hoje.year, hoje.month, hoje.day, h, m, tzinfo=TZ)
try:
    agenda = json.load(open(f"agenda/{hoje}.json"))
except FileNotFoundError:
    print("sem agenda hoje"); sys.exit(0)
posts = json.load(open("posts.json"))
token = os.environ.get("TELEGRAM_TOKEN") or "__SAVED_KEY__"

def tg(metodo, dados):
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/{metodo}",
                                 data=json.dumps(dados).encode(), headers={"Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=20))
    except urllib.error.HTTPError as err:
        return json.load(err)

def inicio(o):
    h, m = map(int, o["hora"].split(":"))
    return dt.datetime(hoje.year, hoje.month, hoje.day, h, m, tzinfo=TZ)

def grande(nome):
    n = nome.lower()
    return any(g in n for g in GRANDES)

atual = next((p for p in posts if p.get("tipo") == "enquete" and p.get("data") == str(hoje)), None)

# 1) encerrar a enquete de hoje quando o jogo começa
if atual:
    if not atual.get("encerrada") and agora >= dt.datetime.fromisoformat(atual["inicio"]):
        if dry:
            print("encerraria enquete", atual["message_id"]); sys.exit(0)
        r = tg("stopPoll", {"chat_id": CHAT, "message_id": atual["message_id"]})
        if r.get("ok") or "already closed" in str(r.get("description", "")):
            atual["encerrada"] = True
            json.dump(posts, open("posts.json", "w"), ensure_ascii=False)
            print("enquete encerrada", atual["message_id"])
        else:
            sys.exit(f"ERRO Telegram: {r.get('description')}")
    else:
        print("enquete de hoje já publicada")
    sys.exit(0)

# 2) publicar a enquete do dia a partir das 10h
if agora.hour < 10:
    print("antes das 10h"); sys.exit(0)
cands = [o for o in agenda if inicio(o) - agora >= dt.timedelta(minutes=30)]
if not cands:
    print("nenhum jogo elegível"); sys.exit(0)
pontos = lambda o: (10 * (grande(o["casa"]) + grande(o["fora"])) + PESO_LIGA.get(o["liga"], 0),
                    inicio(o).hour)  # desempate: horário mais nobre
o = max(cands, key=pontos)
pergunta = f"⚽ Jogo do dia: {o['casa']} x {o['fora']} ({o['liga']}, {o['hora']}). Quem vence?"
opcoes = [o["casa"], "Empate", o["fora"]]
if dry:
    print(pergunta, opcoes); sys.exit(0)
r = tg("sendPoll", {"chat_id": CHAT, "question": pergunta[:300],
                    "options": [{"text": t[:100]} for t in opcoes], "is_anonymous": True})
if not r.get("ok"):
    sys.exit(f"ERRO Telegram: {r.get('description')}")
posts.append({"message_id": r["result"]["message_id"], "data": str(hoje), "tipo": "enquete",
              "inicio": inicio(o).isoformat(), "jogo": f"{o['casa']} x {o['fora']}"})
json.dump(posts, open("posts.json", "w"), ensure_ascii=False)
print("enquete publicada", r["result"]["message_id"], pergunta)
