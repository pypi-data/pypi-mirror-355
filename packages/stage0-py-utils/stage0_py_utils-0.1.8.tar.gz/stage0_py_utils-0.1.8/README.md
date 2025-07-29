# stage0_py_utils

This repo publishes the a pypl module that contains utility code used throughout the stage0 system. See the [server.py](./stage0_py_utils/server.py) for an example of how to use this code. See the [ECHO](./ECHO.md) documentation for information on how the [Stage0 Echo Bot](https://github.com/agile-learning-institute/stage0/blob/main/ECHO.md) is implemented. 

# Contributing

## Prerequisites

- [Stage0 Developer Edition]() #TODO for now just Docker
- [Python 3.12](https://www.python.org/downloads/)
- [Pipenv](https://pipenv.pypa.io/en/latest/installation.html)

## Optional

- [Mongo Compass](https://www.mongodb.com/try/download/compass) - if you want a way to look into the database

## Folder structure for source code

```text
📁 stage0_py_utils/                 # Repo root
│── 📁 stage0_py_utils/
│   │── 📁 agents/                 # Echo Agents (Bot, Conversation, Echo)
│   │── 📁 config/                 # System Wide configuration
│   │── 📁 echo/                   # Echo Chat AI Framework
│   │── 📁 echo_utils/             # Echo related utilities
│   │── 📁 flask_utils/            # Flask related utilities
│   │── 📁 mongo_utils/            # MongoDB Utilities
│   │── 📁 evaluator/              # Echo evaluation utility
│   │── 📁 routes/                 # Echo Flask Routes
│   │── 📁 services/               # Echo Persistence Services (Bot, Conversation)
│   
│── 📁 tests/                      # unittest code structure matches source
│   │── 📁 agents/                       
│   │── 📁 config/                 
│   │── 📁 echo/                   
│   │── ....
│   │── 📁 test_data/              # Testing Data
│   │   │── 📁 config/               # Config file testing data
│   │   │── 📁 evaluate/             # Echo Evaluate test data
│   
│── README.md
│── ...
```
---

# Pipenv Commands
We use pipenv automation to manage dependencies and automate common tasks. Note that running the sample server will use the
configuration values (Tokens, ID's, Port, etc.) from the FRAN bot. You can not run the sample server if the FRAN bot is already running. 

## Install Dependencies
```bash
pipenv install
```

## Clean any previous build output
```bash
pipenv run clean
```

## Build the Package
```bash
pipenv run build
```

## Check the Package is ready for publication
```bash
pipenv run check
```

## Publish the Package
```bash
pipenv run publish
```
NOTE: You should not need to use this, publishing is handled by GitHub Actions CI

## Run sample server locally
```bash
pipenv run local
```

## Run sample server locally with DEBUG logging
```bash
pipenv run debug
```

## Run stepCI testing of Flask API endpoints
```bash
pipenv run stepci
```
NOTE: This assumes that the server is running at localhost:8580. Use ``pipenv run local`` to start the server if needed

