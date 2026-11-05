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
    return 5  # F, CF, ST, LF, RF...


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
    "3-4-2-1": {6: "CD-R", 5: "CD", 4: "CD-L", 2: "RM", 7: "CM-R", 8: "CM-L", 3: "LM", 10: "RAM", 11: "LAM", 9: "F"},
    "4-4-1-1": {2: "RB", 5: "CD-R", 6: "CD-L", 3: "LB", 7: "RM", 4: "CM-R", 8: "CM-L", 11: "LM", 10: "AM", 9: "F"},
    "3-4-3": {6: "CD-R", 5: "CD", 4: "CD-L", 2: "RM", 7: "CM-R", 8: "CM-L", 3: "LM", 10: "RW", 9: "F", 11: "LW"},
    "5-3-2": {2: "RWB", 6: "CD-R", 5: "CD", 4: "CD-L", 3: "LWB", 7: "CM-R", 8: "CM", 11: "CM-L", 10: "F-R", 9: "F-L"},
}
VALIDAS = ("G", "D", "M", "F", "CD", "CB", "LB", "RB", "DM", "CM", "AM", "LM", "RM", "LW", "RW", "W", "WB", "LWB", "RWB", "SW", "CDM", "CAM", "LAM", "RAM", "LDM", "RDM", "CF", "ST", "LF", "RF")


def corrigir_posicoes(r, tit):
    ruins = [a for a in tit if a.get("position", {}).get("abbreviation", "").upper().split("-")[0] not in VALIDAS]
    # com formação conhecida e formationPlace de todos, a numeração Opta é mais confiável que a posição
    usar_opta = (r.get("formation") or "") in OPTA and all(int(a.get("formationPlace") or 0) for a in tit)
    if not ruins and not usar_opta:
        return
    if not ruins and (r.get("formation") or "") not in OPTA:
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
    # VERTICAL 1080x1860 desde 05/11/2026 (feedback de seguidor: deitada ficava pequena no celular).
    # Mandante em cima, visitante embaixo. Versão deitada: /workspace/work/arte_escalacao_horizontal_backup.py
    W, H = 1080, 1860
    im = Image.new("RGB", (W, H), VERDE); d = ImageDraw.Draw(im)
    ros = {r["homeAway"]: r for r in s["rosters"]}
    lum = lambda c: 0.299*c[0]+0.587*c[1]+0.114*c[2]
    if os.path.exists(LOGO):
        lg = Image.open(LOGO).convert("RGBA"); lg.thumbnail((100, 100)); im.paste(lg, (28, 20), lg)
    meio = W/2
    t = "ESCALAÇÕES"; d.text((meio-d.textlength(t, font=f(60, True))/2, 18), t, font=f(60, True), fill=OURO)
    sub = f'{o["liga"]} · {o["hora"].replace(":", "h")}'
    d.text((meio-d.textlength(sub, font=f(32))/2, 92), sub, font=f(32), fill=(200, 205, 210))
    cx0, cx1 = 30, W-30
    BAR = 96
    top_y, fy0 = 150, 150+BAR+12
    fy1 = H-80-BAR-12; bot_y = fy1+12
    # faixas dos times (mandante em cima, visitante embaixo)
    for lado, nm, url, y in (("home", o["casa"], o["lc"], top_y), ("away", o["fora"], o["lf"], bot_y)):
        d.rounded_rectangle((cx0, y, cx1, y+BAR), 18, fill=VERDE2)
        c = img_url(url, 72)
        if c: im.paste(c, (cx0+20+(72-c.width)//2, y+12+(72-c.height)//2), c)
        sz = 44
        while d.textlength(nm, font=f(sz, True)) > 640 and sz > 22: sz -= 1
        d.text((cx0+112, y+(BAR-sz)//2-4), nm, font=f(sz, True), fill="white")
        fm = ros[lado].get("formation") or ""
        if fm:
            fw = d.textlength(fm, font=f(32, True))
            d.rounded_rectangle((cx1-fw-50, y+24, cx1-20, y+BAR-24), 14, fill=(52, 56, 61))
            d.text((cx1-fw-35, y+28), fm, font=f(32, True), fill=(255, 235, 150))
    # campo em pé
    d.rounded_rectangle((cx0, fy0, cx1, fy1), 12, fill=(26, 92, 54))
    for k in range(1, 14, 2):
        yy = fy0+(fy1-fy0)*k/14
        d.rectangle((cx0, yy, cx1, yy+(fy1-fy0)/14), fill=(30, 100, 59))
    L = (215, 240, 220); mid = (fy0+fy1)/2; cxm = W/2
    d.rounded_rectangle((cx0, fy0, cx1, fy1), 12, outline=L, width=3)
    d.line((cx0, mid, cx1, mid), fill=L, width=3)
    d.ellipse((cxm-95, mid-95, cxm+95, mid+95), outline=L, width=3)
    for cima in (True, False):
        a, b = (fy0, fy0+150) if cima else (fy1-150, fy1)
        d.rectangle((cxm-230, a, cxm+230, b), outline=L, width=3)
        a, b = (fy0, fy0+55) if cima else (fy1-55, fy1)
        d.rectangle((cxm-100, a, cxm+100, b), outline=L, width=3)
    cores = {}
    for lado in ("home", "away"):
        r = ros[lado]
        bg = cor(r["team"].get("color"), OURO if lado == "home" else (255, 255, 255))
        if sum((x-y)**2 for x, y in zip(bg, (26, 92, 54)))**0.5 < 90: bg = cor(r["team"].get("alternateColor"), (255, 255, 255))
        if lado == "away" and sum((x-y)**2 for x, y in zip(bg, cores["home"]))**0.5 < 90:
            bg = cor(r["team"].get("alternateColor"), (255, 255, 255))
            if sum((x-y)**2 for x, y in zip(bg, cores["home"]))**0.5 < 90: bg = (255, 255, 255)
        cores[lado] = bg
        tx = "black" if lum(bg) > 140 else "white"
        ls = linhas(r); n = len(ls); meia = mid-fy0
        for i, linha in enumerate(ls):
            frac = 0.04+0.86*i/max(1, n-1)
            y = fy0+50+frac*(meia-125) if lado == "home" else fy1-70-frac*(meia-125)
            k = len(linha)
            for j, a in enumerate(linha):
                jj = k-1-j if lado == "home" else j   # mandante desce: esquerda dele fica à direita da tela
                x = cx0+(cx1-cx0)*(jj+1)/(k+1)
                R = 34
                d.ellipse((x-R, y-R, x+R, y+R), fill=bg, outline="white", width=3)
                num = str(a.get("jersey", ""))
                d.text((x-d.textlength(num, font=f(28, True))/2, y-17), num, font=f(28, True), fill=tx)
                nm = nome(a); sz = 27
                lim = min(230, (cx1-cx0)/(k+1) - 12)
                while d.textlength(nm, font=f(sz, True)) > lim and sz > 16: sz -= 1
                tw = d.textlength(nm, font=f(sz, True))
                d.rounded_rectangle((x-tw/2-7, y+R+3, x+tw/2+7, y+R+sz+13), 7, fill=(16, 18, 20))
                d.text((x-tw/2, y+R+5), nm, font=f(sz, True), fill="white")
    d.text((34, H-58), "Horários de Brasília", font=f(26), fill=(200, 205, 210))
    sg = "Siga: @hojetemjogobr"
    d.text((W-34-d.textlength(sg, font=f(34, True)), H-64), sg, font=f(34, True), fill=OURO)
    im.save(dst)

if __name__ == "__main__":
    liga, ev, casa, fora, nl, hora, dst = sys.argv[1:8]
    s = json.load(urllib.request.urlopen(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga}/summary?event={ev}", timeout=20))
    tl = {r["homeAway"]: r["team"]["id"] for r in s["rosters"]}
    u = lambda i: f"https://a.espncdn.com/i/teamlogos/soccer/500/{i}.png"
    arte({"casa": casa, "fora": fora, "liga": nl, "hora": hora, "lc": u(tl["home"]), "lf": u(tl["away"])}, s, dst)
    print(dst)
