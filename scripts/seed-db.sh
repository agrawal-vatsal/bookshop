#!/bin/bash

set -e

echo "==> Applying Alembic migrations..."
alembic upgrade head

echo "==> Beginning database seeding using extracted book data..."
python -m app.ingestion.seed

echo "==> Database seeding complete!"
