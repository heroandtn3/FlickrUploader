#!/usr/bin/env python

import xml.etree.ElementTree as ET
import requests
import flickr_auth as auth
import sys

class FlickrApi():
    api_key = '34c6e64bd0e8a8e72e5cc6f0794d0c93'
    app_secret = '9bc9e08ac4fc7abc'
    
    def __init__(self):
        auth.do_oauth()

    def test_login(self):
        url = 'http://api.flickr.com/services/rest'
        parameters = dict()
        parameters['nojsoncallback'] = '1'
        parameters['format'] = 'json'
        parameters['method'] = 'flickr.test.login'
        parameters = auth.gen_oauth_params('GET', url, parameters)
        resp = requests.get(url, params=parameters)
        print(resp.text)

    def get_upload_status(self):
        url = 'http://api.flickr.com/services/rest'
        parameters = dict()
        parameters['nojsoncallback'] = '1'
        parameters['format'] = 'json'
        parameters['method'] = 'flickr.people.getUploadStatus'
        parameters = auth.gen_oauth_params('GET', url, parameters)
        resp = requests.get(url, params=parameters)
        print(resp.text)

    def upload_photo(self, file_name):
        url = 'http://up.flickr.com/services/upload'
        files = {'photo': open(file_name, 'rb')}
        params = dict()
        params['is_public'] = '0'
        params = auth.gen_oauth_params('POST', url, params)
        resp = requests.post(url, files=files, data=params)
        dom = ET.fromstring(resp.text)
        if dom.get('stat') == 'ok':
            photoid = dom.find('photoid').text
            self.get_photo_links(photoid)
        else:
            print("There's something wrong here")

    def get_photo_links(self, photoid):
        url = 'http://api.flickr.com/services/rest'
        params = dict()
        params['api_key'] = self.api_key
        params['photo_id'] = photoid
        params['method'] = 'flickr.photos.getSizes'
        params = auth.gen_oauth_params('GET', url, params)
        resp = requests.get(url, params=params)
        dom = ET.fromstring(resp.text)
        if dom.get('stat') == 'ok':
            sizes = dom.find('sizes').findall('size')
            for size in sizes:
                print('%12s: %s' % (size.get('label'), size.get('source')))
        else:
            print("There's something wrong here")
        

if __name__ == '__main__':
    api = FlickrApi()
    photo = sys.argv[1]
    api.upload_photo(photo)
    #api.test_login()
    #api.get_upload_status()
    #api.get_photo_links('10513318854')