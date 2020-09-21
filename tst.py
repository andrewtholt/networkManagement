#!/usr/bin/env python3

import urllib
import base64

from bs4 import BeautifulSoup
import requests

def getValue(soup,tag):
    p = soup.find(tag)

    data = []
    for element in soup.find(tag):
        data.append(element)

    return(data)

def main():
    url = 'http://192.168.10.124:2812/_status?format=xml'
    username = 'admin'
    password = 'monit'
    
# create a password manager
    password_mgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    
# Add the username and password.
# If we knew the realm, we could use it instead of None.
# top_level_url = "http://example.com/foo/"
    password_mgr.add_password(None, url, username, password)
    
    handler = urllib.request.HTTPBasicAuthHandler(password_mgr)
    
# create "opener" (OpenerDirector instance)
    opener = urllib.request.build_opener(handler)
    
# use the opener to fetch a URL
    opener.open(url)
    
# Install the opener.
# Now all calls to urllib.request.urlopen use our opener.
    urllib.request.install_opener(opener)
    
    try:
        u2 = urllib.request.urlopen(url)
    
        contents = u2.readline()
    
        soup = BeautifulSoup(contents.decode('utf-8'), 'lxml')
    
        hostname = getValue(soup, 'localhostname')
        print("Getvalue ", hostname[0])

        uptime = getValue(soup, 'uptime')
        print("Getvalue ", uptime[0])
    
    
#    print(soup.prettify())
    
    except urllib.error.HTTPError as e:
        print(e.code)
        print(e.read())
    
    
    
    
    
    
    
main()    
