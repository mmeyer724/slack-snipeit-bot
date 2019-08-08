#Slack SNIPE-IT Bot
## Slack bot that allows users to query data from IT asset inventory system

```
## Overview:
This Slack bot uses v2 of the Python slackclient to interface with the Slack RTM API to respond to user messages about IT assets, right in Slack! Useful for quickly querying the state of IT assets while on the go. Comprehensive documentation on using the Slack Python can be found at https://slack.dev/python-slackclient/

## Requirements:
This app specifies required libraries in the requirements.txt file. Create a new Python virtualenv and import using `pip install -r requirements.txt`. You'll need network access to your Snipe-IT instance, along with an API key generated from a Snipe-IT user that has user and asset read access. For slack, you'll need to create a new Slack App on api.slack.com, and create a bot user to obtain a Slack API token.

## Installation:
Copy the files to your system (/opt/slack-snipeit-bot/*). Fill out settings.conf with your Slack API token and bot ID, along with Snipe-IT base URL and API token. The script will look for a valid settings.conf in the same directory folder.

## Deploying with Docker:
Alternatively, you can build and deploy this bot as a docker image, with the included Dockerfile. Run `docker-compose build && docker-compose up`. Or, push the built image to the container registry of your choice to run on any infrastructure that can handle a Docker container.