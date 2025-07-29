# This file is part of Awesome compiler collection.
#
# Copyright (C) 2025 TrollMii
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from . import config
from . import hasher
from . import awcc_fs
import sys
import os
import hashlib



def compile(file, flags=""):
    hash = hasher.getHashOfFile(file)
    if awcc_fs.blob_exists(hash):
        print(f"[FILE:{hash[:8]}] {file} already in blob")
    else:
        os.makedirs(f"./.awcc/blob/objs/{hasher.get_os_arch()}/{hash[:2]}", exist_ok=True)
        os.makedirs(f"./.awcc/blob/srcs/{hasher.get_os_arch()}/{hash[:2]}", exist_ok=True)
        
        print(f"[FILE:{hash[:8]}] {file} -> awcc:{hash}")
        config.exec_compiler(file, awcc_fs.blob_getfile(hash), flags)
        config.exec_copy(file, f'./.awcc/blob/srcs/{hasher.get_os_arch()}/{hash[:2]}/{hash[2:]}.blob')

        awcc_fs.register_file(file, "C", hash)
    return hash

def link(hashes: list, flags="", ld="clang"):
    fhash = hashlib.sha1("".join([awcc_fs.short_to_long_hash(i) for i in hashes]).encode("utf-8")).hexdigest()
    if awcc_fs.blob_exists(fhash):
        print(f"[LINK:{fhash[:8]}] already in blob")
    else: 
        os.makedirs(f"./.awcc/blob/objs/{hasher.get_os_arch()}/{fhash[:2]}", exist_ok=True)
        print(f"[LINK:{fhash[:8]}] -> awcc:{fhash}")
        input = []
        for h in hashes:
            if len(h) < 40:
                h = awcc_fs.short_to_long_hash(h)
            input.append(awcc_fs.blob_getfile(h))
        input = " ".join(input)

        config.exec_linker(input, awcc_fs.blob_getfile(fhash), flags)
        awcc_fs.register_file("", "LINKED", fhash)
    return hash

    
