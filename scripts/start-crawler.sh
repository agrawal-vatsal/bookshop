#!/bin/bash

set -e

echo "==> Starting the Bookshop async crawler..."

# Optionally activate your virtualenv here:
# source venv/bin/activate

python -m app.ingestion.crawler

echo "==> Crawler finished. Raw HTML files saved in data/raw_html/"
