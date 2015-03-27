#!/usr/bin/env bash
# OLD VERSION
# install script for ubuntu(?)

sudo apt-get update
# password for mysql server
sudo apt-get install git-core python-virtualenv mongodb mysql-server libmysqlclient-dev libxml2-dev libxslt1-dev emma 
sudo apt-get install build-essential python-dev python-numpy python-setuptools python-scipy libatlas-dev libatlas3-base
sudo apt-get install python-dev libmysqlclient-dev
sudo apt-get install python-bcrypt
sudo apt-get install gfortran
sudo apt-get install libffi-dev
sudo pip install boto mysql
sudo dpkg -i database/robomongo-0.8.4-x86_64.deb
virtualenv venv/
source venv/bin/activate
# update language
pip install -r requirements.txt
sudo mysql -u root -p -e "CREATE DATABASE matching_system;"
sudo mysql -u root -p matching_system < database/matching_system.sql 
mongorestore database/dump
