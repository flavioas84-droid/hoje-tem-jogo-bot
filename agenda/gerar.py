"""Gera a(s) arte(s) da agenda do dia.
Uso (cwd = pasta do projeto): python3 agenda/gerar.py agenda/AAAA-MM-DD.json agenda/AAAA-MM-DD.png "Título"
Até 15 jogos: uma imagem (o .png pedido). Mais que isso: divide por igual em várias
artes (AAAA-MM-DD-1.png, -2.png...), com "(1/2)" no título. Imprime os arquivos gerados, um por linha.
"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

MAX = 15
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
f = lambda s, b=False: ImageFont.truetype(FONTE + ("-Bold" if b else "") + ".ttf", s)


def arte(J, titulo, dst):
    W, RH, HD = 1080, 118, 200
    H = HD + RH * len(J) + 70
    im = Image.new("RGB", (W, H), (16, 18, 20))
    d = ImageDraw.Draw(im)
    try:
        lg = Image.open("/workspace/hoje-tem-jogo-logo-circulo.png").convert("RGBA")
        lg.thumbnail((160, 160)); im.paste(lg, (30, 20), lg)
    except Exception:
        pass
    d.text((210, 45), "AGENDA DO DIA", font=f(54, True), fill=(255, 215, 0))

    def fit(t, mx, sz, b=True):
        while d.textlength(t, font=f(sz, b)) > mx and sz > 16:
            sz -= 1
        return f(sz, b)

    d.text((210, 115), titulo, font=fit(titulo, 840, 34, False), fill="white")

    def crest(p, x, y, s=56):
        try:
            c = Image.open(p).convert("RGBA"); c.thumbnail((s, s))
            im.paste(c, (x + (s - c.width) // 2, y + (s - c.height) // 2), c)
        except Exception:
            pass

    def tvicon(x, y, c=(255, 235, 150)):
        d.line((x + 9, y + 1, x + 15, y + 7), fill=c, width=2)
        d.line((x + 21, y + 1, x + 15, y + 7), fill=c, width=2)
        d.rounded_rectangle((x, y + 7, x + 30, y + 25), 4, outline=c, width=3)
        d.line((x + 9, y + 28, x + 21, y + 28), fill=c, width=2)

    for i, o in enumerate(J):
        y = HD + i * RH
        d.rounded_rectangle((20, y + 6, W - 20, y + RH - 6), 18, fill=(34, 37, 41) if i % 2 == 0 else (28, 31, 35))
        d.rounded_rectangle((20, y + 6, 28, y + RH - 6), 4, fill=(0, 176, 80))
        d.text((40, y + 22), o["hora"].replace(":", "h"), font=f(36, True), fill=(46, 204, 113))
        d.text((40, y + 66), o["liga"], font=fit(o["liga"], 190, 20, False), fill=(190, 196, 202))
        if o.get("rodada"):
            d.text((40, y + 89), f'{o["rodada"]}ª rodada', font=f(18), fill=(140, 148, 156))
        crest("escudos/" + o["lc"].split("/")[-1], 245, y + 16)
        t = f'{o["casa"]}  x  {o["fora"]}'
        d.text((312, y + 22), t, font=fit(t, 660, 30), fill="white")
        crest("escudos/" + o["lf"].split("/")[-1], W - 100, y + 16)
        tvicon(312, y + 70)
        d.text((350, y + 68), o["tv"], font=fit(o["tv"], 620, 22, False), fill=(255, 235, 150))
    d.text((40, H - 52), "Horários de Brasília", font=f(22), fill=(190, 196, 202))
    sg = "Siga: @hojetemjogobr"
    d.text((im.width - 40 - d.textlength(sg, font=f(30, True)), H - 58), sg, font=f(30, True), fill=(255, 215, 0))
    im.save(dst)


src, dst, titulo = sys.argv[1], sys.argv[2], sys.argv[3]
todos = sorted(json.load(open(src)), key=lambda o: (o["hora"], o["liga"]))
n = max(1, -(-len(todos) // MAX))
k = -(-len(todos) // n) if todos else 1
partes = [todos[i:i + k] for i in range(0, len(todos), k)] or [[]]
for pi, J in enumerate(partes):
    out = dst if len(partes) == 1 else dst.replace(".png", f"-{pi + 1}.png")
    tit = titulo if len(partes) == 1 else f"{titulo}  ({pi + 1}/{len(partes)})"
    arte(J, tit, out)
    print(out)
