#!/bin/bash

echo "🧪 Running tests..."
bash scripts/install.sh
python3 -m pytest judge/ --junit-xml=unit.xml -n 9

