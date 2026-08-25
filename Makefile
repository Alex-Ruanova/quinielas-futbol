# Quinielas de Fútbol — desarrollo local y despliegue
#
# Despliegue completo desde cero:
#   make infra          terraform apply (crea RDS, ECR, Fargate, tunel, bucket)
#   make deploy         imagen -> ECR -> ECS, y frontend -> S3
#   make seed-prod      temporada de demo en la RDS de produccion
#   make admin-prod EMAIL=tu@correo.com
#
# Y para tirarlo:
#   make destroy

SHELL         := /bin/bash
REGION        ?= us-east-1
PROJECT       ?= quinielas
APP_HOST      ?= nexutest.norvaru.com
API_URL       ?= https://nexutest-api.norvaru.com
LOCAL_DB      ?= postgresql+psycopg://quinielas:quinielas@localhost:5432/quinielas

# `uv` ignora el venv de la raiz si VIRTUAL_ENV apunta a otro sitio.
UV := cd backend && unset VIRTUAL_ENV &&

.PHONY: help up down backend web seed admin test check \
        infra deploy deploy-backend deploy-web seed-prod admin-prod logs destroy

help: ## Muestra esta ayuda
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "};{printf "  \033[1m%-16s\033[0m %s\n",$$1,$$2}'

# ─── Local ────────────────────────────────────────────────────────────────────

up: ## Levanta PostgreSQL y aplica las migraciones
	docker compose up -d db
	@until docker compose exec -T db pg_isready -U quinielas >/dev/null 2>&1; do sleep 1; done
	$(UV) DATABASE_URL=$(LOCAL_DB) uv run alembic upgrade head

down: ## Detiene PostgreSQL
	docker compose down

backend: ## Corre el backend en :8000
	$(UV) DATABASE_URL=$(LOCAL_DB) CORS_ORIGIN=http://localhost:5173 \
		uv run uvicorn app.main:app --reload --port 8000

web: ## Corre el frontend en :5173
	cd web && npm run dev -- --port 5173 --strictPort

seed: ## Siembra la temporada de demo en local
	$(UV) DATABASE_URL=$(LOCAL_DB) uv run python scripts/seed_demo.py

admin: ## Promueve una cuenta a admin (make admin EMAIL=tu@correo.com)
	@test -n "$(EMAIL)" || { echo "Falta EMAIL=..."; exit 1; }
	$(UV) DATABASE_URL=$(LOCAL_DB) uv run python scripts/create_admin.py $(EMAIL)

test: ## Suite del backend
	$(UV) DATABASE_URL=$(LOCAL_DB) uv run pytest tests/ -v

check: ## Tipado, lint y tipos del frontend
	$(UV) uv run mypy --strict app
	$(UV) uv run ruff check app tests
	cd web && npm run check

# ─── Despliegue ───────────────────────────────────────────────────────────────

infra: ## terraform apply (pide confirmacion)
	cd infra && terraform init -input=false && terraform apply

deploy: deploy-backend deploy-web ## Publica backend y frontend
	@echo
	@echo "  App:  https://$(APP_HOST)"
	@echo "  API:  $(API_URL)"

deploy-backend: ## Imagen -> ECR -> redespliegue de ECS
	$(eval ECR := $(shell cd infra && terraform output -raw ecr_repository))
	$(eval REG := $(shell echo $(ECR) | cut -d/ -f1))
	aws ecr get-login-password --region $(REGION) | docker login --username AWS --password-stdin $(REG)
	docker build --platform linux/amd64 -f backend/Dockerfile -t $(ECR):latest backend/
	docker push $(ECR):latest
	aws ecs update-service --cluster $(PROJECT) --service backend \
		--force-new-deployment --region $(REGION) --no-cli-pager >/dev/null
	@echo "Redespliegue lanzado. Sigue el progreso con: make logs"

deploy-web: ## Build del frontend -> S3
	cd web && PUBLIC_API_URL=$(API_URL) npm run build
	aws s3 sync web/build/ s3://$(APP_HOST)/ --delete --region $(REGION)

# Los scripts corren en local contra la RDS, que no es publica. Se resuelve
# ejecutandolos dentro de un task de ECS, que si esta en la VPC. Para el MVP
# basta con abrir temporalmente el acceso; ver docs/deploy.md.
seed-prod: ## Siembra la temporada de demo en produccion
	$(eval SECRET := $(shell cd infra && terraform output -raw database_url_secret))
	$(UV) DATABASE_URL="$$(aws secretsmanager get-secret-value --secret-id $(SECRET) \
		--query SecretString --output text --region $(REGION))" \
		uv run python scripts/seed_demo.py

admin-prod: ## Promueve una cuenta a admin en produccion (EMAIL=...)
	@test -n "$(EMAIL)" || { echo "Falta EMAIL=..."; exit 1; }
	$(eval SECRET := $(shell cd infra && terraform output -raw database_url_secret))
	$(UV) DATABASE_URL="$$(aws secretsmanager get-secret-value --secret-id $(SECRET) \
		--query SecretString --output text --region $(REGION))" \
		uv run python scripts/create_admin.py $(EMAIL)

logs: ## Logs del backend en CloudWatch
	aws logs tail /ecs/$(PROJECT)-backend --follow --region $(REGION)

destroy: ## Destruye toda la infraestructura
	cd infra && terraform destroy
