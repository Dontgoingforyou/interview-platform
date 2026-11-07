# =============================================================================
# Makefile пет-проекта «Платформа собеседований»
# =============================================================================
# Использование: make <команда>
# =============================================================================

.PHONY: help install test lint coverage clean build up up-build down restart logs shell migrate makemigrations collectstatic seed status rebuild logs-web logs-celery check-deps pre-commit typecheck lint-frontend test-frontend env

# Цвета для вывода
BLUE := \033[0;34m
GREEN := \033[0;32m
NC := \033[0m # No Color
COMPOSE := docker compose --env-file .env.local -p interview-management-local

.env.local:
	cp .env.example .env.local
	@echo "$(GREEN).env.local создан из .env.example$(NC)"

env: .env.local

# Активированный shell-venv make не видит: команды всё равно шли через poetry run.
# Если есть .venv — используем его бинарники; иначе fallback на poetry.
ifeq ($(wildcard .venv/bin/python),)
  RUN := poetry run
else
  RUN := .venv/bin/
endif

# По умолчанию показываем справку
help:
	@echo "$(BLUE)=========================================$(NC)"
	@echo "$(GREEN)  Платформа собеседований$(NC)"
	@echo "$(BLUE)=========================================$(NC)"
	@echo ""
	@echo "Доступные команды:"
	@echo ""
	@echo "  $(GREEN)Development:$(NC)"
	@echo "    make install        - Создать .venv и установить зависимости"
	@echo "    make test           - Запустить тесты pytest"
	@echo "    make lint           - Запустить flake8"
	@echo "    make typecheck      - Запустить mypy"
	@echo "    make lint-frontend  - ESLint и проверка типов фронтенда"
	@echo "    make test-frontend  - Тесты фронтенда (Vitest)"
	@echo "    make coverage       - Тесты с отчётом coverage"
	@echo "    make clean          - Удалить временные файлы"
	@echo ""
	@echo "  $(GREEN)Docker:$(NC)"
	@echo "    make build          - Собрать Docker-образы"
	@echo "    make up             - Запустить"
	@echo "    make up-build       - Собрать образы и запустить"
	@echo "    make down           - Остановить"
	@echo "    make restart        - Перезапустить"
	@echo "    make status         - Статус контейнеров"
	@echo "    make logs           - Логи"
	@echo "    make logs-web       - Логи web"
	@echo "    make logs-celery    - Логи celery"
	@echo "    make shell          - Shell в контейнере web"
	@echo "    make rebuild        - Пересобрать с нуля"
	@echo ""
	@echo "  $(GREEN)Django:$(NC)"
	@echo "    make migrate        - Применить миграции"
	@echo "    make makemigrations - Создать миграции"
	@echo "    make collectstatic  - Собрать статику"
	@echo "    make seed           - Учебные записи в уже запущенный web"
	@echo ""

# =============================================================================
# Development команды
# =============================================================================

install:
	@echo "$(BLUE)Установка зависимостей в .venv...$(NC)"
	python3 -m venv .venv
	.venv/bin/python -m pip install -U pip 'poetry>=2.2,<3'
	.venv/bin/poetry install
	@echo "$(GREEN)Зависимости установлены$(NC)"

test:
	@echo "$(BLUE)Запуск тестов...$(NC)"
	DISABLE_VECTOR_SIGNALS=1 $(RUN)pytest -v
	@echo "$(GREEN)Тесты завершены$(NC)"

lint:
	@echo "$(BLUE)Запуск линтера...$(NC)"
	$(RUN)flake8 project tests --count --statistics
	@echo "$(GREEN)Линтинг завершен$(NC)"

pre-commit:
	@echo "$(BLUE)Запуск pre-commit по всем файлам...$(NC)"
	$(RUN)pre-commit run --all-files
	@echo "$(GREEN)pre-commit завершен$(NC)"

typecheck:
	@echo "$(BLUE)Запуск mypy...$(NC)"
	$(RUN)mypy project/core/ project/interviews/ project/interns/ project/offers/ project/debts/ project/sad_intern/ project/managers/ project/directions/ project/companies/ project/employees/ project/developers/ project/accounts/ project/vector_search/ project/knowledge_base_app/ project/interns_portal/ project/interviews_database/ project/transcriptions/
	@echo "$(GREEN)Проверка типов завершена$(NC)"

lint-frontend:
	@echo "$(BLUE)Запуск линтера фронтенда...$(NC)"
	@test -x project/frontend/node_modules/.bin/eslint || { echo "Нет зависимостей фронтенда. Выполните: cd project/frontend && npm ci"; exit 1; }
	cd project/frontend && npm run lint && npm run typecheck
	@echo "$(GREEN)Линтинг фронтенда завершен$(NC)"

test-frontend:
	@echo "$(BLUE)Запуск тестов фронтенда...$(NC)"
	@test -x project/frontend/node_modules/.bin/vitest || { echo "Нет зависимостей фронтенда. Выполните: cd project/frontend && npm ci"; exit 1; }
	cd project/frontend && npm run test
	@echo "$(GREEN)Тесты фронтенда завершены$(NC)"

coverage:
	@echo "$(BLUE)Запуск тестов с coverage...$(NC)"
	DISABLE_VECTOR_SIGNALS=1 $(RUN)pytest --cov --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage отчет создан в htmlcov/index.html$(NC)"

clean:
	@echo "$(BLUE)Очистка временных файлов...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage
	@echo "$(GREEN)Временные файлы удалены$(NC)"

# =============================================================================
# Docker команды (local development)
# =============================================================================

build: .env.local
	@echo "$(BLUE)Сборка Docker образов...$(NC)"
	$(COMPOSE) build --no-cache
	@echo "$(GREEN)Образы собраны$(NC)"

up: .env.local
	@echo "$(BLUE)Запуск контейнеров...$(NC)"
	$(COMPOSE) up -d
	@echo "$(GREEN)Контейнеры запущены$(NC)"
	@echo ""
	@echo "Сайт: http://localhost:82"
	@echo "API:  http://localhost:8001"
	@echo "Вход: admin / demo-admin, manager / demo-manager, student / demo-student"

up-build: .env.local
	@echo "$(BLUE)Сборка и запуск контейнеров...$(NC)"
	$(COMPOSE) up --build
	@echo "$(GREEN)Контейнеры собраны и запущены$(NC)"
	@echo ""
	@echo "Сайт: http://localhost:82"
	@echo "API:  http://localhost:8001"
	@echo "Вход: admin / demo-admin, manager / demo-manager, student / demo-student"

down: .env.local
	@echo "$(BLUE)Остановка контейнеров...$(NC)"
	$(COMPOSE) down
	@echo "$(GREEN)Контейнеры остановлены$(NC)"

restart: down up

logs: .env.local
	@echo "$(BLUE)Логи контейнеров:$(NC)"
	$(COMPOSE) logs -f --tail=100

shell: .env.local
	@echo "$(BLUE)Открытие shell в web контейнере...$(NC)"
	$(COMPOSE) exec web bash

# =============================================================================
# Django команды
# =============================================================================

migrate: .env.local
	@echo "$(BLUE)Запуск миграций БД...$(NC)"
	$(COMPOSE) exec web python manage.py migrate
	@echo "$(GREEN)Миграции применены$(NC)"

makemigrations: .env.local
	@echo "$(BLUE)Создание миграций...$(NC)"
	$(COMPOSE) exec web python manage.py makemigrations
	@echo "$(GREEN)Миграции созданы$(NC)"

collectstatic: .env.local
	@echo "$(BLUE)Сбор статических файлов...$(NC)"
	$(COMPOSE) exec web python manage.py collectstatic --noinput
	@echo "$(GREEN)Статические файлы собраны$(NC)"

seed: .env.local
	@echo "$(BLUE)Учебные записи...$(NC)"
	$(COMPOSE) exec web python manage.py seed_demo_data
	@echo "$(GREEN)Учебные записи готовы$(NC)"

# =============================================================================
# Дополнительные полезные команды
# =============================================================================

# Показать статус контейнеров
status: .env.local
	@echo "$(BLUE)Статус контейнеров:$(NC)"
	$(COMPOSE) ps

# Полная пересборка с нуля
rebuild: .env.local
	@echo "$(BLUE)Полная пересборка...$(NC)"
	$(COMPOSE) down -v
	$(COMPOSE) build --no-cache
	$(COMPOSE) up -d
	@echo "$(GREEN)Пересборка завершена$(NC)"

# Просмотр логов web контейнера
logs-web: .env.local
	$(COMPOSE) logs -f web

# Просмотр логов celery worker
logs-celery: .env.local
	$(COMPOSE) logs -f celery_worker

# Проверка зависимостей Python
check-deps:
	@echo "$(BLUE)Проверка зависимостей...$(NC)"
	.venv/bin/poetry show --outdated
