import urllib.request
import json
import codecs
import pprint
import csv
import re
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
cache_file_path = os.path.join(script_directory, 'recent_kill_list.csv')
type_id_path = os.path.join(script_directory, 'typeids.csv')


def main():
    config = ConfigHandler()
    data = DataHandler(config)
    data.read_kill_list_file()
    web_handler = WebHandler()
    url = web_handler.generate_zkillboard_url(data, config)
    reader = codecs.getreader('utf-8')
    response = json.load(reader(urllib.request.urlopen(url)))
    # Used for testing. To save Json data from zKillboard, then read from it when testing.
    # Helps to not spam request to zKillboard
    #    with open('json_info.txt', 'w') as json_file:
    #        json_file.write(pprint.pformat(response))
    #     with open('json_info.txt', 'r') as json_file:
    #            response = json.loads(fixLazyJson(json_file.read()))
    if_new_kill = False
    for kill_mail in response:
        kill = KillMail(kill_mail)
        if data.check_if_new_kill(kill):
            if_new_kill = True
            web_handler.get_html_page(kill)
            slack_message = SlackMessage(kill, web_handler, config)
            encoded_slack_message = slack_message.encode_slack_message()
            urllib.request.urlopen(config.get_slack_web_hook(), encoded_slack_message)
            data.add_kill_id(kill.get_kill_id())
    if if_new_kill:
        data.write_kill_list_file()


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

    def get_kill_link(self):
        kill_link = 'https://zkillboard.com/kill/' + str(self.kill.get_kill_id())
        return kill_link

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


class DataHandler:
    def __init__(self, config):
        self.kill_list = []
        self.config = config

    def get_cache_size(self):
        return self.config.get_cache_size()

    def get_recent_kill_id(self):
        return self.config.get_recent_kill()

    def get_kill_list(self):
        return self.kill_list

    def add_kill_id(self, kill_id):
        self.kill_list.append(kill_id)

    def check_if_new_kill(self, kill):
        kill_list = self.get_kill_list()
        for kill_id in kill_list:
            if str(kill.get_kill_id()) == str(kill_id):
                return False

        else:
            return True

    def write_kill_list_file(self):
        try:
            with open(cache_file_path, 'w', newline='') as kill_list_file:
                writer = csv.writer(kill_list_file, delimiter='\n')
                self.kill_list.sort(reverse=True)
                while len(self.kill_list) > self.get_cache_size():
                    del self.kill_list[-1]
                writer.writerow(self.kill_list)
        except:
            print('Error writing recent_kill_list.csv')

    def read_kill_list_file(self):
        try:
            with open(cache_file_path, 'r', newline='') as kill_list_file:
                file_reader = csv.reader(kill_list_file, delimiter='\n')
                for kill_id in file_reader:
                    self.kill_list.append(kill_id[0])
                # Needed to convert the items in the list from Strings to Ints because csv.reader returns a
                # list of Strings
                self.kill_list = list(map(int, self.kill_list))
        except FileNotFoundError:
            print('recent_kill_id_list.csv not found\nUsing recent_kill\n')
            self.kill_list = [self.get_recent_kill_id()]


class WebHandler:
    def __init__(self):
        self.image_url = ''
        self.description = ''
        self.html = ''

    def get_image_url(self):
        self.find_image_url()
        return self.image_url

    def get_description(self):
        self.find_description()
        return self.description

    def get_html_page(self, kill):
        url = 'https://zkillboard.com/kill/' + str(kill.get_kill_id())
        reader = codecs.getreader('utf-8')
        html = reader(urllib.request.urlopen(url))
        self.html = html.read()

    def find_image_url(self):
        image_regex = re.compile('<meta\sname=["\']og:image["\']\scontent=["\'](.*?)["\']>')
        image_list = image_regex.findall(self.html)
        self.image_url = image_list[0]

    def find_description(self):
        description_regex = re.compile('<meta\sname=["\']og:description["\']\scontent=["\'](.*?)["\']>')
        description_list = description_regex.findall(self.html)
        self.description = self.remove_total_value_from_title(description_list[0])

    def generate_zkillboard_url(self, data, config):
        url = 'https://zkillboard.com/api/'
        url += 'allianceID/' + str(config.get_alliance_id()) + '/'
        url += 'afterKillID/' + str(min(data.get_kill_list())) + '/'
        url += 'no-items/no-attackers/'
        return url

    def remove_total_value_from_title(self, title):
        if ' Total Value:' in title:
            title = title[:title.find(' Total Value:')]
        return title


class ConfigHandler:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.read_config_file()

    def generate_config_file(self):
        self.config.add_section('General Settings')
        self.config.set('General Settings', 'alliance_id', '')
        self.config.set('General Settings', 'corporation_id', '')
        self.config.set('General Settings', 'cache_size', '10')
        self.config.set('General Settings', 'recent_kill_id', '')

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

    def get_cache_size(self):
        try:
            return int(self.config.get('General Settings', 'cache_size'))
        except:
            return 10

    def get_recent_kill(self):
        try:
            return int(self.config.get('General Settings', 'recent_kill_id'))
        except:
            print('Error Getting recent_kill_id From Config.ini')
            sys.exit()

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

# Only used for testing to fix reading json data from saved file.
def fixLazyJson(in_text):
    tokengen = tokenize.generate_tokens(StringIO(in_text).readline)

    result = []
    for tokid, tokval, _, _, _ in tokengen:
        # fix unquoted strings
        if (tokid == token.NAME):
            if tokval not in ['true', 'false', 'null', '-Infinity', 'Infinity', 'NaN']:
                tokid = token.STRING
                tokval = u'"%s"' % tokval

        # fix single-quoted strings
        elif (tokid == token.STRING):
            if tokval.startswith("'"):
                tokval = u'"%s"' % tokval[1:-1].replace('"', '\\"')

        # remove invalid commas
        elif (tokid == token.OP) and ((tokval == '}') or (tokval == ']')):
            if (len(result) > 0) and (result[-1][1] == ','):
                result.pop()

        # fix single-quoted strings
        elif (tokid == token.STRING):
            if tokval.startswith("'"):
                tokval = u'"%s"' % tokval[1:-1].replace('"', '\\"')

        result.append((tokid, tokval))

    return tokenize.untokenize(result)

main()
