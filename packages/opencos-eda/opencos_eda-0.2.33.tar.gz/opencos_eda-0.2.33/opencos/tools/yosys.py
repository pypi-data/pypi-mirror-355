''' opencos.tools.yosys - base class for slang_yosys.py, invio_yosys.py, tabbycad_yosys.py

Contains classes for ToolYosys
'''

# pylint: disable=R0801 # (calling functions with same arguments)

import shutil
import subprocess

from opencos import util
from opencos.eda_base import Tool
from opencos.commands import CommandSynth

class ToolYosys(Tool):
    '''Parent class for ToolTabbyCadYosys, ToolInvioYosys, ToolSlangYosys'''

    _TOOL = 'yosys'
    _EXE = 'yosys'
    _URL = 'https://yosyshq.readthedocs.io/en/latest/'

    yosys_exe = ''
    sta_exe = ''
    sta_version = ''

    def get_versions(self) -> str:
        if self._VERSION:
            return self._VERSION

        path = shutil.which(self._EXE)
        if not path:
            self.error(f'"{self._EXE}" not in path or not installed, see {self._URL}')
        else:
            self.yosys_exe = path

        # Unforunately we don't have a non-PATH friendly support on self._EXE to set
        # where standalone 'sta' is. Even though Yosys has 'sta' internally, Yosys does
        # not fully support timing constraints or .sdc files, so we have to run 'sta'
        # standalone.
        sta_path = shutil.which('sta')
        if sta_path:
            util.debug(f'Also located "sta" via {sta_path}')
            self.sta_exe = sta_path
            sta_version_ret = subprocess.run(
                [self.sta_exe, '-version'], capture_output=True, check=False
            )
            util.debug(f'{self.yosys_exe} {sta_version_ret=}')
            sta_ver = sta_version_ret.stdout.decode('utf-8').split()[0]
            if sta_ver:
                self.sta_version = sta_ver

        version_ret = subprocess.run(
            [self.yosys_exe, '--version'], capture_output=True, check=False
        )
        util.debug(f'{self.yosys_exe} {version_ret=}')

        # Yosys 0.48 (git sha1 aaa534749, clang++ 14.0.0-1ubuntu1.1 -fPIC -O3)
        words = version_ret.stdout.decode('utf-8').split()

        if len(words) < 2:
            self.error(f'{self.yosys_exe} --version: returned unexpected str {version_ret=}')
        self._VERSION = words[1]
        return self._VERSION

    def set_tool_defines(self):
        self.defines.update({
            'OC_TOOL_YOSYS': None
        })
        if 'OC_LIBRARY' not in self.defines:
            self.defines.update({
                'OC_LIBRARY_BEHAVIORAL': None,
                'OC_LIBRARY': "0"
            })


class CommonSynthYosys(CommandSynth, ToolYosys):
    '''Common parent class used by invio_yosys and tabbycad_yosys

    for child classes: CommandSynthInvioYosys and tabbycad_yosys.CommandSynthTabbyCadYosys
    '''

    def __init__(self, config:dict):
        CommandSynth.__init__(self, config=config)
        ToolYosys.__init__(self, config=self.config)

        self.args.update({
            'yosys-synth': 'synth',              # synth_xilinx, synth_altera, etc (see: yosys help)
            'yosys-pre-synth': ['prep', 'proc'], # command run in yosys prior to yosys-synth.
            'yosys-blackbox': [],                # list of modules that yosys will blackbox.
        })

    def do_it(self) -> None:
        self.set_tool_defines()
        self.write_eda_config_and_args()

        if self.is_export_enabled():
            self.do_export()
            return

        self.write_and_run_yosys_f_files()

    def write_and_run_yosys_f_files(self, **kwargs) -> None:
        '''Derived classes must define, to run remainder of do_it() steps'''
        raise NotImplementedError
