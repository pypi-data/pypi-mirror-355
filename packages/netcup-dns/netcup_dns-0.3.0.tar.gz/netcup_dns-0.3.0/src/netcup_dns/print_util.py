#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys


# https://www.freedesktop.org/software/systemd/man/latest/sd-daemon.html
#
# define SD_EMERG   "<0>"  /* system is unusable */
# define SD_ALERT   "<1>"  /* action must be taken immediately */
# define SD_CRIT    "<2>"  /* critical conditions */
# define SD_ERR     "<3>"  /* error conditions */
# define SD_WARNING "<4>"  /* warning conditions */
# define SD_NOTICE  "<5>"  /* normal but significant condition */
# define SD_INFO    "<6>"  /* informational */
# define SD_DEBUG   "<7>"  /* debug-level messages */

def print_emerg(message: object):
    do_print('<0> ', message, file=sys.stderr)


def print_alert(message: object):
    do_print('<1> ', message, file=sys.stderr)


def print_crit(message: object):
    do_print('<2> ', message, file=sys.stderr)


def print_err(message: object):
    do_print('<3> ', message, file=sys.stderr)


def print_warning(message: object):
    do_print('<4> ', message, file=sys.stderr)


def print_notice(message: object):
    do_print('<5> ', message)


def print_info(message: object):
    do_print('<6> ', message)


def print_debug(message: object):
    do_print('<7> ', message)


def do_print(line_prefix: str, message: object, file=sys.stdout) -> None:
    # Prefix each line in str(object) with `line_prefix`.
    prefixed = line_prefix + str(message).replace('\n', '\n' + line_prefix)
    print(prefixed, file=file)
