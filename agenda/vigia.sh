#!/usr/bin/env bash
# Vigia do canal: a cada 5 min roda enquete, escalações (só antes do apito), resultados e,
# às 10h/14h/18h de Brasília, 1 notícia. Sai antes de 5h40 de execução ou à 00h00 de Brasília.
set -u
git config user.name "hoje-tem-jogo-bot"
git config user.email "actions@users.noreply.github.com"
inicio=$(date +%s)
while true; do
  git pull --rebase -q || true
  python3 agenda/enquete.py || true
  python3 agenda/escalacoes.py || true
  python3 agenda/resultados.py || true
  if python3 - <<'PY'
import json, datetime as dt
from zoneinfo import ZoneInfo
agora = dt.datetime.now(ZoneInfo("America/Sao_Paulo"))
hoje = str(agora.date())
feitas = sum(1 for p in json.load(open("posts.json")) if p.get("tipo") == "noticia" and p.get("data") == hoje)
devidas = sum(1 for h in (10, 14, 18) if agora.hour >= h)
raise SystemExit(0 if feitas < devidas else 1)
PY
  then python3 agenda/noticias.py || true; fi
  if ! git diff --quiet posts.json; then
    git add posts.json && git commit -q -m "Posts do vigia"
    git pull --rebase -q && git push -q || { git rebase --abort 2>/dev/null; git reset -q --hard origin/main; }
  fi
  agora=$(date +%s); hora=$(TZ=America/Sao_Paulo date +%H)
  if [ $((agora - inicio)) -gt 20400 ] || [ "$hora" = "23" -a "$(TZ=America/Sao_Paulo date +%M)" -ge 55 ]; then break; fi
  sleep 300
done
