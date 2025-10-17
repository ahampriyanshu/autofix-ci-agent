#!/bin/bash

bash scripts/install.sh
echo "🧪 Running tests..."
python3 -m pytest judge/ --junit-xml=unit.xml -n 9

