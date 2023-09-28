from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import os
import requests
import google
class CseIdp( object ):
  SCOPES = [ 'openid' , 'email' ]
  def __init__(self, client_secret_file):
    if not os.path.isabs(client_secret_file):
      client_secret_file = os.path.abspath(client_secret_file)
    self._client_secret_file = client_secret_file
    self._creds = None
  def get_authn_token(self):
    self._get_creds()
    return self._creds.id_token
  def _get_creds(self):
    if self._creds and self._creds.valid:
      return
    if self._creds:
      try :
        self._creds.refresh(Request())
        if self._creds.valid:
          return
      except RefreshError:
        pass
# Google Python client library work-around for servers changing scopes
    os.environ[ 'OAUTHLIB_RELAX_TOKEN_SCOPE' ] = 'True'
    flow = InstalledAppFlow.from_client_secrets_file(self._client_secret_file, scopes=self.SCOPES)
    self._creds = flow.run_local_server(open_browser=False, port= 0 )