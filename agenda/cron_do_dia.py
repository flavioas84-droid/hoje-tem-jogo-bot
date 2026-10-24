"""Ajusta o horário do resultados.yml (escalações, enquete e resultados) aos jogos da agenda do dia.
Uso (cwd = raiz do projeto): python3 agenda/cron_do_dia.py agenda/AAAA-MM-DD.json
Roda a cada 15 min só nas horas que vão de 90 min antes do 1º apito de cada jogo
até 2h30 depois dele (escalação sai ~1h antes; resultado ~2h depois). Depois suba
.github/workflows/resultados.yml com gh_sync.py push.
"""
import sys, json, re

jogos = json.load(open(sys.argv[1]))
horas = set()
for j in jogos:
    h, m = map(int, j["hora"].split(":"))
    ini = h * 60 + m + 180          # Brasília -> UTC (UTC-3), em minutos
    for t in range(ini - 90, ini + 151, 15):
        horas.add((t // 60) % 24)
if horas:
    crons = [f'    - cron: "*/15 {",".join(map(str, sorted(horas)))} * * *"   # gerado por cron_do_dia.py (UTC)']
else:
    crons = ['    - cron: "0 15 * * *"   # dia sem jogos (gerado por cron_do_dia.py)']
yml = open(".github/workflows/resultados.yml").read()
yml = re.sub(r"  schedule:\n(?:    - cron:.*\n)+", "  schedule:\n" + "\n".join(crons) + "\n", yml)
open(".github/workflows/resultados.yml", "w").write(yml)
print("\n".join(crons))
