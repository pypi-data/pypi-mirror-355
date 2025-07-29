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


import hashlib
import os
import platform
import sys

def get_os_arch():
    system = platform.system().lower()
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        arch = "x64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    elif machine in ("i386", "i686", "x86"):
        arch = "x86"
    else:
        arch = machine

    return f"{system}-{arch}"

def getHashOfFile(file):
    return hashlib.sha1((open(file, 'r').read()).replace(" ", "").replace("\n", "").replace("\t", "").encode('utf8')).hexdigest()+"."+get_os_arch()