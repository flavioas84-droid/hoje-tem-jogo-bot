"""Arte de escalação (campo com os 11 de cada time na formação), no visual da agenda.
Uso como módulo: arte(o, summary, "saida.png")   o = jogo da agenda, summary = JSON do summary da ESPN.
Teste: python3 agenda/arte_escalacao.py <liga_espn> <event_id> "Casa" "Fora" "Liga" "HH:MM" saida.png
"""
import io, os, sys, json, urllib.request
from PIL import Image, ImageDraw, ImageFont

FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
f = lambda s, b=False: ImageFont.truetype(FONTE + ("-Bold" if b else "") + ".ttf", s)
OURO, VERDE, VERDE2 = (255, 215, 0), (16, 18, 20), (34, 37, 41)
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


# Quando a ESPN manda os titulares com posição "SUB" (ou sem posição), usa o formationPlace
# (numeração Opta: 1 goleiro, 2 LD, 3 LE, 5/6 zagueiros...) para deduzir a posição.
OPTA = {
    "4-2-3-1": {2: "RB", 5: "CD-R", 6: "CD-L", 3: "LB", 4: "DM-R", 8: "DM-L", 7: "RAM", 10: "AM", 11: "LAM", 9: "F"},
    "4-4-2": {2: "RB", 5: "CD-R", 6: "CD-L", 3: "LB", 7: "RM", 4: "CM-R", 8: "CM-L", 11: "LM", 10: "F-R", 9: "F-L"},
    "4-3-3": {2: "RB", 5: "CD-R", 6: "CD-L", 3: "LB", 8: "CM-R", 4: "CM", 10: "CM-L", 7: "RW", 9: "F", 11: "LW"},
    "4-1-4-1": {2: "RB", 5: "CD-R", 6: "CD-L", 3: "LB", 4: "DM", 7: "RM", 8: "CM-R", 10: "CM-L", 11: "LM", 9: "F"},
    "3-5-2": {6: "CD-R", 5: "CD", 4: "CD-L", 2: "RWB", 7: "CM-R", 8: "CM", 11: "CM-L", 3: "LWB", 10: "F-R", 9: "F-L"},
    "3-4-3": {6: "CD-R", 5: "CD", 4: "CD-L", 2: "RM", 7: "CM-R", 8: "CM-L", 3: "LM", 10: "RW", 9: "F", 11: "LW"},
    "5-3-2": {2: "RWB", 6: "CD-R", 5: "CD", 4: "CD-L", 3: "LWB", 7: "CM-R", 8: "CM", 11: "CM-L", 10: "F-R", 9: "F-L"},
}
VALIDAS = ("G", "D", "M", "F", "CD", "CB", "LB", "RB", "DM", "CM", "AM", "LM", "RM", "LW", "RW", "W", "WB", "LWB", "RWB", "SW", "CDM", "CAM", "LAM", "RAM", "LDM", "RDM")


def corrigir_posicoes(r, tit):
    ruins = [a for a in tit if a.get("position", {}).get("abbreviation", "").upper().split("-")[0] not in VALIDAS]
    if not ruins:
        return
    mapa = OPTA.get(r.get("formation") or "", OPTA["4-2-3-1"])
    for a in tit:
        fp = int(a.get("formationPlace") or 0)
        ab = "G" if fp == 1 else mapa.get(fp, "M")
        a["position"] = dict(a.get("position", {}), abbreviation=ab)


def linhas(r):
    tit = [a for a in r["roster"] if a.get("starter")]
    corrigir_posicoes(r, tit)
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

    # cabeçalho centralizado (no álbum o Telegram corta as laterais da miniatura)
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA"); lg.thumbnail((96, 96)); im.paste(lg, (30, 18), lg)
    meio = W / 2
    t = "ESCALAÇÕES"
    d.text((meio - d.textlength(t, font=f(54, True)) / 2, 14), t, font=f(54, True), fill=OURO)
    sub = f'{o["liga"]} · {o["hora"].replace(":", "h")}'
    d.text((meio - d.textlength(sub, font=f(28)) / 2, 80), sub, font=f(28), fill=(200, 205, 210))

    # faixa dos times: Mandante [escudo] x [escudo] Visitante, tudo junto do centro
    y0 = 126
    d.rounded_rectangle((20, y0, W - 20, y0 + 112), 18, fill=VERDE2)
    xs = f(40, True)
    d.text((meio - d.textlength("x", font=xs) / 2, y0 + 26), "x", font=xs, fill=(200, 205, 210))
    CR = 84
    for lado, nm, url in (("home", o["casa"], o["lc"]), ("away", o["fora"], o["lf"])):
        fm = ros[lado].get("formation") or ""
        sz = 42
        while d.textlength(nm, font=f(sz, True)) > 520 and sz > 20: sz -= 1
        tw = d.textlength(nm, font=f(sz, True)); fw = d.textlength(fm, font=f(22))
        c = img_url(url, CR)
        ty = y0 + 14 + (42 - sz) // 2
        if lado == "home":
            cx = meio - 40 - CR
            if c: im.paste(c, (int(cx + (CR - c.width) // 2), y0 + 14 + (CR - c.height) // 2), c)
            d.text((cx - 18 - tw, ty), nm, font=f(sz, True), fill="white")
            d.text((cx - 18 - fw, y0 + 72), fm, font=f(22), fill=(255, 235, 150))
        else:
            cx = meio + 40
            if c: im.paste(c, (int(cx + (CR - c.width) // 2), y0 + 14 + (CR - c.height) // 2), c)
            d.text((cx + CR + 18, ty), nm, font=f(sz, True), fill="white")
            d.text((cx + CR + 18, y0 + 72), fm, font=f(22), fill=(255, 235, 150))

    # campo deitado: mandante ataca da esquerda pra direita
    cx0, cy0, cx1, cy1 = 40, 256, W - 40, H - 70
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 12, fill=(26, 92, 54))
    for k in range(1, 12, 2):
        xx = cx0 + (cx1 - cx0) * k / 12
        d.rectangle((xx, cy0, xx + (cx1 - cx0) / 12, cy1), fill=(30, 100, 59))
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
        if abs(lum(bg) - lum((26, 92, 54))) < 40:
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
                d.rounded_rectangle((x - tw / 2 - 6, y + R + 2, x + tw / 2 + 6, y + R + sz + 10), 6, fill=(16, 18, 20))
                d.text((x - tw / 2, y + R + 4), nm, font=f(sz, True), fill="white")

    d.text((40, H - 50), "Horários de Brasília", font=f(22), fill=(200, 205, 210))
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
