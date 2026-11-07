# nginx

Единственный входной прокси. Контейнер из `docker-compose.yml` слушает http://localhost:82 и отдаёт статику и медиа с диска, остальное проксирует в Gunicorn (`web:8000`).

Конфиг: `nginx/nginx.conf`.
