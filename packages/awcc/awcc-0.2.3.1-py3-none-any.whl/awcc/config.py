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
import json
import os
config = {
    'version': '0.1',
    'compiler': 'gcc -c {{file}} -o {{output}} {{flags}}',
    'linker': 'gcc {{input}} -o {{output}} {{flags}}',
    "copy": "cp {{src}} {{dest}}"
}
if os.path.exists('.awcc/config.json'):
    with open('.awcc/config.json', 'r') as f:
        _config = json.load(f)
        if _config['version'] != None:
            config['version'] = _config["version"]
        if _config['linker'] != None:
            config['linker'] = _config["linker"]
        if _config['compiler'] != None:
            config['compiler'] = _config["compiler"]
        if _config['copy'] != None:
            config['copy'] = _config["copy"]
        
COMPILER_USAGE: str = config['compiler']
LINKER_USAGE: str = config['linker']
COPY_USAGE: str = config['copy']

def exec_compiler(input, output, flags):
    os.system(COMPILER_USAGE.replace("{{input}}", input).replace("{{output}}", output).replace("{{flags}}", flags))

def exec_linker(input, output, flags):
    os.system(LINKER_USAGE.replace('{{output}}', output).replace('{{flags}}', flags).replace('{{input}}', input))

def exec_copy(src, dest):
    os.system(COPY_USAGE.replace('{{src}}', src).replace('{{dest}}', dest))