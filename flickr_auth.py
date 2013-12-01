#!/usr/bin/env python

import time
import urllib.parse
import base64
import hmac
import hashlib
import requests
import json
import os.path

api_key = '34c6e64bd0e8a8e72e5cc6f0794d0c93'
api_secret = '9bc9e08ac4fc7abc'
key = api_secret + '&'
oauth_token = ''
oauth_token_secret = ''
oauth_verifier = ''
CONFIG_FILE = 'flickr.cfg'

def get_oauth_token():
    '''
    If success, get oauth_token and oauth_token_secret.
    '''
    global key
    global oauth_token
    global oauth_token_secret
    url = 'http://www.flickr.com/services/oauth/request_token'
    #url = 'http://requestb.in/1acqk8s1'
    params = {'oauth_callback': 'http://www.example.com'}
    params = _gen_unoauth_params('GET', url, params)
    resp = requests.get(url, params=params)
    r = resp.text
    if 'oauth_callback_confirmed=true' in r:
        pairs = r.split('&')
        oauth_token = pairs[1].split('=')[1]
        oauth_token_secret = pairs[2].split('=')[1]
        key = api_secret + '&' + oauth_token_secret

def authorize():
    '''
    Authorize permission with user account.
    '''
    global oauth_verifier
    url = 'http://www.flickr.com/services/oauth/authorize'
    url += '?oauth_token={0}&perms=write'.format(oauth_token)
    print('Open this link with your browse:', url)
    line = input('Paste your oauth_verifier here: ')
    oauth_verifier = line.strip()

def access_token():
    global oauth_verifier, oauth_token, oauth_token_secret, key
    url = 'http://www.flickr.com/services/oauth/access_token'
    params = {
        'oauth_token': oauth_token,
        'oauth_verifier': oauth_verifier
    }
    params = _gen_unoauth_params('GET', url, params)
    resp = requests.get(url, params=params)
    fields = resp.text.split('&')
    oauth_token = fields[1].split('=')[1]
    oauth_token_secret = fields[2].split('=')[1]
    key = api_secret + '&' + oauth_token_secret


def _gen_unoauth_params(method, url, params={}):
    params['oauth_nonce'] = str(int(time.time()))
    params['oauth_timestamp'] = str(int(time.time()))
    params['oauth_consumer_key'] = api_key
    params['oauth_signature_method'] = 'HMAC-SHA1'
    params['oauth_version'] = '1.0'
    params['oauth_signature'] = _gen_signature(method, url, params)
    return params

def _gen_signature(method, url, parameters={}):
    '''
    Generate and return signature as string.
    '''
    base = method + '&' + urllib.parse.quote(url, safe='')
    params = ''
    for name in sorted(parameters.keys()):
        params += urllib.parse.quote(name) + '=' + urllib.parse.quote(parameters[name], safe='') + '&'
    params = urllib.parse.quote(params[:-1], safe='')
    base += '&' + params
    #print(base)
    
    hashed = hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()
    b = base64.encodestring(hashed)
    b = b.rstrip()

    # the signature
    signature = b.decode()
    #print(signature)
    return signature


def save_config(filename=CONFIG_FILE):
        config = dict()
        config['oauth_token'] = oauth_token
        config['oauth_token_secret'] = oauth_token_secret
        config['oauth_verifier'] = oauth_verifier
        f = open(filename, 'w')
        f.write(json.dumps(config))
        f.close()

def load_config(filename=CONFIG_FILE):
    try:
        f = open(filename)
        data = ''
        while True:
            line = f.readline()
            if len(line) == 0:
                break
            data += line
        config = json.loads(data)
        global oauth_token, oauth_token_secret, oauth_verifier, key
        oauth_token = config['oauth_token']
        oauth_token_secret = config['oauth_token_secret']
        oauth_verifier = config['oauth_verifier']
        key = api_secret + '&' + oauth_token_secret
        f.close()
        return True
    except:
        return False

def gen_config(filename=CONFIG_FILE):
    global key
    key = api_secret + '&'
    get_oauth_token()
    authorize()
    access_token()
    save_config(filename)

def gen_oauth_params(method, url, params={}):
    params['oauth_token'] = oauth_token
    params = _gen_unoauth_params(method, url, params)
    return params

def do_oauth():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(cur_dir, CONFIG_FILE)
    if not load_config(filename):
        gen_config(filename)

if __name__ == '__main__':
    do_oauth()