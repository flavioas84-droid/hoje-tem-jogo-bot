"""Posta 1 notícia curta da ESPN Brasil no canal Hoje Tem Jogo.
Uso (cwd = raiz do repo): python3 agenda/noticias.py [--dry]
- Lê os feeds de notícias da ESPN (pt-BR) das ligas abaixo.
- Só artigos (nada de vídeo), das últimas 24h, sem nada de apostas.
- Posta manchete + resumo + crédito com link e registra em posts.json (tipo "noticia").
"""
import json, os, sys, re, html, urllib.request, datetime as dt, subprocess

dry = "--dry" in sys.argv
BR = dt.timezone(dt.timedelta(hours=-3))
agora = dt.datetime.now(BR)
hoje = agora.date().isoformat()
CHAT = "-1003873202735"
FEEDS = ["bra.1", "bra.2", "eng.1", "esp.1", "ita.1", "ger.1", "fra.1", "por.1", "conmebol.libertadores"]

# Regra do canal (MP 1.394/2026): nada envolvendo apostas.
PROIBIDO = re.compile(
    r"palpite|apost|\bodds?\b|\bbets?\b|bet365|betano|superbet|cota[cç][aã]o|progn[oó]stic|bol[aã]o|cassino|"
    r"gambl|tipster|loteria|onde assistir|de gra[cç]a no youtube",
    re.I)

posts = json.load(open("posts.json"))
feitos = {str(p.get("noticia")) for p in posts if p.get("noticia")}

arts = {}
for f in FEEDS:
    u = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{f}/news?lang=pt&region=br&limit=25"
    try:
        dados = json.load(urllib.request.urlopen(u, timeout=20))
    except Exception:
        continue
    for a in dados.get("articles", []):
        if a.get("type") != "dStory":
            continue
        link = a.get("links", {}).get("web", {}).get("href", "")
        texto = " ".join([a.get("headline", ""), a.get("description", ""), link])
        if not link or PROIBIDO.search(texto):
            continue
        if any(PROIBIDO.search(c.get("description", "")) for c in a.get("categories", [])):
            continue
        try:
            pub = dt.datetime.fromisoformat(a["published"].replace("Z", "+00:00"))
        except Exception:
            continue
        if agora - pub > dt.timedelta(hours=24) or str(a["id"]) in feitos:
            continue
        arts[str(a["id"])] = (pub, a, link)

if not arts:
    print("nenhuma notícia nova"); sys.exit(0)

pub, a, link = max(arts.values(), key=lambda t: t[0])
e = html.escape
autor = a.get("byline") or "ESPN.com.br"
credito = "ESPN.com.br" if "espn" in autor.lower() else f"{autor}, ESPN.com.br"
texto = f"📰 <b>{e(a['headline'])}</b>"
if a.get("description"):
    texto += f"\n\n{e(a['description'])}"
texto += f"\n\nFonte: <a href=\"{e(link)}\">{e(credito)}</a>"

if dry:
    print(texto); sys.exit(0)

token = os.environ.get("TELEGRAM_TOKEN") or "__SAVED_KEY__"
r = subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{token}/sendMessage",
                    "-d", f"chat_id={CHAT}", "-d", "parse_mode=HTML",
                    "--data-urlencode", f"text={texto}"], capture_output=True, text=True)
resp = json.loads(r.stdout or "{}")
if not resp.get("ok"):
    sys.exit(f"ERRO Telegram: {resp.get('description')}")
posts.append({"message_id": resp["result"]["message_id"], "data": hoje, "tipo": "noticia", "noticia": str(a["id"])})
json.dump(posts, open("posts.json", "w"), ensure_ascii=False)
print("publicado", resp["result"]["message_id"], a["headline"])
