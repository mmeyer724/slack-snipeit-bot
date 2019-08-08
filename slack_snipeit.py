#!/bin/python3
# slack-snipeit-bot

try:
    import logging
    import configparser
    import os
    import slack
    import json
    import requests
    import traceback
    import re
except Exception:
    logging.error("Exception occurred", exc_info=True)
    exit(1)


# Find settings.conf
logging.debug("Searching for settings.conf file.")
config = configparser.ConfigParser()
config.read("settings.conf")
if 'snipe-it' not in set(config):
    logging.error("No valid settings.conf was found in the current directory")
    raise SystemExit("No settings.conf file")

# Get variables from settings.conf:
slack_bot_token = config['slack']['api_token']
slack_bot_id = config['slack']['bot_id']
snipe_token = config['snipe-it']['api_token']
snipe_base_url = config['snipe-it']['base_url']
logging.debug(f"The configured SNIPE-IT base url is: {snipe_base_url}")
snipe_api_base_url = f"{snipe_base_url}api/v1/"

# Setup headers for making our request
headers = {
    'Authorization': f"Bearer {snipe_token}",
    'content-type': "application/json",
    'accept': "application/json"
    }


class SnipeLookups:
    """Returns data from SNIPE-IT"""

    def get_users_assets(self):
        snipe_api_user_url = f"{snipe_api_base_url}users"
        querystring = {"search":self,"limit":"1","sort":"username","order":"desc"}
        query = requests.request("GET", snipe_api_user_url, headers=headers, params=querystring)
        data = query.json()
        if query.status_code is not 200:
            logging.error(query.status_code)
        else:
            logging.debug(query.status_code)
            number_of_results = data['total']
            if number_of_results == 0:
                response = f"\nSorry, couldn't find anything for username `{self}`"
            else:
                logging.debug(query.status_code)
                try:
                    user_id = data['rows'][0]['id']
                    user_name = data['rows'][0]['name']
                    logging.debug(f"{user_name}, USERID: {user_id}")
                    snipe_api_assets_url = f"{snipe_api_base_url}users/{user_id}/assets"
                    query = requests.request("GET", snipe_api_assets_url, headers=headers)
                    data = query.json()
                    number_of_results = data['total']
                    response = f"\nReturned *{number_of_results}* results for {user_name}.\n"
                    for i in data['rows']:
                        snipe_asset_id = i['id']
                        asset_tag = i['asset_tag']
                        serial_number = i['serial']
                        model_name = i['model']['name']
                        link_to_snipe = f"{snipe_base_url}hardware/{snipe_asset_id}"
                        response += f"\n*Model:* {model_name}"
                        response += f"\n*Serial Number:* `{serial_number}`"
                        response += f"\n*Asset Tag:* `{asset_tag}`"
                        response += f"\n:link: _Link to asset:_ {link_to_snipe}"
                        response += f"\n:arrow_right: _Click here to checkin_ {link_to_snipe}/checkin\n\n"
                    return response
                except Exception:
                    logging.error("Exception occurred", exc_info=True)
        return response

    def get_asset_by_serial(self):
        snipe_api_hardwarebyserial_url = f"{snipe_api_base_url}hardware/byserial/{self}"
        query = requests.request("GET", snipe_api_hardwarebyserial_url, headers=headers)
        data = query.json()
        if query.status_code is not 200:
            logging.error(query.status_code)
        else:
            logging.debug(query.status_code)
            try:
                number_of_results = data['total']
                if number_of_results == 0:
                    response = f"\nSorry, couldn't find anything for serial number `{self}`"
                else:
                    for i in data['rows']:
                        snipe_asset_id = i['id']
                        asset_tag = i['asset_tag']
                        model_name = i['model']['name']
                        assigned_to_name = i['assigned_to']['name']
                        status_meta = i['status_label']['status_meta']
                        link_to_snipe = f"{snipe_base_url}hardware/{snipe_asset_id}"
                        response = f"\n*Model:* {model_name}"
                        response += f"\n*Asset Tag:* `{asset_tag}`"
                        if status_meta == "deployed":
                            response += f"\n*Status:* Checked out to `{assigned_to_name}` \n:link: _Link to asset:_ {link_to_snipe} \n:arrow_right: _Click here to checkin:_ {link_to_snipe}/checkin\n"
                        elif status_meta == "deployable":
                            response += f"\n*Status:* Deployable. \n:link: _Link to asset:_ {link_to_snipe} \n:arrow_right:_Click here to checkout: {link_to_snipe}/checkin\n"
            except Exception as i:
                logging.error("Exception occurred", exc_info=True)
        return response

    def get_asset_by_assettag(self):
        snipe_api_hardwarebyassettag_url = f"{snipe_api_base_url}hardware/bytag/{self}"
        query = requests.request("GET", snipe_api_hardwarebyassettag_url, headers=headers)
        data = query.json()
        if 'id' not in data:
            response = f"\nSorry, couldn't find anything for asset tag `{self}`."
        else:
            try:
                snipe_asset_id = data['id']
                model_name = data['model']['name']
                serial = data['serial']
                status_meta = data['status_label']['status_meta']
                assigned_to_name = data['assigned_to']['name']
                link_to_snipe = f"{snipe_base_url}hardware/{snipe_asset_id}"
                response = f"\n*Model:* {model_name}"
                response += f"\n*Serial Number:* `{serial}`"
                if status_meta == "deployed":
                    response += f"\n*Status:* Checked out to `{assigned_to_name}` \n:link: _Link to asset:_ {link_to_snipe} \n:arrow_right: _Click here to checkin:_ {link_to_snipe}/checkin\n\n"
                elif status_meta == "deployable":
                    response += f"\n*Status:* Deployable. \n:link: _Link to asset:_ {link_to_snipe} \n _Click here to checkout: {link_to_snipe}/checkin\n\n"                
            except Exception:
                logging.error("Exception occurred", exc_info=True)
        return response

MENTION_REGEX = "^<@(|[WU].+?)>(.*)" # parse @mention'ing
def parse_direct_mention(messsage_text):
    logging.debug(f'Feeding {messsage_text} to the parse_direct_mention function')
    if messsage_text is not None: # Prevent editing previously sent messages from causing script to crash
        matches = re.search(MENTION_REGEX, messsage_text) # the first returned group from the regex search contains the bot username, the second group contains the remaining message
        if matches:
            logging.debug(f"Matches group(1): {matches.group(1)}")
            logging.debug(f"Matches group(2).strip(): {matches.group(1)}")
            return (matches.group(1), matches.group(2).strip())
        else:
            return None,None
    else:
        logging.debug("No message text found in DM")
        return None,None


@slack.RTMClient.run_on(event='message')
def message(**payload):

    default_response = "_No 'user', 'serial' or 'asset' argument specified. Type '@snipe-it help' to learn how to use this bot._"

    help_response = "*Usage:*\n\
        *user*          _username (ex. jcuriano)_                      -- print asset information for a user\n\
        *serial*        _serial number (ex. C02XXXXXXXXX)_  -- print asset information about a serial\n\
        *asset*         _asset tag (ex. 010101)_                      -- print information about an asset tag"
    data = payload['data']
    web_client = payload["web_client"]
    channel_id = data.get("channel")
    messsage_text = data.get("text")
    mentioned_id, message = parse_direct_mention(messsage_text)
    if mentioned_id == f"{slack_bot_id}": # only reply if the snipe-it bot user is @ mentioned.
        response = None
        message = message.lower()
        logging.debug(f"Message: {message}")
        if message.startswith("help"):
            response = help_response
        elif message.startswith("user"):
            message = message.split()
            username = message[1]
            response = SnipeLookups.get_users_assets(username)
        elif message.startswith("serial"):
            try:
                message = message.split()
                serial = message[1]
            except Exception as i:
                response = f"ERROR: {i}, please provide a serial."
            if serial:
                response = SnipeLookups.get_asset_by_serial(serial)
        elif message.startswith("asset"):
            try:
                message = message.split()
                assettag = message[1]
                response = SnipeLookups.get_asset_by_assettag(assettag)
            except Exception as i:
                response = f"ERROR: {i}, please provide an asset tag."
            if assettag:
                response = SnipeLookups.get_asset_by_assettag(assettag)

        #Post the response back to Slack
        web_client.chat_postMessage(
        channel = channel_id,
        text=response or default_response
        )
    else:
        logging.debug("Nothing to do")

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    rtm_client = slack.RTMClient(token=slack_bot_token)
    rtm_client.start()