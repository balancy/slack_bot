# Makefile

# Define a default target
.DEFAULT_GOAL := help

# Help target to list available commands
help:
	@echo "Available commands:"
	@echo "make launch   - Build and start the containers in detached mode"
	@echo "make stop     - Stop the running containers"
	@echo "make down     - Stop and remove the containers"

# Target to build and start the containers in detached mode
launch:
	@echo "Building and starting containers..."
	docker-compose up -d --build

# Target to stop the running containers
stop:
	@echo "Stopping containers..."
	docker-compose stop

# Target to stop and remove the containers
down:
	@echo "Stopping and removing containers..."
	docker-compose down
