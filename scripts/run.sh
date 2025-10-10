#!/bin/bash

bash scripts/install.sh
echo "🚀 Starting the app..."
streamlit run app.py --server.port 8000

