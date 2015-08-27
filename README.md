# Student-Supervisor matching system

Based on [Scinet3](https://github.com/xiaohan2012/rl-search) system.

Contributors:
* [Gao Yuan](https://github.com/gaoyuankidult)
* [Arttu Modig](https://github.com/Dalar)
* [Kalle Ilves](https://github.com/Kaltsoon)
* [Kaj Sotala](https://github.com/ksotala)

# Installing

## Linux (Ubuntu)

grab current installation

`git clone https://github.com/Dalar/Matching-System.git`

`sudo apt-get update`

I think most of these were already installed but just in case
```
sudo apt-get install python-virtualenv mongodb mysql-server python-dev
sudo apt-get install python-scipy
sudo apt-get install -y nodejs
```

if the following line doesn't work, then try doing `sudo apt-get install npm` first
(npm should have come with node.js but I think it didn't for me)

`sudo npm install npm -g`

`npm config set prefix '~/.npm-packages'`

open:

`sudo pico ~/.bashrc`

append the following line to bashrc, then save and close:

`export PATH="$PATH:$HOME/.npm-packages/bin"`

back on the command line `source ~/.bashrc`

```
npm install -g bower
npm install -g grunt-cli
```

now navigate to the root of the git project you cloned, if you're not
there already

`cd Matching-System`

at some point one of the installers might ask you whether to use a
library that angular needs or a library that Matching-Project needs,
I chose to use the one that M-P needs and it seemed to work okay

```
virtualenv venv/
source venv/bin/activate
pip install -r requirements.txt
```

```
npm install
bower install
```

## Mac OSX (tested on 10.9)

First, install [Homebrew](http://brew.sh/) package manager, and check that it works:

```shell
brew update
brew doctor
```

Python 2 is recommended to be installed through Homebrew:

`brew install python2`

Remember to use [virtual environments](http://docs.python-guide.org/en/latest/dev/virtualenvs/) on Python.

`pip install virtualenv`

Use pip only inside virtualenv afterwards!

HINT: It's good practise to make a shell command "syspip" or "gpip" for global pip installs, see e.g.:
http://hackercodex.com/guide/python-development-environment-on-mac-osx/

for more virtualenv power:
http://www.marinamele.com/2014/05/install-python-virtualenv-virtualenvwrapper-mavericks.html

`pip install virtualenvwrapper`

Get on installing:

```shell
brew install mongodb
brew install mysql
brew install numpy
brew install scipy
brew install node  # node.js
```

Install web framework:

```shell
npm install -g bower
npm install -g grunt-cli
```

Navigate to the root of the git project you cloned, if you're not
there already

`cd Matching-System`

Install web framework components:

```shell
npm install
bower install
```

Activate your Python virtualenv and then install Python requirement:

`pip install -r requirements.txt`

OK, then you should have a basic installation!

# Usage

Run the run-server.sh script, then point your browser to localhost:8899.

# Updating the data

People's publication records are based on BibTeX files downloaded from http://dblp.uni-trier.de/ . To add a new person or update a previous one:
* Add the new/updated .bib file to bibtex\_processing/bibtex_source
* Run bibtex\_processing/process_bibtex.sh
* If you added new people, go add their details into docs/people/people.txt - the system will ignore them until they can be found from this file

If you wish to generate new topic models with different parameters, look at the conditional code block in process_bibtex.sh as well as http://mallet.cs.umass.edu/ in order to figure out how.

# Known issues

* Sometimes the list of topics in the recommender system comes out looking weird/unreadable. Just generate a new set of topics (by clicking next or starting a new search).
* You can access a profile page that's a remnant of the old system, but doesn't actually do anything.

# Backend notes

* A bunch of the code in app.py is inherited from the old system, which was keyword-based rather than topic-based. As a result, some variable names that talk about keywords actually refer to topics. This can be a little confusing.
* The main files used by the backend are app.py, extractors.py, analyzer.py, and newHandlers.py. 
