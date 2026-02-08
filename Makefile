.PHONY: build-base build-all up down logs clean

# Build the base image
build-base:
	docker build -t contentpulse-base:latest -f docker/Dockerfile.base .

# Build all service images (requires base image)
build-all: build-base
	docker-compose -f docker/docker-compose.yml build

# Start all services
up: build-base
	docker-compose -f docker/docker-compose.yml up -d

# Start with logs
up-logs: build-base
	docker-compose -f docker/docker-compose.yml up

# Stop all services
down:
	docker-compose -f docker/docker-compose.yml down

# View logs
logs:
	docker-compose -f docker/docker-compose.yml logs -f

# View logs for specific service
logs-%:
	docker-compose -f docker/docker-compose.yml logs -f $*

# Clean up volumes and images
clean:
	docker-compose -f docker/docker-compose.yml down -v
	docker rmi contentpulse-base:latest || true

# Rebuild everything from scratch
rebuild: clean build-all
