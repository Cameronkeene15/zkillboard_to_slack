import urllib.request
import json
import codecs
import pprint
import csv

# for fixLazyJson
import tokenize
import token
from io import *

alliance_id = 99004364
corporation_id = 98380820


def main():
    slack_web_hook = 'https://hooks.slack.com/services/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'
    url = generate_zkillboard_url()
    reader = codecs.getreader('utf-8')
    response = json.load(reader(urllib.request.urlopen(url)))
    with open('json_info.txt', 'w') as json_file:
        json_file.write(pprint.pformat(response))
    #    with open('json_info.txt', 'r') as json_file:
    #        response = json.loads(fixLazyJson(json_file.read()))
    kill_list = []
    for kill_mail in response:
        kill = KillMail(kill_mail)
        if check_if_new_kill(kill):
            pprint.pformat(kill_mail)
            slack_message = SlackMessage(kill)
            encoded_slack_message = slack_message.encode_slack_message()
#            req = urllib.request.urlopen(slack_web_hook, encoded_slack_message)
#            page = req.read()
#            print(page)
        kill_list = generate_kill_id_list(kill, kill_list)
    write_last_kill_list(kill_list, 10)
    print('Finished')


def generate_zkillboard_url():
    url = 'https://zkillboard.com/api/'
    url += 'allianceID/99004364/'
    #    url += 'afterKillID/53857444/'
    url += 'afterKillID/' + str(min(get_last_kill_list())[0]) + '/'
    url += 'no-items/no-attackers/'
    return url


def check_if_new_kill(kill):
    kill_list = get_last_kill_list()
    for kill_id in kill_list:
        if str(kill.get_kill_id()) == str(kill_id[0]):
            print('already have this kill')
            return False

    else:
        return True


def get_last_kill_list():
    try:
        with open('recent_kill_id_list.csv', 'r', newline='') as kill_list_file:
            file_reader = csv.reader(kill_list_file, delimiter='\n')
            kill_list = list(file_reader)
    except:
        kill_list = ['0']
    return kill_list



def generate_kill_id_list(kill, kill_list):
    kill_list.append(kill.get_kill_id())
    return kill_list


def write_last_kill_list(kill_list, cache_size):
    with open('recent_kill_id_list.csv', 'w', newline='') as kill_list_file:
        writer = csv.writer(kill_list_file, delimiter='\n')
        kill_list.sort(reverse=True)
        while len(kill_list) > cache_size:
            print('removing: ' + str(kill_list[-1]))
            del kill_list[-1]
        writer.writerow(kill_list)






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
    def __init__(self, kill):
        self.kill = kill

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

    def get_thumb_nail_url(self):
        url = 'https://image.eveonline.com/Render/'
        url += str(self.kill.get_ship_id())
        url += '_64.png'
        print(url)
        return url

    def format_isk_value(self, value):
        value = '{:,.2f}'.format(value)
        return value

    def generate_slack_message(self):
        slack_message = {"username": "zKillboard",
                         "attachments": [
                             {
                                 "title": self.generate_message_title(),
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
                                         "value": self.format_isk_value(self.kill.get_kill_value()),
                                         "short": False
                                     }
                                 ],
                                 "thumb_url": self.get_thumb_nail_url(),
                             }
                         ],
                         "icon_emoji": self.get_message_icon_emoji()}
        return slack_message

    def encode_slack_message(self):
        encoded_message = json.dumps(self.generate_slack_message()).encode('utf-8')
        return encoded_message


main()
