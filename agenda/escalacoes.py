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
         "Liga Portugal": "por.1", "Saudi Pro League": "ksa.1",
         "Libertadores": "conmebol.libertadores", "Sul-Americana": "conmebol.sudamericana",
         "Copa do Brasil": "bra.copa_do_brazil", "Champions League": "uefa.champions",
         "Europa League": "uefa.europa", "Conference League": "uefa.europa.conf",
         "Paulistão": "bra.camp.paulista", "Carioca": "bra.camp.carioca", "Gauchão": "bra.camp.gaucho",
         "Mineiro": "bra.camp.mineiro", "Eliminatórias": "fifa.worldq.conmebol",
         "Argentino": "arg.1", "MLS": "usa.1", "Eredivisie": "ned.1",
         "Copa da Liga Inglesa": "eng.league_cup", "Colombiano": "col.1", "Mexicano": "mex.1"}
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

blocos, chaves, jogos = [], [], []
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
        # Escalação só ANTES do apito inicial (regra do usuário, 24/10): jogo começado ou encerrado não sai.
        if ev["status"]["type"].get("state") != "pre" and not teste:
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
            blocos.append("\n".join(linhas)); chaves.append(chave); jogos.append((o, s))
        break

if not blocos:
    print("nenhuma escalação nova"); sys.exit(0)
texto = "📋 ESCALAÇÕES\n\n" + "\n\n".join(blocos)
token = os.environ.get("TELEGRAM_TOKEN") or "__SAVED_KEY__"

# 1º: tenta mandar como arte (uma imagem por jogo; álbum se forem vários)
ids = []
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from arte_escalacao import arte
    fotos = []
    for n, (o, sm) in enumerate(jogos):
        arq = f"/tmp/escalacao-{n}.png"
        arte(o, sm, arq)
        fotos.append((arq, f"📋 Escalações: {o['casa']} x {o['fora']} · {o['liga']} · {o['hora'].replace(':', 'h')}"))
    if dry:
        print("\n".join(a for a, _ in fotos)); sys.exit(0)
    for k in range(0, len(fotos), 10):
        grupo = fotos[k:k + 10]
        if len(grupo) == 1:
            cmd = ["curl", "-s", f"https://api.telegram.org/bot{token}/sendPhoto", "-F", f"chat_id={CHAT}",
                   "-F", f"photo=@{grupo[0][0]}", "-F", f"caption={grupo[0][1]}"]
        else:
            media = [{"type": "photo", "media": f"attach://f{j}", "caption": c} for j, (_, c) in enumerate(grupo)]
            cmd = ["curl", "-s", f"https://api.telegram.org/bot{token}/sendMediaGroup", "-F", f"chat_id={CHAT}",
                   "-F", "media=" + json.dumps(media, ensure_ascii=False)]
            cmd += sum([["-F", f"f{j}=@{a}"] for j, (a, _) in enumerate(grupo)], [])
        resp = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout or "{}")
        if not resp.get("ok"):
            raise RuntimeError(resp.get("description"))
        res = resp["result"]
        ids += [m["message_id"] for m in (res if isinstance(res, list) else [res])]
except SystemExit:
    raise
except Exception as err:
    print("arte falhou, mandando em texto:", err)

if not ids:
    if dry:
        print(texto); sys.exit(0)
    r = subprocess.run(["curl", "-s", f"https://api.telegram.org/bot{token}/sendMessage",
                        "-d", f"chat_id={CHAT}", "-d", "parse_mode=HTML", "-d", "disable_web_page_preview=true",
                        "--data-urlencode", f"text={texto}"], capture_output=True, text=True)
    resp = json.loads(r.stdout or "{}")
    if not resp.get("ok"):
        sys.exit(f"ERRO Telegram: {resp.get('description')}")
    ids = [resp["result"]["message_id"]]
for mid in ids:
    posts.append({"message_id": mid, "data": str(hoje), "tipo": "escalacao", "jogos": chaves})
json.dump(posts, open("posts.json", "w"), ensure_ascii=False)
print("publicado", ids, len(chaves), "jogos")
