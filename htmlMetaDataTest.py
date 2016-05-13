import re
import urllib.request
import codecs

url = 'https://zkillboard.com/kill/53934370/'
reader = codecs.getreader('utf-8')
keywordregex = re.compile('<meta\sname=["\']og:description["\']\scontent=["\'](.*?)["\']>')
html = reader(urllib.request.urlopen(url))
keywordlist = keywordregex.findall(html.read())
if len(keywordlist) > 0:
    keywordlist = keywordlist[0]
    keywordlist = keywordlist.split(", ")
print(keywordlist)