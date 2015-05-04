#!/bin/bash

git pull
source venv/bin/activate

sudo service mongodb start
cd src
python app.py
