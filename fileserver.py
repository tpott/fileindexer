# fileserver.py
# Trevor Pottinger
# Sun Apr 26 16:06:00 PDT 2020

import argparse
import hashlib
import http.server
import os
import socketserver
import ssl


# __enter__ and __exit__ is necessary to use the below syntax of `with Server(..) as ..`
class TCPServer(socketserver.TCPServer):
  def __enter__(self):
    return self

  def __exit__(self, *args):
    self.server_close()

  # Except these methods are to pass info to MyHandler without recomputing it
  def setFileDict(self, file_dict):
    self.file_dict = file_dict

  def getFileDict(self):
    return self.file_dict


class MyHandler(http.server.SimpleHTTPRequestHandler):
  # self.RequestHandlerClass(request, client_address, self)
  # This gets called on every request before `.handle()`
  #def __init__(self, *args, **kwargs):
    #super().__init__(*args, **kwargs)
  def setup(self):
    # self.server gets instantiated in socketserver.StreamRequestHandler
    if type(self.server) != TCPServer:
      return
    self.file_dict = self.server.getFileDict()
    super().setup()

  def unexpectedLen(self, path, expected_len):
    # TODO f-format str
    err = b'Got path len %d, expected %d' % (len(path), expected_len)
    self.send_response(http.server.HTTPStatus.BAD_REQUEST)
    self.send_header('Content-Length', len(err))
    self.end_headers()
    self.wfile.write(err)
    return

  def iAmAlive(self):
    s = b'1-AM-ALIVE'
    self.send_response(http.server.HTTPStatus.OK)
    self.send_header('Content-Length', len(s))
    self.end_headers()
    self.wfile.write(s)
    return

  def fileNotFound(self, path):
    err = b'File not found'
    self.send_response(http.server.HTTPStatus.NOT_FOUND)
    self.send_header('Content-Length', len(err))
    self.end_headers()
    self.wfile.write(err)
    return

  def differentFileSize(path, local_path, current_size, expected_size):
    # TODO include more debugging info?
    err = b'File has changed sizes'
    self.send_response(http.server.HTTPStatus.INTERNAL_SERVER_ERROR)
    self.send_header('Content-Length', len(err))
    self.end_headers()
    self.wfile.write(err)
    return

  def differentFileContent(path, local_path, hex_digest):
    # TODO include more debugging info?
    err = b'File content has changed'
    self.send_response(http.server.HTTPStatus.INTERNAL_SERVER_ERROR)
    self.send_header('Content-Length', len(err))
    self.end_headers()
    self.wfile.write(err)
    return

  def do_GET(self):
    path = self.path[1:]  # drop the leading forward slash
    expected_len = self.file_dict['expected_hex_len']
    if path == 'status':
      self.iAmAlive()
    if len(path) != expected_len:
      self.unexpectedLen(path, expected_len)
      return
    if path not in self.file_dict['files']:
      self.fileNotFound(path)
      return
    expected_size, local_path = self.file_dict['files'][path]
    current_size = os.stat(local_path).st_size
    if current_size != expected_size:
      self.differentFileSize(path, local_path, current_size, expected_size)
      return
    file_data = None
    with open(local_path, 'rb') as f:
      # TODO load the data in chunks. only validate the hash at the end.
      file_data = f.read()
    if len(file_data) != current_size:
      self.differentFileSize(path, local_path, len(file_data), current_size)
      return
    # TODO pass the hash func in through file_dict
    hasher = hashlib.new('md5')
    hasher.update(file_data)
    hex_digest = hasher.hexdigest()
    if hex_digest != path:
      self.differentFileContent(path, local_path, hex_digest)
      return
    self.send_response(http.server.HTTPStatus.OK)
    # TODO Other potentially good headers: Content-type, Last-Modified
    self.send_header('Content-Length', current_size)
    self.end_headers()
    # TODO use shutil.copyfileobj
    self.wfile.write(file_data)


def main() -> None:
  parser = argparse.ArgumentParser('Simple webserver')
  parser.add_argument('file_list', help='TSV list of files')
  args = parser.parse_args()

  expected_len = None
  # TODO define a dataclass
  # TODO pass the hash func in through file_dict
  files = {}  # type: Dict[str, Union[int, Dict[Hex, Tuple[Count, str]]]]
  # TODO parse args.file_list
  headers = None
  with open(args.file_list, 'rb') as f:
    for line in f:
      cols = list(map(
        lambda x: x.decode('utf-8'),
        line.rstrip(b'\n').split(b'\t')
      ))
      if headers is None:
        assert len(cols) == 4, 'Expected: path, file_name, file_size, some_hash'
        assert cols[0] == 'path'
        assert cols[1] == 'file_name'
        assert cols[2] == 'file_size'
        # TODO import FileHash from filelist.py
        assert cols[3] in ['md5', 'sha1', 'sha256']
        headers = cols
        continue
      if expected_len is None:
        expected_len = len(cols[3])
      else:
        # TODO f-format str
        assert len(cols[3]) == expected_len, 'Got hash len %d, expected %d' % (len(cols[3]), expected_len)
      files[cols[3]] = (int(cols[2]), os.path.join(cols[0], cols[1]))

  # TODO f-format str
  assert expected_len is not None, 'Didn\'t process any files from %s' % args.file_list

  PORT = 8000
  # This avoids "Address already in use" errors while testing
  TCPServer.allow_reuse_address = True
  with TCPServer(('0.0.0.0', PORT), MyHandler) as httpd:
    # TODO define a dataclass
    httpd.setFileDict({'expected_hex_len': expected_len, 'files': files})
    # TODO f-format str
    print('Serving at port:', PORT)
    # Generate a self signed cert by running the following:
    # `openssl req -nodes -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 30`
    # TODO automatically shell out with `os.system()` to create keys when necessary
    httpd.socket = ssl.wrap_socket(
      httpd.socket,
      server_side=True,
      keyfile='key.pem',
      certfile='cert.pem',
      ssl_version=ssl.PROTOCOL_TLSv1_2
    )
    httpd.serve_forever()


if __name__ == '__main__':
  main()
