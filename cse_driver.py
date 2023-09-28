from apiclient.http import HttpRequest
from apiclient.model import JsonModel
from email.encoders import encode_noop
from email.generator import BytesGenerator
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from google.oauth2 import service_account
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.http import MediaIoBaseUpload
from urllib.parse import urlencode
import google
import httplib2
import io
import json

class CseDriver( object ):
  GOOGLEAPIS_URL = 'https://www.googleapis.com'
  DRIVE_API_VERSION = 'v3beta'
  DRIVE_FILES = f'drive/{DRIVE_API_VERSION}/files'
  FILES_METADATA_URL = f'{GOOGLEAPIS_URL}/{DRIVE_FILES}'
  FILES_UPLOAD_URL = f'{GOOGLEAPIS_URL}/upload/{DRIVE_FILES}'
  ENCRYPTED_MIME_TYPE_PREFIX = 'application/vnd.google-gsuite.encrypted'
  OCTET_STREAM = 'application/octet-stream'
  HEADERS = {
    'accept' : 'application/json',
    'accept-encoding' : 'gzip, deflate',
    'user-agent' : '(gzip)',
  }
  PARAMS = {
    'alt' : 'json' ,
    'supportsTeamDrives' : 'true'
  }
  SCOPES = ['https://www.googleapis.com/auth/drive']
  def __init__(self, sa_key_file):
    self._sa_key_file = sa_key_file
    self._creds = service_account.Credentials.from_service_account_file(self._sa_key_file, scopes=self.SCOPES)
    self._model = JsonModel()
    self._http = httplib2.Http()
    self._delegated_user_email = None
  def set_delegated_user(self, user_email):
    self._delegated_user_email = user_email
  def generate_cse_token(self, parent_id= None ):
    if not self._delegated_user_email:
      raise Exception('Delegated user email not set')
    creds = self._creds.with_subject(self._delegated_user_email)
    authorized_http = AuthorizedHttp(creds, http=self._http)
    params = self._new_params({'role' : 'writer'})
    if parent_id:
      params['parentId'] = parent_id
    url = f'{self.FILES_METADATA_URL}/generateCseToken?{urlencode(params)}'
    headers = self._new_headers({})
    request = HttpRequest(
      http=authorized_http,
      postproc=self._model.response,
      uri=url,
      method='GET',
      body= None,
      headers=headers,
      methodId='drive.files.generateCseToken')
    response = request.execute()
    return response
# Uploads the data as a CSE document; return the file metadata as a dict
  def cse_upload(self, data_fp, file_id, filename, encryption_details, parent_id, content_type):
    if not self._delegated_user_email:
      raise Exception('Delegated user email not set')
    creds = self._creds.with_subject(self._delegated_user_email)
    authorized_http = AuthorizedHttp(creds, http=self._http)
    params = self._new_params({'uploadType' : 'multipart'})
    url = f'{self.FILES_UPLOAD_URL}?{urlencode(params)}'
    file_metadata = {
      'id' : file_id,
      'title' : filename,
      'filename' : filename,
      'mimeType' : self._get_cse_mime_type(content_type),
      'clientEncryptionDetails' : encryption_details,
    }

    if 'v3' in self.DRIVE_API_VERSION:
      file_metadata['name'] = filename
    if parent_id:
      file_metadata['parents'] = [parent_id]
      
    msgRoot = self._build_media_upload_message(file_metadata, data_fp)
    body = self._get_message_body(msgRoot)
    boundary = msgRoot.get_boundary()
    
    type = f'multipart/related; boundary=\"{boundary}\"'
    headers = self._new_headers({'content-type': type })
    request = HttpRequest(
      http=authorized_http,
      postproc=self._model.response,
      uri=url,
      method='POST',
      body=body,
      headers=headers,
      methodId='drive.files.insert')
    response = request.execute()
    return response
# Returns the payload part of a given jwt, as a dict
  def get_jwt_payload(self, jwt):
    return google.auth.jwt.decode(token=jwt, verify=False)
# Returns new encryption-details, as a dict
  def new_encryption_details(self, kacls_id, wdek, resource_key_hash):
    decryption_metadata = {
    'wrappedKey' : wdek,
    'kaclsId' : kacls_id,
    'aes256GcmChunkSize' : 'default',
    'keyFormat' : 'tinkAesGcmKey',
    'encryptionResourceKeyHash' : resource_key_hash,
    }
    return {
    'encryptionState' : 'encrypted',
    'decryption_metadata' : decryption_metadata
    }
  def _new_params(self, more_params):
    params = self.PARAMS.copy()
    params.update(more_params)
    return params
  
  def _new_headers(self, more_headers):
    headers = self.HEADERS.copy()
    headers.update(more_headers)
    return headers
  
  def _get_cse_mime_type(self, content_type = None ):
    if not content_type:
      content_type = self.OCTET_STREAM
    return f'{self.ENCRYPTED_MIME_TYPE_PREFIX}; content=\"{content_type}\"'
  
  def _build_media_upload_message(self, file_metadata, data_fp):
  # multipart/related upload
    msgRoot = MIMEMultipart('related')
    setattr(msgRoot, '_write_headers', lambda self: None)
  # 1st part: metadata
    msg = MIMENonMultipart('application', 'json')
    msg.set_payload(json.dumps(file_metadata))
    msgRoot.attach(msg)
  # 2nd part: data
    media_upload = MediaIoBaseUpload(fd=data_fp, mimetype=self.OCTET_STREAM)
    payload = media_upload.getbytes(0, media_upload.size())
    msg = MIMEApplication(_data=payload, _encoder=encode_noop)
    msg['Content-Transfer-Encoding'] = 'binary'
    filename = file_metadata['filename']
    msg['Content-Disposition'] = f'form-data; name="upload"; filename="{filename}"'
    msgRoot.attach(msg)
    return msgRoot
  def _get_message_body(self, msgRoot):
    # encode the body: note that we can' t use `as_string`, because
    # it plays games with `From ` lines.
    fp = io.BytesIO()
    g = _BytesGenerator(fp, mangle_from_=False)
    g.flatten(msgRoot, unixfrom=False)
    body = fp.getvalue()
    return body
class _BytesGenerator(BytesGenerator):
  _write_lines = BytesGenerator.write