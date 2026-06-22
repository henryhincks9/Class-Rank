PY=python
DOCKER_IMAGE=class-rank

.PHONY: help build up down logs shell test lint

help:
	@echo "make build     - Build Docker image"
	@echo "make up        - Start services with docker-compose"
	@echo "make down      - Stop services"
	@echo "make logs      - Show web service logs"
	@echo "make shell     - Open shell in web container"
	@echo "make test      - Run quick syntax check"

build:
	docker build -t $(DOCKER_IMAGE) .

up:
	docker-compose up --build -d

down:
	docker-compose down

logs:
	docker-compose logs -f web

shell:
	docker run --rm -it -v $(PWD):/app -w /app $(DOCKER_IMAGE) /bin/bash

test:
	$(PY) -m py_compile server.py

lint:
	@echo "No linter configured; consider adding flake8 or pylint"
