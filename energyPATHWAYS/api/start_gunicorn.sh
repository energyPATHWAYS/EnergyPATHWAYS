#!/usr/bin/env bash
sudo gunicorn -c gunicorn_config.py api:app
