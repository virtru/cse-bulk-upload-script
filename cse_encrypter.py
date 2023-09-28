#
# cse_encrypter.py
#
import tink
from tink import aead
class CseEncrypter( object ):
  SAFE_CHUNK_COUNT_LIMIT = 1 << 30
  PLAINTEXT_CHUNK_SIZE = 2097152 # 2MiB
  MAGIC_HEADER = bytes([ 0x99 , 0x5E , 0xCC , 0x5E ])
  def __init__(self):
    self._buffer_size = self.PLAINTEXT_CHUNK_SIZE
    self._current_chunk_count = 0
    self._key = None
    self._aead = None
  def encrypt(self, plaintext, ciphertext):
    aead.register()
    key_template = aead.aead_key_templates.AES256_GCM_RAW
    keyset_handle = tink.new_keyset_handle(key_template)
    self._key = self._get_key_from_handle(keyset_handle)
    self._aead = keyset_handle.primitive(aead.Aead)
    ciphertext.write(self.MAGIC_HEADER)
    buf = bytearray (self._buffer_size)
    while True:
      n = plaintext.readinto(buf)
      data = self._prefix(buf, n)
      if n < self._buffer_size:
        ciphertext.write(self._update(data, is_last_chunk=True))
        break
      ciphertext.write(self._update(data, is_last_chunk=False))
# Get the key used in last `encrypt` call.
# Base64-encode this before sending to KACLS.
  def get_key(self):
    return self._key
  def _update(self, data, is_last_chunk):
    if self._current_chunk_count + 1 > self.SAFE_CHUNK_COUNT_LIMIT:
      raise Exception( 'Input too large' )
    associated_data = self._get_associated_data(self._current_chunk_count, is_last_chunk)
    chunk = self._aead.encrypt(data, associated_data)
    self._current_chunk_count += 1
    return chunk
  def _get_key_from_handle(self, keyset_handle):
    keyset = keyset_handle._keyset
    key = keyset.key[ 0 ]
    key_data = key.key_data
    return key_data.value
  def _prefix(self, buf, n):
    assert n <= len (buf)
    if n == len (buf):
      return bytes(buf)
    return bytes(buf[ 0 :n])
  def _get_associated_data(self, chunk_index, is_last_chunk):
    data = bytearray (chunk_index.to_bytes( 4 , 'big' ))
    if is_last_chunk:
      data.append( 1 )
    else:
      data.append( 0 )
    return bytes(data)