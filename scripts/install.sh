#!/bin/bash

bash scripts/cleanup.sh
echo "📦 Installing dependencies..."
pip install -q --disable-pip-version-check -r requirements.txt


