import os
import sys
import datetime

import faults
import strings
from DataManager import LocalDataManager
from ApplicationManager import ApplicationManager

from kamaki.clients import ClientError


class PithosUtilities(object):
    def __init__(self, client):
        self.client = client

    def get_containers(self):
        try:
            folders = []
            resp = self.client.list_containers()
            for item in resp:
                folders.append(item['name'])

            return folders
        except ClientError as e:
            print e
            
    def get_objects(self, container):
        try:
            objects = []
            self.client.container = container
            resp = self.client.list_objects()
            for item in resp:
                objects.append([item['name'], '20KB'])
                
            return objects
        except ClientError as e:
            print e

class PithosFile(object):
    def __init__(self, container, filename, client):
        self.client = client
        self.client.container = container

        self.filename = filename
        self.container = container

    def rename(self, new_filename):
        try:
            path = '/{}/{}'.format(self.container, new_filename)
            response = self.client.object_move(self.filename,
                                               destination=path)
            self.filename = new_filename
        except ClientError as e:
            print e

    def move(self, new_container):
        try:
            path = '/{}/{}'.format(new_container, self.filename)
            response = self.client.object_move(self.filename,
                                               destination=path)
            self.container = new_container
            self.client.container = new_container
        except ClientError as e:
            print e

    def delete(self):
        try:
            response = self.client.object_delete(self.filename)
        except ClientError as e:
            print e


class PithosUploader(object):
    def __init__(self, path, remote='pithos', offset=0, client=None):
        self.client = client
        self.path = path
        self.remote = remote #Container
        self.offset = offset #Progress

        self.target_length = os.path.getsize(path)

    def upload_chunked(self, chunk_size=128*1024): #Chunk size unused.
        try:
            with open(self.path, 'rb') as f:
                try:
                    for i in self.client.upload_object(os.path.basename(self.path), f, public=True):
                        self.offset += i
                        try:
                            yield (float(self.offset)/self.target_length, self.path)
                        except ZeroDivisionError:
                            #The file was empty, it's 100% by default.
                            yield (1.0, self.path)
                except ClientError as e:
                    if e.status == 413: #Out of quota, http://tinyurl.com/pkmpuk6
                        yield (3, None)
                    elif e.status in [401, 404]:
                        yield (12, None)
                    elif 'Errno 11004' in e.message:
                        yield (22, None)
                    return
        except IOError as e:
            yield (2, None)

    def complete_upload(self):
        history_entry = {}

        objname = os.path.basename(self.path)
        objinfo = self.client.get_object_info(objname)
        history_entry['name'] = objname
        date = str(datetime.datetime.now())
        history_entry['date'] = date[:date.index('.')]
        history_entry['path'] = self.remote
        history_entry['link'] = objinfo['x-object-public']

        return history_entry
