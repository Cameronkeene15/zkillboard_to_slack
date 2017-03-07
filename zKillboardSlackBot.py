import requests
import json
import pprint
import csv
import configparser
import sys
import os

# for fixLazyJson
import tokenize
import token
from io import *

# Used so that the Config.ini and recent_kill_list.csv are always in the same location as the script
script_directory = os.path.dirname(os.path.realpath(__file__))
config_file_path = os.path.join(script_directory, 'Config.ini')


def main():
    config = ConfigHandler()                                                # sets up a config object
    killmail = True

    while(killmail != None):
        response = requests.get('https://redisq.zkillboard.com/listen.php')     # gets a killmail from zkillboard
        response.encoding = 'utf-8'                                             # sets encoding to UTF-8
        json_data = response.json()                                             # gets the json data in the response

        killmail = json_data['package']

        kill = KillMail(killmail)

        slack_message = SlackMessage(kill, config)
        encoded_slack_message = slack_message.encode_slack_message()
        requests.post(config.get_slack_web_hook(), data=encoded_slack_message)




class KillMail:
    def __init__(self, json_kill_mail):
        self.json_kill_mail = json_kill_mail

    def get_kill_id(self):
        return self.json_kill_mail['killID']

    def get_kill_time(self):
        return self.json_kill_mail['killTime']

    def get_moon_id(self):
        return self.json_kill_mail['moonID']

    def get_position(self):
        return self.json_kill_mail['position']

    def get_solar_system_id(self):
        return self.json_kill_mail['solarSystemID']

    def get_victim_alliance_id(self):
        return self.json_kill_mail['victim']['allianceID']

    def get_victim_alliance_name(self):
        return self.json_kill_mail['victim']['allianceName']

    def get_victim_character_id(self):
        return self.json_kill_mail['victim']['characterID']

    def get_victim_character_name(self):
        return self.json_kill_mail['victim']['characterName']

    def get_victim_corporation_id(self):
        return self.json_kill_mail['victim']['corporationID']

    def get_victim_corporation_name(self):
        return self.json_kill_mail['victim']['corporationName']

    def get_damage_taken(self):
        return self.json_kill_mail['victim']['damageTaken']

    def get_faction_id(self):
        return self.json_kill_mail['victim']['factionID']

    def get_faction_name(self):
        return self.json_kill_mail['victim']['factionName']

    def get_ship_id(self):
        return self.json_kill_mail['victim']['shipTypeID']

    def get_zkb_hash(self):
        return self.json_kill_mail['zkb']['hash']

    def get_number_involved(self):
        return self.json_kill_mail['zkb']['involved']

    def get_location_id(self):
        return self.json_kill_mail['zkb']['locationID']

    def get_points(self):
        return self.json_kill_mail['zkb']['points']

    def get_kill_value(self):
        return self.json_kill_mail['zkb']['totalValue']

    def get_ship_name(self):
        try:
            cvs_file = csv.reader(codecs.open(type_id_path, 'r', encoding='utf-8'))
            for row in cvs_file:
                if row[0] == str(self.json_kill_mail['victim']['shipTypeID']):
                    return row[1]
            else:
                return 'Item Name Unknown'
        except:
            print('Error Getting Ship Type')


class SlackMessage:
    def __init__(self, kill, web_handler, config):
        self.kill = kill
        self.web_handler = web_handler
        self.config = config

    def get_message_color(self):
        if self.config.get_alliance_id() == self.kill.get_victim_alliance_id() or self.config.get_corporation_id() == self.kill.get_victim_corporation_id():
            color = self.config.get_slack_loss_color()
        else:
            color = self.config.get_slack_kill_color()
        return color

    def get_message_icon_emoji(self):
        if self.config.get_alliance_id() == self.kill.get_victim_alliance_id() or self.config.get_corporation_id() == self.kill.get_victim_corporation_id():
            icon_emoji = self.config.get_slack_loss_emoji()
        else:
            icon_emoji = self.config.get_slack_kill_emoji()
        return icon_emoji

    def get_message_user_name(self):
        if self.config.get_alliance_id() == self.kill.get_victim_alliance_id() or self.config.get_corporation_id() == self.kill.get_victim_corporation_id():
            user_name = self.config.get_slack_loss_username()
        else:
            user_name = self.config.get_slack_kill_username()
        return user_name

    # Old format, decided to use V2 instead because it takes up less space and fields does not repeat the title.
    def generate_slack_message(self):
        slack_message = {
            "username": self.get_message_user_name(),
            "attachments": [
                {
                    "title": self.web_handler.get_description(),
                    "title_link": self.get_kill_link(),
                    "color": self.get_message_color(),
                    "fields": [
                        {
                            "title": "Date",
                            "value": self.kill.get_kill_time(),
                            "short": True

                        },
                        {
                            "title": "Ship Name",
                            "value": self.kill.get_ship_name(),
                            "short": True
                        },
                        {
                            "title": "Pilot Name",
                            "value": self.kill.get_victim_character_name(),
                            "short": True
                        },
                        {
                            "title": "Corporation Name",
                            "value": self.kill.get_victim_corporation_name(),
                            "short": True
                        },
                        {
                            "title": "Total Value",
                            "value": ('{:,.2f}'.format(self.kill.get_kill_value()) + ' ISK'),
                            "short": False
                        }
                    ],
                    "thumb_url": self.web_handler.get_image_url(),
                }
            ],
            "icon_emoji": self.get_message_icon_emoji()
        }
        return slack_message

# Took out repetitive info so now just descriptive title with link to kill and total value are shown.
# Makes the killmails posted in slack much more compact and easier to view.
    def generate_slack_message_v2(self):
        slack_message = {
            "username": self.get_message_user_name(),
            "attachments": [
                {
                    "title": self.web_handler.get_description(),
                    "title_link": self.get_kill_link(),
                    "color": self.get_message_color(),
                    "fields": [
                        {
                            "title": "Total Value",
                            "value": ('{:,.2f}'.format(self.kill.get_kill_value()) + ' ISK'),
                            "short": False
                        }
                    ],
                    "thumb_url": self.web_handler.get_image_url(),
                    "fallback": "New Killmail!",
                }
            ],
            "icon_emoji": self.get_message_icon_emoji()
        }
        return slack_message

    def encode_slack_message(self):
        encoded_message = json.dumps(self.generate_slack_message_v2()).encode('utf-8')
        return encoded_message


class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.read_config_file()

    def generate_config_file(self):
        self.config.add_section('General Settings')
        self.config.set('General Settings', 'alliance_id', '')
        self.config.set('General Settings', 'corporation_id', '')

        self.config.add_section('Slack Settings')
        self.config.set('Slack Settings', 'slack_web_hook', 'https://hooks.slack.com/services/')
        self.config.set('Slack Settings', 'kill_username', 'Kill')
        self.config.set('Slack Settings', 'kill_emoji', ':sunglasses:')
        self.config.set('Slack Settings', 'kill_color', '#36a64f')
        self.config.set('Slack Settings', 'loss_username', 'Loss')
        self.config.set('Slack Settings', 'loss_emoji', ':skull_and_crossbones:')
        self.config.set('Slack Settings', 'loss_color', '#ff0000')
        try:
            with open(config_file_path, 'w') as config_file:
                self.config.write(config_file)
        except:
            print('Error Generating Config File!')

    def read_config_file(self):
        try:
            with open(config_file_path) as config_file:
                self.config.read_file(config_file)
        except FileNotFoundError:
            print('Could Not Find Config File\nGenerating Config File Now')
            self.generate_config_file()
            print('Config File Now Available! Go Configure It!')
            sys.exit()
        except:
            print('Error Reading Config File!')

    def get_alliance_id(self):
        try:
            return int(self.config.get('General Settings', 'alliance_id'))
        except:
            return 0

    def get_corporation_id(self):
        try:
            return int(self.config.get('General Settings', 'corporation_id'))
        except:
            return 0

    def get_slack_web_hook(self):
        try:
            return self.config.get('Slack Settings', 'slack_web_hook')
        except:
            print('Error Getting slack_web_hook From Config.ini')
            sys.exit()

    def get_slack_kill_username(self):
        try:
            return self.config.get('Slack Settings', 'kill_username')
        except:
            print('Error Getting kill_username From Config.ini')
            sys.exit()

    def get_slack_kill_emoji(self):
        try:
            return self.config.get('Slack Settings', 'kill_emoji')
        except:
            print('Error Getting kill_emoji From Config.ini')
            sys.exit()

    def get_slack_kill_color(self):
        try:
            return self.config.get('Slack Settings', 'kill_color')
        except:
            print('Error Getting kill_color From Config.ini')
            sys.exit()

    def get_slack_loss_username(self):
        try:
            return self.config.get('Slack Settings', 'loss_username')
        except:
            print('Error Getting loss_username From Config.ini')
            sys.exit()

    def get_slack_loss_emoji(self):
        try:
            return self.config.get('Slack Settings', 'loss_emoji')
        except:
            print('Error Getting loss_emoji From Config.ini')
            sys.exit()

    def get_slack_loss_color(self):
        try:
            return self.config.get('Slack Settings', 'loss_color')
        except:
            print('Error Getting loss_color From Config.ini')


main()
