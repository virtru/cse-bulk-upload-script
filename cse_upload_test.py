import io
import mimetypes
import pathlib
from cse_driver import CseDriver
from cse_encrypter import CseEncrypter
from cse_idp import CseIdp
from cse_util import *
from cse_wrapper import CseWrapper

def upload(input, parent_id, filename, authn, driver):
  # TODO: Input parameters
  encrypter = CseEncrypter()
  wrapper = CseWrapper()
  content_type = mimetypes.guess_type(input)[ 0 ]
  cse_token = driver.generate_cse_token(parent_id)
  jwt = cse_token[ 'jwt' ]
  file_id = cse_token[ 'fileId' ]
  kacls_id = cse_token[ 'currentKaclsId' ]
  jwt_payload = driver.get_jwt_payload(jwt)
  resource_name = jwt_payload[ 'resource_name' ]
  kacls_url = jwt_payload[ 'kacls_url' ]
  perimeter_id = jwt_payload.get( 'perimeter_id' , '' )
  outp = io.BytesIO()
  with open ( input , 'rb' ) as inp:
    encrypter.encrypt(inp, outp)
  key = encrypter.get_key()
  wdek = wrapper.privileged_wrap(key, resource_name, authn, kacls_url, perimeter_id)
  resource_key_hash = wrapper.resource_key_hash(key, resource_name)
  encryption_details = driver.new_encryption_details(kacls_id, b64urlencode(wdek.encode()), b64urlencode(resource_key_hash.encode()))
  data_fp = outp
  file = driver.cse_upload(data_fp,
    file_id,
    filename,
    encryption_details,
    parent_id,
    content_type)

  outp.close()
  print ( 'Uploaded: ' + file[ 'id' ])