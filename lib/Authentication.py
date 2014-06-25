import json
import httplib2

import local
import logger
import faults
from DataManager import Manager
from DataManager import LocalDataManager

from kamaki.clients import ClientError
from astakosclient import AstakosClient
from astakosclient import errors as AstakosErrors
from dropbox import rest
from dropbox.client import DropboxClient
from dropbox.client import DropboxOAuth2FlowNoRedirect
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import Credentials
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.client import AccessTokenRefreshError

class PithosFlow(object):
    def start(self):
        return local.Pithos_LOGINURL

    def finish(self, token):
        s = AstakosClient(token, local.Pithos_AUTHURL, logger=logger.logger_factory('astakosclient'))
        s.authenticate()
        return token

class GoogleDriveFlowWrapper(object):
    def __init__(self, flow):
        self.flow = flow

    def start(self):
        return self.flow.step1_get_authorize_url()

    def finish(self, code):
        return self.flow.step2_exchange(code)

class AuthManager(Manager):
    def __init__(self):
        self.auth_functions = [self._dropbox_auth,
                               self._pithos_auth,
                               self._googledrive_auth]
        self.service_auth = dict(zip(self.services, self.auth_functions))

        self.add_functions = [self._dropbox_add_user,
                              self._pithos_add_user,
                              self._googledrive_add_user]
        self.add_user = dict(zip(self.services, self.add_functions))

        self.logger = logger.logger_factory(self.__class__.__name__)

    #exposed functions
    def authenticate(self, service):
        assert(service in self.services)

        return self.service_auth[service]()

    def add_and_authenticate(self, service, key):
        assert(service in self.services)

        return self.add_user[service](key)

    def get_flow(self, service):
        assert(service in self.services)

        return getattr(self, '_get_{}_flow'.format(service.lower()))()
    #end of exposed functions

    def _pithos_auth(self):
        access_token = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        access_token = dataManager.get_credentials('Pithos')
        try:
            dm = LocalDataManager()
            s = AstakosClient(access_token, local.Pithos_AUTHURL)
            auth_data = s.authenticate()
            pithos_url = self._get_pithos_public_url(auth_data)
            uuid = auth_data['access']['user']['id']
            pithosClient = PithosClient(pithos_url, access_token, uuid)
        except (AstakosErrors.Unauthorized, faults.InvalidAuth) as e:
            raise faults.InvalidAuth('Pithos-Auth')
        except (AstakosErrors.AstakosClientException, faults.NetworkError) as e:
            raise faults.NetworkError('No internet-Auth')

        return pithosClient

    def _pithos_add_user(self, key):
        dataManager = LocalDataManager()
        dataManager.set_credentials('Pithos', key)
        return self._pithos_auth()

    #https://www.dropbox.com/developers/core/docs/error handling
    def _dropbox_auth(self):
        access_token = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        access_token = dataManager.get_credentials('Dropbox')

        dropboxClient = DropboxClient(access_token)

        try:
            dropboxClient.account_info()
        except rest.ErrorResponse as e:
            if e.status == 401:
                raise faults.InvalidAuth('Dropbox-Auth')
        except rest.RESTSocketError as e:
            raise faults.NetworkError('No internet-Auth')

        return dropboxClient

    def _dropbox_add_user(self, key):
        dataManager = LocalDataManager()
        dataManager.set_credentials('Dropbox', key)
        return self._dropbox_auth()

    #http://tinyurl.com/kdv3ttb
    def _googledrive_auth(self):
        credentials = None
        dataManager = LocalDataManager()

        #A KeyError will be raised if there is no token.
        credentials = dataManager.get_credentials('GoogleDrive')

        credentials = Credentials.new_from_json(credentials)
        http = credentials.authorize(httplib2.Http())
        try:
            drive_service = build('drive', 'v2', http=http)
        except httplib2.ServerNotFoundError:
            raise faults.NetworkError('No internet.')

        try:
            #Check whether the target folder exists
            container = dataManager.get_service_root('GoogleDrive')
            if container:
                arguments = ['title = "{}"'.format(container),
                             'mimeType = "application/vnd.google-apps.folder"',
                             'trashed = False']
                q = ' and '.join(arguments)
                response = drive_service.files().list(q=q).execute()
                if not response['items']:
                    #Create the folder
                    self.logger.info('GoogleDrive folder changed:{}'.format(container))
                    body = {'title':container, 'mimeType':'application/vnd.google-apps.folder'}
                    response = drive_service.files().insert(body=body).execute()
                    dataManager.set_folder_id(response['id'])
                else:
                    dataManager.set_folder_id(response['items'][0]['id'])
        except errors.HttpError as e:
            #raise
            raise faults.NetworkError('No internet.')
        except AccessTokenRefreshError:
            raise faults.InvalidAuth('GoogleDrive')

        dataManager.set_credentials('GoogleDrive', credentials)
        return drive_service

    def _googledrive_add_user(self, credentials):
        dataManager = LocalDataManager()
        dataManager.set_credentials('GoogleDrive', credentials)
        return self._googledrive_auth()

    def _get_dropbox_flow(self):
        return DropboxOAuth2FlowNoRedirect(local.Dropbox_APPKEY,
                                           local.Dropbox_APPSECRET)

    def _get_googledrive_flow(self):
        flow = OAuth2WebServerFlow(local.GoogleDrive_APPKEY, local.GoogleDrive_APPSECRET,
                                   local.GoogleDrive_OAUTHSCOPE, local.GoogleDrive_REDIRECTURI)
        return GoogleDriveFlowWrapper(flow)

    def _get_pithos_flow(self):
        return PithosFlow()

    def _get_pithos_public_url(self, endpoints, type=u'object-store'):
        r = endpoints[u'access'][u'serviceCatalog']
        for i in r:
            if i[u'type'] == type:
                return i[u'endpoints'][0][u'publicURL']
        return None
