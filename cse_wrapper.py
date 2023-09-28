import hashlib
import hmac
import requests
from cse_util import *
class CseWrapper( object ):
  PRIV_WRAP = '/privilegedwrap'
  def __init__(self):
    pass
# Returns a base64-encoded wrapped_key computed by the KACLS
  def privileged_wrap(self, key, resource_name, authn, kacls_url, perimeter_id= '' ):
    wrap_url = kacls_url + self.PRIV_WRAP
    request = {
    'key' : b64encode(key),
    'resource_name' : resource_name,
    'perimeter_id' : perimeter_id,
    'authentication' : authn,
    'reason' : 'test import'
    }
    r = requests.post(wrap_url, json=request)
    if r.status_code != requests.codes.ok:
      raise Exception( 'Wrap failed: ' + r.text)
    response = r.json()
    return response[ 'wrapped_key' ]
# Returns a locally-computed base64-encoded resource_key_hash
  def resource_key_hash(self, key, resource_name):
    perimeter_id = ""
    data = f'ResourceKeyDigest:{resource_name}:{perimeter_id}' .encode()
    hash = hmac.digest(key, data, hashlib.sha256)
    return b64encode( hash )