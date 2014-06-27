import sys
if ".." not in sys.path:
    sys.path.append("..")

from lib.Authentication import AuthManager


class Model(object):
    def __init__(self):
        self.am = AuthManager()
