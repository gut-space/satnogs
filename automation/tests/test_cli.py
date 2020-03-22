import unittest
from subprocess import Popen, PIPE


def run(binfile, params, env = None):
    """Runs file specified as binfile, passes all parameters.
       Returns a pair of returncode, stdout"""
    par = [binfile]
    if params and len(params):
        par += params

    # @todo: set passed env variable, if any
    p = Popen(par, stdout=PIPE)
    output = p.communicate()[0]
    return p.returncode, output.decode("utf-8")

def check_output(output: str, strings):
    """Checks if specified output (presumably stdout) has appropriate content. strings
       is a list of strings that are expected to be present. They're expected
       to appear in the specified order, but there may be other things
       printed in between them. Will assert if string is not found. Returns number
       of found strings."""
    offset = 0
    cnt = 0
    for s in strings:
        new_offset = output.find(s, offset)

        if (new_offset == -1):
            assert False, "Not found an expected string: '%s'" % s

        cnt += 1
    return cnt

def check_command(bin, params, exp_code = 0, exp_strings = []):
    """Runs specified command (bin) with parameters (params) and expected
       the return code to be exp_code. """

    # Run the command
    result = run(bin, params)

    assert result[0] == exp_code

    if (len(exp_strings)):
        check_output(result[1], exp_strings)

def test_cli_exec():
    """Checks if the cli.py file is there and is executable."""
    import os
    assert os.access("cli.py", os.X_OK)

def test_cli_help():
    exp = [ "usage: satnogs-gut [-h] {clear,logs,plan,pass,config}",
            "positional arguments:",
            "{clear,logs,plan,pass,config}",
            "clear               Clear all schedule receiving",
            "logs                Show logs",
            "plan                Schedule planning receiving",
            "pass                Information about passes",
            "config              Configuration",
            "-h, --help            show this help message and exit"
    ]
    exp_code = 0

    check_command("./cli.py", None, exp_code, exp)
