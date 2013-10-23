#!/usr/bin/env python

import http.client
import hashlib
import xml.etree.ElementTree as ET
import urllib.parse
import time
import json
import hmac
import base64
import mimetypes
import os
import requests

class FlickrApi():
    api_key = '34c6e64bd0e8a8e72e5cc6f0794d0c93'
    app_secret = '9bc9e08ac4fc7abc'
    host = 'www.flickr.com'
    
    def __init__(self):
        if not self.load_config():
            self.key = self.app_secret + '&'
            self.oauth_token, self.oauth_token_secret = self.get_request_token()
            self.key = self.app_secret + '&' + self.oauth_token_secret
            self.authorize()
            self.access_token()
            self.save_config()

    def md5(self, data):
        '''
        Return md5 hash as string.
        '''
        md5 = hashlib.md5()
        md5.update(bytes(data, 'UTF-8'))
        return md5.hexdigest()

    def sha1(self, data):
        '''
        Return sha1 hash as string
        '''
        sha1 = hashlib.sha1()
        sha1.update(bytes(data, 'UTF-8'))
        return sha1.hexdigest()

    def gen_signature(self, method, path, parameters={}, host=host):
        '''
        Generate and return signature as string.
        '''
        base = method + '&' + urllib.parse.quote('http://' + host + path, safe='')
        params = ''
        for name in sorted(parameters.keys()):
            if not isinstance(parameters.get(name), str):
                #print(parameters.get(name))
                continue
            params += name + '=' + parameters[name] + '&'
        params = urllib.parse.quote(params[:-1])
        base += '&' + params
        #print(base)
        
        hashed = hmac.new(self.key.encode(), base.encode(), hashlib.sha1).digest()
        b = base64.encodestring(hashed)
        b = b.rstrip()

        # the signature
        #signature = urllib.parse.quote(b)
        signature = b.decode()
        #print(signature)
        return signature

    def gen_url(self, path, parameters):
        '''
        Generate and return path with parameters as string
        '''
        request_url = path
        if len(parameters) > 0:
            request_url += '?'
            for name in sorted(parameters.keys()):
                request_url += name + '=' + parameters[name] + '&'

            # remove last '&' character and spaces
            request_url = request_url[:-1].replace(' ', '')
        #print('http://' + self.host + request_url)
        return request_url

    def http_get(self, path, parameters, headers={}, host=host, oauth=False):
        '''
        Send HTTP GET request
        Return response as dict by default.
        '''
        if oauth:
            parameters['oauth_signature'] = self.gen_signature('GET', path, parameters, host)
        conn = http.client.HTTPConnection(host)
        conn.request('GET', self.gen_url(path, parameters))
        resp = conn.getresponse()
        format = parameters.get('format') # avoid KeyError exception
        if format == 'json':
            decoded_result = resp.read().decode()
            #print(decoded_result)
            result = json.loads(decoded_result)
        elif oauth:
            result = dict()
            items = resp.read().decode().split('&')
            for item in items:
                name, value = item.split('=')
                result[name] = value
                if name == 'oauth_problem':
                    break
        else:
            # default is xml
            result = ET.fromstring(resp.read().decode())
        return result

    def http_post(self, path, parameters, headers={}, host=host, oauth=False, files=None):
        '''
        Send HTTP POST request
        Return response as dict by default.
        '''
        #print(headers)
        if oauth:
            parameters['oauth_signature'] = self.gen_signature('POST', path, parameters)
        params = urllib.parse.urlencode(parameters)
        #print(params)
        conn = http.client.HTTPConnection(host)
        conn.request('POST', path, params, headers)
        resp = conn.getresponse()
        print(resp.status, resp.reason)
        return resp.read()

    def get_request_token(self):
        path = '/services/oauth/request_token'
        parameters = dict()
        parameters['oauth_nonce'] = str(int(time.time()))
        parameters['oauth_timestamp'] = str(int(time.time()))
        parameters['oauth_consumer_key'] = self.api_key
        parameters['oauth_signature_method'] = 'HMAC-SHA1'
        parameters['oauth_version'] = '1.0'
        parameters['oauth_callback'] = 'http%3A%2F%2Fwww.example.com'
        #parameters['oauth_signature'] = self.gen_signature('GET', path, parameters)
        result = self.http_get(path, parameters, oauth=True)
        if result.get('oauth_callback_confirmed') == 'true':
            self.oauth_token = result['oauth_token']
            self.oauth_token_secret = result['oauth_token_secret']
            return self.oauth_token, self.oauth_token_secret
        else:
            return result

    def authorize(self):
        path = '/services/oauth/authorize'
        parameters = dict()
        parameters['oauth_token'] = self.oauth_token
        parameters['perms'] = 'write'
        link = 'http://' + self.host + self.gen_url(path, parameters)
        print('Open this link with your browse to confirm:', link)
        oauth_verifier = input('Paste you verifier here: ')
        self.oauth_verifier = str(oauth_verifier).replace(' ', '')

    def access_token(self):
        path = '/services/oauth/access_token'
        parameters = dict()
        parameters['oauth_nonce'] = str(int(time.time()))
        parameters['oauth_timestamp'] = str(int(time.time()))
        parameters['oauth_verifier'] = self.oauth_verifier
        parameters['oauth_consumer_key'] = self.api_key
        parameters['oauth_signature_method'] = 'HMAC-SHA1'
        parameters['oauth_version'] = '1.0'
        parameters['oauth_token'] = self.oauth_token
        #parameters['oauth_signature'] = self.gen_signature('GET', path, parameters)
        self.http_get(path, parameters, oauth=True)
        #print(result)

    def save_config(self):
        config = dict()
        config['oauth_token'] = self.oauth_token
        config['oauth_token_secret'] = self.oauth_token_secret
        config['oauth_verifier'] = self.oauth_verifier
        f = open('flickr.cfg', 'w')
        f.write(json.dumps(config))

    def load_config(self):
        try:
            f = open('flickr.cfg')
            data = ''
            while True:
                line = f.readline()
                if len(line) == 0:
                    break
                data += line
            config = json.loads(data)
            self.oauth_token = config['oauth_token']
            self.oauth_token_secret = config['oauth_token_secret']
            self.oauth_verifier = config['oauth_verifier']
            self.key = self.app_secret + '&' + self.oauth_token_secret
        except:
            return False
        return True

    def test_login(self):
        host = 'api.flickr.com'
        path = '/services/rest'
        parameters = dict()
        parameters['nojsoncallback'] = '1'
        parameters['oauth_nonce'] = str(int(time.time()))
        parameters['oauth_timestamp'] = str(int(time.time()))
        parameters['oauth_consumer_key'] = self.api_key
        parameters['oauth_verifier'] = self.oauth_verifier
        parameters['api_key'] = self.api_key
        parameters['oauth_signature_method'] = 'HMAC-SHA1'
        parameters['oauth_version'] = '1.0'
        parameters['oauth_token'] = self.oauth_token
        parameters['format'] = 'json'
        parameters['method'] = 'flickr.test.login'
        print(self.http_get(path, parameters, host=host, oauth=True))

    def get_upload_status(self):
        host = 'api.flickr.com'
        path = '/services/rest'
        parameters = dict()
        parameters['nojsoncallback'] = '1'
        parameters['oauth_nonce'] = str(int(time.time()))
        parameters['oauth_timestamp'] = str(int(time.time()))
        parameters['oauth_consumer_key'] = self.api_key
        parameters['oauth_verifier'] = self.oauth_verifier
        #parameters['api_key'] = self.api_key
        parameters['oauth_signature_method'] = 'HMAC-SHA1'
        parameters['oauth_version'] = '1.0'
        parameters['oauth_token'] = self.oauth_token
        parameters['format'] = 'json'
        parameters['method'] = 'flickr.people.getUploadStatus'
        print(self.http_get(path, parameters, host=host, oauth=True))

    def upload_photo(self, file_name):
        url = 'http://up.flickr.com/services/upload'
        #url = 'http://requestb.in/wkgdufwk'
        files = {'photo': open(file_name, 'rb')}

        parameters = dict()
        parameters['oauth_signature_method'] = 'HMAC-SHA1'
        parameters['oauth_timestamp'] = str(int(time.time()))
        parameters['oauth_nonce'] = str(int(time.time()))
        parameters['oauth_consumer_key'] = self.api_key
        parameters['oauth_token'] = self.oauth_token
        parameters['oauth_version'] = '1.0'
        parameters['oauth_verifier'] = self.oauth_verifier
        parameters['oauth_signature'] = self.gen_signature(
            'POST', 
            '/services/upload', 
            parameters=parameters,
            host='up.flickr.com')

        r = requests.post(url, files=files, data=parameters)
        print(r.text)

if __name__ == '__main__':
    api = FlickrApi()
    #api.upload_photo('image.jpg')
    api.test_login()
    #api.get_upload_status()