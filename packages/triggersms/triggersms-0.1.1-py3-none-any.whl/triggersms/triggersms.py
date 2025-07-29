# Tested working in:
# Python 3.7.3
# Python 2.7.16
# Python 2.6.6
import sys
import json

try:
        # python3
        from urllib.request import Request
        from urllib.request import urlopen
        from urllib.error import HTTPError
        from urllib.error import URLError
except ImportError:
        # python2
        from urllib2 import Request
        from urllib2 import urlopen
        from urllib2 import HTTPError
        from urllib2 import URLError

try:
        # python3
        from json.decoder import JSONDecodeError
except:
        # python2
        JSONDecodeError = ValueError

def hello():
        print("Hello, World!")

if __name__ == "__main__":
        hello()