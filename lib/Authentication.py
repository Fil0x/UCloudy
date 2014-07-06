import json
import httplib2

import strings
import logger
import faults
from DataManager import Manager
from DataManager import LocalDataManager

from kamaki.clients import ClientError
from kamaki.clients.pithos import PithosClient
from astakosclient import AstakosClient
from astakosclient import errors as AstakosErrors

class PithosFlow(object):
    def start(self):
        return strings.Pithos_LOGINURL

    def finish(self, token):
        s = AstakosClient(token, strings.Pithos_AUTHURL, logger=logger.logger_factory('astakosclient'))
        s.authenticate()
        return token

class AuthManager(Manager):
    def __init__(self):
        self.logger = logger.logger_factory(self.__class__.__name__)

    #exposed functions
    def authenticate(self):
        access_token = None

        #A KeyError will be raised if there is no token.
        access_token = LocalDataManager().get_token()
        try:
            s = AstakosClient(access_token, strings.Pithos_AUTHURL)
            auth_data = s.authenticate()
            username = auth_data['access']['user']['name']
            pithos_url = self._get_pithos_public_url(auth_data)
            uuid = auth_data['access']['user']['id']
            pithosClient = PithosClient(pithos_url, access_token, uuid)
            resp = pithosClient.list_containers()
        except (AstakosErrors.Unauthorized, faults.InvalidAuth) as e:
            raise faults.InvalidAuth('Pithos-Auth')
        except (AstakosErrors.AstakosClientException, faults.NetworkError) as e:
            raise faults.NetworkError('No internet-Auth')

        return (pithosClient, username)

    def add_and_authenticate(self, key):
        dataManager = LocalDataManager()
        dataManager.set_credentials('Pithos', key)
        return self._pithos_auth()

    def get_flow(self):
        return PithosFlow()
    #end of exposed functions

    def _get_pithos_public_url(self, endpoints, type=u'object-store'):
        r = endpoints[u'access'][u'serviceCatalog']
        for i in r:
            if i[u'type'] == type:
                return i[u'endpoints'][0][u'publicURL']
        return None
