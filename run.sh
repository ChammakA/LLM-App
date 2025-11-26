#!/bin/bash
# One-command run for Flask app
export FLASK_APP=app.py
export FLASK_ENV=development
source venv/bin/activate
python app.py