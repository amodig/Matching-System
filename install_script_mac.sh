#!/usr/bin/env bash
# install script for OS X (10.9)

# How to install Homebrew:
# ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

brew update

# Make sure you have Homebrew Python installed and a working virtualenv

# brew install python  # install Python 2.7.x
# pip install virtualenv  # Use pip only inside virtualenv afterwards!

# HINT: It's good practise to make a shell command "syspip" or "gpip" for global pip installs,
# see e.g.: http://hackercodex.com/guide/python-development-environment-on-mac-osx/

# for more virtualenv power:
# http://www.marinamele.com/2014/05/install-python-virtualenv-virtualenvwrapper-mavericks.html
# pip install virtualenvwrapper

brew install mongodb
brew install mysql
brew install numpy
brew install scipy

# Activate your Python virtualenv and install requirement:
# pip install -r requirements.txt

# NLTK needs these packages:
# models/maxent_treebank_pos_tagger
# corpora/stopwords

# Restore databases
sudo mysql -u root -p -e "CREATE DATABASE matching_system;"
sudo mysql -u root -p matching_system < database/matching_system.sql 
mongorestore database/dump

# Run MongoDB daemon like this (default port should be correct):
# mongod --dbpath database/