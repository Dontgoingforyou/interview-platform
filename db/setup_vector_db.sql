-- SQL скрипт для установки pgvector в векторной БД
-- Используется при инициализации контейнера Docker

-- Установка расширения pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Проверка установки
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Готово! Миграции Django создадут остальные таблицы
