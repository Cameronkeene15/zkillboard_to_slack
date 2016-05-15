import urllib.request
import json
import codecs
import pprint
import csv
import re

# for fixLazyJson
import tokenize
import token
from io import *

# change this to your webhook for the slack channel that you want kills posted to.
slack_web_hook = 'https://hooks.slack.com/services/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'
# slack_web_hook = 'https://hooks.slack.com/services/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'

# change these to your corp id and alliance id. ONLY ALLIANCE ID WORKS RIGHT NOW!
# TO DO: fix these so that only one is required, will probably do this as modes once a config file is incorporated.
alliance_id = 99004364
corporation_id = 98380820

# Change this to a recent kill that has occured on your alliance or corp killboard>
# It is used so that at first run when there is no recent_kill_id_list.csv, it will not pull the last 200 kills from
# zKillboard
recent_kill = 53953253


def main():
    cache_size = 10
    data = DataHandler(cache_size)
    data.read_kill_list_file()
    web_handler = WebHandler()
    url = web_handler.generate_zkillboard_url(data)
    reader = codecs.getreader('utf-8')
    response = json.load(reader(urllib.request.urlopen(url)))
    #    with open('json_info.txt', 'w') as json_file:
    #        json_file.write(pprint.pformat(response))
    #     with open('json_info.txt', 'r') as json_file:
    #            response = json.loads(fixLazyJson(json_file.read()))
    if_new_kill = False
    for kill_mail in response:
        kill = KillMail(kill_mail)
        if data.check_if_new_kill(kill):
            if_new_kill = True
            pprint.pformat(kill_mail)
            web_handler.get_html_page(kill)
            slack_message = SlackMessage(kill, web_handler)
            encoded_slack_message = slack_message.encode_slack_message()
            req = urllib.request.urlopen(slack_web_hook, encoded_slack_message)
            page = req.read()
            print(page)
            data.add_kill_id(kill.get_kill_id())
    if if_new_kill:
        data.write_kill_list_file()


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
        cvs_file = csv.reader(codecs.open('typeids.csv', 'r', encoding='utf-8'))
        for row in cvs_file:
            if row[0] == str(self.json_kill_mail['victim']['shipTypeID']):
                return row[1]
        else:
            return 'Item Name Unknown'


class SlackMessage:
    def __init__(self, kill, web_handler):
        self.kill = kill
        self.web_handler = web_handler

    def generate_message_title(self):
        victim = self.kill.get_victim_character_name()
        corporation = self.kill.get_victim_corporation_name()
        ship_name = self.kill.get_ship_name()

        title = victim + '(' + corporation + ') lost their ' + ship_name
        return title

    def get_kill_link(self):
        kill_link = 'https://zkillboard.com/kill/' + str(self.kill.get_kill_id())
        return kill_link

    def get_message_color(self):
        if alliance_id == self.kill.get_victim_alliance_id() or corporation_id == self.kill.get_victim_corporation_id():
            color = '#ff0000'
        else:
            color = '#36a64f'
        return color

    def get_message_icon_emoji(self):
        if alliance_id == self.kill.get_victim_alliance_id() or corporation_id == self.kill.get_victim_corporation_id():
            icon_emoji = ':skull_and_crossbones:'
        else:
            icon_emoji = ':sunglasses:'
        return icon_emoji

    def get_message_user_name(self):
        if alliance_id == self.kill.get_victim_alliance_id() or corporation_id == self.kill.get_victim_corporation_id():
            user_name = 'Loss'
        else:
            user_name = 'Kill'
        return user_name

    def get_thumb_nail_url(self):
        url = 'https://image.eveonline.com/Render/'
        url += str(self.kill.get_ship_id())
        url += '_64.png'
        print(url)
        return url

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
    def __init__(self, cache_size):
        self.kill_list = []
        self.cache_size = cache_size

    def set_cache_size(self, cache_size):
        self.cache_size = cache_size

    def get_cache_size(self):
        return self.cache_size

    def get_kill_list(self):
        return self.kill_list

    def set_kill_list(self, new_list):
        self.kill_list = new_list

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
        print(self.kill_list)
        try:
            with open('recent_kill_list.csv', 'w', newline='') as kill_list_file:
                writer = csv.writer(kill_list_file, delimiter='\n')
                self.kill_list.sort(reverse=True)
                while len(self.kill_list) > self.cache_size:
                    print('removing: ' + str(self.kill_list[-1]))
                    del self.kill_list[-1]
                writer.writerow(self.kill_list)
        except:
            print('Error writing recent_kill_list.csv')

    def read_kill_list_file(self):
        try:
            with open('recent_kill_list.csv', 'r', newline='') as kill_list_file:
                file_reader = csv.reader(kill_list_file, delimiter='\n')
                for kill_id in file_reader:
                    self.kill_list.append(kill_id[0])
                # Needed to convert the Items in the list from Strings to Ints because csv.reader returns a
                # list of Strings
                self.kill_list = list(map(int, self.kill_list))
        except FileNotFoundError:
            print('recent_kill_id_list.csv now found\nUsing recent_kill\n')
            self.kill_list = [recent_kill]


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


    def generate_zkillboard_url(self, data):
        url = 'https://zkillboard.com/api/'
        url += 'allianceID/' + str(alliance_id) + '/'
        url += 'afterKillID/' + str(min(data.get_kill_list())) + '/'
        url += 'no-items/no-attackers/'
        print(url)
        return url

    def remove_total_value_from_title(self, title):
        if ' Total Value:' in title:
            title = title[:title.find(' Total Value:')]
        print(title)
        return title



main()
