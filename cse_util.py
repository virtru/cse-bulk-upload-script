#
# cse_util.py
#
import base64
# Returns a base64-encoded string of the data bytes
def b64encode(data):
  return base64.b64encode(data).decode()
# Returns a url-base64-encoded string of the data bytes
def b64urlencode(data):
  return base64.b64encode(data, altchars=b'-_' ).decode()
# Returns a raw-url-base64-encoded string of the data bytes
def b64rawurlencode(data):
  return b64urlencode(data).rstrip( '=' )
# Returns a base64-decoded string of the data bytes
def b64decode(data):
  return base64.b64decode(data).decode()
# Returns a url-base64-decoded string of the data bytes
def b64urldecode(data):
  return base64.b64decode(data, altchars=b'-_' ).decode()
# Returns a raw-url-base64-decoded string of the data bytes
def b64rawurldecode(data):
  return b64urldecode(data + '===' )