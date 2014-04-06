#!/usr/bin/env python

import xml.etree.ElementTree as ET
import requests
import flickr_auth as auth
import sys
from urllib.request import urlopen
from collections import OrderedDict

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

    def upload_from_file(self, filename):
        f = open(filename, 'rb')
        return self.upload(f)


    def upload_from_url(self, url):
        """
        Upload photo from image's url.
        """
        data = urlopen(url).read()
        return self.upload(data)

    def upload(
            self, f, title='', description='', tags='',
            is_public='0', is_friend='0', is_family='0',
            safety_level='2', hidden='2'):
        """
        Upload photo from file object.

        f
            The file to upload.

        title (optional)
            The title of the photo.

        description (optional)
            A description of the photo. May contain some limited HTML.
       
        tags (optional)
            A space-seperated list of tags to apply to the photo.
       
        is_public, is_friend, is_family (optional)
            Set to 0 for no, 1 for yes. 
            Specifies who can view the photo.
       
        safety_level (optional)
            Set to 1 for Safe, 2 for Moderate, or 3 for Restricted.
      
        hidden (optional)
            Set to 1 to keep the photo in global search results, 
            2 to hide from public searches.

        Return: photo's ID if upload successful.
        """
        url = 'http://up.flickr.com/services/upload'
        files = {'photo': f}
        params = {
            'title': title,
            'description': description,
            'tags': tags,
            'is_public': is_public,
            'is_friend': is_friend,
            'is_family': is_family,
            'safety_level': safety_level,
            'hidden': hidden
        }
        params = auth.gen_oauth_params('POST', url, params)
        resp = requests.post(url, files=files, data=params)
        dom = ET.fromstring(resp.text)
        if dom.get('stat') == 'ok':
            photoid = dom.find('photoid').text
            return photoid
        else:
            print("There's something wrong here")

    def get_photo_links(self, photoid):
        """
        Get photo's links of uploaded image

        photoid: ID of uploaded image

        Return: dict of links.
        """
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
            links = OrderedDict()
            for size in sizes:
                links[size.get('label')] = size.get('source')
            return links
        else:
            print("There's something wrong here")
        

if __name__ == '__main__':
    api = FlickrApi()
    photo = sys.argv[1]
    photoid = api.upload_from_file(photo)
    links = api.get_photo_links(photoid)
    out = []
    for size, link in links.items():
        out.append('%12s:%s' % (size, link))
    print('\n'.join(out))
    #api.upload_from_url(photo)
    #api.test_login()
    #api.get_upload_status()
    #api.get_photo_links('10513318854')