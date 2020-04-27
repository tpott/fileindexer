# filelist.py
# Trevor Pottinger
# Sun Apr 26 14:26:49 PDT 2020

import argparse
import hashlib
import os
import sys
from typing import (List, NewType)

# TODO make this an enum
HashFunc = NewType('HashFunc', str)
Hex = NewType('Hex', str)


def hashFile(path: str, func: HashFunc) -> Hex:
  hasher = hashlib.new(str(func))
  with open(path, 'rb') as f:
    # TODO chunk this better
    hasher.update(f.read())
  return Hex(hasher.hexdigest())


def run(root_dir: str, funcs: List[HashFunc], verbose: int) -> None:
  header = ['path', 'file_name', 'file_size']
  for func in funcs:
    header.append(str(func))
  print("\t".join(header))
  # TODO wrap this in a func that returns a List and apply multiprocessing
  for root, _, files in os.walk(root_dir):
    for file_name in files:
      path = os.path.join(root, file_name)
      try:
        file_size = os.stat(path).st_size
      except FileNotFoundError:
        # Possibly a broken symbolic link
        if verbose > 0:
          print('Failed to read file %s' % path, file=sys.stderr)
        continue
      row = [root, file_name, str(file_size)]
      for func in funcs:
        row.append(str(hashFile(path, func)))
      print("\t".join(row))


def main() -> None:
  parser = argparse.ArgumentParser('Prints a list of files to stdout')
  parser.add_argument('root_dir', help='The root directory to scan')
  parser.add_argument('-v', '--verbose', action='count', default=0)
  parser.add_argument('--md5', action='store_true', help='Print the MD5 of the file content')
  parser.add_argument('--sha1', action='store_true', help='Print the SHA1 of the file content')
  parser.add_argument('--sha256', action='store_true', help='Print the SHA256 of the file content')
  args = parser.parse_args()
  funcs = []
  if args.md5:
    funcs.append(HashFunc('md5'))
  if args.sha1:
    funcs.append(HashFunc('sha1'))
  if args.sha256:
    funcs.append(HashFunc('sha256'))
  run(args.root_dir, funcs, args.verbose)


if __name__ == '__main__':
  main()
