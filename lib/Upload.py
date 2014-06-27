import re
import os
import sys
import socket
import datetime
import httplib2
from StringIO import StringIO

import strings
import faults
from DataManager import LocalDataManager
from ApplicationManager import ApplicationManager

from kamaki.clients import ClientError

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
