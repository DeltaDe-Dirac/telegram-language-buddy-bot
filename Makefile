.PHONY: test test-unit test-integration build-integration run-integration clean-integration

# Run all tests
test: test-unit test-integration

# Run unit tests
test-unit:
	python -m pytest tests/ -v --cov=src --cov-report=xml --cov-report=term -m "not integration"

# Run integration tests
test-integration: build-integration run-integration clean-integration

# Build integration test environment
build-integration:
	docker-compose -f docker-compose.test.yml build

# Run integration tests
run-integration:
	docker-compose -f docker-compose.test.yml --profile test up --abort-on-container-exit

# Clean up integration test environment
clean-integration:
	docker-compose -f docker-compose.test.yml down -v --remove-orphans

# Quick integration test run (no rebuild)
quick-integration:
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# View integration test logs
logs-integration:
	docker-compose -f docker-compose.test.yml logs

# Debug: Access running containers
debug-integration:
	docker-compose -f docker-compose.test.yml exec app bash

# Clean all Docker resources
clean-all:
	docker-compose -f docker-compose.test.yml down -v --remove-orphans --rmi all
	docker system prune -f
