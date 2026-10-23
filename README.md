# Hoje Tem Jogo — bot de resultados

Posta no canal t.me/hojetemjogobr os resultados dos jogos da agenda do dia, com os autores dos gols.

- `agenda/AAAA-MM-DD.json`: agenda do dia (enviada todo dia às 00:10 pelo Hark).
- `agenda/resultados.py`: consulta a ESPN e posta os jogos encerrados ainda não publicados.
- `posts.json`: registro dos posts do canal (usado pela limpeza diária).
- `.github/workflows/resultados.yml`: roda a cada 15 minutos, das 11h às 23h45 (Brasília).

Precisa do segredo `TELEGRAM_TOKEN` em Settings > Secrets and variables > Actions.
