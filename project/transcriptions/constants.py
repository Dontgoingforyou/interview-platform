# Если processing не обновлялась дольше — при опросе статуса считаем задачу мёртвой (см. heartbeat в tasks).
TRANSCRIPTION_PROCESSING_STALE_MINUTES = 90

# Не ставить вторую Celery-задачу, если уже pending и запись недавно трогали (дубли с фронта / гонки).
TRANSCRIPTION_PENDING_COOLDOWN_MINUTES = 5

# Обновление updated_at во время долгого вызова Deepgram (секунды).
TRANSCRIPTION_PROCESSING_HEARTBEAT_SECONDS = 300
