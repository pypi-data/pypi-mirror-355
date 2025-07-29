#!/usr/bin/env python3

# SPDX-License-Identifier: MPL-2.0

import subprocess
import os
import sys
import shutil
import re
import signal
import argparse
import shlex

import opencos
from opencos import util, files
from opencos import eda_config
from opencos import eda_base
from opencos.eda_base import Tool, which_tool

# Globals

debug_respawn = False
util.progname = "EDA"


# ******************************************************************************
# MAIN

# Set config['command_handler'] entries for (command, Class) so we know which
# eda command (such as, command: eda sim) is handled by which class (such as class: CommandSim)
# These are also overriden depending on the tool, for example --tool verilator sets
# "sim": CommandSimVerilator.
def init_config(config: dict,  quiet=False, tool=None) -> dict:
    '''Sets or clears entries in config (dict) so tools can be re-loaded.'''

    from opencos.commands import CommandSim, CommandElab, CommandSynth, \
        CommandFList, CommandProj, CommandMulti, CommandToolsMulti, \
        CommandSweep, CommandBuild, CommandWaves, CommandUpload, CommandOpen, \
        CommandExport

    # If config didn't set the auto_tools_order, then use a fully populated default
    # dict:
    config = eda_config.get_config_merged_with_defaults(config)

    config['command_handler'] = {
        "sim"         : CommandSim,
        "elab"        : CommandElab,
        "synth"       : CommandSynth,
        "flist"       : CommandFList,
        "proj"        : CommandProj,
        "multi"       : CommandMulti,
        "tools-multi" : CommandToolsMulti,
        "sweep"       : CommandSweep,
        "build"       : CommandBuild,
        "waves"       : CommandWaves,
        "upload"      : CommandUpload,
        "open"        : CommandOpen,
        "export"      : CommandExport,
    }

    config['auto_tools_found'] = dict()
    config['tools_loaded'] = set()
    config = auto_tool_setup(config=config, quiet=quiet, tool=tool)
    return config




def usage(tokens: list, config: dict, command=""):
    '''Returns an int shell return code, given remaining args (tokens list) and eda command.

    config is the config dict. Used to check valid commands in config['command_handler']

    Note that we pass the command (str) if possible, so things like:
     > eda help sim --tool verilator
    Will still return this message. This allows args like --config-yml=<file> to work with
    the help message if command is blank, such as:
     > eda --config-yml=<file> help
    '''

    if command == "":
        print(
"""
Usage:
    eda [<options>] <command> [options] <files|targets, ...>

Where <command> is one of:

    sim          - Simulates a DEPS target
    elab         - Elaborates a DEPS target (sort of sim based LINT)
    synth        - Synthesizes a DEPS target
    flist        - Create dependency from a DEPS target
    proj         - Create a project from a DEPS target for GUI sim/waves/debug
    multi        - Run multiple DEPS targets, serially or in parallel
    tools-multi  - Same as 'multi' but run on all available tools, or specfied using --tools
    sweep        - Sweep one or more arguments across a range, serially or in parallel
    build        - Build for a board, creating a project and running build flow
    waves        - Opens waveform from prior simulation
    upload       - Uploads a finished design into hardware
    open         - Opens a project
    export       - Export files related to a target, tool independent
    help         - This help (without args), or i.e. "eda help sim" for specific help

And <files|targets, ...> is one or more source file or DEPS markup file target,
    such as .v, .sv, .vhd[l], .cpp files, or a target key in a DEPS.[yml|yaml|toml|json].
    Note that you can prefix source files with `sv@`, `v@`, `vhdl@` or `cpp@` to
    force use that file as systemverilog, verilog, vhdl, or C++, respectively.

"""
        )
        eda_base.print_base_help()
        return 0
    elif command in config['command_handler'].keys():
        sco = config['command_handler'][command](config=config) # sub command object
        sco.help(tokens=tokens)
        return util.exit(0)
    else:
        util.info(f"Valid commands are: ")
        for k in sorted(config['command_handler'].keys()):
            util.info(f"   {k:20}")
        return util.error(f"Cannot provide help, don't understand command: '{command}'")

def interactive(config: dict):
    read_file = False
    while True:
        if read_file:
            line = f.readline()
            if line:
                print("%s->%s" % (fname, line), end="")
            else:
                read_file = False
                f.close()
                continue
        else:
            line = input('EDA->')
        m = re.match(r'^([^\#]*)\#.*$', line)
        if m: line = m.group(1)
        tokens = line.split()
        original_args = tokens.copy()
        # NOTE: interactive will not correctly handle --config-yml arg (from eda_config.py),
        # but we should do a best effor to re-parse args from util.py, such as
        # --quiet, --color, --fancy, --logfile, --debug or --debug-level, etc
        _, tokens = util.process_tokens(tokens)
        process_tokens(tokens=tokens, original_args=original_args, config=config, interactive=True)


def auto_tool_setup(warnings:bool=True, config=None, quiet=False, tool=None) -> dict:
    '''Returns an updated config, uses config['auto_tools_order'][0] dict, calls tool_setup(..)

    -- adds items to config['tools_loaded'] set
    -- updates config['command_handler'][command] with a Tool class

    Input arg tool can be in the form (for example):
      tool='verlator', tool='verilator=/path/to/verilator.exe'
      If so, updates config['auto_tools_order'][tool]['exe']
    '''
    import importlib.util

    tool = eda_config.update_config_auto_tool_order_for_tool(
        tool=tool, config=config
    )

    assert 'auto_tools_order' in config
    assert type(config['auto_tools_order']) is list
    assert type(config['auto_tools_order'][0]) is dict

    for name, value in config['auto_tools_order'][0].items():
        if tool and tool != name:
            continue # if called with tool=(some_name), then only load that tool.

        util.debug(f"Checking for ability to run tool: {name}")
        exe = value.get('exe', str())
        if type(exe) is list:
            exe_list = exe
        elif type(exe) is str:
            exe_list = [exe] # make it a list
        else:
            util.error(f'eda.py: config["auto_tools_order"][0] for {name=} {value=} has bad type for {exe=}')
            continue

        has_all_py = True
        requires_py_list = value.get('requires_py', list())
        for pkg in requires_py_list:
            spec = importlib.util.find_spec(pkg)
            if not spec:
                has_all_py = False
                util.debug(f"... No, missing pkg {spec}")

        has_all_env = True
        requires_env_list = value.get('requires_env', list())
        for env in requires_env_list:
            if not os.environ.get(env, ''):
                has_all_env = False
                util.debug(f"... No, missing env {env}")

        has_all_exe = True
        for exe in exe_list:
            assert exe != '', f'{tool=} {value=} value missing "exe" {exe=}'
            p = shutil.which(exe)
            if not p:
                has_all_exe = False
                util.debug(f"... No, missing exe {exe}")

        if has_all_exe:
            requires_cmd_list = value.get('requires_cmd', list())
            for cmd in requires_cmd_list:
                cmd_list = shlex.split(cmd)
                try:
                    proc = subprocess.run(cmd_list, capture_output=True, input=b'exit\n\n')
                    if proc.returncode != 0:
                        if not quiet:
                            util.debug(f"For tool {name} missing required command ({proc.returncode=}): {cmd_list=}")
                        has_all_exe = False
                except:
                    has_all_exe = False
                    util.debug(f"... No, exception running {cmd_list}")


        if all([has_all_py, has_all_env, has_all_exe]):
            exe = exe_list[0]
            p = shutil.which(exe)
            config['auto_tools_found'][name] = exe # populate key-value pairs w/ first exe in list
            if not quiet:
                util.info(f"Detected {name} ({p}), auto-setting up tool {name}")
            tool_setup(tool=name, quiet=True, auto_setup=True, warnings=warnings, config=config)

    return config


def tool_setup(tool: str, config: dict, quiet: bool = False, auto_setup: bool = False,
               warnings: bool = True):
    ''' Adds items to config["tools_loaded"] (set) and updates config['command_handler'].

    config is potentially updated for entry ['command_handler'][command] with a Tool class.

    Input arg tool can be in the form (for example):
      tool='verlator', tool='verilator=/path/to/verilator.exe'

    '''
    import importlib

    tool = eda_config.update_config_auto_tool_order_for_tool(
        tool=tool, config=config
    )

    if not quiet and not auto_setup:
        util.info(f"Setup for tool: '{tool}'")

    if not tool:
        return

    if tool not in config['auto_tools_order'][0]:
        tools = list(config.get('auto_tools_order', [{}])[0].keys())
        cfg_yaml_fname = config.get('config-yml', None)
        util.error(f"Don't know how to run tool_setup({tool=}), is not in",
                   f"config['auto_tools_order'] for {tools=}",
                   f"from {cfg_yaml_fname}")
        return

    if tool not in config['auto_tools_found']:
        cfg_yaml_fname = config.get('config-yml', None)
        util.error(f"Don't know how to run tool_setup({tool=}), is not in",
                   f"{config['auto_tools_found']=} from {cfg_yaml_fname}")
        return

    if auto_setup and tool is not None and tool in config['tools_loaded']:
        # Do I realy need to warn if a tool was loaded from auto_tool_setup(),
        # but then I also called it via --tool verilator? Only warn if auto_setup=True:
        if warnings:
            util.warning(f"tool_setup: {auto_setup=} already setup for {tool}?")

    entry = config['auto_tools_order'][0].get(tool, dict())
    tool_cmd_handler_dict = entry.get('handlers', dict())

    for command, str_class_name in tool_cmd_handler_dict.items():
        current_handler_cls = config['command_handler'].get(command, None)
        ext_mod = None

        if auto_setup and current_handler_cls is not None and issubclass(current_handler_cls, Tool):
            # If we're not in auto_setup, then always override (aka arg --tool=<this tool>)
            # skip, already has a tool associated with it, and we're in auto_setup=True
            continue

        if str_class_name not in globals():
            cls = util.import_class_from_string(str_class_name)
        else:
            cls = globals().get(str_class_name, None)

        assert issubclass(cls, Tool), f'{str_class_name=} is does not have Tool class associated with it'
        util.debug(f'Setting {cls=} for {command=} in config.command_handler')
        config['command_handler'][command] = cls

    config['tools_loaded'].add(tool)


def process_tokens(tokens: list, original_args: list, config: dict, interactive=False):
    # this is the top level token processing function.  tokens can come from command line, setup file, or interactively.
    # we do one pass through all the tokens, triaging them into:
    # - those we can execute immediate (help, quit, and global opens like --debug, --color)
    # - a command (sim, synth, etc)
    # - command arguments (--seed, +define, +incdir, etc) which will be deferred and processed by the command

    deferred_tokens = []
    command = ""

    parser = eda_base.get_argparser()
    try:
        parsed, unparsed = parser.parse_known_args(tokens + [''])
        unparsed = list(filter(None, unparsed))
    except argparse.ArgumentError:
        return util.error(f'problem attempting to parse_known_args for {tokens=}')

    config['tool'] = parsed.tool

    # We support a few way of handling quit, exit, or --quit, --exit, -q
    if parsed.quit or parsed.exit or 'exit' in unparsed or 'quit' in unparsed:
        return util.exit(0)
    if parsed.help or 'help' in unparsed:
        if 'help' in unparsed:
            # We'll figure out the command first before applying help, so
            # usage(tokens, config, command) doesn't have a custom argparser guessing.
            unparsed.remove('help')
            parsed.help = True
    if parsed.eda_safe:
        eda_config.update_config_for_eda_safe(config)

    if not interactive:
        # Run init_config() now, we deferred it in main(), but only run it
        # for this tool (or tool=None to figure it out)
        config = init_config(config, tool=parsed.tool)
        if not config:
            util.error(f'eda.py main: problem loading config, {args=}')
            return 3


    util.debug(f'eda process_tokens: {parsed=} {unparsed=}')
    for value in unparsed:
        if value in config['command_handler'].keys():
            command = value
            unparsed.remove(value)
            break

    # Deal with help, now that we have the command (if it was set).
    if parsed.help:
        if not command:
            # if we didn't find the command in config['command_handler'], and
            # since we're entering help anyway (will exit) set command to the
            # first unparsed word looking arg:
            for arg in unparsed:
                if not arg.startswith('-'):
                    command = arg
        return usage(tokens=unparsed, config=config, command=command)

    if parsed.tool:
        tool_setup(parsed.tool, config=config)

    deferred_tokens = unparsed
    if command == "":
        util.error("Didn't get a command!")
        return 1

    sco = config['command_handler'][command](config=config) # sub command object
    util.debug(f'{command=}')
    util.debug(f'{sco.config=}')
    util.debug(f'{type(sco)=}')
    if not parsed.tool and command not in config.get('command_determines_tool', []):
        use_tool = which_tool(command, config)
        util.info(f"--tool not specified, using default for {command=}: {use_tool}")

    rc = check_command_handler_cls(command_obj=sco, command=command, parsed_args=parsed)
    if rc > 0:
        util.debug(f'Return from main process_tokens({tokens=}), {rc=}, {type(sco)=},'
                   f'unparsed={deferred_tokens}')
        return rc

    # Add the original, nothing-parsed args to the Command.config dict.
    sco.config['eda_original_args'] = original_args

    setattr(sco, 'command_name', command) # as a safeguard, b/c 'command' is not always passed to 'sco'
    unparsed = sco.process_tokens(deferred_tokens)

    # query the status from the Command object (0 is pass, > 0 is fail)
    rc = getattr(sco, 'status', 1)
    util.debug(f'Return from main process_tokens({tokens=}), {rc=}, {type(sco)=}, {unparsed=}')
    return rc


def check_command_handler_cls(command_obj:object, command:str, parsed_args) -> int:
    sco = command_obj
    for cls in getattr(sco, 'CHECK_REQUIRES', []):
        if not isinstance(sco, cls):
            # If someone set --tool verilator for command=synth, then our 'sco' will have defaulted
            # to CommandSynth with no tool attached. If we don't have a tool set, error and return.
            util.warning(f"{command=} is using handling class '{type(sco)}' (but missing",
                         f"requirement {cls}, likely because we aren't using a derived class",
                         "for a specific tool)")
            parsed_tool = getattr(parsed_args, 'tool', '??')
            return util.error(f"EDA {command=} for tool '{parsed_tool}' is not",
                              f"supported (this tool '{parsed_tool}' cannot run {command=})")
    return 0


# **************************************************************
# **** Interrupt Handler

def signal_handler(sig, frame):
    util.fancy_stop()
    util.info('Received Ctrl+C...', start='\nINFO: [EDA] ')
    util.exit(-1)

# **************************************************************
# **** Startup Code


def main(*args):
    ''' Returns return code (int), entry point for calling eda.main(*list) directly in py code'''

    args = list(args)
    if len(args) == 0:
        # If not one passed args, then use sys.argv:
        args = sys.argv[1:]

    original_args = args.copy() # save before any parsing.

    # Set global --debug, --quiet, --color  early before parsing other args:
    util_parsed, unparsed = util.process_tokens(args)

    util.debug(f"main: file: {os.path.realpath(__file__)}")
    util.debug(f"main: args: {args=}")

    if util_parsed.version:
        # Do not consider parsed.quiet, print the version and exit:
        print(f'eda {opencos.__version__} ({opencos.__pyproject_name__})')
        sys.exit(0)

    if not util.args['quiet']:
        util.info(f'eda: version {opencos.__version__}')

    # Handle --config-yml= arg
    config, unparsed = eda_config.get_eda_config(unparsed)


    # Note - we used to call: config = init_config(config=config)
    # However, we now defer calling init_config(..) until eda.process_tokens(..)

    util.info("*** OpenCOS EDA ***")

    if len(args) == 0 or (len(args) == 1 and '--debug' in args):
        # special snowflake case if someone called with a singular arg --debug
        # (without --help or exit)
        util.debug(f"Starting automatic tool setup: init_config()")
        config = init_config(config=config)
        if not config:
            util.error(f'eda.py main: problem loading config, {args=}')
            return 3
        return interactive(config=config)
    else:
        return process_tokens(tokens=list(unparsed), original_args=original_args,
                              config=config)


def main_cli(support_respawn=False):
    ''' Returns None, will exit with return code. Entry point for package script or __main__.'''

    if support_respawn and '--no-respawn' not in sys.argv:
        # If someone called eda.py directly (aka, __name__ == '__main__'),
        # then we still support a legacy mode of operation - where we check
        # for OC_ROOT (in env, or git repo) to make sure this is the right
        # location of eda.py by calling main_cli(support_respawn=True).
        # Otherwise, we do not respawn $OC_ROOT/bin/eda.py
        # Can also be avoided with --no-respawn.

        # Note - respawn will never work if calling as a package executable script,
        # which is why our package entrypoint will be main_cli() w/out support_respawn.
        main_maybe_respawn()


    signal.signal(signal.SIGINT, signal_handler)
    util.global_exit_allowed = True
    # Strip eda or eda.py from sys.argv, we know who we are if called from __main__:
    rc = main()
    util.exit(rc)


def main_maybe_respawn():
    ''' Returns None, will respawn - run - exit, or will return and the command

    is expected to run in main_cli()'''

    # First we check if we are respawning
    this_path = os.path.realpath(__file__)
    if debug_respawn: util.info(f"RESPAWN: this_path : '{this_path}'")
    oc_root = util.get_oc_root()
    if debug_respawn: util.info(f"RESPAWN: oc_root   : '{oc_root}'")
    cwd = util.getcwd()
    if debug_respawn: util.info(f"RESPAWN: cwd       : '{cwd}'")
    if oc_root:
        new_paths = [
            os.path.join(oc_root, 'opencos', 'eda.py'),
            os.path.join(oc_root, 'bin', 'eda'),
        ]
        if debug_respawn: util.info(f"RESPAWN: {new_paths=} {this_path=}")
        if this_path not in new_paths and os.path.exists(new_paths[0]):
            # we are not the correct version of EDA for this Git repo, we should respawn
            util.info(f"{this_path} respawning {new_paths[0]} in {cwd} with --no-respawn")
            sys.argv[0] = new_paths[0]
            sys.argv.insert(1, '--no-respawn')
            proc = subprocess.Popen(sys.argv, shell=0, cwd=cwd, universal_newlines=True)
            while True:
                try:
                    proc.communicate()
                    break
                except KeyboardInterrupt:
                    continue
            # get exit status from proc and return it
            util.exit(proc.returncode, quiet=True)
        else:
            if debug_respawn: util.info(f"RESPAWN: {oc_root=} respawn not necessary")
    else:
        if debug_respawn: util.info("RESPAWN: respawn not necessary")


if __name__ == '__main__':
    main_cli(support_respawn=True)

# IDEAS:
# * options with no default (i.e. if user doesn't override, THEN we set it, like "seed" or "work-dir") can be given a
#   special type (DefaultVar) versus saying "None" so that help can say more about it (it's a string, it's default val
#   is X, etc) and it can be queried as to whether it's really a default val.  This avoids having to avoid default vals
#   that user can never set (-1, None, etc) which make it hard to infer the type.  this same object can be given help
#   info and simply "render" to the expected type (str, integer, etc) when used.
