#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@summary: Test script (and module) for unit tests on mailaddress class and objects.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 Frank Brehm, Berlin
@license: LGPL3
"""

import copy
import logging
import os
import random
import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

libdir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.insert(0, libdir)

from fb_tools.common import pp

from general import FbToolsTestcase, get_arg_verbose, init_root_logger

LOG = logging.getLogger('test_mailaddress')


# =============================================================================
class TestMailaddress(FbToolsTestcase):
    """Testcase for unit tests on module fb_tools.mailaddress and class MailAddress."""

    # -------------------------------------------------------------------------
    def setUp(self):
        """Execute this on setting up before calling each particular test method."""
        if self.verbose >= 1:
            print()

        # if 'fb_tools.mailaddress' in sys.modules:
        #     LOG.debug("Reloading module 'fb_tools.mailaddress' ...")
        #     reload(fb_tools.mailaddress)

    # -------------------------------------------------------------------------
    def tearDown(self):
        """Tear down routine for calling each particular test method."""
        # LOG.debug("Current loaded modules:\n" + pp(sys.modules))
        pass

    # -------------------------------------------------------------------------
    def test_import(self):
        """Test import of fb_tools.mailaddress."""
        LOG.info(self.get_method_doc())

        import fb_tools.mailaddress
        LOG.debug('Version of fb_tools.mailaddress: {!r}'.format(
            fb_tools.mailaddress.__version__))

    # -------------------------------------------------------------------------
    def test_object(self):
        """Test init of a simple mailaddress object."""
        LOG.info(self.get_method_doc())

        test_address = 'frank@brehm-online.com'

        from fb_tools import MailAddress

        address = MailAddress(test_address, verbose=self.verbose)
        LOG.debug('MailAddress %r: {!r}'.format(address))
        LOG.debug('MailAddress %s: {}'.format(address))

        self.assertEqual(str(address), test_address)

        other_address = MailAddress(test_address, verbose=self.verbose)
        LOG.debug('Other MailAddress: {}'.format(other_address))
        self.assertIsNot(address, other_address)
        self.assertEqual(address, other_address)

        LOG.debug('Copying address ...')
        yet_another_address = copy.copy(address)
        LOG.debug('Yet Another MailAddress: {}'.format(yet_another_address))
        self.assertIsNot(address, yet_another_address)
        self.assertEqual(address, yet_another_address)
        self.assertEqual(yet_another_address.verbose, self.verbose)

        still_another_address = MailAddress(test_address, verbose=self.verbose)
        LOG.debug('Still Another MailAddress: {}'.format(still_another_address))
        self.assertEqual(address, still_another_address)

        wrong_verboses = ('uhu', -3)
        for verb in wrong_verboses:
            LOG.debug('Testing wrong verbose level {!r} ...'.format(verb))
            with self.assertRaises((TypeError, ValueError)) as cm:
                address = MailAddress(test_address, verbose=verb)
                LOG.error('This should not be visible: {!r}'.format(address))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        expected_dict = {
            '__class_name__': 'MailAddress',
            'domain': 'brehm-online.com',
            'empty_ok': False,
            'user': 'frank',
            'verbose': self.verbose
        }
        expected_tuple = ('frank', 'brehm-online.com', self.verbose, False)

        got_dict = address.as_dict()
        LOG.debug('MailAddress.as_dict():\n' + pp(got_dict))
        self.assertEqual(got_dict, expected_dict)

        got_tuple = address.as_tuple()
        LOG.debug('MailAddress.as_tuple():\n' + pp(got_tuple))
        self.assertEqual(got_tuple, expected_tuple)

    # -------------------------------------------------------------------------
    def test_empty_address(self):
        """Test nit of an empty mailaddress object."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress
        from fb_tools.errors import BaseMailAddressError

        LOG.debug('Testing raise on init empty mail address ...')
        with self.assertRaises(BaseMailAddressError) as cm:
            address = MailAddress(verbose=self.verbose)
            LOG.error('This should not be visible: {!r}'.format(address))
        e = cm.exception
        LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        LOG.debug('Testing successful init of an empty mail address ...')
        address = MailAddress(empty_ok=True, verbose=self.verbose)
        LOG.debug('Empty MailAddress {a!r}: {s!r}'.format(
            a=address, s=str(address)))
        self.assertEqual(str(address), '')

    # -------------------------------------------------------------------------
    def test_compare(self):
        """Test comparision of mail addresses."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress

        a1 = 'uhu@banane.de'
        a2 = 'Uhu@Banane.de'
        a3 = 'frank.brehm@uhu-banane.de'
        a4 = 'frank-brehm@uhu-banane.de'

        LOG.debug('Testing equality with different verbose levels.')
        address1 = MailAddress(a1, verbose=1)
        address2 = MailAddress(a1, verbose=2)
        self.assertEqual(address1, address2)

        LOG.debug('Testing equality of addresses with different cases.')
        address1 = MailAddress(a1, verbose=self.verbose)
        address2 = MailAddress(a2, verbose=self.verbose)
        self.assertEqual(address1, address2)

        LOG.debug('Testing inequality of addresses with minor differences.')
        address1 = MailAddress(a3, verbose=self.verbose)
        address2 = MailAddress(a4, verbose=self.verbose)
        self.assertNotEqual(address1, address2)

    # -------------------------------------------------------------------------
    def test_wrong_addresses(self):
        """Test init of wrong mailaddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress
        from fb_tools.errors import BaseMailAddressError

        correct_addresses = (
            ('frank.brehm', 'frank.brehm', False),
            ('uhu_banane.de', 'uhu_banane.de', False),
            ('@uhu-banane.de', '@uhu-banane.de', True),
            ('uhu@banane.de', 'uhu@banane.de', False),
            ('Uhu@Banane.de', 'uhu@banane.de', False),
            ('ich@mueller.de', 'ich@mueller.de', False),
            ('root+bla@banane.de', 'root+bla@banane.de', False),
            ('root+bla.uhu-banane.de@banane.de', 'root+bla.uhu-banane.de@banane.de', False),
            ('root+bla+blub@banane.de', 'root+bla+blub@banane.de', False),
            ('frank.uwe@banane.de', 'frank.uwe@banane.de', False),
            ('frank.uwe.brehm@banane.de', 'frank.uwe.brehm@banane.de', False),
            ('frank-uwe.61@banane.de', 'frank-uwe.61@banane.de', False),
            ('frank_uwe@banane.de', 'frank_uwe@banane.de', False),
            ('frank_uwe.61@banane.de', 'frank_uwe.61@banane.de', False),
            ('root@localhost', 'root@localhost', False),
            ('bla@uhu.xn--j1amh', 'bla@uhu.xn--j1amh', False),
            ('uhu@xn--nschknstrt-dcbfe.de', 'uhu@xn--nschknstrt-dcbfe.de', False),
            ('me@xn--fiqz9s', 'me@xn--fiqz9s', False),
            ('@localhost', '@localhost', True),
            ('@abc.de', '@abc.de', True),
            ('@xn--fiqz9s', '@xn--fiqz9s', True),
            ('@uhu.xn--j1amh', '@uhu.xn--j1amh', True),
        )

        for token in correct_addresses:
            addr = token[0]
            expected = token[1]
            no_user_ok = token[2]
            LOG.debug('Testing mail address {a!r} => {e!r} ...'.format(a=addr, e=expected))
            address = MailAddress(addr, verbose=self.verbose, no_user_ok=no_user_ok)
            LOG.debug('Successful mail address from {s!r}: {a!r} => {r!r}'.format(
                s=addr, a=str(address), r=address))
            self.assertEqual(str(address), expected)

        wrong_addresses = (
            True, 1, ('uhu@banane.de', ), ['uhu@banane.de'], 'uhu:banane', 'uhu!banane', 'a@b@c',
            'müller.de', 'ich@Müller.de', '@uhu_banane.de', 'frank@uhu_banane.de',
        )

        for addr in wrong_addresses:
            LOG.debug('Testing wrong mail address {!r} ...'.format(addr))
            with self.assertRaises(BaseMailAddressError) as cm:
                address = MailAddress(addr, verbose=self.verbose)
                LOG.error('This should not be visible: {!r}'.format(address))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_wrong_user(self):
        """Test  wrong users on init of mailaddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress
        from fb_tools.errors import BaseMailAddressError

        domain = 'uhu-banane.de'
        correct_users = (
            None, '', 'a', 'me', 'Frank', 'Frank-Uwe', 'soeren', 'root+bla',
            'root+bla.uhu-banane.de', 'root+bla+blub'
        )
        wrong_users = (
            'Frank Uwe', 'Sören', True, 1, 'uhu:banane', 'uhu!banane', 'a@b', 'a@b@c',
            'root+bla blub'
        )

        for user in correct_users:
            LOG.debug('Testing correct user {!r} ...'.format(user))
            address = MailAddress(user=user, domain=domain, verbose=self.verbose)
            LOG.debug('Successful mail address from {u!r} (@{d}): {a!r} => {r!r}'.format(
                u=user, d=domain, a=str(address), r=address))

        for user in wrong_users:
            LOG.debug('Testing wrong user {!r} ...'.format(user))
            with self.assertRaises(BaseMailAddressError) as cm:
                address = MailAddress(user=user, domain=domain, verbose=self.verbose)
                LOG.error('This should not be visible: {!r}'.format(address))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_to_str(self):
        """Test typecasting to str."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress

        data = (
            ('uhu', 'banane.de', 'uhu@banane.de', 'uhu@banane.de'),
            ('Uhu', 'Banane.de', 'uhu@banane.de', 'uhu@banane.de'),
            ('uhu', None, 'uhu', 'uhu@'),
            (None, 'banane.de', '@banane.de', 'banane.de'),
            (None, None, '', ''),
        )

        for row in data:
            address = MailAddress(
                user=row[0], domain=row[1], verbose=self.verbose, empty_ok=True)
            LOG.debug('Testing typecasting or address {!r}.'.format(address))
            LOG.debug('Expected: Str(adress): {s!r}, adress.str_for_access(): {a!r}'.format(
                s=row[2], a=row[3]))
            addr_str = str(address)
            addr_access_str = address.str_for_access()
            LOG.debug('Str(adress): {s!r}, adress.str_for_access(): {a!r}'.format(
                s=addr_str, a=addr_access_str))
            self.assertEqual(addr_str, row[2])
            self.assertEqual(addr_access_str, row[3])

    # -------------------------------------------------------------------------
    def test_sorting_simple(self):
        """Test sorting simple MailAddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress

        addr_list = (
            ('a1', 'banane.de'),
            ('a2', 'banane.de'),
            ('uhu', 'banane.de'),
            ('Uhu', 'Banane.de'),
            ('uhu', None),
            (None, 'banane.de'),
            ('Uhu', 'xylophon.de'),
            (None, None),
        )

        expected_list = [
            '',
            'uhu',
            '@banane.de',
            'a1@banane.de',
            'a2@banane.de',
            'uhu@banane.de',
            'uhu@banane.de',
            'uhu@xylophon.de',
        ]

        result_list = []

        alist = []
        for row in random.sample(addr_list, k=len(addr_list)):
            address = MailAddress(
                user=row[0], domain=row[1], verbose=self.verbose, empty_ok=True)
            alist.append(address)
        LOG.debug('Shuffeled address list:\n{}'.format(pp(alist)))
        addr_list = sorted(alist)
        LOG.debug('Sorted address list:\n{}'.format(pp(addr_list)))
        LOG.debug('Expected address list:\n{}'.format(pp(expected_list)))
        for addr in addr_list:
            result_list.append(str(addr))
        LOG.debug('Sorted address list:\n{}'.format(pp(result_list)))
        self.assertEqual(expected_list, result_list)

    # -------------------------------------------------------------------------
    def test_qualified_address(self):
        """Test init of a qualified mailaddress object."""
        LOG.info(self.get_method_doc())

        test_user = 'frank'
        test_domain = 'brehm-online.com'
        test_address = '{u}@{d}'.format(u=test_user, d=test_domain)
        test_name = 'Frank Brehm'
        test_full_address = '{n} <{a}>'.format(n=test_name, a=test_address)

        from fb_tools import QualifiedMailAddress

        address1 = QualifiedMailAddress(test_full_address, verbose=self.verbose)
        LOG.debug('QualifiedMailAddress %r: {!r}'.format(address1))
        LOG.debug('QualifiedMailAddress %s: {!r}'.format(str(address1)))

        self.assertEqual(address1.user, test_user)
        self.assertEqual(address1.domain, test_domain)
        self.assertEqual(address1.name, test_name)

        self.assertEqual(str(address1), test_full_address)

        address2 = QualifiedMailAddress(
            user=test_user, domain=test_domain, name=test_name, verbose=self.verbose)
        LOG.debug('Other QualifiedMailAddress %r: {!r}'.format(address2))
        LOG.debug('Other QualifiedMailAddress %s: {!r}'.format(str(address2)))
        self.assertIsNot(address1, address2)
        self.assertEqual(address1, address2)

        address3 = copy.copy(address1)
        LOG.debug('Yet Another QualifiedMailAddress: {!r}'.format(str(address3)))
        self.assertIsNot(address1, address3)
        self.assertEqual(address1, address3)
        self.assertEqual(address2, address3)
        self.assertEqual(address3.verbose, self.verbose)

        test_name4 = 'Brehm, Frank'
        test_full_address4 = '"{n}" <{a}>'.format(n=test_name4, a=test_address)
        address4 = QualifiedMailAddress(test_full_address4, verbose=self.verbose)
        LOG.debug('QualifiedMailAddress %r: {!r}'.format(address4))
        LOG.debug('QualifiedMailAddress %s: {!r}'.format(str(address4)))
        self.assertEqual(address4.user, test_user)
        self.assertEqual(address4.domain, test_domain)
        self.assertEqual(address4.name, test_name4)
        self.assertEqual(str(address4), test_full_address4)

        expected_dict = {
            '__class_name__': 'QualifiedMailAddress',
            'domain': 'brehm-online.com',
            'empty_ok': False,
            'name': 'Frank Brehm',
            'user': 'frank',
            'verbose': self.verbose
        }
        expected_tuple = ('frank', 'brehm-online.com', 'Frank Brehm', self.verbose, False)

        got_dict = address1.as_dict()
        LOG.debug('MailAddress.as_dict():\n' + pp(got_dict))
        self.assertEqual(got_dict, expected_dict)

        got_tuple = address1.as_tuple()
        LOG.debug('MailAddress.as_tuple():\n' + pp(got_tuple))
        self.assertEqual(got_tuple, expected_tuple)

    # -------------------------------------------------------------------------
    def test_empty_qualified_address(self):
        """Test init of an empty qualified mailaddress object."""
        LOG.info(self.get_method_doc())

        from fb_tools import QualifiedMailAddress
        from fb_tools.errors import BaseMailAddressError

        LOG.debug('Testing raise on init empty qualified mail address ...')
        with self.assertRaises(BaseMailAddressError) as cm:
            address = QualifiedMailAddress(verbose=self.verbose)
            LOG.error('This should not be visible: {!r}'.format(address))
        e = cm.exception
        LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        LOG.debug('Testing successful init of an empty qualified mail address ...')
        address = QualifiedMailAddress(empty_ok=True, verbose=self.verbose)
        LOG.debug('Empty QualifiedMailAddress {a!r}: {s!r}'.format(
            a=address, s=str(address)))
        self.assertEqual(str(address), '<undisclosed recipient>')

    # -------------------------------------------------------------------------
    def test_wrong_init_full_address(self):
        """Test wrong init of a qualified mailaddress object."""
        LOG.info(self.get_method_doc())

        name = 'Frank Brehm'
        user = 'frank.uwe'
        domain = 'banane.de'
        addr = '{n} <{u}@{d}>'.format(n=name, u=user, d=domain)

        from fb_tools import QualifiedMailAddress

        LOG.debug(
            'Testing raise on init qualified mail address with wrong positional arguments ...')
        with self.assertRaises(TypeError) as cm:
            address = QualifiedMailAddress(addr, user, domain, verbose=self.verbose)
            LOG.error('This should not be visible: {!r}'.format(address))
        e = cm.exception
        LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        LOG.debug('Testing init qualified mail address only with keyword arguments ...')
        address = QualifiedMailAddress(user=user, domain=domain, name=name, verbose=self.verbose)
        msg = 'Successful qualified mail address from user {u!r}, domain {d!r} and '
        msg += 'name {n!r}: {a!r}.'
        LOG.debug(msg.format(u=user, d=domain, n=name, a=str(address)))
        self.assertEqual(str(address), addr)

        LOG.debug(
            'Testing raise on init qualified mail address with wrong keyword arguments ...')
        with self.assertRaises(RuntimeError) as cm:
            address = QualifiedMailAddress(addr, user=user, verbose=self.verbose)
            LOG.error('This should not be visible: {!r}'.format(address))
        e = cm.exception
        LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))
        with self.assertRaises(RuntimeError) as cm:
            address = QualifiedMailAddress(addr, domain=domain, verbose=self.verbose)
            LOG.error('This should not be visible: {!r}'.format(address))
        e = cm.exception
        LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))
        with self.assertRaises(RuntimeError) as cm:
            address = QualifiedMailAddress(addr, name=name, verbose=self.verbose)
            LOG.error('This should not be visible: {!r}'.format(address))
        e = cm.exception
        LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_wrong_qual_address(self):
        """Test init of correct and wrong  qualified mailaddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import QualifiedMailAddress
        from fb_tools.errors import BaseMailAddressError

        correct_addresses = (
            ('uhu@banane.de', 'uhu@banane.de'),
            ('Uhu@Banane.de', 'uhu@banane.de'),
            ('ich@mueller.de', 'ich@mueller.de'),
            ('root+bla@banane.de', 'root+bla@banane.de'),
            ('root+bla.uhu-banane.de@banane.de', 'root+bla.uhu-banane.de@banane.de'),
            ('root+bla+blub@banane.de', 'root+bla+blub@banane.de'),
            ('frank.uwe@banane.de', 'frank.uwe@banane.de'),
            ('frank.uwe.brehm@banane.de', 'frank.uwe.brehm@banane.de'),
            ('frank-uwe.61@banane.de', 'frank-uwe.61@banane.de'),
            ('frank_uwe@banane.de', 'frank_uwe@banane.de'),
            ('frank_uwe.61@banane.de', 'frank_uwe.61@banane.de'),
            ('Frank Brehm <frank.uwe@banane.de>', 'Frank Brehm <frank.uwe@banane.de>'),
            ('Frank Brehm    <frank.uwe@banane.de>', 'Frank Brehm <frank.uwe@banane.de>'),
            ('Frank Brehm<frank.uwe@banane.de>', 'Frank Brehm <frank.uwe@banane.de>'),
            ('<frank.uwe@banane.de>', 'frank.uwe@banane.de'),
            ('"" <frank.uwe@banane.de>', 'frank.uwe@banane.de'),
            ('" " <frank.uwe@banane.de>', '" " <frank.uwe@banane.de>'),
            ('"Frank Brehm" <frank.uwe@banane.de>', 'Frank Brehm <frank.uwe@banane.de>'),
            ('"Frank   Brehm" <frank.uwe@banane.de>', 'Frank   Brehm <frank.uwe@banane.de>'),
            ('"Brehm, Frank" <frank.uwe@banane.de>', '"Brehm, Frank" <frank.uwe@banane.de>'),
            ('"Brehm;; Frank" <frank.uwe@banane.de>', '"Brehm;; Frank" <frank.uwe@banane.de>'),
            ('"Brehm < Frank" <frank.uwe@banane.de>', '"Brehm < Frank" <frank.uwe@banane.de>'),
            ('"Brehm > Frank" <frank.uwe@banane.de>', '"Brehm > Frank" <frank.uwe@banane.de>'),
            ('"Brehm@Frank" <frank.uwe@banane.de>', '"Brehm@Frank" <frank.uwe@banane.de>'),
            ('"Brehm|Frank" <frank.uwe@banane.de>', '"Brehm|Frank" <frank.uwe@banane.de>'),
            ('Jörg Schüßler <jsc@banane.de>', 'Jörg Schüßler <jsc@banane.de>'),
        )

        for token in correct_addresses:
            addr = token[0]
            expected = token[1]
            LOG.debug('Testing qualified mail address {a!r} => {e!r} ...'.format(
                a=addr, e=expected))
            address = QualifiedMailAddress(addr, verbose=self.verbose)
            LOG.debug('Successful qualified mail address from {s!r}: {a!r} => {r!r}'.format(
                s=addr, a=str(address), r=address))
            self.assertEqual(str(address), expected)

        wrong_addresses = (
            True, 1, ('uhu@banane.de', ), ['uhu@banane.de'], 'uhu:banane', 'uhu!banane', 'a@b@c',
            'müller.de', 'ich@Müller.de', 'ich@müller', '@uhu_banane.de', 'frank@uhu_banane.de',
            'frank.brehm', 'uhu_banane.de', '@uhu-banane.de', '"Frank Brehm <frank.uwe@banane.de>',
            'Frank Brehm" <frank.uwe@banane.de>', '<frank.uwe@banane.de> "Frank Brehm"',
            'Brehm < Frank <frank.uwe@banane.de>', 'Brehm < Frank <frank.uwe@banane.de>',
            'Brehm@Frank <frank.uwe@banane.de>', 'Brehm|Frank <frank.uwe@banane.de>',
        )

        for addr in wrong_addresses:
            LOG.debug('Testing wrong mail address {!r} ...'.format(addr))
            with self.assertRaises(BaseMailAddressError) as cm:
                address = QualifiedMailAddress(addr, verbose=self.verbose)
                LOG.error('This should not be visible: {!r}'.format(address))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

    # -------------------------------------------------------------------------
    def test_qual_to_simple(self):
        """Test getting a simple MailAddress from a qualified mailaddress object."""
        LOG.info(self.get_method_doc())

        test_user = 'frank'
        test_domain = 'brehm-online.com'
        test_address = '{u}@{d}'.format(u=test_user, d=test_domain)
        test_name = 'Frank Brehm'
        test_full_address = '{n} <{a}>'.format(n=test_name, a=test_address)

        from fb_tools import MailAddress, QualifiedMailAddress

        full_address = QualifiedMailAddress(test_full_address, verbose=self.verbose)
        LOG.debug('QualifiedMailAddress: {!r}'.format(str(full_address)))

        simple_address = full_address.simple()
        LOG.debug('Simple MailAddress %r: {!r}'.format(simple_address))
        LOG.debug('Simple MailAddress %s: {!r}'.format(str(simple_address)))

        self.assertIsInstance(simple_address, MailAddress)
        self.assertNotIsInstance(simple_address, QualifiedMailAddress)
        self.assertEqual(simple_address.user, test_user)
        self.assertEqual(simple_address.domain, test_domain)
        self.assertEqual(simple_address.verbose, self.verbose)
        self.assertEqual(str(simple_address), test_address)

    # -------------------------------------------------------------------------
    def test_equality(self):
        """Test equality of MailAddress and QualifiedMailAddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress as MA
        from fb_tools import QualifiedMailAddress as QMA

        test_data = (
            (MA('frank@brehm-online.com'), MA('frank@brehm-online.com'), True),
            (MA('frank@brehm-online.com'), MA('Frank@Brehm-online.com'), True),
            (MA('frank@brehm-online.com'), QMA('frank@brehm-online.com'), True),
            (MA('frank@brehm-online.com'), QMA('Frank@Brehm-online.com'), True),
            (QMA('frank@brehm-online.com'), MA('frank@brehm-online.com'), True),
            (QMA('frank@brehm-online.com'), MA('Frank@Brehm-online.com'), True),
            (QMA('frank@brehm-online.com'), QMA('frank@brehm-online.com'), True),
            (QMA('frank@brehm-online.com'), QMA('Frank@Brehm-online.com'), True),
            (MA('frank@brehm-online.com'), None, False),
            (QMA('frank@brehm-online.com'), None, False),
            (MA('frank@brehm-online.com'), True, False),
            (QMA('frank@brehm-online.com'), True, False),
            (MA('frank@brehm-online.com'), 1, False),
            (QMA('frank@brehm-online.com'), 2, False),
            (MA('frank@brehm-online.com'), 'frank@brehm-online.com', False),
            (QMA('frank@brehm-online.com'), 'frank@brehm-online.com', False),
            (MA('frank@brehm-online.com'), [MA('frank@brehm-online.com')], False),
            (QMA('frank@brehm-online.com'), [QMA('frank@brehm-online.com')], False),
            (QMA('frank@brehm-online.com'), QMA('<Frank@Brehm-online.com>'), True),
            (QMA('frank@brehm-online.com'), QMA('"" <Frank@Brehm-online.com>'), False),
            (MA('frank@brehm-online.com'), QMA('"" <Frank@Brehm-online.com>'), False),
            (QMA('"Frank Brehm" <frank@brehm-online.com>'),
                QMA('"Frank Brehm" <Frank@Brehm-online.com>'), True),
            (QMA('"Frank Brehm" <frank@brehm-online.com>'),
                QMA('"frank brehm" <frank@brehm-online.com>'), False),
        )

        for test_tuple in test_data:
            addr1 = test_tuple[0]
            if isinstance(addr1, MA):
                addr1.verbose = self.verbose
            addr2 = test_tuple[1]
            if isinstance(addr2, MA):
                addr2.verbose = self.verbose
            expected = test_tuple[2]

            msg = 'Testing {a1!r} == {a2!r}, expected: {ex}.'
            LOG.debug(msg.format(a1=addr1, a2=addr2, ex=expected))

            result = False
            if addr1 == addr2:
                result = True
            LOG.debug('Got as result: {}.'.format(result))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_lt(self):
        """Test '<'-operator of MailAddress and QualifiedMailAddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress as MA
        from fb_tools import QualifiedMailAddress as QMA

        addr1 = MA('frank@brehm-online.com', verbose=self.verbose)
        addr2 = QMA('frank@brehm-online.com', verbose=self.verbose)

        test_data = (None, True, 1, 'frank@brehm-online.com', [addr1])

        LOG.debug("Testing '<'-operator whith a wrong comparition partner.")

        for addr in test_data:
            LOG.debug('Testing wrong mail address {!r} ...'.format(addr))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} < {a2!r}.'.format(a1=addr1, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr1 < addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} < {a2!r}.'.format(a1=addr2, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr2 < addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} < {a2!r}.'.format(a1=addr, a2=addr2))
            with self.assertRaises(TypeError) as cm:
                if addr < addr2:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        test_data = (
            (MA('frank@brehm-online.com'), MA('frank@brehm-online.com'), False),
            (MA('frank@brehm-online.com'), MA('Frank@Brehm-online.com'), False),
            (MA('frank@brehm-online.com'), QMA('frank@brehm-online.com'), False),
            (QMA('frank@brehm-online.com'), MA('frank@brehm-online.com'), False),
            (MA('frank@brehm-online.com'), QMA('"Frank" <frank@brehm-online.com>'), True),
            (QMA('"Frank" <frank@brehm-online.com>'), MA('frank@brehm-online.com'), False),
            (MA('a@brehm-online.com'), MA('b@brehm-online.com'), True),
            (MA('b@brehm-online.com'), MA('a@brehm-online.com'), False),
            (MA('a@brehm-online.com'), QMA('b@brehm-online.com'), True),
            (MA('b@brehm-online.com'), QMA('a@brehm-online.com'), False),
            (QMA('a@brehm-online.com'), MA('b@brehm-online.com'), True),
            (QMA('b@brehm-online.com'), MA('a@brehm-online.com'), False),
            (QMA('a@brehm-online.com'), QMA('b@brehm-online.com'), True),
            (QMA('b@brehm-online.com'), QMA('a@brehm-online.com'), False),
            (MA('a@brehm-online.com'), QMA('"b" <b@brehm-online.com>'), True),
            (MA('b@brehm-online.com'), QMA('"a" <a@brehm-online.com>'), False),
            (QMA('"a" <a@brehm-online.com>'), MA('b@brehm-online.com'), True),
            (QMA('"b" <b@brehm-online.com>'), MA('a@brehm-online.com'), False),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"b" <uhu@brehm-online.com>'), True),
            (QMA('"b" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), False),
            (QMA('"A" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), True),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"B" <uhu@brehm-online.com>'), True),
        )

        for test_tuple in test_data:
            addr1 = test_tuple[0]
            if isinstance(addr1, MA):
                addr1.verbose = self.verbose
            addr2 = test_tuple[1]
            if isinstance(addr2, MA):
                addr2.verbose = self.verbose
            expected = test_tuple[2]

            msg = 'Testing {a1!r} < {a2!r}, expected: {ex}.'
            LOG.debug(msg.format(a1=addr1, a2=addr2, ex=expected))

            result = False
            if addr1 < addr2:
                result = True
            if self.verbose > 2:
                LOG.debug('Got as result: {}.'.format(result))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_gt(self):
        """Test '>'-operator of MailAddress and QualifiedMailAddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress as MA
        from fb_tools import QualifiedMailAddress as QMA

        addr1 = MA('frank@brehm-online.com', verbose=self.verbose)
        addr2 = QMA('frank@brehm-online.com', verbose=self.verbose)

        test_data = (None, True, 1, 'frank@brehm-online.com', [addr1])

        LOG.debug("Testing '>'-operator whith a wrong comparition partner.")

        for addr in test_data:
            LOG.debug('Testing wrong mail address {!r} ...'.format(addr))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} > {a2!r}.'.format(a1=addr1, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr1 > addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} > {a2!r}.'.format(a1=addr2, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr2 > addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} > {a2!r}.'.format(a1=addr, a2=addr2))
            with self.assertRaises(TypeError) as cm:
                if addr > addr2:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        test_data = (
            (MA('frank@brehm-online.com'), MA('frank@brehm-online.com'), False),
            (MA('frank@brehm-online.com'), MA('Frank@Brehm-online.com'), False),
            (MA('frank@brehm-online.com'), QMA('frank@brehm-online.com'), False),
            (QMA('frank@brehm-online.com'), MA('frank@brehm-online.com'), False),
            (MA('frank@brehm-online.com'), QMA('"Frank" <frank@brehm-online.com>'), False),
            (QMA('"Frank" <frank@brehm-online.com>'), MA('frank@brehm-online.com'), True),
            (MA('a@brehm-online.com'), MA('b@brehm-online.com'), False),
            (MA('b@brehm-online.com'), MA('a@brehm-online.com'), True),
            (MA('a@brehm-online.com'), QMA('b@brehm-online.com'), False),
            (MA('b@brehm-online.com'), QMA('a@brehm-online.com'), True),
            (QMA('a@brehm-online.com'), MA('b@brehm-online.com'), False),
            (QMA('b@brehm-online.com'), MA('a@brehm-online.com'), True),
            (QMA('a@brehm-online.com'), QMA('b@brehm-online.com'), False),
            (QMA('b@brehm-online.com'), QMA('a@brehm-online.com'), True),
            (MA('a@brehm-online.com'), QMA('"b" <b@brehm-online.com>'), False),
            (MA('b@brehm-online.com'), QMA('"a" <a@brehm-online.com>'), True),
            (QMA('"a" <a@brehm-online.com>'), MA('b@brehm-online.com'), False),
            (QMA('"b" <b@brehm-online.com>'), MA('a@brehm-online.com'), True),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"b" <uhu@brehm-online.com>'), False),
            (QMA('"b" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), True),
            (QMA('"A" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), False),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"B" <uhu@brehm-online.com>'), False),
        )

        for test_tuple in test_data:
            addr1 = test_tuple[0]
            if isinstance(addr1, MA):
                addr1.verbose = self.verbose
            addr2 = test_tuple[1]
            if isinstance(addr2, MA):
                addr2.verbose = self.verbose
            expected = test_tuple[2]

            msg = 'Testing {a1!r} > {a2!r}, expected: {ex}.'
            LOG.debug(msg.format(a1=addr1, a2=addr2, ex=expected))

            result = False
            if addr1 > addr2:
                result = True
            if self.verbose > 2:
                LOG.debug('Got as result: {}.'.format(result))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_le(self):
        """Test '<='-operator of MailAddress and QualifiedMailAddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress as MA
        from fb_tools import QualifiedMailAddress as QMA

        addr1 = MA('frank@brehm-online.com', verbose=self.verbose)
        addr2 = QMA('frank@brehm-online.com', verbose=self.verbose)

        test_data = (None, True, 1, 'frank@brehm-online.com', [addr1])

        LOG.debug("Testing '<='-operator whith a wrong comparition partner.")

        for addr in test_data:
            LOG.debug('Testing wrong mail address {!r} ...'.format(addr))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} <= {a2!r}.'.format(a1=addr1, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr1 <= addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} <= {a2!r}.'.format(a1=addr2, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr2 <= addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} <= {a2!r}.'.format(a1=addr, a2=addr2))
            with self.assertRaises(TypeError) as cm:
                if addr <= addr2:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        test_data = (
            (MA('frank@brehm-online.com'), MA('frank@brehm-online.com'), True),
            (MA('frank@brehm-online.com'), MA('Frank@Brehm-online.com'), True),
            (MA('frank@brehm-online.com'), QMA('frank@brehm-online.com'), True),
            (QMA('frank@brehm-online.com'), MA('frank@brehm-online.com'), True),
            (MA('frank@brehm-online.com'), QMA('"Frank" <frank@brehm-online.com>'), True),
            (QMA('"Frank" <frank@brehm-online.com>'), MA('frank@brehm-online.com'), False),
            (MA('a@brehm-online.com'), MA('b@brehm-online.com'), True),
            (MA('b@brehm-online.com'), MA('a@brehm-online.com'), False),
            (MA('a@brehm-online.com'), QMA('b@brehm-online.com'), True),
            (MA('b@brehm-online.com'), QMA('a@brehm-online.com'), False),
            (QMA('a@brehm-online.com'), MA('b@brehm-online.com'), True),
            (QMA('b@brehm-online.com'), MA('a@brehm-online.com'), False),
            (QMA('a@brehm-online.com'), QMA('b@brehm-online.com'), True),
            (QMA('b@brehm-online.com'), QMA('a@brehm-online.com'), False),
            (MA('a@brehm-online.com'), QMA('"b" <b@brehm-online.com>'), True),
            (MA('b@brehm-online.com'), QMA('"a" <a@brehm-online.com>'), False),
            (QMA('"a" <a@brehm-online.com>'), MA('b@brehm-online.com'), True),
            (QMA('"b" <b@brehm-online.com>'), MA('a@brehm-online.com'), False),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"b" <uhu@brehm-online.com>'), True),
            (QMA('"b" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), False),
            (QMA('"A" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), True),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"B" <uhu@brehm-online.com>'), True),
        )

        for test_tuple in test_data:
            addr1 = test_tuple[0]
            if isinstance(addr1, MA):
                addr1.verbose = self.verbose
            addr2 = test_tuple[1]
            if isinstance(addr2, MA):
                addr2.verbose = self.verbose
            expected = test_tuple[2]

            msg = 'Testing {a1!r} <= {a2!r}, expected: {ex}.'
            LOG.debug(msg.format(a1=addr1, a2=addr2, ex=expected))

            result = False
            if addr1 <= addr2:
                result = True
            if self.verbose > 2:
                LOG.debug('Got as result: {}.'.format(result))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_ge(self):
        """Test '>='-operator of MailAddress and QualifiedMailAddress objects."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress as MA
        from fb_tools import QualifiedMailAddress as QMA

        addr1 = MA('frank@brehm-online.com', verbose=self.verbose)
        addr2 = QMA('frank@brehm-online.com', verbose=self.verbose)

        test_data = (None, True, 1, 'frank@brehm-online.com', [addr1])

        LOG.debug("Testing '>='-operator whith a wrong comparition partner.")

        for addr in test_data:
            LOG.debug('Testing wrong mail address {!r} ...'.format(addr))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} >= {a2!r}.'.format(a1=addr1, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr1 >= addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} >= {a2!r}.'.format(a1=addr2, a2=addr))
            with self.assertRaises(TypeError) as cm:
                if addr2 >= addr:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

            if self.verbose > 2:
                LOG.debug('Testing {a1!r} >= {a2!r}.'.format(a1=addr, a2=addr2))
            with self.assertRaises(TypeError) as cm:
                if addr >= addr2:
                    LOG.error('This should not be visible: {!r}'.format(addr))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        test_data = (
            (MA('frank@brehm-online.com'), MA('frank@brehm-online.com'), True),
            (MA('frank@brehm-online.com'), MA('Frank@Brehm-online.com'), True),
            (MA('frank@brehm-online.com'), QMA('frank@brehm-online.com'), True),
            (QMA('frank@brehm-online.com'), MA('frank@brehm-online.com'), True),
            (MA('frank@brehm-online.com'), QMA('"Frank" <frank@brehm-online.com>'), False),
            (QMA('"Frank" <frank@brehm-online.com>'), MA('frank@brehm-online.com'), True),
            (MA('a@brehm-online.com'), MA('b@brehm-online.com'), False),
            (MA('b@brehm-online.com'), MA('a@brehm-online.com'), True),
            (MA('a@brehm-online.com'), QMA('b@brehm-online.com'), False),
            (MA('b@brehm-online.com'), QMA('a@brehm-online.com'), True),
            (QMA('a@brehm-online.com'), MA('b@brehm-online.com'), False),
            (QMA('b@brehm-online.com'), MA('a@brehm-online.com'), True),
            (QMA('a@brehm-online.com'), QMA('b@brehm-online.com'), False),
            (QMA('b@brehm-online.com'), QMA('a@brehm-online.com'), True),
            (MA('a@brehm-online.com'), QMA('"b" <b@brehm-online.com>'), False),
            (MA('b@brehm-online.com'), QMA('"a" <a@brehm-online.com>'), True),
            (QMA('"a" <a@brehm-online.com>'), MA('b@brehm-online.com'), False),
            (QMA('"b" <b@brehm-online.com>'), MA('a@brehm-online.com'), True),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"b" <uhu@brehm-online.com>'), False),
            (QMA('"b" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), True),
            (QMA('"A" <uhu@brehm-online.com>'), QMA('"a" <uhu@brehm-online.com>'), False),
            (QMA('"a" <uhu@brehm-online.com>'), QMA('"B" <uhu@brehm-online.com>'), False),
        )

        for test_tuple in test_data:
            addr1 = test_tuple[0]
            if isinstance(addr1, MA):
                addr1.verbose = self.verbose
            addr2 = test_tuple[1]
            if isinstance(addr2, MA):
                addr2.verbose = self.verbose
            expected = test_tuple[2]

            msg = 'Testing {a1!r} >= {a2!r}, expected: {ex}.'
            LOG.debug(msg.format(a1=addr1, a2=addr2, ex=expected))

            result = False
            if addr1 >= addr2:
                result = True
            if self.verbose > 2:
                LOG.debug('Got as result: {}.'.format(result))
            self.assertEqual(result, expected)

    # -------------------------------------------------------------------------
    def test_init_mailaddresslist(self):
        """Test of a MailAddressList object."""
        LOG.info(self.get_method_doc())

        from fb_tools import MailAddress
        from fb_tools import QualifiedMailAddress
        from fb_tools import MailAddressList

        saddr1 = 'frank@brehm-online.com'
        qaddr1 = '"Frank Brehm" <frank@brehm-online.com>'
        saddr2 = 'a@test.com'
        saddr3 = 'b@test.com'

        sma1 = MailAddress(saddr1, verbose=self.verbose)
        qma1 = QualifiedMailAddress(qaddr1, verbose=self.verbose)

        LOG.debug('Testing init of an empty list.')
        address_list = MailAddressList(verbose=self.verbose, initialized=True)
        LOG.debug('MailAddressList %r: {!r}'.format(address_list))
        LOG.debug('MailAddressList %s: {}'.format(address_list))
        LOG.debug('MailAddressList as dict:\n{}'.format(pp(address_list.as_dict())))
        self.assertEqual(len(address_list), 0)

        LOG.debug('Testing init with a non empty list.')
        src = [saddr1, qaddr1]

        address_list = MailAddressList(*src, verbose=self.verbose, initialized=True)
        LOG.debug('MailAddressList %r: {!r}'.format(address_list))
        LOG.debug('MailAddressList %s: {}'.format(address_list))
        LOG.debug('MailAddressList as dict:\n{}'.format(pp(address_list.as_dict())))
        self.assertEqual(len(address_list), 2)
        self.assertIsInstance(address_list[0], MailAddress)
        self.assertNotIsInstance(address_list[0], QualifiedMailAddress)
        self.assertIsInstance(address_list[1], QualifiedMailAddress)

        address_list = MailAddressList(
            *src, verbose=self.verbose, may_simple=False, initialized=True)
        LOG.debug('MailAddressList %r: {!r}'.format(address_list))
        LOG.debug('MailAddressList %s: {}'.format(address_list))
        self.assertEqual(len(address_list), 2)
        self.assertIsInstance(address_list[0], QualifiedMailAddress)
        self.assertIsInstance(address_list[1], QualifiedMailAddress)

        src = [sma1, qma1]

        address_list = MailAddressList(*src, verbose=self.verbose, initialized=True)
        LOG.debug('MailAddressList %r: {!r}'.format(address_list))
        LOG.debug('MailAddressList %s: {}'.format(address_list))
        self.assertEqual(len(address_list), 2)
        self.assertIsInstance(address_list[0], MailAddress)
        self.assertNotIsInstance(address_list[0], QualifiedMailAddress)
        self.assertIsInstance(address_list[1], QualifiedMailAddress)

        address_list = MailAddressList(
            *src, verbose=self.verbose, may_simple=False, initialized=True)
        LOG.debug('MailAddressList %r: {!r}'.format(address_list))
        LOG.debug('MailAddressList %s: {}'.format(address_list))
        self.assertEqual(len(address_list), 2)
        self.assertIsInstance(address_list[0], QualifiedMailAddress)
        self.assertIsInstance(address_list[1], QualifiedMailAddress)

        LOG.debug('Testing copying of a MailAddressList.')

        address_list = MailAddressList(verbose=self.verbose, initialized=True, *src)
        copy_list = copy.copy(address_list)
        LOG.debug('Copied MailAddressList %r: {!r}'.format(copy_list))
        LOG.debug('Copied MailAddressList %s: {}'.format(copy_list))
        self.assertEqual(len(copy_list), 2)
        self.assertIsInstance(copy_list[0], MailAddress)
        self.assertNotIsInstance(copy_list[0], QualifiedMailAddress)
        self.assertIsInstance(copy_list[1], QualifiedMailAddress)
        self.assertIsNot(address_list, copy_list)
        self.assertEqual(address_list.appname, copy_list.appname)
        self.assertEqual(address_list.verbose, copy_list.verbose)
        self.assertEqual(address_list.base_dir, copy_list.base_dir)
        self.assertEqual(address_list.empty_ok, copy_list.empty_ok)
        self.assertEqual(address_list.may_simple, copy_list.may_simple)
        self.assertEqual(address_list.initialized, copy_list.initialized)
        self.assertIsNot(address_list[0], copy_list[0])
        self.assertEqual(address_list[0], copy_list[0])
        self.assertIsNot(address_list[1], copy_list[1])
        self.assertEqual(address_list[1], copy_list[1])

        LOG.debug('Testing reversing of a MailAddressList.')

        address_list = MailAddressList(verbose=self.verbose, initialized=True, *src)
        reverse_list = reversed(address_list)
        LOG.debug('Reversed MailAddressList %r: {!r}'.format(reverse_list))
        LOG.debug('Reversed MailAddressList %s: {}'.format(reverse_list))
        LOG.debug('Reversed MailAddressList as dict:\n{}'.format(pp(reverse_list.as_dict())))
        self.assertEqual(address_list[0], reverse_list[1])
        self.assertEqual(address_list[1], reverse_list[0])

        LOG.debug('Testing extending of a MailAddressList.')

        src1 = [saddr1, saddr2]
        src2 = [saddr3]
        alist1 = MailAddressList(verbose=self.verbose, initialized=True, *src1)
        wrong_appenders = (None, 1, 'uhu')

        for appender in wrong_appenders:
            with self.assertRaises(TypeError) as cm:
                alist2 = alist1 + appender
                LOG.debug('Extended MailAddressList %r: {!r}'.format(alist2))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        for appender in wrong_appenders:
            with self.assertRaises(TypeError) as cm:
                alist2 = appender + alist1
                LOG.debug('Extended MailAddressList %r: {!r}'.format(alist2))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        for appender in wrong_appenders:
            with self.assertRaises(TypeError) as cm:
                alist1 += appender
                LOG.debug('Extended MailAddressList %r: {!r}'.format(alist1))
            e = cm.exception
            LOG.debug('{c} raised: {e}'.format(c=e.__class__.__name__, e=e))

        alist_extended = alist1 + src2
        LOG.debug('Extended MailAddressList %r: {!r}'.format(alist_extended))
        self.assertEqual(len(alist_extended), 3)

        alist2 = MailAddressList(verbose=self.verbose, initialized=True, *src2)

        alist_extended = alist1 + alist2
        LOG.debug('Extended MailAddressList %r: {!r}'.format(alist_extended))
        self.assertEqual(len(alist_extended), 3)


# =============================================================================
if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    LOG.info('Starting tests ...')

    suite = unittest.TestSuite()

    suite.addTest(TestMailaddress('test_import', verbose))
    suite.addTest(TestMailaddress('test_object', verbose))
    suite.addTest(TestMailaddress('test_empty_address', verbose))
    suite.addTest(TestMailaddress('test_compare', verbose))
    suite.addTest(TestMailaddress('test_wrong_addresses', verbose))
    suite.addTest(TestMailaddress('test_wrong_user', verbose))
    suite.addTest(TestMailaddress('test_to_str', verbose))
    suite.addTest(TestMailaddress('test_sorting_simple', verbose))
    suite.addTest(TestMailaddress('test_qualified_address', verbose))
    suite.addTest(TestMailaddress('test_empty_qualified_address', verbose))
    suite.addTest(TestMailaddress('test_wrong_init_full_address', verbose))
    suite.addTest(TestMailaddress('test_wrong_qual_address', verbose))
    suite.addTest(TestMailaddress('test_qual_to_simple', verbose))
    suite.addTest(TestMailaddress('test_equality', verbose))
    suite.addTest(TestMailaddress('test_lt', verbose))
    suite.addTest(TestMailaddress('test_gt', verbose))
    suite.addTest(TestMailaddress('test_le', verbose))
    suite.addTest(TestMailaddress('test_ge', verbose))
    suite.addTest(TestMailaddress('test_init_mailaddresslist', verbose))

    runner = unittest.TextTestRunner(verbosity=verbose)

    result = runner.run(suite)


# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
