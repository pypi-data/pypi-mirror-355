#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on common.py.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""

import locale
import logging
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

import six

# Setting the user’s preferred locale settings
locale.setlocale(locale.LC_ALL, '')

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

LOG = logging.getLogger('test_common')


# =============================================================================
class TestFbCommon(FbToolsTestcase):
    """Testcase for unit tests on common.py."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on seting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import module fb_tools.common."""
        LOG.info(self.get_method_doc())

        import fb_tools.common

        LOG.info('Module version of fb_tools.common is {!r}.'.format(
            fb_tools.common.__version__))

    # -------------------------------------------------------------------------
    def test_to_unicode(self):
        """Test module function to_unicode()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import to_unicode

        data = []
        data.append((None, None))
        data.append((1, 1))
        data.append(('a', 'a'))
        data.append((b'a', 'a'))

        for pair in data:

            src = pair[0]
            tgt = pair[1]
            result = to_unicode(src)
            LOG.debug('Testing to_unicode(%r) => %r, result %r', src, tgt, result)

            if isinstance(src, (str, bytes)):
                self.assertIsInstance(result, str)
            else:
                self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_to_utf8(self):
        """Test module function to_utf8()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import to_utf8

        data = []
        data.append((None, None))
        data.append((1, 1))
        data.append(('a', b'a'))
        data.append((b'a', b'a'))

        for pair in data:

            src = pair[0]
            tgt = pair[1]
            result = to_utf8(src)
            LOG.debug('Testing to_utf8(%r) => %r, result %r', src, tgt, result)

            if isinstance(src, (str, bytes)):
                self.assertIsInstance(result, bytes)
            else:
                self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_to_str(self):
        """Test module function to_str()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import to_str

        data = []
        data.append((None, None))
        data.append((1, 1))
        data.append(('a', 'a'))
        data.append((b'a', 'a'))

        for pair in data:

            src = pair[0]
            tgt = pair[1]
            result = to_str(src)
            LOG.debug('Testing to_str(%r) => %r, result %r', src, tgt, result)

            if isinstance(src, (str, bytes)):
                self.assertIsInstance(result, str)
            else:
                self.assertNotIsInstance(result, (str, bytes))

            self.assertEqual(tgt, result)

    # -------------------------------------------------------------------------
    def test_human2mbytes(self):
        """Test module function human2mbytes()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import human2mbytes

        loc = locale.getlocale()    # get current locale
        encoding = loc[1]
        LOG.debug('Current locale is %r.', loc)
        german = ('de_DE', encoding)

        do_switch_locales = True
        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning('Got a {c}: {e}'.format(c=e.__class__.__name__, e=e))
            do_switch_locales = False

        if do_switch_locales:
            LOG.debug('Setting to locale {!r} to be secure.'.format('C'))
            locale.setlocale(locale.LC_ALL, 'C')
            LOG.debug('Current locale is now {!r}.'.format(locale.getlocale()))

        test_pairs_int_si = (
            ('1048576', 1),
            ('1MiB', 1),
            ('1 MiB', 1),
            ('1 MiB', 1),
            (' 1 MiB	', 1),
            ('1.2 MiB', int(1.2)),
            ('1 GiB', 1024),
            ('1 GB', 953),
            ('1.2 GiB', int(1.2 * 1024)),
            ('102400 KB', 100),
            ('100000 KB', 97),
            ('102400 MB', int(1024 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('100000 MB', int(1000 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('102400 MiB', 1024 * 100),
            ('100000 MiB', 1000 * 100),
            ('102400 GB', int(1024 * 1000 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('100000 GB', int(1000 * 1000 * 1000 * 1000 * 100 / 1024 / 1024)),
            ('102400 GiB', 1024 * 1024 * 100),
            ('100000 GiB', 1024 * 1000 * 100),
            ('1024 TB', int(1024 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 TB', int(1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 TiB', 1024 * 1024 * 1024),
            ('1000 TiB', 1024 * 1024 * 1000),
            ('1024 PB', int(1024 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 PB', int(1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 PiB', 1024 * 1024 * 1024 * 1024),
            ('1000 PiB', 1024 * 1024 * 1024 * 1000),
            ('1024 EB', int(1024 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 EB', int(1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 EiB', 1024 * 1024 * 1024 * 1024 * 1024),
            ('1000 EiB', 1024 * 1024 * 1024 * 1024 * 1000),
            ('1024 ZB', int(1024 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1000 ZB', int(1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 * 1000 / 1024 / 1024)),
            ('1024 ZiB', 1024 * 1024 * 1024 * 1024 * 1024 * 1024),
            ('1000 ZiB', 1024 * 1024 * 1024 * 1024 * 1024 * 1000),
        )

        for pair in test_pairs_int_si:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing human2mbytes({src!r}) => {exp!r}'.format(
                    src=src, exp=expected))
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        if do_switch_locales:
            # Switch back to saved locales
            LOG.debug('Switching back to saved locales {!r}.'.format(loc))
            locale.setlocale(locale.LC_ALL, loc)                            # restore saved locale

    # -------------------------------------------------------------------------
    def test_human2mbytes_l10n(self):
        """Testing localisation of human2mbytes()."""
        LOG.info(self.get_method_doc())

        loc = locale.getlocale()                                        # get current locale
        encoding = loc[1]
        LOG.debug('Current locale is {!r}.'.format(loc))
        german = ('de_DE', encoding)

        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning('Got a {c}: {e}'.format(c=e.__class__.__name__, e=e))
            return True

        LOG.debug('Setting to locale {!r} to be secure.'.format('C'))
        locale.setlocale(locale.LC_ALL, 'C')
        LOG.debug('Current locale is now {!r}.'.format(locale.getlocale()))

        from fb_tools.common import human2mbytes

        pairs_en = (
            ('1.2 GiB', int(1.2 * 1024)),
            ('1.2 TiB', int(1.2 * 1024 * 1024)),
        )

        pairs_de = (
            ('1,2 GiB', int(1.2 * 1024)),
            ('1,2 TiB', int(1.2 * 1024 * 1024)),
            ('1.024 MiB', 1024),
            ('1.055,4 GiB', int(10554 * 1024 / 10)),
        )

        LOG.debug('Testing english decimal radix character {!r}.'.format('.'))
        for pair in pairs_en:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing localisation of human2mbytes({src!r}) => {exp!r}'.format(
                    src=src, exp=expected))
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        # Switch to german locales
        LOG.debug('Switching to german locale {!r}.'.format(german))
        # use German locale; name might vary with platform
        locale.setlocale(locale.LC_ALL, german)
        LOG.debug('Current locale is now {!r}.'.format(locale.getlocale()))

        LOG.debug('Testing german decimal radix character {!r}.'.format(','))
        for pair in pairs_de:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing localisation of human2mbytes({src!r}) => {exp!r}'.format(
                    src=src, exp=expected))
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        # Switch back to english locales
        locale.setlocale(locale.LC_ALL, 'C')    # restore saved locale

        LOG.debug('Testing english decimal radix character {!r} again.'.format('.'))
        for pair in pairs_en:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing localisation of human2mbytes({src!r}) => {exp!r}'.format(
                    src=src, exp=expected))
            result = human2mbytes(src, si_conform=True)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, int)
            self.assertEqual(expected, result)

        # Switch back to saved locales
        LOG.debug('Switching back to saved locales {!r}.'.format(loc))
        locale.setlocale(locale.LC_ALL, loc)    # restore saved locale

    # -------------------------------------------------------------------------
    def test_bytes2human(self):
        """Test module function bytes2human()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import bytes2human

        loc = locale.getlocale()    # get current locale
        encoding = loc[1]
        LOG.debug('Current locale is {!r}.'.format(loc))
        german = ('de_DE', encoding)

        do_switch_locales = True
        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning('Got a {c}: {e}'.format(c=e.__class__.__name__, e=e))
            do_switch_locales = False

        if do_switch_locales:
            LOG.debug('Setting to locale {!r} to be secure.'.format('C'))
            locale.setlocale(locale.LC_ALL, 'C')
            LOG.debug('Current locale is now {!r}.'.format(locale.getlocale()))

        test_pairs_no_si = (
            (0, '0 Bytes'),
            (1, '1 Byte'),
            (5, '5 Bytes'),
            (5 * 1024, '5 KiB'),
            (1999 * 1024 * 1024, '1999 MiB'),
            (2047 * 1024 * 1024, '2047 MiB'),
            (2048 * 1024 * 1024, '2 GiB'),
            (2304 * 1024 * 1024, '2.25 GiB'),
        )

        for pair in test_pairs_no_si:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing bytes2human({src!r}) => {exp!r}'.format(src=src, exp=expected))
            result = bytes2human(src)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, str)
            self.assertEqual(expected, result)

        test_pairs_no_si = (
            (0, '0 Bytes'),
            (1, '1 Byte'),
            (5, '5 Bytes'),
            (5 * 1024, '5.00 KiB'),
            (1999 * 1024 * 1024, '1999.00 MiB'),
            (2047 * 1024 * 1024, '2047.00 MiB'),
            (2048 * 1024 * 1024, '2.00 GiB'),
            (2304 * 1024 * 1024, '2.25 GiB'),
        )

        prec = 2

        for pair in test_pairs_no_si:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing bytes2human({src!r}) precission {prec} => {exp!r}'.format(
                    src=src, prec=prec, exp=expected))
            result = bytes2human(src, precision=prec)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, str)
            self.assertEqual(expected, result)

        if do_switch_locales:
            # Switch back to saved locales
            LOG.debug('Switching back to saved locales {!r}.'.format(loc))
            locale.setlocale(locale.LC_ALL, loc)                            # restore saved locale

    # -------------------------------------------------------------------------
    def test_to_bool(self):
        """Test module function to_bool()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import to_bool

        class TestClass(object):

            pass

        test_object = TestClass()

        class TestClassTrue(object):

            if sys.version_info[0] > 2:
                def __bool__(self):
                    return True
            else:
                def __nonzero__(self):
                    return True

        test_object_true = TestClassTrue()

        class TestClassFalse(object):

            if sys.version_info[0] > 2:
                def __bool__(self):
                    return False
            else:
                def __nonzero__(self):
                    return False

        test_object_false = TestClassFalse()

        class TestClassFilled(object):

            def __len__(self):
                return 1

        test_object_filled = TestClassFilled()

        class TestClassEmpty(object):

            def __len__(self):
                return 0

        test_object_empty = TestClassEmpty()

        test_pairs = (
            (None, False),
            (True, True),
            (False, False),
            (0, False),
            (0.0, False),
            (1, True),
            (1.0, True),
            (-1, True),
            ('', False),
            ('yes', True),
            ('YES', True),
            ('Yes', True),
            ('y', True),
            ('no', False),
            ('NO', False),
            ('No', False),
            ('n', False),
            ('true', True),
            ('False', False),
            ('On', True),
            ('Off', False),
            (test_object, True),
            (test_object_true, True),
            (test_object_false, False),
            (test_object_filled, True),
            (test_object_empty, False),
        )

        test_pairs_de = (
            ('ja', True),
            ('JA', True),
            ('Ja', True),
            ('j', True),
            ('nein', False),
            ('NEIN', False),
            ('Nein', False),
            ('n', False),
        )

        for pair in test_pairs:

            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing to_bool({src!r}) => {exp!r}'.format(src=src, exp=expected))
            result = to_bool(src)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, bool)
            self.assertEqual(expected, result)

        # Switch to german locales
        loc = locale.getlocale()                                        # get current locale
        encoding = loc[1]
        LOG.debug('Current locale is {!r}.'.format(loc))
        german = ('de_DE', encoding)
        try:
            locale.setlocale(locale.LC_ALL, german)
        except Exception as e:
            LOG.warning('Got a {c}: {e}'.format(c=e.__class__.__name__, e=e))
            return True

        # use German locale; name might vary with platform
        LOG.debug('Switching to german locale {!r}.'.format(german))
        locale.setlocale(locale.LC_ALL, german)

        LOG.debug('Testing german Yes/No expressions for to_bool().')
        for pair in test_pairs_de:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing localisation of to_bool({src!r}) => {exp!r}'.format(
                    src=src, exp=expected))
            result = to_bool(src)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertIsInstance(result, bool)
            self.assertEqual(expected, result)

        # Switch back to saved locales
        LOG.debug('Switching back to saved locales {!r}.'.format(loc))
        locale.setlocale(locale.LC_ALL, loc)                            # restore saved locale

    # -------------------------------------------------------------------------
    def test_indent(self):
        """Test module function indent()."""
        LOG.info(self.get_method_doc())

        from fb_tools.common import indent

        ind = '  '
        initial_ind = ' '

        LOG.debug('Testing indent() without a separate initial_prefix.')
        test_pairs = (
            ('', ''),
            ('a', ind + 'a'),
            ('\na', '\n' + ind + 'a'),
            ('a\nb', ind + 'a\n' + ind + 'b'),
            ('a\n	b', ind + 'a\n' + ind + '	b'),
            ('a\n\nb', ind + 'a\n\n' + ind + 'b'),
            ('a\n \nb', ind + 'a\n \n' + ind + 'b'),
        )
        for pair in test_pairs:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing indenting {src!r} => {tgt!r}'.format(src=src, tgt=expected))
            result = indent(src, ind)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertEqual(expected, result)

        LOG.debug('Testing indent() with a separate initial_prefix.')
        test_pairs = (
            ('', ''),
            ('a', initial_ind + 'a'),
            ('\na', '\n' + ind + 'a'),
            ('a\nb', initial_ind + 'a\n' + ind + 'b'),
            ('a\n	b', initial_ind + 'a\n' + ind + '	b'),
            ('a\n\nb', initial_ind + 'a\n\n' + ind + 'b'),
            ('a\n \nb', initial_ind + 'a\n \n' + ind + 'b'),
        )
        for pair in test_pairs:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing indenting {src!r} => {tgt!r}'.format(src=src, tgt=expected))
            result = indent(src, ind, initial_prefix=initial_ind)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertEqual(expected, result)

        LOG.debug('Testing indent() with a predicate function.')

        def test_predicate(line):
            if line.strip().startswith('b'):
                return False
            return line.strip()

        test_pairs = (
            ('', ''),
            ('a', ind + 'a'),
            ('\na', '\n' + ind + 'a'),
            ('a\nb', ind + 'a\nb'),
            ('a\nb\nc', ind + 'a\nb\n' + ind + 'c'),
            ('a\n b', ind + 'a\n b'),
            ('a\nB', ind + 'a\n' + ind + 'B'),
            ('a\nba', ind + 'a\nba'),
            ('a\n	b', ind + 'a\n	b'),
            ('a\n\nb', ind + 'a\n\nb'),
            ('a\n\nc', ind + 'a\n\n' + ind + 'c'),
            ('a\n \nb', ind + 'a\n \nb'),
            ('a\n \nc', ind + 'a\n \n' + ind + 'c'),
        )
        for pair in test_pairs:
            src = pair[0]
            expected = pair[1]
            if self.verbose > 1:
                LOG.debug('Testing indenting {src!r} => {tgt!r}'.format(src=src, tgt=expected))
            result = indent(src, ind, predicate=test_predicate)
            if self.verbose > 1:
                LOG.debug('Got result: {!r}'.format(result))
            self.assertEqual(expected, result)

    # -------------------------------------------------------------------------
    def test_compare_ldap_values(self):
        """Test module function compare_ldap_values()."""
        LOG.info(self.get_method_doc())

        if six.PY2:
            bin_a = 'a'
            bin_b = 'b'
            text_a = u'a'
        else:
            bin_a = b'a'
            bin_b = b'b'
            text_a = 'a'

        test_values = (
            (1, 1, True),
            (1, [1], True),
            ([1], 1, True),
            ([1], [1], True),
            ('1', 1, True),
            (' 1', 1, False),
            ('a', 'a', True),
            ('a', 'A', True),
            ('A', 'a', True),
            ('A', 'A', True),
            ('b', 'a', False),
            ('', 'a', False),
            (['a', 'b'], ['a', 'b'], True),
            (['a', 'b'], ['b', 'a'], True),
            (['a'], ['a', 'b'], False),
            (bin_a, text_a, True),
            (bin_a, text_a, True),
            (bin_a, bin_b, False),
            (['{crypt}sICBZoVI7wX0s'], ['{crypt}sICBZoVI7wX0s'], True),
            ('{crypt}sICBZoVI7wX0s', '{crypt}sICBZoVI7wX0s', True),
            ('{crypt}sICBZoVI7wX0s', b'{crypt}sICBZoVI7wX0s', True),
            (['{crypt}sICBZoVI7wX0s'], [b'{crypt}sICBZoVI7wX0s'], True),
            ([b'{crypt}sICBZoVI7wX0s'], [b'{crypt}sICBZoVI7wX0s'], True),
        )

        from fb_tools.common import compare_ldap_values

        for test_tuple in test_values:

            first = test_tuple[0]
            second = test_tuple[1]
            expected = test_tuple[2]
            result = compare_ldap_values(first, second)
            LOG.debug('Compared {f!r} and {s!r}, result: {res} (expected: {ex}).'.format(
                f=first, s=second, res=result, ex=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_timeinterval2delta(self):
        """Test module function timeinterval2delta()."""
        LOG.info(self.get_method_doc())

        from datetime import timedelta
        from fb_tools.common import set_debug_timeinterval2delta
        from fb_tools.common import timeinterval2delta

        if self.verbose > 2:
            set_debug_timeinterval2delta(True)

        test_data_valid = (
            (0, 0),
            ('0', 0),
            (1, 1),
            ('1', 1),
            ('0.1', 0.1),
            ('1s', 1),
            ('1.1 s', 1.1),
            ('5m', 300),
            ('5 m 10s', 310),
            ('10 s 5m', 310),
            ('2h 2', 7202),
            ('2h 3m 2.222', 2 * 3600 + 3 * 60 + 2.222),
            ('12.5 h', 12 * 3600 + 1800),
            ('3d , 13h, 4.5 min', 3 * 24 * 3600 + 13 * 3600 + 270),
            (' 14 days, 2 hours', 14 * 24 * 3600 + 2 * 3600),
            ('2 weeks 2 hours', 14 * 24 * 3600 + 2 * 3600),
            ('3 months 2 days', 3 * 30 * 24 * 3600 + 2 * 24 * 3600),
            ('4 years, 11 months', 4 * 365 * 24 * 3600 + 11 * 30 * 24 * 3600),
        )

        for test_tuple in test_data_valid:
            interval = test_tuple[0]
            seconds = test_tuple[1]
            expected = timedelta(seconds=seconds)
            LOG.debug('Test conversion of {i!r} into timedelta "{delta}" ({s} seconds).'.format(
                i=interval, delta=expected, s=seconds))
            result = timeinterval2delta(interval)
            LOG.debug('Got timedelta "{}".'.format(result))
            self.assertIsInstance(result, timedelta)
            self.assertEqual(result, expected)

        class TestClass(object):
            """Pointless test class without a function."""

            def blub(self):
                """Make nothing - senseless method."""
                return None

        from fb_tools.errors import InvalidTimeIntervalError

        test_object = TestClass()

        test_data_invalid = (
            None, '', ' 	', 'bla', test_object, test_object.blub,
            '2h 2h', '2h,, 4min',
        )

        for test_data in test_data_invalid:
            LOG.debug('Test invalid time interval {!r}.'.format(test_data))

            with self.assertRaises(InvalidTimeIntervalError) as cm:
                result = timeinterval2delta(test_data)
                LOG.error('This result should never be visible: {!r}.'.format(result))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))


# =============================================================================

if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestFbCommon('test_import', verbose))
    suite.addTest(TestFbCommon('test_to_unicode', verbose))
    suite.addTest(TestFbCommon('test_to_utf8', verbose))
    suite.addTest(TestFbCommon('test_to_str', verbose))
    suite.addTest(TestFbCommon('test_human2mbytes', verbose))
    suite.addTest(TestFbCommon('test_human2mbytes_l10n', verbose))
    suite.addTest(TestFbCommon('test_bytes2human', verbose))
    suite.addTest(TestFbCommon('test_to_bool', verbose))
    suite.addTest(TestFbCommon('test_indent', verbose))
    suite.addTest(TestFbCommon('test_compare_ldap_values', verbose))
    suite.addTest(TestFbCommon('test_timeinterval2delta', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 fileencoding=utf-8
