.PHONY: up down logs ps build clean

# Start all services
up:
	docker-compose up -d --build

# Stop all services
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-api:
	docker-compose logs -f api

logs-temporal:
	docker-compose logs -f temporal

logs-router:
	docker-compose logs -f event-router

# List running containers
ps:
	docker-compose ps

# Build images without starting
build:
	docker-compose build

# Clean up volumes and images
clean:
	docker-compose down -v --rmi local

# Database shell
db-shell:
	docker-compose exec db psql -U postgres -d minicloud

# MinIO client
minio-shell:
	docker-compose exec minio sh

# Restart a specific service
restart-%:
	docker-compose restart $*

# Scale workers
scale-workers:
	docker-compose up -d --scale temporal-worker=3

# Run tests
test:
	docker-compose exec api pytest

# Show API docs URL
docs:
	@echo "API Docs: http://localhost:8000/docs"
	@echo "MinIO Console: http://localhost:9001"
	@echo "Temporal UI: http://localhost:8080"
	@echo "Airflow: http://localhost:8081"
	@echo "Grafana: http://localhost:3001"
	@echo "Prometheus: http://localhost:9090"
