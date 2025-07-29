#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on fb_tools.colcts.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: GPL3
"""

import logging
import os
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from fb_tools.common import pp

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_colcts')


# =============================================================================
class TestFbCollections(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.colcts."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import of fb_tools.colcts."""
        LOG.info('Testing import of fb_tools.colcts ...')
        import fb_tools.colcts
        LOG.debug('Version of fb_tools.colcts: {!r}'.format(fb_tools.colcts.__version__))

    # -------------------------------------------------------------------------
    def test_init_frozenset(self):
        """Test init of a FrozenCIStringSet object."""
        LOG.info('Testing init of a FrozenCIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongItemTypeError

        LOG.debug('Testing init of an empty set.')
        my_set = FrozenCIStringSet()
        LOG.debug('FrozenCIStringSet %r: {!r}'.format(my_set))
        LOG.debug('FrozenCIStringSet %s: {}'.format(my_set))
        self.assertEqual(my_set.as_list(), [])

        src = ('B', 'a')
        expected = {
            '__class_name__': 'FrozenCIStringSet',
            'items': ['a', 'B'],
        }
        LOG.debug('Checking as_dict(), source: {src}, expeced: {ex}.'.format(
            src=src, ex=expected))
        my_set = FrozenCIStringSet(src)
        result = my_set.as_dict()
        LOG.debug('Result of as_dict(): {}'.format(pp(result)))
        self.assertEqual(expected, result)

        LOG.debug('Trying to add add a value to a FrozenCIStringSet ...')
        with self.assertRaises(AttributeError) as cm:
            my_set.add('bla')
        e = cm.exception
        msg = (
            'AttributeError raised on trying to add a value to a '
            'FrozenCIStringSet object: {}').format(e)
        LOG.debug(msg)

        correct_iterables = (
            (('a',), ['a']),
            (['a'], ['a']),
            (['A'], ['A']),
            (['a', 'b'], ['a', 'b']),
            (['a', 'B'], ['a', 'B']),
            (['b', 'a'], ['a', 'b']),
            (['a', 'a'], ['a']),
            (['a', 'A'], ['A']),
            (['A', 'a'], ['a']),
            (FrozenCIStringSet(['a', 'b']), ['a', 'b']),
            (['a', 'b', 'A'], ['A', 'b']),
        )

        for test_tuple in correct_iterables:
            src = test_tuple[0]
            expected = test_tuple[1]
            LOG.debug('Testing init of a FrozenCIStringSet from {!r}.'.format(src))
            my_set = FrozenCIStringSet(src)
            if self.verbose > 2:
                LOG.debug('FrozenCIStringSet %s: {}'.format(my_set))
            result = my_set.as_list()
            LOG.debug('FrozenCIStringSet as a list: {r!r} (expeced: {ex!r})'.format(
                r=result, ex=expected))
            self.assertEqual(result, expected)

        class Tobj(object):

            def uhu(self):
                return 'banane'

        tobj = Tobj()

        wrong_iterables = (
            'a', 1, {'uhu': 'banane'}, tobj, tobj.uhu)

        for obj in wrong_iterables:

            msg = 'Trying to init a FrozenCIStringSet from {!r} ...'
            LOG.debug(msg.format(obj))
            with self.assertRaises(TypeError) as cm:
                my_set = FrozenCIStringSet(obj)
            e = cm.exception
            msg = ('TypeError raised on init of a FrozenCIStringSet object: {}').format(e)
            LOG.debug(msg)

        iterables_with_wrong_values = (
            [None], [1], ['a', 1], [{'uhu': 'banane'}], [tobj], [tobj.uhu])

        for obj in iterables_with_wrong_values:

            msg = 'Trying to init a FrozenCIStringSet from {!r} ...'
            LOG.debug(msg.format(obj))
            with self.assertRaises(WrongItemTypeError) as cm:
                my_set = FrozenCIStringSet(obj)
            e = cm.exception
            msg = ('WrongItemTypeError raised on init of a FrozenCIStringSet object: {}').format(e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozenset_real_value(self):
        """Test method real_value() of a FrozenCIStringSet object."""
        LOG.info('Testing method real_value() of a FrozenCIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongItemTypeError

        test_tuples = (
            (['A'], 'a', 'A'),
            (['A'], 'A', 'A'),
            (['a'], 'a', 'a'),
            (['a'], 'A', 'a'),
        )

        LOG.debug('Testing real_value() with correct parameters.')
        for test_tuple in test_tuples:
            src = test_tuple[0]
            key = test_tuple[1]
            expected = test_tuple[2]
            my_set = FrozenCIStringSet(src)

            if self.verbose > 2:
                LOG.debug('Testing to get the real value of {v!r} of {s}.'.format(v=key, s=my_set))
            result = my_set.real_value(key)
            if self.verbose > 2:
                LOG.debug('Got {res!r} - expected {ex!r}.'.format(res=result, ex=expected))

            self.assertEqual(result, expected)

        my_set = FrozenCIStringSet(['A', 'b'])

        LOG.debug('Testing real_value() with a parameter of an incorrect type.')
        with self.assertRaises(WrongItemTypeError) as cm:
            value = my_set.real_value(1)
            LOG.debug('Got a value {!r}.'.format(value))
        e = cm.exception
        msg = (
            'WrongItemTypeError raised on real_value() of a '
            'FrozenCIStringSet object: {}').format(e)
        LOG.debug(msg)

        LOG.debug('Testing real_value() with a not existing key.')
        with self.assertRaises(KeyError) as cm:
            value = my_set.real_value('c')
            LOG.debug('Got a value {!r}.'.format(value))
        e = cm.exception
        msg = (
            'KeyError raised on real_value() of a FrozenCIStringSet object: {}').format(e)
        LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozenset_len(self):
        """Test len() of a FrozenCIStringSet object."""
        LOG.info('Testing len() of a FrozenCIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet

        test_tuples = (
            (None, 0),
            ([], 0),
            (['a'], 1),
            (['a', 'b'], 2),
        )

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected_len = test_tuple[1]
            LOG.debug('Testing len() of a FrozenCIStringSet from {!r}.'.format(src))
            my_set = FrozenCIStringSet(src)
            if self.verbose > 2:
                LOG.debug('FrozenCIStringSet %s: {}'.format(my_set))
            result = len(my_set)
            LOG.debug('Got a length of: {}'.format(result))
            self.assertEqual(result, expected_len)

    # -------------------------------------------------------------------------
    def test_frozenset_bool(self):
        """Test bool() of a FrozenCIStringSet object."""
        LOG.info('Testing bool() of a FrozenCIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet

        test_tuples = (
            (None, False),
            ([], False),
            (['a'], True),
            (['a', 'b'], True),
        )

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected_bool = test_tuple[1]
            LOG.debug('Testing bool() of a FrozenCIStringSet from {!r}.'.format(src))
            my_set = FrozenCIStringSet(src)
            if self.verbose > 2:
                LOG.debug('FrozenCIStringSet %s: {}'.format(my_set))
            result = bool(my_set)
            LOG.debug('Got boolean of: {}'.format(result))
            self.assertEqual(result, expected_bool)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_in(self):
        """Test operator 'in' of a FrozenCIStringSet object."""
        LOG.info("Testing operator 'in' of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongItemTypeError

        my_set = FrozenCIStringSet(['a', 'b'])

        valid_items = ('a', 'A', 'b')
        invalid_items = ('c', 'aA', 'bb', '%')
        wrong_items = (None, ['a'], 2, True)

        for item in valid_items:
            LOG.debug('Testing, that {i!r} is a member of {s!r}.'.format(
                i=item, s=my_set.as_list()))
            self.assertIn(item, my_set)

        for item in invalid_items:
            LOG.debug('Testing, that {i!r} is NOT a member of {s!r}.'.format(
                i=item, s=my_set.as_list()))
            self.assertNotIn(item, my_set)

        for item in wrong_items:
            LOG.debug('Testing, that {i!r} has the wrong type to be a member of {s!r}.'.format(
                i=item, s=my_set.as_list()))
            with self.assertRaises(WrongItemTypeError) as cm:
                if item in my_set:
                    LOG.debug('Bla')
            e = cm.exception
            msg = 'WrongItemTypeError on operator in: {}'.format(e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_le(self):
        """Test operator le ('<=', issubset()) of a FrozenCIStringSet object."""
        LOG.info("Testing operator le ('<=', issubset()) of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        my_set = FrozenCIStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], True),
            (['A', 'b'], True),
            (['a', 'B'], True),
            (['a'], False),
            (['a', 'b', 'c'], True),
            (['b', 'c'], False),
        )

        LOG.debug('Trying to compare with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set <= ['a']:
                LOG.debug('Bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on comparing with a wrong object: {}'.format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCIStringSet(src)
            msg = 'Testing, whether set {left!r} is a subset of {right!r}.'.format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set <= test_set:
                result = True
            LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_lt(self):
        """Test operator lt ('<') of a FrozenCIStringSet object."""
        LOG.info("Testing operator lt ('<') of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        my_set = FrozenCIStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], False),
            (['A', 'b'], False),
            (['a', 'B'], False),
            (['a'], False),
            (['a', 'b', 'c'], True),
            (['b', 'c'], False),
        )

        LOG.debug('Trying to compare with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set < ['a']:
                LOG.debug('Bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on comparing with a wrong object: {}'.format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCIStringSet(src)
            msg = 'Testing, whether set {left!r} is a real subset of {right!r}.'.format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set < test_set:
                result = True
            LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_eq(self):
        """Test operator eq ('==') of a FrozenCIStringSet object."""
        LOG.info("Testing operator eq ('==') of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError          # noqa

        my_set = FrozenCIStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], True),
            (['A', 'b'], True),
            (['a', 'B'], True),
            (['a'], False),
            (['a', 'b', 'c'], False),
            (['b', 'c'], False),
        )

        LOG.debug('Trying to compare with a wrong partner ...')
        result = False
        if my_set == ['a', 'b']:
            result = True
        LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=False))
        self.assertEqual(result, False)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCIStringSet(src)
            msg = 'Testing, whether set {left!r} is equal to {right!r}.'.format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set == test_set:
                result = True
            LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_ne(self):
        """Test operator ne ('!=') of a FrozenCIStringSet object."""
        LOG.info("Testing operator ne ('!=') of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError          # noqa

        my_set = FrozenCIStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], False),
            (['A', 'b'], False),
            (['a', 'B'], False),
            (['a'], True),
            (['a', 'b', 'c'], True),
            (['b', 'c'], True),
        )

        LOG.debug('Trying to compare with a wrong partner ...')
        result = True
        if my_set != ['a']:
            result = False
        LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=False))
        self.assertEqual(result, False)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCIStringSet(src)
            msg = 'Testing, whether set {left!r} is not equal to {right!r}.'.format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set != test_set:
                result = True
            LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_gt(self):
        """Test operator gt ('>') of a FrozenCIStringSet object."""
        LOG.info("Testing operator gt ('>') of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        my_set = FrozenCIStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], False),
            (['A', 'b'], False),
            (['a', 'B'], False),
            (['a'], True),
            (['a', 'b', 'c'], False),
            (['b', 'c'], False),
        )

        LOG.debug('Trying to compare with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set > ['a']:
                LOG.debug('Bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on comparing with a wrong object: {}'.format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCIStringSet(src)
            msg = 'Testing, whether set {right!r} is a real subset of {left!r}.'.format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set > test_set:
                result = True
            LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_ge(self):
        """Test operator ge ('>=') of a FrozenCIStringSet object."""
        LOG.info("Testing operator ge ('>=') of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        my_set = FrozenCIStringSet(['a', 'b'])

        test_tuples = (
            (['a', 'b'], True),
            (['A', 'b'], True),
            (['a', 'B'], True),
            (['a'], True),
            (['a', 'b', 'c'], False),
            (['b', 'c'], False),
        )

        LOG.debug('Trying to compare with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if my_set >= ['a']:
                LOG.debug('Bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on comparing with a wrong object: {}'.format(e)
        LOG.debug(msg)

        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            test_set = FrozenCIStringSet(src)
            msg = 'Testing, whether set {right!r} is a subset of {left!r}.'.format(
                left=my_set.as_list(), right=test_set.as_list())
            LOG.debug(msg)
            result = False
            if my_set >= test_set:
                result = True
            LOG.debug('Result: {r} (expected: {e}).'.format(r=result, e=expected))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozenset_operator_or(self):
        """Test operator ge ('|', union()) of a FrozenCIStringSet object."""
        LOG.info("Testing operator ge ('|', union()) of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        set_one = FrozenCIStringSet(['a', 'B', 'c'])
        set_two = FrozenCIStringSet(['b', 'c', 'e'])
        set_three = FrozenCIStringSet(['C', 'd', 'f'])

        set_expected = FrozenCIStringSet(['a', 'b', 'C', 'd', 'e', 'f'])

        LOG.debug('Trying to union with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            my_set = set_one | ['a']                                        # noqa
            LOG.debug('bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on a union with a wrong object: {}'.format(e)
        LOG.debug(msg)

        msg = 'Making a union of frozen sets {one!r}, {two!r} and {three!r}.'
        msg = msg.format(one=set_one.as_list(), two=set_two.as_list(), three=set_three.as_list())
        LOG.debug(msg)
        set_result = set_one | set_two | set_three
        msg = 'Got a union result {res!r} (expecting: {exp!r}).'.format(
            res=set_result.as_list(), exp=set_expected.as_list())
        LOG.debug(msg)
        self.assertEqual(set_result.as_list(), set_expected.as_list())

    # -------------------------------------------------------------------------
    def test_frozenset_operator_and(self):
        """Test operator and ('&', intersection()) of a FrozenCIStringSet object."""
        LOG.info("Testing operator and ('&', intersection()) of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError          # noqa

        set_one = FrozenCIStringSet(['a', 'B', 'c', 'd', 'E', 'f', 'G'])
        set_two = FrozenCIStringSet(['a', 'b', 'd', 'e', 'h'])
        set_three = FrozenCIStringSet(['A', 'b', 'C', 'd', 'f', 'g'])

        set_expected = FrozenCIStringSet(['A', 'b', 'd'])

        LOG.debug('Trying to intersection with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            my_set = set_one & ['a']                                        # noqa
            LOG.debug('bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on a intersection with a wrong object: {}'.format(e)
        LOG.debug(msg)

        msg = 'Making an intersection of frozen sets {one!r}, {two!r} and {three!r}.'
        msg = msg.format(one=set_one.as_list(), two=set_two.as_list(), three=set_three.as_list())
        LOG.debug(msg)
        set_result = set_one & set_two & set_three
        msg = 'Got an intersection result {res!r} (expecting: {exp!r}).'.format(
            res=set_result.as_list(), exp=set_expected.as_list())
        LOG.debug(msg)
        self.assertEqual(set_result.as_list(), set_expected.as_list())

    # -------------------------------------------------------------------------
    def test_frozenset_operator_sub(self):
        """Test operator sub ('-', difference()) of a FrozenCIStringSet object."""
        LOG.info("Testing operator sub ('-', difference()) of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        set_src = FrozenCIStringSet(['a', 'B', 'c', 'd', 'E', 'f', 'G'])
        set_one = FrozenCIStringSet(['a', 'd', ])
        set_two = FrozenCIStringSet(['e', 'f', 'H'])

        set_expected = FrozenCIStringSet(['B', 'c', 'G'])

        LOG.debug('Trying to make a difference with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            my_set = set_one - ['a']                                        # noqa
            LOG.debug('bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on a difference with a wrong object: {}'.format(e)
        LOG.debug(msg)

        msg = 'Making a difference of frozen set {src!r} minus {one!r} and {two!r}.'
        msg = msg.format(src=set_src.as_list(), one=set_one.as_list(), two=set_two.as_list())
        LOG.debug(msg)
        set_result = set_src - set_one - set_two
        msg = 'Got an difference result {res!r} (expecting: {exp!r}).'.format(
            res=set_result.as_list(), exp=set_expected.as_list())
        LOG.debug(msg)
        self.assertEqual(set_result.as_list(), set_expected.as_list())

    # -------------------------------------------------------------------------
    def test_frozenset_operator_xor(self):
        """Test operator xor ('^', symmetric_difference()) of a FrozenCIStringSet object."""
        LOG.info(
            "Testing operator xor ('^', symmetric_difference()) of a FrozenCIStringSet object.")

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        set_one = FrozenCIStringSet(['a', 'B', 'c'])
        set_two = FrozenCIStringSet(['b', 'c', 'H'])

        set_expected = FrozenCIStringSet(['a', 'H'])

        LOG.debug('Trying to make a symmetric difference with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            my_set = set_one ^ ['a']                                        # noqa
            LOG.debug('bla')
        e = cm.exception
        msg = (
            'WrongCompareSetClassError on a symmetric '
            'difference with a wrong object: {}').format(e)
        LOG.debug(msg)

        msg = 'Making a symmetric difference of frozen set {one!r} and {two!r}.'
        msg = msg.format(one=set_one.as_list(), two=set_two.as_list())
        LOG.debug(msg)
        set_result = set_one ^ set_two
        msg = 'Got an isymmetric difference result {res!r} (expecting: {exp!r}).'.format(
            res=set_result.as_list(), exp=set_expected.as_list())
        LOG.debug(msg)
        self.assertEqual(set_result.as_list(), set_expected.as_list())

    # -------------------------------------------------------------------------
    def test_frozenset_method_isdisjoint(self):
        """Test method isdisjoint() of a FrozenCIStringSet object."""
        LOG.info('Testing method isdisjoint() of a FrozenCIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import WrongCompareSetClassError

        set_src = FrozenCIStringSet(['a', 'B', 'c'])
        tuples_test = (
            (['a'], False),
            (['A'], False),
            (['b', 'd'], False),
            (['d'], True),
            (['d', 'E'], True),
        )

        LOG.debug('Trying to exec isdisjoint with a wrong partner ...')
        with self.assertRaises(WrongCompareSetClassError) as cm:
            if set_src.isdisjoint(['a']):
                LOG.debug('bla')
        e = cm.exception
        msg = 'WrongCompareSetClassError on isdisjoint() with a wrong object: {}'.format(e)
        LOG.debug(msg)

        for test_tuple in tuples_test:
            set_test = FrozenCIStringSet(test_tuple[0])
            expected = test_tuple[1]
            LOG.debug(
                'Testing, whether {src!r} is isdisjoint from {tst!r} - expected {exp}.'.format(
                    src=set_src.as_list(), tst=set_test.as_list(), exp=expected))
            res = False
            if set_src.isdisjoint(set_test):
                res = True
            self.assertEqual(res, expected)

    # -------------------------------------------------------------------------
    def test_init_set(self):
        """Test init of a CIStringSet object."""
        LOG.info('Testing init of a CIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import CIStringSet
        from fb_tools.colcts import WrongItemTypeError

        LOG.debug('Testing init of an empty set.')
        my_set = CIStringSet()
        LOG.debug('CIStringSet %r: {!r}'.format(my_set))
        LOG.debug('CIStringSet %s: {}'.format(my_set))
        self.assertEqual(my_set.as_list(), [])

        src = ('B', 'a')
        expected = {
            '__class_name__': 'CIStringSet',
            'items': ['a', 'B'],
        }
        LOG.debug('Checking as_dict(), source: {src}, expeced: {ex}.'.format(
            src=src, ex=expected))
        my_set = CIStringSet(src)
        result = my_set.as_dict()
        LOG.debug('Result of as_dict(): {}'.format(pp(result)))
        self.assertEqual(expected, result)

        correct_iterables = (
            (('a',), ['a']),
            (['a'], ['a']),
            (['A'], ['A']),
            (['a', 'b'], ['a', 'b']),
            (['a', 'B'], ['a', 'B']),
            (['b', 'a'], ['a', 'b']),
            (['a', 'a'], ['a']),
            (['a', 'A'], ['A']),
            (['A', 'a'], ['a']),
            (FrozenCIStringSet(['a', 'b']), ['a', 'b']),
            (CIStringSet(['a', 'b']), ['a', 'b']),
            (['a', 'b', 'A'], ['A', 'b']),
        )

        for test_tuple in correct_iterables:
            src = test_tuple[0]
            expected = test_tuple[1]
            LOG.debug('Testing init of a CIStringSet from {!r}.'.format(src))
            my_set = CIStringSet(src)
            if self.verbose > 2:
                LOG.debug('CIStringSet %s: {}'.format(my_set))
            result = my_set.as_list()
            LOG.debug('CIStringSet as a list: {r!r} (expeced: {ex!r})'.format(
                r=result, ex=expected))
            self.assertEqual(result, expected)

        class Tobj(object):

            def uhu(self):
                return 'banane'

        tobj = Tobj()

        wrong_iterables = (
            'a', 1, {'uhu': 'banane'}, tobj, tobj.uhu)

        for obj in wrong_iterables:

            msg = 'Trying to init a CIStringSet from {} ...'
            LOG.debug(msg.format(pp(obj)))
            with self.assertRaises(TypeError) as cm:
                my_set = CIStringSet(obj)
            e = cm.exception
            msg = ('TypeError raised on init of a CIStringSet object: {}').format(e)
            LOG.debug(msg)

        iterables_with_wrong_values = (
            [None], [1], ['a', 1], [{'uhu': 'banane'}], [tobj], [tobj.uhu])

        for obj in iterables_with_wrong_values:

            msg = 'Trying to init a CIStringSet from {!r} ...'
            LOG.debug(msg.format(obj))
            with self.assertRaises(WrongItemTypeError) as cm:
                my_set = CIStringSet(obj)
            e = cm.exception
            msg = ('WrongItemTypeError raised on init of a CIStringSet object: {}').format(e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_set_add(self):
        """Test method add() of a CIStringSet object."""
        LOG.info('Testing method add() of a CIStringSet object.')

        from fb_tools.colcts import FrozenCIStringSet
        from fb_tools.colcts import CIStringSet
        from fb_tools.colcts import WrongItemTypeError

        src = ['a', 'b']

        tuples_test = (
            ('a', False, ['a', 'b']),
            ('A', False, ['A', 'b']),
            ('A', True, ['a', 'b']),
            ('c', False, ['a', 'b', 'c']),
            (('c', 'd'), False, ['a', 'b', 'c', 'd']),
            (['c', 'd'], False, ['a', 'b', 'c', 'd']),
            (FrozenCIStringSet(['c', 'd']), False, ['a', 'b', 'c', 'd']),
            (CIStringSet(['c', 'd']), False, ['a', 'b', 'c', 'd']),
            (['A', 'd'], False, ['A', 'b', 'd']),
            (['a', 'd'], True, ['a', 'b', 'd']),
        )

        LOG.debug('Test adding valid values ...')
        for test_tuple in tuples_test:
            set_test = CIStringSet(src)
            value = test_tuple[0]
            keep = test_tuple[1]
            expected = test_tuple[2]
            if self.verbose > 2:
                msg = 'Testing adding {v!r} to {s!r}, keep existing is {k}.'.format(
                    v=value, s=set_test, k=keep)
                LOG.debug(msg)
            set_test.add(value, keep=keep)
            result = set_test.values()
            if self.verbose > 2:
                LOG.debug('Got {r!r}, expected {e!r}.'.format(r=result, e=expected))
            self.assertEqual(result, expected)

        LOG.debug('Test adding valid values ...')
        wrong_values = (None, [None], 1, [2], ['c', 3], ['c', ['d']])
        for value in wrong_values:
            set_test = CIStringSet(src)
            if self.verbose > 2:
                msg = 'Trying to add {!r} to a CIStringSet ...'
                LOG.debug(msg.format(value))
            with self.assertRaises(WrongItemTypeError) as cm:
                set_test.add(value)
            e = cm.exception
            msg = (
                'WrongItemTypeError raised on adding an invalid value to a '
                'CIStringSet object: {}').format(e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_init_frozendict(self):
        """Test init of a FrozenCIDict object."""
        LOG.info('Testing init of a FrozenCIDict object.')

        from fb_tools.colcts import FrozenCIDict
        from fb_tools.colcts import FbCollectionsError

        LOG.debug('Testing init of an empty frozen dict.')
        my_dict = FrozenCIDict()
        LOG.debug('FrozenCIDict %r: {!r}'.format(my_dict))
        LOG.debug('FrozenCIDict %s: {}'.format(my_dict))
        self.assertEqual(my_dict.dict(), {})

        src = {
            'a': 'b',
            'num': 3,
            'uhu': 'banane',
        }
        expected = {
            '__class_name__': 'FrozenCIDict',
            'a': 'b',
            'num': 3,
            'uhu': 'banane',
        }
        LOG.debug('Checking as_dict(), source: {src}, expeced: {ex}.'.format(
            src=pp(src), ex=pp(expected)))
        my_dict = FrozenCIDict(**src)
        result = my_dict.as_dict()
        if self.verbose > 2:
            LOG.debug('Result of as_dict(): {}'.format(pp(result)))
        self.assertEqual(expected, result)

        comp = {'one': 1, 'two': 2, 'three': 3}

        LOG.debug('Init a: FrozenCIDict(one=1, two=2, three=3)')
        a = FrozenCIDict(one=1, two=2, three=3)
        result = a.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init b: FrozenCIDict({'one': 1, 'two': 2, 'three': 3})")
        b = FrozenCIDict({'one': 1, 'two': 2, 'three': 3})
        result = b.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init c: FrozenCIDict(zip(['one', 'two', 'three'], [1, 2, 3]))")
        c = FrozenCIDict(zip(['one', 'two', 'three'], [1, 2, 3]))
        result = c.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init d: FrozenCIDict([('two', 2), ('one', 1), ('three', 3)])")
        d = FrozenCIDict([('two', 2), ('one', 1), ('three', 3)])
        result = d.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init e: FrozenCIDict({'three': 3, 'one': 1, 'two': 2})")
        e = FrozenCIDict({'three': 3, 'one': 1, 'two': 2})
        result = e.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init f: FrozenCIDict({'one': 1, 'three': 3}, two=2)")
        f = FrozenCIDict({'one': 1, 'three': 3}, two=2)
        result = f.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        test_tuples = (
            ({'a': 1}, {'a': 1}),
            ({'A': 1}, {'A': 1}),
            ([('a', 1), ('b', 2)], {'a': 1, 'b': 2}),
            ([('a', 1), ('A', 2)], {'A': 2}),
        )

        LOG.debug('Testing init with correct sources.')
        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            if self.verbose > 2:
                LOG.debug('Testing init of a FrozenCIDict from {}.'.format(pp(src)))
            my_dict = FrozenCIDict(src)
            if self.verbose > 3:
                LOG.debug('FrozenCIDict %s: {}'.format(my_dict))
            result = my_dict.dict()
            if self.verbose > 2:
                LOG.debug('FrozenCIDict as a dict: {r} (expeced: {e})'.format(
                    r=pp(result), e=pp(expected)))
            self.assertEqual(result, expected)

        class Tobj(object):

            def uhu(self):
                return 'banane'

        tobj = Tobj()

        wrong_sources = (
            'a', 1, {1: 2}, {None: 2},
            [1], [1, 2],
            [(1,), (2,)], [('a',)], [(1, 1), (2, 2)],
            tobj, tobj.uhu)

        for obj in wrong_sources:

            msg = 'Trying to init a FrozenCIDict from {} ...'
            LOG.debug(msg.format(pp(obj)))
            with self.assertRaises(FbCollectionsError) as cm:
                my_dict = FrozenCIDict(obj)
            e = cm.exception
            if self.verbose > 2:
                msg = '{n} raised on init of a FrozenCIDict object: {e}'.format(
                    n=e.__class__.__name__, e=e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozendict_copy(self):
        """Test copying a FrozenCIDict object."""
        LOG.info('Testing copying a FrozenCIDict object.')

        import copy
        from fb_tools.colcts import FrozenCIDict

        src = {'a': 1, 'B': 2, 'c': 3, 'aA': 4}
        src_dict = FrozenCIDict(src)

        tgt_dict = copy.copy(src_dict)
        tgt = tgt_dict.dict()

        LOG.debug('Checking the equality of the dicts ...')
        self.assertEqual(src, tgt)

        LOG.debug('Checking, that the copy is an instance of FrozenCIDict ...')
        self.assertIsInstance(tgt_dict, FrozenCIDict)

        LOG.debug('Checking, that the copy is not a reference to its origin ...')
        self.assertIsNot(src_dict, tgt_dict)

    # -------------------------------------------------------------------------
    def test_frozendict_real_key(self):
        """Test method real_key() of a FrozenCIDict object."""
        LOG.info('Testing method real_key() of a FrozenCIDict object.')

        from fb_tools.colcts import FrozenCIDict
        from fb_tools.colcts import FbCollectionsError

        test_tuples = (
            ({'A': 1}, 'a', 'A'),
            ({'A': 1}, 'A', 'A'),
            ({'a': 1}, 'a', 'a'),
            ({'a': 1}, 'A', 'a'),
        )

        LOG.debug('Testing real_key() with correct parameters.')
        for test_tuple in test_tuples:
            src = test_tuple[0]
            key = test_tuple[1]
            expected = test_tuple[2]
            my_dict = FrozenCIDict(src)

            if self.verbose > 2:
                LOG.debug('Testing to get the real key of {v!r} of {s}.'.format(
                    v=key, s=my_dict.dict()))
            result = my_dict.real_key(key)
            if self.verbose > 2:
                LOG.debug('Got {res!r} - expected {ex!r}.'.format(res=result, ex=expected))

            self.assertEqual(result, expected)

        my_dict = FrozenCIDict(A=1, b=2)

        LOG.debug('Testing real_key() with a parameter of an incorrect type.')
        with self.assertRaises(FbCollectionsError) as cm:
            value = my_dict.real_key(1)
            LOG.debug('Got a value {!r}.'.format(value))
        e = cm.exception
        msg = '{c} raised on real_key() of a FrozenCIDict object: {e}'
        LOG.debug(msg.format(c=e.__class__.__name__, e=e))

        LOG.debug('Testing real_key() with a not existing key.')
        with self.assertRaises(FbCollectionsError) as cm:
            value = my_dict.real_key('c')
            LOG.debug('Got a value {!r}.'.format(value))
        e = cm.exception
        msg = '{c} raised on real_key() of a FrozenCIDict object: {e}'
        LOG.debug(msg.format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_frozendict_get(self):
        """Test methods get() and __getitem__() of a FrozenCIDict object."""
        LOG.info('Testing methods get() and __getitem__() of a FrozenCIDict object.')

        from fb_tools.colcts import FrozenCIDict
        from fb_tools.colcts import FbCollectionsError

        test_tuples = (
            ({'a': 1, 'b': 2}, 'a', 1),
            ({'a': 1, 'b': 2}, 'b', 2),
            ({'a': 1, 'b': 2}, 'A', 1),
            ({'a': 1, 'b': 2}, 'B', 2),
            ({'A': 1, 'b': 2}, 'a', 1),
            ({'a': 1, 'B': 2}, 'b', 2),
            ({'A': 1, 'b': 2}, 'A', 1),
            ({'a': 1, 'B': 2}, 'B', 2),
        )

        LOG.debug('Testing get() with correct parameters.')
        for test_tuple in test_tuples:
            src = test_tuple[0]
            key = test_tuple[1]
            expected = test_tuple[2]
            my_dict = FrozenCIDict(src)

            if self.verbose > 2:
                LOG.debug('Testing to get the value of key {v!r} of {s} with my_dict[key].'.format(
                    v=key, s=my_dict.dict()))
            result = my_dict[key]
            if self.verbose > 2:
                LOG.debug('Got {res!r} - expected {ex!r}.'.format(res=result, ex=expected))
            self.assertEqual(result, expected)

            if self.verbose > 2:
                LOG.debug((
                    'Testing to get the value of key {v!r} of {s} with '
                    'my_dict.get(key).').format(v=key, s=my_dict.dict()))
            result = my_dict.get(key)
            if self.verbose > 2:
                LOG.debug('Got {res!r} - expected {ex!r}.'.format(res=result, ex=expected))
            self.assertEqual(result, expected)

        wrong_keys = (None, 1, [1], (1, 2), ['a'], {1: 2}, {'a': 1}, b'a', 'c')
        src = {'a': 1, 'B': 2}
        src_dict = FrozenCIDict(src)

        LOG.debug('Testing get() and __getitem__() with a key of an incorrect type.')
        for key in wrong_keys:

            if self.verbose > 2:
                msg = (
                    'Trying to get a value from FrozenCIDict {d} '
                    'for key {k!r} by src_dict[key] ...')
                LOG.debug(msg.format(d=pp(src), k=key))
            with self.assertRaises(FbCollectionsError) as cm:
                result = src_dict[key]
            e = cm.exception
            if self.verbose > 2:
                msg = '{n} raised on src_dict[key] of a FrozenCIDict object: {e}'.format(
                    n=e.__class__.__name__, e=e)
                LOG.debug(msg)

            if self.verbose > 2:
                msg = (
                    'Trying to get a value from FrozenCIDict {d} '
                    'for key {k!r} by src_dict.get(key) ...')
                LOG.debug(msg.format(d=pp(src), k=key))
            with self.assertRaises(FbCollectionsError) as cm:
                result = src_dict.get(key)
            e = cm.exception
            if self.verbose > 2:
                msg = '{n} raised on src_dict.get(key) of a FrozenCIDict object: {e}'.format(
                    n=e.__class__.__name__, e=e)
                LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozendict_keys(self):
        """Test methods keys() and __iter__() of a FrozenCIDict object."""
        LOG.info('Testing methods keys() and __iter__() of a FrozenCIDict object.')

        from fb_tools.colcts import FrozenCIDict
        # from fb_tools.colcts import FbCollectionsError

        src = {'a': 1, 'B': 2, 'c': 3, 'aA': 4}
        src_dict = FrozenCIDict(src)
        expected = ['a', 'aA', 'B', 'c']

        LOG.debug('Testing src_dict.keys() from {} ...'.format(pp(src)))
        result = src_dict.keys()
        if self.verbose > 2:
            LOG.debug('Got {r} - expected {e!r}.'.format(r=pp(result), e=pp(expected)))
        self.assertEqual(result, expected)

        LOG.debug('Testing src_dict.__iter__() from {} ...'.format(pp(src)))
        result = []
        for key in src_dict:
            result.append(key)
        if self.verbose > 2:
            LOG.debug('Got {r} - expected {e!r}.'.format(r=pp(result), e=pp(expected)))
        self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_frozendict_contains(self):
        """Test method __contains__() (operator 'in') of a FrozenCIDict object."""
        LOG.info("Testing method __contains__() (operator 'in') of a FrozenCIDict object.")

        from fb_tools.colcts import FrozenCIDict
        from fb_tools.colcts import FbCollectionsError

        src = {'a': 1, 'B': 2, 'c': 3, 'aA': 4}
        src_dict = FrozenCIDict(src)

        test_tuples = (
            ('a', True),
            ('A', True),
            ('b', True),
            ('B', True),
            ('d', False),
            ('D', False),
            ('aa', True),
            ('ab', False),
        )

        LOG.debug("Testing 'key in src_dict' with correct keys in {} ...".format(pp(src)))
        for test_tuple in test_tuples:
            key = test_tuple[0]
            should_be_in = test_tuple[1]
            if should_be_in:
                if self.verbose > 2:
                    LOG.debug('Testing, that {!r} is contained.'.format(key))
                self.assertIn(key, src_dict)
            else:
                if self.verbose > 2:
                    LOG.debug('Testing, that {!r} is NOT contained.'.format(key))
                self.assertNotIn(key, src_dict)

        wrong_keys = (None, 1, [1], (1, 2), ['a'], {1: 2}, {'a': 1}, b'a')

        LOG.debug("Testing operator 'in' with a key of an incorrect type.")
        for key in wrong_keys:

            if self.verbose > 2:
                msg = 'Testing, whether key {!r} is contained.'.format(key)
                LOG.debug(msg)

            with self.assertRaises(FbCollectionsError) as cm:
                if key in src_dict:
                    LOG.debug('Bla with {!r}'.format(key))
            e = cm.exception
            if self.verbose > 2:
                msg = (
                    '{n} raised on key "{k!r} in src_dict" of a FrozenCIDict '
                    'object: {e}').format(n=e.__class__.__name__, k=key, e=e)
                LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_frozendict_items(self):
        """Test methods items() and values() of a FrozenCIDict object."""
        LOG.info('Testing methods items() and values() of a FrozenCIDict object.')

        from fb_tools.colcts import FrozenCIDict

        src = {'a': 1, 'B': 2, 'c': 3, 'aA': 4}
        src_dict = FrozenCIDict(src)
        expected_items = [('a', 1), ('aA', 4), ('B', 2), ('c', 3)]
        expected_values = [1, 4, 2, 3]

        LOG.debug('Testing src_dict.items() on {}'.format(pp(src_dict.dict())))
        result = src_dict.items()
        if self.verbose > 2:
            LOG.debug('Got {r} - expected {e!r}.'.format(r=pp(result), e=pp(expected_items)))
        self.assertEqual(result, expected_items)

        LOG.debug('Testing src_dict.values() on {}'.format(pp(src_dict.dict())))
        result = src_dict.values()
        if self.verbose > 2:
            LOG.debug('Got {r} - expected {e!r}.'.format(r=pp(result), e=pp(expected_values)))
        self.assertEqual(result, expected_values)

    # -------------------------------------------------------------------------
    def test_frozendict_operator_eq(self):
        """Test operator eq ('==') and ne (!=) of a FrozenCIDict object."""
        LOG.info("Testing operator eq ('==') and ne (!=) of a FrozenCIDict object.")

        from fb_tools.colcts import FrozenCIDict
        from fb_tools.colcts import CIDict

        src = {'a': 1, 'B': 2, 'aA': 4}
        src_dict = FrozenCIDict(src)

        test_tuples = (
            (FrozenCIDict({'a': 1, 'B': 2, 'aA': 4}), True),
            (FrozenCIDict({'A': 1, 'B': 2, 'aA': 4}), True),
            (FrozenCIDict({'A': 1, 'b': 2, 'Aa': 4}), True),
            (CIDict({'a': 1, 'B': 2, 'aA': 4}), False),
            (FrozenCIDict({'B': 2, 'aA': 4}), False),
            (FrozenCIDict({'a': 2, 'B': 2, 'aA': 4}), False),
            ({'a': 1, 'B': 2, 'aA': 4}, False),
            (FrozenCIDict({'a': 1, 'B': 2, 'aA': 4, 'c': 3}), False),
            (('a', 1, 'B', 2, 'aA', 4), False),
            (['a', 1, 'B', 2, 'aA', 4], False),
            ([('a', 1), ('B', 2), ('aA', 4)], False),
            ('a', False),
            (None, False),
            (1, False),
        )

        LOG.debug('Testing __eq__ and __ne__ on FrozenCIDict {}.'.format(pp(src)))

        for test_tuple in test_tuples:
            comp_object = test_tuple[0]
            should_be_equal = test_tuple[1]

            if should_be_equal:
                if self.verbose > 2:
                    LOG.debug('Testing, that {!r} is equal to src_dict ...'.format(comp_object))
                self.assertEqual(src_dict, comp_object)
            else:
                if self.verbose > 2:
                    LOG.debug('Testing, that {!r} is NOT equal to src_dict ...'.format(
                        comp_object))
                self.assertNotEqual(src_dict, comp_object)

    # -------------------------------------------------------------------------
    def test_init_dict(self):
        """Test init of a CIDict object."""
        LOG.info('Testing init of a CIDict object.')

        from fb_tools.colcts import CIDict
        from fb_tools.colcts import FbCollectionsError

        LOG.debug('Testing init of an empty dict.')
        my_dict = CIDict()
        LOG.debug('CIDict %r: {!r}'.format(my_dict))
        LOG.debug('CIDict %s: {}'.format(my_dict))
        self.assertEqual(my_dict.dict(), {})

        src = {
            'a': 'b',
            'num': 3,
            'uhu': 'banane',
        }
        expected = {
            '__class_name__': 'CIDict',
            'a': 'b',
            'num': 3,
            'uhu': 'banane',
        }
        LOG.debug('Checking as_dict(), source: {src}, expeced: {ex}.'.format(
            src=pp(src), ex=pp(expected)))
        my_dict = CIDict(**src)
        result = my_dict.as_dict()
        if self.verbose > 2:
            LOG.debug('Result of as_dict(): {}'.format(pp(result)))
        self.assertEqual(expected, result)

        comp = {'one': 1, 'two': 2, 'three': 3}

        LOG.debug('Init a: CIDict(one=1, two=2, three=3)')
        a = CIDict(one=1, two=2, three=3)
        result = a.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init b: CIDict({'one': 1, 'two': 2, 'three': 3})")
        b = CIDict({'one': 1, 'two': 2, 'three': 3})
        result = b.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init c: CIDict(zip(['one', 'two', 'three'], [1, 2, 3]))")
        c = CIDict(zip(['one', 'two', 'three'], [1, 2, 3]))
        result = c.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init d: CIDict([('two', 2), ('one', 1), ('three', 3)])")
        d = CIDict([('two', 2), ('one', 1), ('three', 3)])
        result = d.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init e: CIDict({'three': 3, 'one': 1, 'two': 2})")
        e = CIDict({'three': 3, 'one': 1, 'two': 2})
        result = e.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        LOG.debug("Init f: CIDict({'one': 1, 'three': 3}, two=2)")
        f = CIDict({'one': 1, 'three': 3}, two=2)
        result = f.dict()
        if self.verbose > 2:
            LOG.debug('Result: {}'.format(pp(result)))
        self.assertEqual(result, comp)

        test_tuples = (
            ({'a': 1}, {'a': 1}),
            ({'A': 1}, {'A': 1}),
            ([('a', 1), ('b', 2)], {'a': 1, 'b': 2}),
            ([('a', 1), ('A', 2)], {'A': 2}),
        )

        LOG.debug('Testing init with correct sources.')
        for test_tuple in test_tuples:
            src = test_tuple[0]
            expected = test_tuple[1]
            if self.verbose > 2:
                LOG.debug('Testing init of a CIDict from {}.'.format(pp(src)))
            my_dict = CIDict(src)
            if self.verbose > 3:
                LOG.debug('CIDict %s: {}'.format(my_dict))
            result = my_dict.dict()
            if self.verbose > 2:
                LOG.debug('CIDict as a dict: {r} (expeced: {e})'.format(
                    r=pp(result), e=pp(expected)))
            self.assertEqual(result, expected)

        class Tobj(object):

            def uhu(self):
                return 'banane'

        tobj = Tobj()

        wrong_sources = (
            'a', 1, {1: 2}, {None: 2},
            [1], [1, 2],
            [(1,), (2,)], [('a',)], [(1, 1), (2, 2)],
            tobj, tobj.uhu)

        for obj in wrong_sources:

            msg = 'Trying to init a CIDict from {} ...'
            LOG.debug(msg.format(pp(obj)))
            with self.assertRaises(FbCollectionsError) as cm:
                my_dict = CIDict(obj)
            e = cm.exception
            if self.verbose > 2:
                msg = '{n} raised on init of a CIDict object: {e}'.format(
                    n=e.__class__.__name__, e=e)
            LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_dict_set(self):
        """Test methods set() and __setitem__() of a CIDict object."""
        LOG.info('Testing methods set() and __setitem__() of a CIDict object.')

        from fb_tools.colcts import CIDict
        from fb_tools.colcts import FbCollectionsError

        test_tuples = (
            ({'a': 1, 'b': 2}, 'a', 1, {'a': 1, 'b': 2},),
            ({'a': 1, 'b': 2}, 'c', 3, {'a': 1, 'b': 2, 'c': 3},),
            ({'a': 1, 'b': 2}, 'A', 1, {'A': 1, 'b': 2},),
        )

        LOG.debug('Testing set() with correct parameters.')
        for test_tuple in test_tuples:

            src = test_tuple[0]
            key = test_tuple[1]
            value = test_tuple[2]
            expected = test_tuple[3]

            if self.verbose > 2:
                LOG.debug((
                    'Testing to set key {k!r} to value {v!r} in {s} with my_dict[key].').format(
                    k=key, v=value, s=src))

            my_dict = CIDict(src)
            my_dict[key] = value
            result_val = my_dict[key]
            result_dict = my_dict.dict()
            if self.verbose > 2:
                LOG.debug((
                    'Got new value {v!r} and dict {d} - expected value {exv!r} and '
                    'dict {exd}.').format(v=result_val, d=result_dict, exv=value, exd=expected))
            self.assertEqual(result_val, value)
            self.assertEqual(result_dict, expected)

            if self.verbose > 2:
                LOG.debug((
                    'Testing to set key {k!r} to value {v!r} in {s} with '
                    'my_dict.set(key, value).').format(k=key, v=value, s=my_dict.dict()))

            my_dict = CIDict(src)
            my_dict.set(key, value)
            result_val = my_dict[key]
            result_dict = my_dict.dict()
            if self.verbose > 2:
                LOG.debug((
                    'Got new value {v!r} and dict {d} - expected value {exv!r} and '
                    'dict {exd}.').format(v=result_val, d=result_dict, exv=value, exd=expected))
            self.assertEqual(result_val, value)
            self.assertEqual(result_dict, expected)

        wrong_keys = (None, 1, [1], (1, 2), ['a'], {1: 2}, {'a': 1}, b'a')
        value = 'bla'
        src = {'a': 1, 'B': 2}
        src_dict = CIDict(src)

        LOG.debug('Testing set() and __setitem__() with a key of an incorrect type.')
        for key in wrong_keys:

            if self.verbose > 2:
                msg = (
                    'Trying to set key {k!r} to value {v!r} in {s} with '
                    'src_dict[key] ...').format(k=key, v=value, s=src)
                LOG.debug(msg)
            with self.assertRaises(FbCollectionsError) as cm:
                src_dict[key] = value
            e = cm.exception
            if self.verbose > 2:
                msg = '{n} raised on src_dict[key] of a CIDict object: {e}'.format(
                    n=e.__class__.__name__, e=e)
                LOG.debug(msg)

            if self.verbose > 2:
                msg = (
                    'Trying to set key {k!r} to value {v!r} in {s} with '
                    'src_dict.set(key, value) ...').format(k=key, v=value, s=my_dict.dict())
                LOG.debug(msg)
            with self.assertRaises(FbCollectionsError) as cm:
                src_dict.set(key, value)
            e = cm.exception
            if self.verbose > 2:
                msg = '{n} raised on src_dict.set(key, value) of a CIDict object: {e}'.format(
                    n=e.__class__.__name__, e=e)
                LOG.debug(msg)

    # -------------------------------------------------------------------------
    def test_dict_del(self):
        """Test method __del__() of a CIDict object."""
        LOG.info('Testing method __del__() of a CIDict object.')

        from fb_tools.colcts import CIDict
        from fb_tools.colcts import FbCollectionsError

        wrong_keys = (None, 1, [1], (1, 2), ['a'], {1: 2}, {'a': 1}, b'a', 'c')
        src = {'a': 1, 'B': 2}

        test_tuples = (
            ('a', {'B': 2}),
            ('b', {'a': 1}),
        )

        LOG.debug('Testing method __del__() with correct keys ...')

        for test_tuple in test_tuples:

            key = test_tuple[0]
            expected = test_tuple[1]

            src_dict = CIDict(src)
            if self.verbose > 2:
                LOG.debug('Deleting key {k!r} from {s} ...'.format(k=key, s=src))
            del src_dict[key]
            result = src_dict.dict()
            if self.verbose > 2:
                LOG.debug('Got {}.'.format(result))
            self.assertEqual(result, expected)

        LOG.debug('Testing __del__() with a key of an incorrect type.')
        src_dict = CIDict(src)
        for key in wrong_keys:

            if self.verbose > 2:
                msg = 'Trying to delete key {k!r} from {s} ...'.format(k=key, s=src)
                LOG.debug(msg)
            with self.assertRaises(FbCollectionsError) as cm:
                del src_dict[key]
            e = cm.exception
            if self.verbose > 2:
                msg = "{n} raised on 'del src_dict[key]' from a CIDict object: {e}".format(
                    n=e.__class__.__name__, e=e)
                LOG.debug(msg)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestFbCollections('test_import', verbose))
    suite.addTest(TestFbCollections('test_init_frozenset', verbose))
    suite.addTest(TestFbCollections('test_frozenset_real_value', verbose))
    suite.addTest(TestFbCollections('test_frozenset_len', verbose))
    suite.addTest(TestFbCollections('test_frozenset_bool', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_in', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_le', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_lt', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_eq', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_ne', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_gt', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_ge', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_or', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_and', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_sub', verbose))
    suite.addTest(TestFbCollections('test_frozenset_operator_xor', verbose))
    suite.addTest(TestFbCollections('test_frozenset_method_isdisjoint', verbose))
    suite.addTest(TestFbCollections('test_init_set', verbose))
    suite.addTest(TestFbCollections('test_set_add', verbose))
    suite.addTest(TestFbCollections('test_init_frozendict', verbose))
    suite.addTest(TestFbCollections('test_frozendict_copy', verbose))
    suite.addTest(TestFbCollections('test_frozendict_real_key', verbose))
    suite.addTest(TestFbCollections('test_frozendict_get', verbose))
    suite.addTest(TestFbCollections('test_frozendict_keys', verbose))
    suite.addTest(TestFbCollections('test_frozendict_contains', verbose))
    suite.addTest(TestFbCollections('test_frozendict_items', verbose))
    suite.addTest(TestFbCollections('test_frozendict_operator_eq', verbose))
    suite.addTest(TestFbCollections('test_init_dict', verbose))
    suite.addTest(TestFbCollections('test_dict_set', verbose))
    suite.addTest(TestFbCollections('test_dict_del', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
