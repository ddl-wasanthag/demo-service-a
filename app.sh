#!/bin/bash
# Install service dependencies at startup.
# The base Domino environment has Python but not fastapi/uvicorn.
pip install -r requirements.txt -q
python app.py
