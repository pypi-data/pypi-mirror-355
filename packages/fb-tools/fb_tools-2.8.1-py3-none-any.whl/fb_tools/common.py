#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for common used functions.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""

# Standard modules
import datetime
import ipaddress
import locale
import logging
import os
import platform
import pprint
import random
import re
import string
import sys
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

try:
    from collections.abc import Sequence
except ImportError:
    from collections import Sequence

# Third party modules
import six

# Own modules
from .errors import InvalidTimeIntervalError
from .xlate import XLATOR

__version__ = '2.1.1'

_ = XLATOR.gettext

LOG = logging.getLogger(__name__)

RE_YES = re.compile(r'^\s*(?:y(?:es)?|true)\s*$', re.IGNORECASE)
RE_NO = re.compile(r'^\s*(?:no?|false|off)\s*$', re.IGNORECASE)
PAT_TO_BOOL_TRUE = locale.nl_langinfo(locale.YESEXPR)
RE_TO_BOOL_TRUE = re.compile(PAT_TO_BOOL_TRUE)
PAT_TO_BOOL_FALSE = locale.nl_langinfo(locale.NOEXPR)
RE_TO_BOOL_FALSE = re.compile(PAT_TO_BOOL_FALSE)

RE_DOT = re.compile(r'\.')
RE_DOT_AT_END = re.compile(r'(\.)*$')
RE_DECIMAL = re.compile(r'^\d+$')
RE_IPV4_PTR = re.compile(r'\.in-addr\.arpa\.$', re.IGNORECASE)
RE_IPV6_PTR = re.compile(r'\.ip6\.arpa\.$', re.IGNORECASE)

RE_MAC_ADRESS = re.compile(r'^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$', re.IGNORECASE)

RE_TF_NAME = re.compile(r'[^a-z0-9_]+', re.IGNORECASE)

RE_FQDN = re.compile(
    r'(?=^.{4,253}$)(^((?!-)[a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,63}\.?$)',
    re.IGNORECASE)

RE_FIRST_LINE = re.compile(r'^([^\n]*)(\r?\n)')

CUR_RADIX = locale.nl_langinfo(locale.RADIXCHAR)
CUR_THOUSEP = locale.nl_langinfo(locale.THOUSEP)
H2MB_PAT = r'^\s*\+?(\d+(?:' + re.escape(CUR_THOUSEP) + r'\d+)*(?:'
H2MB_PAT += re.escape(CUR_RADIX) + r'\d*)?)\s*(\S+)?'
H2MB_RE = re.compile(H2MB_PAT)
RADIX_RE = re.compile(re.escape(CUR_RADIX))
THOUSEP_RE = re.compile(re.escape(CUR_THOUSEP))

RE_B2H_FINAL_ZEROES = re.compile(r'0+$')
RE_B2H_FINAL_SIGNS = re.compile(r'\D+$')

RE_UNIT_BYTES = re.compile(r'^\s*(?:b(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_KBYTES = re.compile(r'^\s*k(?:[bB](?:[Yy][Tt][Ee])?)?\s*$')
RE_UNIT_KIBYTES = re.compile(r'^\s*K[Ii]?(?:[bB](?:[Yy][Tt][Ee])?)?\s*$')
RE_UNIT_MBYTES = re.compile(r'^\s*M(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_MIBYTES = re.compile(r'^\s*Mi(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_GBYTES = re.compile(r'^\s*G(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_GIBYTES = re.compile(r'^\s*Gi(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_TBYTES = re.compile(r'^\s*T(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_TIBYTES = re.compile(r'^\s*Ti(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_PBYTES = re.compile(r'^\s*P(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_PIBYTES = re.compile(r'^\s*Pi(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_EBYTES = re.compile(r'^\s*E(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_EIBYTES = re.compile(r'^\s*Ei(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_ZBYTES = re.compile(r'^\s*Z(?:B(?:yte)?)?\s*$', re.IGNORECASE)
RE_UNIT_ZIBYTES = re.compile(r'^\s*Zi(?:B(?:yte)?)?\s*$', re.IGNORECASE)

DEBUG_TIMEINTERVAL2DELTA = False

RE_UNIT_TIME_SECOND = re.compile(
    r'\s*(\d+(?:\.\d*)?)\s*(?:s(?:ec(?:onds?)?)?)?(?:\s*,)?', re.IGNORECASE)
RE_UNIT_TIME_MINUTE = re.compile(
    r'\s*(\d+(?:\.\d*)?)\s*m(?:in(?:utes?)?)?(?:\s*,)?', re.IGNORECASE)
RE_UNIT_TIME_HOUR = re.compile(r'\s*(\d+(?:\.\d*)?)\s*h(?:ours?)?(?:\s*,)?', re.IGNORECASE)
RE_UNIT_TIME_DAY = re.compile(r'\s*(\d+(?:\.\d*)?)\s*d(?:ays?)?(?:\s*,)?', re.IGNORECASE)
RE_UNIT_TIME_WEEK = re.compile(r'\s*(\d+(?:\.\d*)?)\s*w(?:eeks?)?(?:\s*,)?', re.IGNORECASE)
RE_UNIT_TIME_MONTH = re.compile(r'\s*(\d+(?:\.\d*)?)\s*mon(?:ths?)?(?:\s*,)?', re.IGNORECASE)
RE_UNIT_TIME_YEAR = re.compile(r'\s*(\d+(?:\.\d*)?)\s*y(?:ears?)?(?:\s*,)?', re.IGNORECASE)


# =============================================================================
def pp(value, indent=4, width=99, depth=None):
    """
    Return a pretty print string of the given value.

    @return: pretty print string
    @rtype: str
    """
    pretty_printer = pprint.PrettyPrinter(
        indent=indent, width=width, depth=depth)
    return pretty_printer.pformat(value)


# =============================================================================
def terminal_can_colors(debug=False):
    """
    Detect, whether the current terminal is able to perform ANSI color sequences.

    Both stdout and stderr are checked.

    @return: both stdout and stderr can perform ANSI color sequences
    @rtype: bool

    """
    cur_term = ''
    if 'TERM' in os.environ:
        cur_term = os.environ['TERM'].lower().strip()

    colored_term_list = (
        r'ansi',
        r'linux.*',
        r'screen.*',
        r'[xeak]term.*',
        r'gnome.*',
        r'rxvt.*',
        r'interix',
    )
    term_pattern = r'^(?:' + r'|'.join(colored_term_list) + r')$'
    re_term = re.compile(term_pattern)

    ansi_term = False
    env_term_has_colors = False

    if cur_term:
        if cur_term == 'ansi':
            env_term_has_colors = True
            ansi_term = True
        elif re_term.search(cur_term):
            env_term_has_colors = True
    if debug:
        sys.stderr.write('ansi_term: {a!r}, env_term_has_colors: {h!r}\n'.format(
            a=ansi_term, h=env_term_has_colors))

    has_colors = False
    if env_term_has_colors:
        has_colors = True
    for handle in [sys.stdout, sys.stderr]:
        if (hasattr(handle, 'isatty') and handle.isatty()):
            if debug:
                msg = _('{} is a tty.').format(handle.name)
                sys.stderr.write(msg + '\n')
            if (platform.system() == 'Windows' and not ansi_term):
                if debug:
                    sys.stderr.write(_('Platform is Windows and not ansi_term.') + '\n')
                has_colors = False
        else:
            if debug:
                msg = _('{} is not a tty.').format(handle.name)
                sys.stderr.write(msg + '\n')
            if ansi_term:
                pass
            else:
                has_colors = False

    return has_colors


# =============================================================================
def to_bool(value):
    """Convert from string to boolean values (e.g. from configurations)."""
    if not value:
        return False

    try:
        v_int = int(value)
    except ValueError:
        pass
    except TypeError:
        pass
    else:
        if v_int == 0:
            return False
        else:
            return True

    global PAT_TO_BOOL_TRUE
    global RE_TO_BOOL_TRUE
    global PAT_TO_BOOL_FALSE
    global RE_TO_BOOL_FALSE

    c_yes_expr = locale.nl_langinfo(locale.YESEXPR)
    if c_yes_expr != PAT_TO_BOOL_TRUE:
        PAT_TO_BOOL_TRUE = c_yes_expr
        RE_TO_BOOL_TRUE = re.compile(PAT_TO_BOOL_TRUE)
    # LOG.debug("Current pattern for 'yes': %r.", c_yes_expr)

    c_no_expr = locale.nl_langinfo(locale.NOEXPR)
    if c_no_expr != PAT_TO_BOOL_FALSE:
        PAT_TO_BOOL_FALSE = c_no_expr
        RE_TO_BOOL_FALSE = re.compile(PAT_TO_BOOL_FALSE)
    # LOG.debug("Current pattern for 'no': %r.", c_no_expr)

    v_str = ''
    if isinstance(value, str):
        v_str = value
        if six.PY2:
            if isinstance(value, unicode):                      # noqa
                v_str = value.encode('utf-8')
    elif six.PY3 and isinstance(value, bytes):
        v_str = value.decode('utf-8')
    else:
        v_str = str(value)

    match = RE_YES.search(v_str)
    if match:
        return True
    match = RE_TO_BOOL_TRUE.search(v_str)
    if match:
        return True

    match = RE_NO.search(v_str)
    if match:
        return False
    match = RE_TO_BOOL_FALSE.search(v_str)
    if match:
        return False

    return bool(value)


# =============================================================================
def is_general_string(value):
    """Return, whether the given value is a common string."""
    if isinstance(value, six.string_types):
        return True

    if isinstance(value, six.binary_type):
        return True

    return False


# =============================================================================
def to_unicode(obj, encoding='utf-8'):
    """Convert given value to unicode."""
    do_decode = False
    if six.PY2:
        if isinstance(obj, str):
            do_decode = True
    else:
        if isinstance(obj, (bytes, bytearray)):
            do_decode = True

    if do_decode:
        obj = obj.decode(encoding)

    return obj


# =============================================================================
def to_utf8(obj):
    """Convert given value to a utf-8 encoded byte string."""
    return encode_or_bust(obj, 'utf-8')


# =============================================================================
def encode_or_bust(obj, encoding='utf-8'):
    """Convert given value to a byte string withe the given encoding."""
    do_encode = False
    if six.PY2:
        if isinstance(obj, unicode):                            # noqa
            do_encode = True
    else:
        if isinstance(obj, str):
            do_encode = True

    if do_encode:
        obj = obj.encode(encoding)

    return obj


# =============================================================================
def to_bytes(obj, encoding='utf-8'):
    """Do the same as encode_or_bust()."""
    return encode_or_bust(obj, encoding)


# =============================================================================
def to_str(obj, encoding='utf-8'):
    """Transform he given string-like object into the str-type.

    This will be done according to the current Python version.
    """
    if six.PY2:
        return encode_or_bust(obj, encoding)
    else:
        return to_unicode(obj, encoding)


# =============================================================================
def is_sequence(arg):
    """Return, whether the given value is a sequential object, but nat a str."""
    if not isinstance(arg, Sequence):
        return False

    if hasattr(arg, 'strip'):
        return False

    return True


# =============================================================================
def caller_search_path(*additional_paths):
    """Build a search path for executables.

    Builds a search path for executables from environment $PATH
    including some standard paths.

    @return: all existing search paths
    @rtype: list
    """
    path_list = []
    search_path = os.environ['PATH']
    if not search_path:
        search_path = os.defpath

    search_path_list = [
        pathlib.Path('/opt/pixelpark/bin'),
        pathlib.Path('/www/bin'),
        pathlib.Path('/opt/PPlocal/bin'),
        pathlib.Path('/opt/puppetlabs/bin'),
        pathlib.Path('/opt/puppetlabs/puppet/bin'),
    ]

    for d in additional_paths:
        p = pathlib.Path(d)
        if p not in search_path_list:
            search_path_list.append(p)

    for d in search_path.split(os.pathsep):
        p = pathlib.Path(d)
        if p not in search_path_list:
            search_path_list.append(p)

    default_path = [
        '/bin',
        '/usr/bin',
        '/usr/local/bin',
        '/sbin',
        '/usr/sbin',
        '/usr/local/sbin',
        '/usr/ucb',
        '/usr/sfw/bin',
        '/opt/csw/bin',
        '/usr/openwin/bin',
        '/usr/ccs/bin',
    ]

    for d in default_path:
        p = pathlib.Path(d)
        if p not in search_path_list:
            search_path_list.append(p)

    for d in search_path_list:
        if not d.exists():
            continue
        if not d.is_dir():
            continue
        d_abs = d.resolve()
        if d_abs not in path_list:
            path_list.append(d_abs)

    return path_list


# =============================================================================
def compare_fqdn(x, y):
    """Compare FQDN-like objects."""
    # LOG.debug("Comparing {!r} <=> {!r}.".format(x, y))

    # First check for None values
    if x is None and y is None:
        return 0
    if x is None:
        return -1
    if y is None:
        return 1

    # Check for empty FQDNs
    xs = str(x).strip().lower()
    ys = str(y).strip().lower()

    if xs == '' and ys == '':
        return 0
    if xs == '':
        return -1
    if ys == '':
        return 1

    # Ensure a dot at end
    xs = RE_DOT_AT_END.sub('.', xs)
    ys = RE_DOT_AT_END.sub('.', ys)

    if xs == ys:
        return 0

    # Reverse IPv4 zones first, then reverse IPv6 zones
    if RE_IPV4_PTR.search(xs):
        if not RE_IPV4_PTR.search(ys):
            return -1
    elif RE_IPV4_PTR.search(ys):
        if not RE_IPV4_PTR.search(xs):
            return 1
    elif RE_IPV6_PTR.search(xs):
        if not RE_IPV6_PTR.search(ys):
            return -1
    elif RE_IPV6_PTR.search(ys):
        if not RE_IPV6_PTR.search(xs):
            return 1

    return compare_fqdn_tokens(xs, ys)


# =============================================================================
def compare_fqdn_tokens(xs, ys):
    """Compare tokens from FQDN-like objects."""
    xa = RE_DOT.split(xs)
    xa.reverse()
    xa.pop(0)

    ya = RE_DOT.split(ys)
    ya.reverse()
    ya.pop(0)

    # Compare token from the last to the first
    nr_tokens = min(len(xa), len(ya))
    while nr_tokens > 0:
        token_x = xa.pop(0)
        token_y = ya.pop(0)
        if RE_DECIMAL.match(token_x) and RE_DECIMAL.match(token_y):
            num_x = int(token_x)
            num_y = int(token_y)
            if num_x < num_y:
                return -1
            elif num_x > num_y:
                return 1
        else:
            if token_x < token_y:
                return -1
            elif token_x > token_y:
                return 1
        nr_tokens -= 1

    if len(xa):
        return 1
    if len(ya):
        return -1

    return 0


# =============================================================================
def compare_ldap_values(first, second):
    """Compare objects, which are originated as values of LDAP entries."""
    def _to_str_single(value):

        if is_sequence(value):
            if is_general_string(value[0]):
                return to_str(value[0]).lower()
            return str(value[0]).lower()
        if is_general_string(value):
            return to_str(value).lower()
        return str(value).lower()

    if is_sequence(first) and not is_sequence(second):
        if len(first) == 1:
            str_first = _to_str_single(first)
            str_second = _to_str_single(second)
            if str_first == str_second:
                return True
        return False

    if is_sequence(second) and not is_sequence(first):
        if len(second) == 1:
            str_first = _to_str_single(first)
            str_second = _to_str_single(second)
            if str_first == str_second:
                return True
        return False

    if not is_sequence(first):
        # second is also not an array at this point
        str_first = _to_str_single(first)
        str_second = _to_str_single(second)
        if str_first == str_second:
            return True
        return False

    # Both parameters are arays
    if len(first) != len(second):
        return False
    first_array = []
    for val in first:
        first_array.append(_to_str_single(val))
    first_array.sort()
    second_array = []
    for val in second:
        second_array.append(_to_str_single(val))
    second_array.sort()

    if first_array == second_array:
        return True
    return False


# =============================================================================
def human2mbytes(value, si_conform=False, as_float=False):
    """
    Convert the given human readable byte value (e.g. 5MB, 8.4GiB etc.).

    The could have with a prefix into an integer/float value (without a prefix) of MiBiBytes.
    It raises a ValueError on invalid values.

    Available prefixes are:
        - kB (1000), KB (1024), KiB (1024)
        - MB (1000*1000), MiB (1024*1024)
        - GB (1000^3), GiB (1024^3)
        - TB (1000^4), TiB (1024^4)
        - PB (1000^5), PiB (1024^5)
        - EB (1000^6), EiB (1024^6)
        - ZB (1000^7), ZiB (1024^7)

    @raise ValueError: on an invalid value

    @param value: the value to convert
    @type value: str
    @param si_conform: use factor 1000 instead of 1024 for kB a.s.o.
    @type si_conform: bool
    @param as_float: flag to gives back the value as a float value
                     instead of an integer value
    @type as_float: bool

    @return: amount of MibiBytes
    @rtype:  int or float

    """
    if value is None:
        msg = _('Given value is {!r}.').format(None)
        raise ValueError(msg)

    radix = '.'
    radix = re.escape(radix)

    c_radix = locale.nl_langinfo(locale.RADIXCHAR)
    global CUR_RADIX
    global H2MB_PAT
    global H2MB_RE
    global RADIX_RE
    global CUR_THOUSEP
    global THOUSEP_RE

    c_thousep = locale.nl_langinfo(locale.THOUSEP)
    if c_thousep != CUR_THOUSEP:
        CUR_THOUSEP = c_thousep
        # log.debug("Current separator character for thousands is now %r.",
        #         CUR_THOUSEP)
        THOUSEP_RE = re.compile(re.escape(CUR_THOUSEP))

    if c_radix != CUR_RADIX:
        CUR_RADIX = c_radix
        # log.debug("Current decimal radix is now %r.", CUR_RADIX)
        H2MB_PAT = r'^\s*\+?(\d+(?:' + re.escape(CUR_RADIX) + r'\d*)?)\s*(\S+)?'
        if CUR_THOUSEP:
            H2MB_PAT = r'^\s*\+?(\d+(?:' + re.escape(CUR_THOUSEP) + r'\d+)*(?:'
            H2MB_PAT += re.escape(CUR_RADIX) + r'\d*)?)\s*(\S+)?'
        H2MB_RE = re.compile(H2MB_PAT)
        RADIX_RE = re.compile(re.escape(CUR_RADIX))
    # log.debug("Current pattern: %r", H2MB_PAT)

    value_raw = ''
    unit = None
    match = H2MB_RE.search(value)
    if match is not None:
        value_raw = match.group(1)
        unit = match.group(2)
    else:
        msg = _('Could not determine bytes in {!r}.').format(value)
        raise ValueError(msg)

    if CUR_THOUSEP:
        value_raw = THOUSEP_RE.sub('', value_raw)
    if CUR_RADIX != '.':
        value_raw = RADIX_RE.sub('.', value_raw)
    value_float = float(value_raw)
    if unit is None:
        unit = ''

    factor_bin = 1024
    factor_si = 1000
    if not si_conform:
        factor_si = factor_bin

    # LOG.debug("factor_bin: {b!r}, factor_si: {s!r}".format(b=factor_bin, s=factor_si))

    factor = 1

    final_factor = 1024 * 1024

    while int(value_float) != value_float:
        value_float *= 10
        final_factor *= 10
    value_long = int(value_float)

    factor = _get_factor_human2bytes(unit, factor_bin, factor_si)

    # LOG.debug("Using factor {fa!r}, final factor: {fi!r}.".format(fa=factor, fi=final_factor))
    # LOG.debug("Cur value_long = {!r}.".format(value_long))

    lbytes = factor * value_long
    # LOG.debug("Cur long bytes: {!r}.".format(lbytes))
    mbytes = lbytes / final_factor
    if as_float:
        return float(mbytes)
    if mbytes <= sys.maxsize:
        return int(mbytes)
    return mbytes
    if mbytes != int(mbytes):
        raise ValueError('int {integer!r} != long {long!r}.'.format(
            integer=int(mbytes), long=mbytes))

    mbytes = int(mbytes)

    return mbytes


# =============================================================================
def _get_factor_human2bytes(unit, factor_bin, factor_si):

    factor = 1

    if RE_UNIT_BYTES.search(unit):
        factor = 1
    elif RE_UNIT_KBYTES.search(unit):
        factor = factor_si
    elif RE_UNIT_KIBYTES.search(unit):
        factor = factor_bin
    elif RE_UNIT_MBYTES.search(unit):
        factor = (factor_si * factor_si)
    elif RE_UNIT_MIBYTES.search(unit):
        factor = (factor_bin * factor_bin)
    elif RE_UNIT_GBYTES.search(unit):
        factor = (factor_si ** 3)
    elif RE_UNIT_GIBYTES.search(unit):
        factor = (factor_bin ** 3)
    elif RE_UNIT_TBYTES.search(unit):
        factor = (factor_si ** 4)
    elif RE_UNIT_TIBYTES.search(unit):
        factor = (factor_bin ** 4)
    elif RE_UNIT_PBYTES.search(unit):
        factor = (factor_si ** 5)
    elif RE_UNIT_PIBYTES.search(unit):
        factor = (factor_bin ** 5)
    elif RE_UNIT_EBYTES.search(unit):
        factor = (factor_si ** 6)
    elif RE_UNIT_EIBYTES.search(unit):
        factor = (factor_bin ** 6)
    elif RE_UNIT_ZBYTES.search(unit):
        factor = (factor_si ** 7)
    elif RE_UNIT_ZIBYTES.search(unit):
        factor = (factor_bin ** 7)
    else:
        msg = _("Couldn't detect unit {!r}.").format(unit)
        raise ValueError(msg)

    return factor


# =============================================================================
def bytes2human(
        value, si_conform=False, precision=None, format_str='{value} {unit}'):
    """
    Convert the given value in bytes into a human readable format.

    The limit for electing the next higher prefix is at 1500.

    It raises a ValueError on invalid values.

    @param value: the value to convert
    @type value: long
    @param si_conform: use factor 1000 instead of 1024 for kB a.s.o.,
                       if do so, than the units are for example MB instead MiB.
    @type si_conform: bool
    @param precision: how many digits after the decimal point have to stay
                      in the result
    @type precision: int
    @param format_str: a format string to format the result.
    @type format_str: str

    @return: the value in a human readable format together with the unit
    @rtype: str

    """
    val = int(value)

    if not val:
        return format_str.format(value='0', unit='Bytes')

    base = 1024
    prefixes = {
        1: 'KiB',
        2: 'MiB',
        3: 'GiB',
        4: 'TiB',
        5: 'PiB',
        6: 'EiB',
        7: 'ZiB',
        8: 'YiB',
    }
    if si_conform:
        base = 1000
        prefixes = {
            1: 'kB',
            2: 'MB',
            3: 'GB',
            4: 'TB',
            5: 'PB',
            6: 'EB',
            7: 'ZB',
            8: 'YB',
        }

    exponent = 0

    float_val = float(val)
    while float_val >= (2 * base) and exponent < 8:
        float_val /= base
        exponent += 1

    unit = ''
    if not exponent:
        precision = None
        unit = 'Bytes'
        if val == 1:
            unit = 'Byte'
        value_str = locale.format_string('%d', val)
        return format_str.format(value=value_str, unit=unit)

    unit = prefixes[exponent]
    value_str = ''
    if precision is None:
        value_str = locale.format_string('%f', float_val)
        value_str = RE_B2H_FINAL_ZEROES.sub('', value_str)
        value_str = RE_B2H_FINAL_SIGNS.sub('', value_str)
    else:
        value_str = locale.format_string('%.*f', (precision, float_val))

    if not exponent:
        return value_str

    return format_str.format(value=value_str, unit=unit)


# =============================================================================
def generate_password(length=12):
    """Generate a string of random characters with the givlen length."""
    characters = string.ascii_letters + string.punctuation + string.digits
    password = ''.join(random.choice(characters) for x in range(length))
    return password


# =============================================================================
def get_monday(day):
    """Return the last Monday before the given date.

    If the given date is a Monday itself, then this date will be returned.
    """
    if not isinstance(day, (datetime.date, datetime.datetime)):
        msg = _('Argument {a!r} must be of type {t1!r} or {t2!r}.').format(
            a=day, t1='datetime.date', t2='datetime.datetime')
        raise TypeError(msg)

    # copy of day as datetime.date
    monday = datetime.date(day.year, day.month, day.day)
    # date is Monday => date.weekday() == 0
    if monday.weekday() == 0:
        return monday

    tdiff = datetime.timedelta(monday.weekday())
    monday -= tdiff
    return monday


# =============================================================================
def reverse_pointer(address):
    """Return the tuples or digits of the given IP address in reverse order.

    This is used to build the names of reverse DNS zones.
    """
    addr = ipaddress.ip_address(address)

    if addr.version == 4:
        reverse_octets = str(addr).split('.')[::-1]
        return '.'.join(reverse_octets) + '.in-addr.arpa'
    else:
        reverse_chars = addr.exploded[::-1].replace(':', '')
        return '.'.join(reverse_chars) + '.ip6.arpa'


# =============================================================================
def indent(text, prefix, initial_prefix=None, predicate=None):
    """Add 'prefix' to the beginning of selected lines in 'text'.

    If 'predicate' is provided, 'prefix' will only be added to the lines
    where 'predicate(line)' is True. If 'predicate' is not provided,
    it will default to adding 'prefix' to all non-empty lines that do not
    consist solely of whitespace characters.

    It's a reinventing the wheel - sorry, but in module textwrap of Python 2.7
    this function is not existing.
    """
    if predicate is None:
        def predicate(line):
            return line.strip()

    if initial_prefix is None:
        initial_prefix = prefix

    line_nr = 0
    lines = []
    for line in text.splitlines(True):
        pfx = prefix if line_nr else initial_prefix
        line_nr += 1
        if predicate(line):
            lines.append(pfx + line)
        else:
            lines.append(line)

    return ''.join(lines)

# =============================================================================
def set_debug_timeinterval2delta(enable_debug=False):
    """Set the module property DEBUG_TIMEINTERVAL2DELTA to a boolean value."""
    global DEBUG_TIMEINTERVAL2DELTA

    if to_bool(enable_debug):
        DEBUG_TIMEINTERVAL2DELTA = True
    else:
        DEBUG_TIMEINTERVAL2DELTA = False

# =============================================================================
def timeinterval2delta(interval):
    """
    Try to convert the given textual time interval into a datetime.timeinterval object.

    The interval may consists of tokens of float values with a measurement unit.
    If a token is a float value without a measurement unit, then seconds are assumed.
    Valid measurement units (as regular expressions) are:
    * 's(ec(onds?)?)?'
    * 'm(in(utes?)?)?' == 60 seconds
    * 'h(ours?)*' == 3600 seconds
    * 'd(ays?)?' == 3600 * 24 seconds
    * 'w(eeks?)?' == 3600 * 24 * 7 seconds
    * 'mon(ths?)?' == 3600 * 24 * 30 seconds
    * 'y(ears?)?' == 3600 * 24 * 365 seconds

    @raise InvalidTimeIntervalError: if the interval could not be interpreted
    """
    if interval is None:
        raise InvalidTimeIntervalError(None)
    intrvl = str(interval).strip()
    if intrvl == '':
        raise InvalidTimeIntervalError(interval)

    seconds = 0

    if DEBUG_TIMEINTERVAL2DELTA:
        LOG.debug('Start value: {!r}'.format(intrvl))

    m = RE_UNIT_TIME_YEAR.search(intrvl)
    if m:
        years = float(m[1])
        intrvl = RE_UNIT_TIME_YEAR.sub('', intrvl, 1)
        seconds += years * 3600 * 24 * 365
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After year: match {m!r}, years {y!r}, new value {i!r}, new secs {s}.'.format(
                    m=m[1], y=years, i=intrvl, s=seconds))

    m = RE_UNIT_TIME_MONTH.search(intrvl)
    if m:
        months = float(m[1])
        intrvl = RE_UNIT_TIME_MONTH.sub('', intrvl, 1)
        seconds += months * 3600 * 24 * 30
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After months: match {m!r}, months {mo!r}, new value {i!r}, new secs {s}.'.format(
                    m=m[1], mo=months, i=intrvl, s=seconds))

    m = RE_UNIT_TIME_WEEK.search(intrvl)
    if m:
        weeks = float(m[1])
        intrvl = RE_UNIT_TIME_WEEK.sub('', intrvl, 1)
        seconds += weeks * 3600 * 24 * 7
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After weeks: match {m!r}, weeks {w!r}, new value {i!r}, new secs {s}.'.format(
                    m=m[1], w=weeks, i=intrvl, s=seconds))

    m = RE_UNIT_TIME_DAY.search(intrvl)
    if m:
        days = float(m[1])
        intrvl = RE_UNIT_TIME_DAY.sub('', intrvl, 1)
        seconds += days * 3600 * 24
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After days: match {m!r}, days {d!r}, new value {i!r}, new secs {s}.'.format(
                    m=m[1], d=days, i=intrvl, s=seconds))

    m = RE_UNIT_TIME_HOUR.search(intrvl)
    if m:
        hours = float(m[1])
        intrvl = RE_UNIT_TIME_HOUR.sub('', intrvl, 1)
        seconds += hours * 3600
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After hours: match {m!r}, hours {h!r}, new value {i!r}, new secs {s}.'.format(
                    m=m[1], h=hours, i=intrvl, s=seconds))

    m = RE_UNIT_TIME_MINUTE.search(intrvl)
    if m:
        minutes = float(m[1])
        intrvl = RE_UNIT_TIME_MINUTE.sub('', intrvl, 1)
        seconds += minutes * 60
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After minutes: match {m!r}, minutes {mi!r}, new value {i!r}, '
                'new secs {s}.'.format(m=m[1], mi=minutes, i=intrvl, s=seconds))

    m = RE_UNIT_TIME_SECOND.search(intrvl)
    if m:
        secs = float(m[1])
        intrvl = RE_UNIT_TIME_SECOND.sub('', intrvl, 1)
        seconds += secs
        if DEBUG_TIMEINTERVAL2DELTA:
            LOG.debug(
                'After seconds: match {m!r}, seconds {se!r}, new value {i!r}, '
                'new secs {s}.'.format(m=m[1], se=secs, i=intrvl, s=seconds))

    intrvl = intrvl.strip()
    if DEBUG_TIMEINTERVAL2DELTA:
        LOG.debug('Final value: {i!r}, seconds at last: {s}'.format(i=intrvl, s=seconds))
    if intrvl != '':
        raise InvalidTimeIntervalError(interval)

    return datetime.timedelta(seconds=seconds)


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
