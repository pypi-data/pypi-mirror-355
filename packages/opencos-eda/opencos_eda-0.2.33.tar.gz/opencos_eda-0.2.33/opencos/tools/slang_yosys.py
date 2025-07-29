''' opencos.tools.slang_yosys - classes for: eda [synth|elab] --tool=slang_yosys

Contains classes for ToolSlangYosys, CommandSynthSlangYosys
'''

# pylint: disable=R0801 # (duplicate code in derived classes, such as if-condition return.)

import os

from opencos import util
from opencos.commands import CommandSynth
from opencos.tools.yosys import ToolYosys

class ToolSlangYosys(ToolYosys):
    '''Uses slang.so in yosys plugins directory, called via yosys > plugin -i slang'''
    _TOOL = 'slang_yosys'
    _URL = [
        'https://github.com/povik/yosys-slang',
        'https://github.com/The-OpenROAD-Project/OpenSTA',
        'https://yosyshq.readthedocs.io/en/latest/',
        'https://github.com/MikePopoloski/slang',
    ]

    def set_tool_defines(self):
        super().set_tool_defines()
        self.defines.update({
            'OC_TOOL_SLANG': None,
        })


class CommandSynthSlangYosys(CommandSynth, ToolSlangYosys):
    '''CommandSynthSlangYosys is a command handler for: eda synth --tool=slang_yosys'''

    def __init__(self, config: dict):
        CommandSynth.__init__(self, config)
        ToolSlangYosys.__init__(self, config=self.config)
        self.args.update({
            'sta': False,
            'liberty-file': '',
            'sdc-file': '',
            'yosys-synth': 'synth',       # synth_xilinx, synth_altera, etc (see: yosys help)
            'yosys-pre-synth': ['prep', 'proc'], # command run in yosys prior to yosys-synth.
            'yosys-blackbox': [],                # list of modules that yosys will blackbox.
        })
        self.args_help.update({
            'sta': 'After running Yosys, run "sta" with --liberty-file.' \
            + ' sta can be installed via: https://github.com/The-OpenROAD-Project/OpenSTA',
            'sdc-file': '.sdc file to use with --sta, if not present will use auto constraints',
            'liberty-file': 'Single liberty file for synthesis and sta,' \
            + ' for example: github/OpenSTA/examples/nangate45_slow.lib.gz',
            'yosys-synth': 'The synth command provided to Yosys, see: yosys help.',
            'yosys-pre-synth': 'Yosys commands performed prior to running "synth"' \
            + ' (or eda arg value for --yosys-synth)',
            'yosys-blackbox': 'List of modules that yosys will blackbox, likely will need these' \
            + ' in Verilog-2001 for yosys to read outside of slang and synth',
        })

        self.slang_out_dir = ''
        self.yosys_out_dir = ''
        self.slang_v_path = ''
        self.yosys_v_path = ''
        self.full_work_dir = ''
        self.blackbox_list = []

    def do_it(self) -> None:
        CommandSynth.do_it(self)

        if self.is_export_enabled():
            return

        self._write_and_run_yosys_f_files()

    def _write_and_run_yosys_f_files(self):
        '''
        1. Creates and runs: yosys.slang.f
           -- should create post_slang_ls.txt
        2. python will examine this .txt file and compare to our blackbox_list (modules)
        3. Creates and runs: yosys.synth.f
           -- does blackboxing and synth steps
        4. Creates a wrapper for human debug and reuse: yosys.f
        '''

        # Note - big assumption here that "module myname" is contained in myname.[v|sv]:
        # we use both synth-blackbox and yosys-blackbox lists to blackbox modules in the
        # yosys step (not in the slang step)
        self.blackbox_list = self.args.get('yosys-blackbox', [])
        self.blackbox_list += self.args.get('synth-blackbox', [])
        util.debug(f'slang_yosys: {self.blackbox_list=}')

        # create {work_dir} / yosys
        self.full_work_dir = self.args.get('work-dir', '')
        if not self.full_work_dir:
            self.error(f'work_dir={self.full_work_dir} is not set')
        self.full_work_dir = os.path.abspath(self.full_work_dir)
        self.slang_out_dir = os.path.join(self.full_work_dir, 'slang')
        self.yosys_out_dir = os.path.join(self.full_work_dir, 'yosys')
        for p in [self.slang_out_dir, self.yosys_out_dir]:
            util.safe_mkdir(p)

        self.slang_v_path = os.path.join(self.slang_out_dir, f'{self.args["top"]}.v')
        self.yosys_v_path = os.path.join(self.yosys_out_dir, f'{self.args["top"]}.v')


        # Run our created yosys.slang.f script
        # Note - this will always run, even if --stop-before-compile is set.
        slang_command_list = self._create_yosys_slang_f() # util.ShellCommandList

        # Create and run yosys.synth.f
        synth_command_list = self._create_yosys_synth_f() # util.ShellCommandList

        # Optinally create and run a sta.f:
        sta_command_list = self._create_sta_f() # [] or util.ShellCommandList

        # We create a run_yosys.sh wrapping these scripts, but we do not run this one.
        util.write_shell_command_file(
            dirpath=self.args['work-dir'],
            filename='run_yosys.sh',
            command_lists=[
                # Gives us bash commands with tee and pipstatus:
                slang_command_list,
                synth_command_list,
                sta_command_list,
            ],
        )

        # Do not run this if args['stop-before-compile'] is True
        # TODO(drew): I could move this earlier if I ran this whole process out of
        # a side generated .py file, but we need to query things to generate the synth script.
        if self.args.get('stop-before-compile', False):
            return

        # Run the synth commands standalone:
        self.exec(work_dir=self.full_work_dir, command_list=synth_command_list,
                  tee_fpath=synth_command_list.tee_fpath)

        if self.args['sta']:
            self.exec(work_dir=self.full_work_dir, command_list=sta_command_list,
                      tee_fpath=sta_command_list.tee_fpath)

        if self.status == 0:
            util.info(f'yosys: wrote verilog to {self.yosys_v_path}')


    def _get_read_slang_cmd_str(self) -> str:

        read_slang_cmd = [
            'read_slang',
            '--ignore-unknown-modules',
            '--best-effort-hierarchy',
        ]

        for name,value in self.defines.items():
            if not name:
                continue
            if name in ['SIMULATION']:
                continue

            if value is None:
                read_slang_cmd.append(f'--define-macro {name}')
            else:
                read_slang_cmd.append(f'--define-macro {name}={value}')

        # We must define SYNTHESIS for oclib_defines.vh to work correctly.
        if 'SYNTHESIS' not in self.defines:
            read_slang_cmd.append('--define-macro SYNTHESIS')

        for path in self.incdirs:
            read_slang_cmd.append(f'-I {path}')

        for path in self.files_v:
            read_slang_cmd.append(path)

        for path in self.files_sv:
            read_slang_cmd.append(path)

        read_slang_cmd.append(f'--top {self.args["top"]}')
        return ' '.join(read_slang_cmd)


    def _create_yosys_slang_f(self) -> util.ShellCommandList:
        '''Returns the util.ShellCommandList for: yosys --scriptfile yosys.slang.f'''

        script_slang_lines = [
            'plugin -i slang'
        ]

        script_slang_lines += [
            self._get_read_slang_cmd_str(), # one liner.
            # This line does the 'elaborate' step, and saves out a .v to slang_v_path.
            f'write_verilog {self.slang_v_path}',
            # this ls command will dump all the module instances, which we'll need to
            # know for blackboxing later. This is not in bash, this is within slang
            'tee -o post_slang_ls.txt ls',
        ]

        with open(os.path.join(self.full_work_dir, 'yosys.slang.f'), 'w',
                  encoding='utf-8') as f:
            f.write('\n'.join(script_slang_lines))

        # Run our created yosys.slang.f script
        # Note - this will always run, even if --stop-before-compile is set.
        slang_command_list = util.ShellCommandList(
            [self.yosys_exe, '--scriptfile', 'yosys.slang.f'],
            tee_fpath = 'yosys.slang.log'
        )
        self.exec(
            work_dir=self.full_work_dir,
            command_list=slang_command_list,
            tee_fpath=slang_command_list.tee_fpath
        )
        util.info('yosys.slang.f: wrote: ',
                  os.path.join(self.full_work_dir, 'post_slang_ls.txt'))

        # We create a run_slang.sh wrapping these scripts, but we do not run this one.
        util.write_shell_command_file(
            dirpath=self.args['work-dir'],
            filename='run_slang.sh',
            command_lists=[
                # Gives us bash commands with tee and pipstatus:
                slang_command_list,
            ],
        )
        return slang_command_list

    def _get_yosys_blackbox_list(self) -> list:
        '''Based on the results in post_slang_ls.txt, create blackbox commands for

        yosys.synth.f script. Uses self.blackbox_list.
        '''
        yosys_blackbox_list = []
        with open(os.path.join(self.full_work_dir, 'post_slang_ls.txt'),
                  encoding='utf-8') as f:
            # compare these against our blackbox modules:
            for line in f.readlines():
                util.debug(f'post_slang_ls.txt: {line=}')
                if line.startswith('  '):
                    line = line.strip()
                    if len(line.split()) == 1:
                        # line has 1 word and starts with leading spaces:
                        # get the base module if it has parameters, etc:
                        # slang will output something like foo$various_parameters, so the base
                        # module is before the $ in their instance name.
                        base_module = line.split('$')[0]
                        if base_module in self.blackbox_list:
                            # we need the full (stripped whitespace) line
                            yosys_blackbox_list.append(line)
        return yosys_blackbox_list

    def _create_yosys_synth_f(self) -> util.ShellCommandList:
        # Create yosys.synth.f
        yosys_synth_f_path = os.path.join(self.full_work_dir, 'yosys.synth.f')

        # Based on the results in post_slang_ls.txt, create blackbox commands for
        # yosys.synth.f script.
        yosys_blackbox_list = self._get_yosys_blackbox_list()

        synth_command = self.args.get('yosys-synth', 'synth')
        if self.args['flatten-all']:
            synth_command += ' -flatten'

        if self.args['liberty-file'] and not os.path.exists(self.args['liberty-file']):
            self.error(f'--liberty-file={self.args["liberty-file"]} file does not exist')

        with open(yosys_synth_f_path, 'w', encoding='utf-8') as f:
            lines = [
                # Since we exited yosys, we have to re-open the slang .v file
                f'read_verilog -sv -icells {self.slang_v_path}',
            ]

            if self.args['liberty-file']:
                lines.append('read_liberty -lib ' + self.args['liberty-file'])

            for inst in yosys_blackbox_list:
                lines.append('blackbox ' + inst)

            lines += self.args.get('yosys-pre-synth', [])
            lines.append(synth_command)

            # TODO(drew): I need a blackbox flow here? Or a memory_libmap?
            #   --> https://yosyshq.readthedocs.io/projects/yosys/en/latest/cmd/memory_libmap.html
            # TODO(drew): can I run multiple liberty files?
            if self.args['liberty-file']:
                lines += [
                    'dfflibmap -liberty ' + self.args['liberty-file'],
                    #'memory_libmap -lib ' + self.args['liberty-file'], # Has to be unzipped?
                    'abc -liberty  ' + self.args['liberty-file'],
                ]

            lines.append(f'write_verilog {self.yosys_v_path}')
            f.write('\n'.join(lines))

        synth_command_list = util.ShellCommandList(
            [self.yosys_exe, '--scriptfile', 'yosys.synth.f'],
            tee_fpath = 'yosys.synth.log'
        )
        return synth_command_list


    def _create_sta_f(self) -> list:

        if not self.args['sta']:
            return []

        if not self.args['liberty-file']:
            self.error('--sta is set, but need to also set --liberty-file=<file>')

        if self.args['sdc-file']:
            if not os.path.exists(self.args['sdc-file']):
                self.error(f'--sdc-file={self.args["sdc-file"]} file does not exist')

        if not self.sta_exe:
            self.error(f'--sta is set, but "sta" was not found in PATH, see: {self._URL}')

        sta_command_list = util.ShellCommandList(
            [ self.sta_exe, '-no_init', '-exit', 'sta.f' ],
            tee_fpath = 'sta.log'
        )

        # Need to create sta.f:
        if self.args['sdc-file']:
            sdc_path = self.args['sdc-file']
        else:
            # Need to create sdc.f:
            sdc_path = 'sdc.f'
            self._create_sdc_f()

        with open(os.path.join(self.args['work-dir'], 'sta.f'), 'w',
                  encoding='utf-8') as f:
            lines = [
                'read_liberty ' + self.args['liberty-file'],
                'read_verilog ' + self.yosys_v_path,
                'link_design ' + self.args['top'],
                'read_sdc ' + sdc_path,
                'report_checks',
            ]
            f.write('\n'.join(lines))

        return util.ShellCommandList(
            sta_command_list,
            tee_fpath = 'sta.log'
        )


    def _create_sdc_f(self) -> None:
        if self.args['sdc-file']:
            # already exists from args, return b/c nothing to create.
            return

        with open(os.path.join(self.args['work-dir'], 'sdc.f'), 'w',
                  encoding='utf-8') as f:
            clock_name = self.args['clock-name']
            period = self.args['clock-ns']
            name_not_equal_clocks_str = f'NAME !~ "{clock_name}"'
            lines = [
                f'create_clock -add -name {clock_name} -period {period} [get_ports ' \
                + '{' + clock_name + '}];',
                f'set_input_delay -max {self.args["idelay-ns"]} -clock {clock_name}' \
                + ' [get_ports * -filter {DIRECTION == IN && ' \
                + name_not_equal_clocks_str + '}];',
                f'set_output_delay -max {self.args["odelay-ns"]} -clock {clock_name}' \
                + ' [get_ports * -filter {DIRECTION == OUT}];',
            ]
            f.write('\n'.join(lines))


class CommandElabSlangYosys(CommandSynthSlangYosys):
    '''CommandSynthSlangYosys is a command handler for: eda synth --tool=slang_yosys

    Runs slang-yosys as elab only (does not run the synthesis portion), but is
    run with SIMULATION not defined, SYNTHESIS defined.
    '''
    def __init__(self, config):
        super().__init__(config)
        self.command_name = 'elab'
        self.args.update({
            'stop-before-compile': True,
            'lint': True
        })
