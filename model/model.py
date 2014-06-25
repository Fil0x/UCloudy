import sys
if ".." not in sys.path:
    sys.path.append("..")

from lib.Upload import UploadQueue
from lib.Authentication import AuthManager


class Model(object):
    def __init__(self):
        self.uq = UploadQueue()
        self.am = AuthManager()
