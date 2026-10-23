"""Arte de escalação (campo com os 11 de cada time na formação), no visual da agenda.
Uso como módulo: arte(o, summary, "saida.png")   o = jogo da agenda, summary = JSON do summary da ESPN.
Teste: python3 agenda/arte_escalacao.py <liga_espn> <event_id> "Casa" "Fora" "Liga" "HH:MM" saida.png
"""
import io, os, sys, json, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
f = lambda s, b=False: ImageFont.truetype(FONTE + ("-Bold" if b else "") + ".ttf", s)
OURO, VERDE, VERDE2 = (255, 215, 0), (10, 70, 40), (18, 95, 55)
LOGO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "logo.png")


def img_url(u, s):
    try:
        cache = "/tmp/esc_" + u.rsplit("/", 1)[-1]
        if not os.path.exists(cache):
            open(cache, "wb").write(urllib.request.urlopen(u, timeout=20).read())
        c = Image.open(cache).convert("RGBA"); c.thumbnail((s, s)); return c
    except Exception:
        return None


def profundidade(p):
    p = p.upper().split("-")[0]
    if p == "G": return 0
    if p in ("CD", "LB", "RB", "D", "SW", "CB"): return 1
    if p in ("LWB", "RWB", "WB"): return 1.5
    if p in ("DM", "CDM", "LDM", "RDM"): return 2
    if p in ("CM", "LM", "RM", "M"): return 3
    if p in ("AM", "CAM", "LAM", "RAM"): return 3.5
    if p in ("LW", "RW", "W"): return 4
    return 5


def lateral(p):
    p = p.upper()
    if p[0] == "L" and p != "L": return -2
    if p[0] == "R" and p != "R": return 2
    if p.endswith("-L"): return -1
    if p.endswith("-R"): return 1
    return 0


def linhas(r):
    tit = [a for a in r["roster"] if a.get("starter")]
    gk = [a for a in tit if a["position"]["abbreviation"].upper() == "G"][:1]
    resto = sorted([a for a in tit if a not in gk], key=lambda a: (profundidade(a["position"]["abbreviation"]), a.get("formationPlace", 0)))
    try:
        nums = [int(x) for x in (r.get("formation") or "").split("-")]
        assert sum(nums) == len(resto)
    except Exception:
        nums = [4, 4, 2] if len(resto) == 10 else [len(resto)]
    out, i = [gk], 0
    for n in nums:
        out.append(sorted(resto[i:i + n], key=lambda a: lateral(a["position"]["abbreviation"]))); i += n
    return out


def nome(a):
    at = a["athlete"]
    n = at.get("lastName") or at.get("displayName", "")
    if len(n) > 14 and at.get("shortName"): n = at["shortName"]
    return n


def cor(h, padrao):
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except Exception:
        return padrao


def arte(o, s, dst):
    W, H = 1600, 1000
    im = Image.new("RGB", (W, H), VERDE)
    d = ImageDraw.Draw(im)
    ros = {r["homeAway"]: r for r in s["rosters"]}

    def lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    # cabeçalho: logo + título; mandante à esquerda, visitante à direita
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA"); lg.thumbnail((96, 96)); im.paste(lg, (30, 18), lg)
    d.text((140, 22), "ESCALAÇÕES", font=f(46, True), fill=OURO)
    sub = f'{o["liga"]} · {o["hora"].replace(":", "h")}'
    d.text((142, 78), sub, font=f(26), fill=(200, 230, 210))

    y0 = 130
    d.rounded_rectangle((20, y0, W - 20, y0 + 96), 18, fill=VERDE2)
    meio = W / 2
    d.text((meio - d.textlength("x", font=f(34, True)) / 2, y0 + 22), "x", font=f(34, True), fill=(200, 230, 210))
    for lado, nm, url in (("home", o["casa"], o["lc"]), ("away", o["fora"], o["lf"])):
        fm = ros[lado].get("formation") or ""
        sz = 34
        while d.textlength(nm, font=f(sz, True)) > 560 and sz > 18: sz -= 1
        tw = d.textlength(nm, font=f(sz, True)); fw = d.textlength(fm, font=f(22), )
        c = img_url(url, 72)
        if lado == "home":
            if c: im.paste(c, (40 + (72 - c.width) // 2, y0 + 12 + (72 - c.height) // 2), c)
            d.text((130, y0 + 12), nm, font=f(sz, True), fill="white")
            d.text((130, y0 + 58), fm, font=f(22), fill=(255, 235, 150))
        else:
            if c: im.paste(c, (W - 112 + (72 - c.width) // 2, y0 + 12 + (72 - c.height) // 2), c)
            d.text((W - 130 - tw, y0 + 12), nm, font=f(sz, True), fill="white")
            d.text((W - 130 - fw, y0 + 58), fm, font=f(22), fill=(255, 235, 150))

    # campo deitado: mandante ataca da esquerda pra direita
    cx0, cy0, cx1, cy1 = 40, 250, W - 40, H - 70
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 12, fill=(30, 120, 65))
    for k in range(1, 12, 2):
        xx = cx0 + (cx1 - cx0) * k / 12
        d.rectangle((xx, cy0, xx + (cx1 - cx0) / 12, cy1), fill=(34, 128, 70))
    L = (215, 240, 220); mid = (cx0 + cx1) / 2; cym = (cy0 + cy1) / 2
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 12, outline=L, width=3)
    d.line((mid, cy0, mid, cy1), fill=L, width=3)
    d.ellipse((mid - 85, cym - 85, mid + 85, cym + 85), outline=L, width=3)
    for esq in (True, False):
        a, b = (cx0, cx0 + 140) if esq else (cx1 - 140, cx1)
        d.rectangle((a, cym - 200, b, cym + 200), outline=L, width=3)
        a, b = (cx0, cx0 + 50) if esq else (cx1 - 50, cx1)
        d.rectangle((a, cym - 90, b, cym + 90), outline=L, width=3)

    for lado in ("home", "away"):
        r = ros[lado]
        bg = cor(r["team"].get("color"), OURO if lado == "home" else (255, 255, 255))
        if abs(lum(bg) - lum((30, 120, 65))) < 40:
            bg = cor(r["team"].get("alternateColor"), (255, 255, 255))
        tx = "black" if lum(bg) > 140 else "white"
        ls = linhas(r)
        n = len(ls)
        meia = mid - cx0
        for i, linha in enumerate(ls):
            frac = 0.05 + 0.88 * i / max(1, n - 1)
            x = cx0 + 55 + frac * (meia - 120) if lado == "home" else cx1 - 55 - frac * (meia - 120)
            k = len(linha)
            for j, a in enumerate(linha):
                # mandante olhando pra direita: esquerda dele = em cima; visitante espelhado
                jj = j if lado == "home" else k - 1 - j
                y = cy0 + (cy1 - cy0) * (jj + 1) / (k + 1) - 12
                R = 28
                d.ellipse((x - R, y - R, x + R, y + R), fill=bg, outline="white", width=3)
                num = str(a.get("jersey", ""))
                d.text((x - d.textlength(num, font=f(22, True)) / 2, y - 14), num, font=f(22, True), fill=tx)
                nm = nome(a); sz = 20
                while d.textlength(nm, font=f(sz, True)) > 150 and sz > 13: sz -= 1
                tw = d.textlength(nm, font=f(sz, True))
                d.rounded_rectangle((x - tw / 2 - 6, y + R + 2, x + tw / 2 + 6, y + R + sz + 10), 6, fill=(12, 60, 34))
                d.text((x - tw / 2, y + R + 4), nm, font=f(sz, True), fill="white")

    d.text((40, H - 50), "Horários de Brasília", font=f(22), fill=(200, 230, 210))
    sg = "Siga: @hojetemjogobr"
    d.text((W - 40 - d.textlength(sg, font=f(30, True)), H - 56), sg, font=f(30, True), fill=OURO)
    im.save(dst)


if __name__ == "__main__":
    liga, ev, casa, fora, nl, hora, dst = sys.argv[1:8]
    s = json.load(urllib.request.urlopen(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/summary?event={ev}", timeout=20))
    tl = {r["homeAway"]: r["team"]["id"] for r in s["rosters"]}
    u = lambda i: f"https://a.espncdn.com/i/teamlogos/soccer/500/{i}.png"
    arte({"casa": casa, "fora": fora, "liga": nl, "hora": hora, "lc": u(tl["home"]), "lf": u(tl["away"])}, s, dst)
    print(dst)
