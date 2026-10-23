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
    W, H = 1080, 1350
    im = Image.new("RGB", (W, H), VERDE)
    d = ImageDraw.Draw(im)
    ros = {r["homeAway"]: r for r in s["rosters"]}

    # cabeçalho
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA"); lg.thumbnail((110, 110)); im.paste(lg, (30, 22), lg)
    d.text((160, 30), "ESCALAÇÕES", font=f(50, True), fill=OURO)
    sub = f'{o["liga"]} · {o["hora"].replace(":", "h")}'
    d.text((162, 92), sub, font=f(28), fill=(200, 230, 210))

    # placa dos times
    y0 = 150
    d.rounded_rectangle((20, y0, W - 20, y0 + 90), 18, fill=VERDE2)
    for lado, x, url in (("home", 40, o["lc"]), ("away", W - 110, o["lf"])):
        c = img_url(url, 70)
        if c: im.paste(c, (x + (70 - c.width) // 2, y0 + 10 + (70 - c.height) // 2), c)
    fm = lambda l: (ros[l].get("formation") or "")
    t = f'{o["casa"]}  x  {o["fora"]}'
    sz = 34
    while d.textlength(t, font=f(sz, True)) > 800 and sz > 18: sz -= 1
    d.text((W / 2 - d.textlength(t, font=f(sz, True)) / 2, y0 + 12), t, font=f(sz, True), fill="white")
    ff = f'{fm("home")}  ·  {fm("away")}'
    d.text((W / 2 - d.textlength(ff, font=f(24)) / 2, y0 + 56), ff, font=f(24), fill=(255, 235, 150))

    # campo
    cx0, cy0, cx1, cy1 = 40, 260, W - 40, H - 80
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 12, fill=(30, 120, 65))
    for k in range(10):
        if k % 2:
            yy = cy0 + (cy1 - cy0) * k / 10
            d.rectangle((cx0, yy, cx1, yy + (cy1 - cy0) / 10), fill=(34, 128, 70))
    L = (215, 240, 220); mid = (cy0 + cy1) / 2; cxm = (cx0 + cx1) / 2
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 12, outline=L, width=3)
    d.line((cx0, mid, cx1, mid), fill=L, width=3)
    d.ellipse((cxm - 90, mid - 90, cxm + 90, mid + 90), outline=L, width=3)
    for top in (True, False):
        a, b = (cy0, cy0 + 150) if top else (cy1 - 150, cy1)
        d.rectangle((cxm - 220, a, cxm + 220, b), outline=L, width=3)
        a, b = (cy0, cy0 + 55) if top else (cy1 - 55, cy1)
        d.rectangle((cxm - 100, a, cxm + 100, b), outline=L, width=3)

    def lum(c): return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    for lado in ("home", "away"):
        r = ros[lado]
        bg = cor(r["team"].get("color"), OURO if lado == "home" else (255, 255, 255))
        if abs(lum(bg) - lum((30, 120, 65))) < 40:
            bg = cor(r["team"].get("alternateColor"), (255, 255, 255))
        tx = "black" if lum(bg) > 140 else "white"
        ls = linhas(r)
        n = len(ls)
        for i, linha in enumerate(ls):
            # mandante embaixo atacando pra cima; visitante em cima atacando pra baixo
            frac = 0.06 + 0.86 * i / max(1, n - 1)
            meia = (mid - cy0)
            y = cy1 - 45 - frac * (meia - 70) if lado == "home" else cy0 + 45 + frac * (meia - 70)
            k = len(linha)
            for j, a in enumerate(linha):
                jj = j if lado == "home" else k - 1 - j  # visitante de frente: espelha
                x = cx0 + (cx1 - cx0) * (jj + 1) / (k + 1)
                R = 30
                d.ellipse((x - R, y - R, x + R, y + R), fill=bg, outline="white", width=3)
                num = str(a.get("jersey", ""))
                d.text((x - d.textlength(num, font=f(24, True)) / 2, y - 15), num, font=f(24, True), fill=tx)
                nm = nome(a); sz = 22
                while d.textlength(nm, font=f(sz, True)) > (cx1 - cx0) / (k + 1) - 6 and sz > 13: sz -= 1
                tw = d.textlength(nm, font=f(sz, True))
                d.rounded_rectangle((x - tw / 2 - 6, y + R + 2, x + tw / 2 + 6, y + R + sz + 10), 6, fill=(0, 0, 0, 0) if False else (12, 60, 34))
                d.text((x - tw / 2, y + R + 4), nm, font=f(sz, True), fill="white")

    d.text((40, H - 55), "Horários de Brasília", font=f(22), fill=(200, 230, 210))
    sg = "Siga: @hojetemjogobr"
    d.text((W - 40 - d.textlength(sg, font=f(30, True)), H - 61), sg, font=f(30, True), fill=OURO)
    im.save(dst)


if __name__ == "__main__":
    liga, ev, casa, fora, nl, hora, dst = sys.argv[1:8]
    s = json.load(urllib.request.urlopen(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/summary?event={ev}", timeout=20))
    tl = {r["homeAway"]: r["team"]["id"] for r in s["rosters"]}
    u = lambda i: f"https://a.espncdn.com/i/teamlogos/soccer/500/{i}.png"
    arte({"casa": casa, "fora": fora, "liga": nl, "hora": hora, "lc": u(tl["home"]), "lf": u(tl["away"])}, s, dst)
    print(dst)
