#!/bin/bash
python -m flask db upgrade
gunicorn --config gunicorn.conf.py app:app