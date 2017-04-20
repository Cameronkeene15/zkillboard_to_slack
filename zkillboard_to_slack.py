#!/usr/bin/env python3

import requests
import json
import configparser
import sys
import os
import re
import pprint

# Used so that the Config.ini and recent_kill_list.csv are always in the same location as the script
script_directory = os.path.dirname(os.path.realpath(__file__))
config_file_path = os.path.join(script_directory, 'config.ini')


def main():
    config = ConfigHandler()                            # sets up a config object
    killmail_status = 0
    url = 'https://redisq.zkillboard.com/listen.php'
    queue_id = config.get_queue_id()
    if queue_id:
        url = url + '?queueID=' + queue_id
    response = requests.get(url)
    response.encoding = 'utf-8'
    json_data = response.json()
    killmail = json_data['package']

    while killmail is not None:
        kill = KillMail(killmail)

        for attacker in kill.get_attackers_info():
            try:
                if attacker['corporation']['id'] == config.get_corporation_id():
                    killmail_status = 1
                    #print('set killstatus to 1')
            except:
                print('', end='')

        try:
            if kill.get_victim_corporation_id() == config.get_corporation_id():
                #print('set killstatus to 2')
                killmail_status = 2
        except:
            print('', end='')
        #print('killmail status: ' + str(killmail_status))
        if killmail_status > 0:
            slack_message = SlackMessage(kill, config)
            encoded_slack_message = slack_message.encode_slack_message()
            requests.post(config.get_slack_web_hook(), data=encoded_slack_message)

            print('posted killmail: ' + str(kill.get_killmail_id()))
            killmail_status = 0

        response = requests.get(url)
        json_data = response.json()                                             # gets the json data in the response
        killmail = json_data['package']


# Class KillMail allows for easy reading of the json data that is returned from the request.
class KillMail:
    def __init__(self, json_kill_mail):
        self.json_kill_mail = json_kill_mail
        self.final_blow_attacker = self.get_final_blow_info()
        self.top_damage_attacker = self.get_top_damage_info()

    def get_killmail_id(self):
        return self.json_kill_mail['killID']

    def get_attacker_count(self):
        return self.json_kill_mail['killmail']['attackerCount']

    def get_attackers_info(self):
        return self.json_kill_mail['killmail']['attackers']

    def get_final_blow_info(self):
        for attacker in self.get_attackers_info():
            if attacker['finalBlow']:
                return attacker

    def get_final_blow_name(self):
        try:
            if 'character' in self.final_blow_attacker:
                return self.final_blow_attacker['character']['name']
            elif 'corporation' in self.final_blow_attacker:
                return self.final_blow_attacker['corporation']['name']
            elif 'faction' in self.final_blow_attacker:
                return self.final_blow_attacker['faction']['name']
            else:
                print('\n\nFinal Blow name Error: \n')
                pprint.pprint(self.json_kill_mail)
                print()
                return '$No Name$'
        except:
            print('\n\nFinal Blow name Error: \n')
            pprint.pprint(self.json_kill_mail)
            print()
            return '$No Name$'


    def get_top_damage_info(self):
        top_damage = 0
        top_damage_info = None
        try:
            for attacker in self.get_attackers_info():
                if top_damage < attacker['damageDone']:
                    top_damage = attacker['damageDone']
                    top_damage_info = attacker
            return top_damage_info
        except:
            print('\n\nTop Damage info Error: \n')
            pprint.pprint(self.json_kill_mail)
            print()
            return top_damage_info

    def get_top_damage_name(self):
        try:

            if 'character' in self.top_damage_attacker:
                return self.top_damage_attacker['character']['name']
            elif 'faction' in self.top_damage_attacker:
                return self.top_damage_attacker['faction']['name']
            elif 'corporation' in self.top_damage_attacker:
                return self.top_damage_attacker['corporation']['name']
            else:
                print("\n\nTop damage name Error: \n")
                pprint.pprint(self.json_kill_mail)
                print()
                return '$No Name$'
        except:
            print("\n\nTop damage name Error: \n")
            pprint.pprint(self.json_kill_mail)
            print()
            return '$No Name$'

    def get_kill_time(self):
        return self.json_kill_mail['killmail']['killTime']

    def get_solar_system_name(self):
        return self.json_kill_mail['killmail']['solarSystem']['name']

    def get_victim_character_id(self):
        return self.json_kill_mail['killmail']['victim']['character']['id']

    def get_victim_character_name(self):
        try:
            if 'character' in self.json_kill_mail['killmail']['victim']:
                return self.json_kill_mail['killmail']['victim']['character']['name']
            elif 'corporation' in self.json_kill_mail['killmail']['victim']:
                return self.json_kill_mail['killmail']['victim']['corporation']['name']
            elif 'alliance' in self.json_kill_mail['killmail']['victim']:
                return self.json_kill_mail['killmail']['victim']['alliance']['name']
            else:
                print('\n\nKillamil data with no victim char name error : \n')
                pprint.pprint(self.json_kill_mail())
                print()
                return '$No Name$'
        except:
            print('\n\nKillamil data with no victim char name error : \n')
            pprint.pprint(self.json_kill_mail())
            print()
            return '$No Name$'

    def get_victim_alliance_id(self):
        return self.json_kill_mail['killmail']['victim']['alliance']['id']

    def get_victim_alliance_name(self):
        return self.json_kill_mail['killmail']['victim']['alliance']['name']

    def get_victim_corporation_id(self):
        return self.json_kill_mail['killmail']['victim']['corporation']['id']

    def get_victim_corporation_name(self):
        return self.json_kill_mail['killmail']['victim']['corporation']['name']

    def get_victim_damage_taken(self):
        return self.json_kill_mail['killmail']['victim']['damageTaken']

    def get_victim_ship_icon(self):
        icon_url = self.json_kill_mail['killmail']['victim']['shipType']['icon']['href']
        fixed_url = re.sub(r'Type', 'Render', icon_url)
        return fixed_url

    def get_victim_ship_name(self):
        return self.json_kill_mail['killmail']['victim']['shipType']['name']

    def get_killmail_value(self):
        return self.json_kill_mail['zkb']['totalValue']


# Class SlackMessage handles putting all the necessary information into the formatted slack message per killmail.
class SlackMessage:
    def __init__(self, kill, config):
        self.kill = kill
        self.config = config

    def determine_if_kill(self):
        is_kill = None
        for attacker in self.kill.get_attackers_info():
            if attacker['corporation']['id'] == self.config.get_corporation_id():
                is_kill = True
        if self.config.get_corporation_id() == self.kill.get_victim_corporation_id:
            is_kill = False
        return is_kill

    def get_message_color(self):
        if self.config.get_corporation_id() == self.kill.get_victim_corporation_id():
            color = self.config.get_slack_loss_color()
        else:
            color = self.config.get_slack_kill_color()
        return color

    def get_message_icon_emoji(self):
        if self.config.get_corporation_id() == self.kill.get_victim_corporation_id():
            icon_emoji = self.config.get_slack_loss_emoji()
        else:
            icon_emoji = self.config.get_slack_kill_emoji()
        return icon_emoji

    def get_message_user_name(self):
        if self.config.get_corporation_id() == self.kill.get_victim_corporation_id():
            user_name = self.config.get_slack_loss_username()
        else:
            user_name = self.config.get_slack_kill_username()
        return user_name

    def get_kill_description(self):
        description = self.kill.get_victim_character_name() + ' lost their ' + self.kill.get_victim_ship_name() + ' in ' + self.kill.get_solar_system_name()
        return description

    def get_kill_link(self):
        url = 'http://www.zkillboard.com/kill/' + str(self.kill.get_killmail_id()) + '/'
        return url

    # Old format, decided to use V2 instead because it takes up less space and fields does not repeat the title.
    def generate_slack_message(self):
        slack_message = {
            "username": self.get_message_user_name(),
            "attachments": [
                {
                    "title": self.get_kill_description(),
                    "title_link": self.get_kill_link(),
                    "color": self.get_message_color(),
                    "fields": [
                        {
                            "title": "Final Blow",
                            "value": self.kill.get_final_blow_name(),
                            "short": True

                        },
                        {
                            "title": "Top Damage",
                            "value": self.kill.get_top_damage_name(),
                            "short": True
                        },
                        {
                            "title": "Total Value",
                            "value": ('{:,.2f}'.format(self.kill.get_killmail_value()) + ' ISK'),
                            "short": False
                        }
                    ],
                    "thumb_url": self.kill.get_victim_ship_icon(),
                    "fallback": "New Killmail!",
                }
            ],
            "icon_emoji": self.get_message_icon_emoji()
        }
        return slack_message

    def encode_slack_message(self):
        encoded_message = json.dumps(self.generate_slack_message()).encode('utf-8')
        return encoded_message


# Class ConfigHandler handles generating the config file if there is not one.
# It also handles the opening of the file and reading of settings from it.
class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.read_config_file()

    def generate_config_file(self):
        self.config.add_section('General Settings')
#        self.config.set('General Settings', 'alliance_id', '')
        self.config.set('General Settings', 'corporation_id', '')
        self.config.set('General Settings', 'queue_id', '')

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

#    def get_alliance_id(self):
#        try:
#            return int(self.config.get('General Settings', 'alliance_id'))
#        except:
#            return 0

    def get_corporation_id(self):
        try:
            return int(self.config.get('General Settings', 'corporation_id'))
        except:
            return 0

    def get_queue_id(self):
        try:
            return self.config.get('General Settings', 'queue_id')
        except:
            return False

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
