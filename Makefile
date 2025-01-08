.PHONY: migrate-new migrate-up migrate-down migrate-status migrate-history

migrate-init:
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini stamp head
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini upgrade head

migrate-new:
	@if [ "$(m)" = "" ]; then \
		echo "Please provide a migration message"; \
		echo "Usage: make migrate-new m='your migration message'"; \
		exit 1; \
	fi
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini revision --autogenerate -m "$(m)"

migrate-up:
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini upgrade head

migrate-down:
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini downgrade -1

migrate-status:
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini current

migrate-history:
	docker exec -it realestagent-web-1 alembic -c app/alembic.ini history