# Student-Supervisor matching system

Based on [Scinet3](https://github.com/xiaohan2012/rl-search) system.

Contributors:
* [Gao Yuan](https://github.com/gaoyuankidult)
* [Arttu Modig](https://github.com/Dalar)
* [Kalle Ilves](https://github.com/Kaltsoon)

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


## More

For extracting keywords, NLTK software needs these packages:

* models/maxent_treebank_pos_tagger
* corpora/stopwords

Restore databases

```shell
sudo mysql -u root -p -e "CREATE DATABASE matching_system;"
sudo mysql -u root -p matching_system < database/matching_system.sql 
mongorestore database/dump
```

Run MongoDB daemon like this (default port should be correct):
`mongod --dbpath database/`


# New API

## GET /profile

### Response (JSON-format)

<pre>
{
   "user": "foo",
   "email": "foo.bar@foo.bar",
   "bio": "Hello world!",
   "files": [{"name": "file1.pdf,
              "title": "Title 1",
              ...},
             {"name": "file2.pdf,
              "title": "Title 2",
              ...},
              ...]
}
</pre>

# Index.html

## GET /search

### Response

<code>keywords : ["keyword", ...]</code>


## POST /search 

### Params

<code>{ search_keyword: "keyword", keywords: ["keyword", "keyword", ...] }</code>


### Response

<pre>{
	keywords: [
		{
			id: 1,
			text: "keyword",
			exploitation: 0.5,
			exploration: 0.3
		},
		...
	],
	persons: [
		{
			name: "Kalle Ilves",
			email: "N.Asokan[at]cs.helsinki.fi"
			room: "D212"
			phone: "+358 2941 51225"
			homepage: "http://cs.helsinki.fi/~asokan"
			reception_time: "By appointment"
			group: "Secure Systems"
			keywords: [1, 2, 3, ...],
			articles: [
				{
					id: 1,
					title: "Some title",
					abstract: "Some abstract",
					url: "www.myarticle.com"
				},
				...
			]
		},
		...
	]
}
</pre>

## POST/next

### Params

<pre>
{
	keywords: [
		{
			id: 1
			text: "keyword"
			weight: 0.2
		},
		...

	],
	
	// These are keywords (id of each removed keyword) removed by the user
	removed: [1, 2, 3]
}
</pre>

### Response

<pre>{
	keywords: [
		{
			id: 1,
			text: "keyword",
			exploitation: 0.5,
			exploration: 0.3
		},
		...
	],
	persons: [
		{
			name: "Kalle Ilves",
			email: "N.Asokan[at]cs.helsinki.fi"
			room: "D212"
			phone: "+358 2941 51225"
			homepage: "http://cs.helsinki.fi/~asokan"
			reception_time: "By appointment"
			group: "Secure Systems"
			profile_picture: "my_profile_image.jpg",
			keywords: [1, 2, 3, ...],
			articles: [
				{
					title: "Some title",
					abstract: "Some abstract",
					url: "www.myarticle.com"
				},
				...
			]
		},
		...
	]
}</pre>

## GET chart_data

{
	charts : [],
	articles: [
		{
			title: "title",
			id: 1
		},
		...
	]
}

## GET article_matrix

### Params

<pre>
{
	ids: [1, 2, 3, ...]
}
</pre>

### Response

## When more than 10 articles are selected 
<pre>
{
	matrix: 
	[
		[
			1,
			2,
			3
		]
	]
}
</pre>

## When less than 10 articlesare selected
<pre>
{
	matrix: 
	[
		[
			{
				value:1, 
				title: "",
				auther: "",
				abstract: ""
			} ...
		]
	]
	topic_model_relation:
	{
		articleID:topicID,
		...
	}
	topic_data:
	{
		topicID:
		[
			{ text: "keyword1", possibility: "possibility1" },
			...
		],
		...
	}
}
</pre>


## Post related_articles

### Params

<pre>
{
	id:1
}
</pre>

### Response

## When less than 10 articlesare selected
<pre>
{
	matrix: 
	[
		{
			distance:1, 
			title: "",
			auther: "",
			abstract: ""
		} ...
	]
}
</pre>
## Tasks for gao

- topic models data
- clean data for all authers
- formalize the preprocessing step

## Tasks

- <strike> merge deselete and select icon </strike> 
- <strike> chart bug when number of astracts are big than 20</strike>

- Chart data (persons and keyword counts + persons and keyword weights)
- <strike>A small bug lies in acquiring abstracts. The expand button is wrong</strike> *done*
