#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: The module for the classes of the update-ddns application.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import, print_function

# Standard modules
import copy
import datetime
import ipaddress
import logging
import os
import re
import time
from pathlib import Path

# Third party module
from babel.dates import LOCALTZ

from six.moves.urllib.parse import quote

import yaml

# Own modules
from . import BaseDdnsApplication
from .config import DdnsConfiguration
from .errors import DdnsAppError
from .errors import InvalidUpdateStatusFileError
from .. import __version__ as GLOBAL_VERSION
from ..common import pp
from ..errors import CommonDirectoryError
from ..errors import DirectoryAccessError
from ..errors import DirectoryNotDirError
from ..errors import DirectoryNotExistsError
from ..errors import FileAccessError
from ..errors import FileNotExistsError
from ..errors import FileNotRegularFileError
from ..handling_obj import HandlingObject
from ..xlate import XLATOR, format_list

__version__ = '2.4.3'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class UpdateDdnsStatus(HandlingObject):
    """
    A class encapsulating the last or current status of updating DDNS.

    It contains methods for reading or writing a status file.
    """

    re_has_whitespace = re.compile(r'\s')

    # -------------------------------------------------------------------------
    def __init__(
            self, domain, workdir=None, version=__version__, initialized=False,
            timestamp=None, status_code=None, status_text=None,
            *args, **kwargs):
        """Initialise a UpdateDdnsStatus object."""
        self._domain = None
        self._workdir = None
        self._timestamp = time.time()
        self._status_code = None
        self._status_text = None

        super(UpdateDdnsStatus, self).__init__(
            version=version,
            initialized=False,
            *args, **kwargs
        )

        if workdir:
            self.workdir = workdir
        else:
            self.workdir = self.base_dir / 'status'

        if domain:
            self.domain = domain

        if not self.domain:
            msg = _('No valid domain given on initialization of a {} object.').format(
                self.__class__.__name__)
            raise ValueError(msg)

        if status_code:
            self.status_code = status_code

        if status_text:
            self.status_text = status_text

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def domain(self):
        """Return the domain, for which the status is held."""
        return self._domain

    @domain.setter
    def domain(self, value):
        if value is None:
            self._domain = None
            return
        val = str(value).strip()
        if val == '':
            self._domain = None
            return

        if self.re_has_whitespace.search(val):
            msg = _('Invalid domain {!r} given, whitespaces are not allowed.').format(value)
            raise ValueError(msg)

        self._domain = val

    # -------------------------------------------------------------------------
    @property
    def workdir(self):
        """Return the working directory, wher to search, read and write the status file."""
        return self._workdir

    @workdir.setter
    def workdir(self, value):
        if value is None:
            self._workdir = None
            return

        workdir = Path(value)
        if not workdir.is_absolute():
            workdir = workdir.resolve()

        self._workdir = workdir

    # -------------------------------------------------------------------------
    @property
    def filename_base(self):
        """Return the base filename for reading the last or writing the current update status."""
        if not self.domain:
            return None

        return 'status.update-ddns.{}.yaml'.format(self.domain)

    # -------------------------------------------------------------------------
    @property
    def filename_abs(self):
        """Return the absolute filename for the update status file."""
        if not self.filename_base:
            return None

        return self.workdir / self.filename_base

    # -------------------------------------------------------------------------
    @property
    def timestamp(self):
        """Return the UNIX timestamp of the update."""
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        if value is None:
            msg = _('A timestamp must not be None.')
            raise TypeError(msg)
        self._timestamp = float(value)

    # -------------------------------------------------------------------------
    @property
    def update_date(self):
        """Return the timestamp of the update as a datetime.datetime object."""
        return datetime.datetime.fromtimestamp(self.timestamp, LOCALTZ)

    # -------------------------------------------------------------------------
    @property
    def status_code(self):
        """Return the numeric status code of the update."""
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        if value is None:
            self._status_code = None
        else:
            self._status_code = int(value)

    # -------------------------------------------------------------------------
    @property
    def status_text(self):
        """Return the textual reason of responded HTTP Status of the update."""
        return self._status_text

    @status_text.setter
    def status_text(self, value):
        if value is None:
            self._status_text = None
            return
        val = str(value).strip()
        if val == '':
            self._status_text = None
            return
        self._status_text = val

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(UpdateDdnsStatus, self).as_dict(short=short)

        res['domain'] = self.domain
        res['filename_base'] = self.filename_base
        res['filename_abs'] = self.filename_abs
        res['status_code'] = self.status_code
        res['status_text'] = self.status_text
        res['timestamp'] = self.timestamp
        res['update_date'] = self.update_date
        res['workdir'] = self.workdir

        return res

    # -------------------------------------------------------------------------
    def check_workdir(self, check_writeable=False):
        """
        Check current working directory.

        Raise a kind of CommonDirectoryError, if it is not useable.
        """
        if self.verbose > 1:
            LOG.debug(_('Checking working directory {d!r} for updating {what} ...').format(
                d=str(self.workdir), what='DDNS'))

        if not isinstance(self.workdir, Path):
            raise CommonDirectoryError(self.workdir, _('working directory is not a path object.'))

        if not self.workdir.exists():
            raise DirectoryNotExistsError(self.workdir)

        if not self.workdir.is_dir():
            raise DirectoryNotDirError(self.workdir)

        if not os.access(self.workdir, os.R_OK | os.X_OK):
            raise DirectoryAccessError(self.workdir, _('working directory is not readable.'))

        if check_writeable:
            if not os.access(self.workdir, os.W_OK):
                raise DirectoryAccessError(self.workdir, _('working directory is not writeable.'))

    # -------------------------------------------------------------------------
    def check_statusfile(self, check_writeable=False, raise_on_not_existing=False):
        """Check a status YAML file."""
        if self.verbose > 1:
            LOG.debug(_('Checking update status file {!r} ...').format(str(self.filename_abs)))

        if not self.filename_abs.exists():
            if raise_on_not_existing:
                raise FileNotExistsError(self.filename_abs)
            LOG.debug(_('Update status file {!r} does not exists.').format(
                str(self.filename_abs)))
            return

        if not self.filename_abs.is_file():
            raise FileNotRegularFileError(self.filename_abs)

        if not os.access(self.filename_abs, os.R_OK):
            raise FileAccessError(self.filename_abs, _('update status file is not readable.'))

        if check_writeable:
            if not os.access(self.filename_abs, os.W_OK):
                raise FileAccessError(
                    self.filename_abs, _('update status file is not writeable.'))

    # -------------------------------------------------------------------------
    def write_status(self):
        """Write the current update status into a status YAML file."""
        LOG.debug(_('Write status into {!r} ...').format(str(self.filename_abs)))

        if self.filename_abs.exists():
            self.check_statusfile(check_writeable=True)
        else:
            self.check_workdir(check_writeable=True)

        data = {
            'domain': self.domain,
            'status_code': self.status_code,
            'status_text': self.status_text,
            'timestamp': self.timestamp,
            'update_date': self.update_date.isoformat(' ')
        }

        if self.verbose > 1:
            LOG.debug(_('Data to write in status file:') + '\n' + pp(data))

        if self.simulate:
            msg = _('Simulation mode, file {!r} will not be written.').format(
                str(self.filename_abs))
            LOG.info(msg)
            return

        with self.filename_abs.open('wt', encoding='utf-8', errors='surrogateescape') as fh:
            yaml.dump(
                data, fh, Dumper=yaml.SafeDumper, explicit_start=True,
                width=99, default_flow_style=False)

    # -------------------------------------------------------------------------
    def read_status(self):
        """Read the last update status from a status YAML file."""
        LOG.debug(_('Read status from {!r} ...').format(str(self.filename_abs)))

        self.check_statusfile(raise_on_not_existing=True)

        with self.filename_abs.open('rt', encoding='utf-8', errors='surrogateescape') as fh:
            data = yaml.safe_load(fh)

        if self.verbose > 1:
            LOG.debug(_('Read data from YAML:') + '\n' + pp(data))

        if 'status_code' in data:
            self.status_code = data['status_code']

        if 'status_text' in data:
            self.status_text = data['status_text']

        if 'timestamp' in data:
            self.timestamp = data['timestamp']
        else:
            raise InvalidUpdateStatusFileError(
                self.filename_abs, _('no timestamp of last update found.'))


# =============================================================================
class UpdateDdnsApplication(BaseDdnsApplication):
    """Class for the application objects."""

    show_assume_options = False
    show_console_timeout_option = False
    show_force_option = True
    show_simulate_option = True

    default_logfile = Path('/var/log/ddns/ddnss-update.log')

    # -------------------------------------------------------------------------
    def __init__(
        self, version=GLOBAL_VERSION, initialized=None, description=None,
            *args, **kwargs):
        """Initialise a UpdateDdnsApplication object."""
        self.last_ipv4_address = None
        self.last_ipv6_address = None
        self.current_ipv4_address = None
        self.current_ipv6_address = None
        self.txt_records = []
        self.cur_resolved_addresses = {}
        self.forced_update_interval = DdnsConfiguration.default_forced_update_interval
        self.last_update_timestamp = None

        self._force_desc_msg = _('Updating the DDNS records, even if seems not to be changed.')

        if description is None:
            description = _(
                'Tries to update the A and/or AAAA record at ddns.de with the current '
                'IP address.')
        valid_proto_list = copy.copy(DdnsConfiguration.valid_protocols)

        self._ipv4_help = _('Update only the {} record with the public IP address.').format('A')
        self._ipv6_help = _('Update only the {} record with the public IP address.').format('AAAA')
        self._proto_help = _(
            'The IP protocol, for which the appropriate DNS record should be updated with the '
            'public IP (one of {c}, default {d!r}).').format(c=format_list(
                valid_proto_list, do_repr=True, style='or'), d='any')

        super(UpdateDdnsApplication, self).__init__(
            version=version,
            description=description,
            initialized=False,
            *args, **kwargs
        )

        if initialized is None:
            self.initialized = True
        else:
            if initialized:
                self.initialized = True

    # -------------------------------------------------------------------------
    def init_arg_parser(self):
        """Initiate the argument parser."""
        update_group = self.arg_parser.add_argument_group(_('Update DDNS options'))

        update_group.add_argument(
            '-U', '--user', metavar=_('USER'), dest='user',
            help=_('The username to login at ddns.de.')
        )

        update_group.add_argument(
            '-P', '--password', metavar=_('PASSWORD'), dest='password',
            help=_('The password of the user to login at ddns.de.')
        )

        domain_group = update_group.add_mutually_exclusive_group()

        domain_group.add_argument(
            '-A', '--all', '--all-domains', action='store_true', dest='all_domains',
            help=_('Update all domains, which are connected whith the given ddns account.'),
        )

        domain_group.add_argument(
            '-D', '--domain', nargs='+', metavar=_('DOMAIN'), dest='domains',
            help=_('The particular domain(s), which should be updated (if not all).')
        )

        super(UpdateDdnsApplication, self).init_arg_parser()

    # -------------------------------------------------------------------------
    def post_init(self):
        """
        Execute post-init actions.

        Method to execute before calling run(). Here could be done some
        finishing actions after reading in commandline parameters,
        configuration a.s.o.
        """
        super(UpdateDdnsApplication, self).post_init()
        self.initialized = False
        self.forced_update_interval = self.cfg.forced_update_interval.total_seconds()

        self.perform_arg_parser_late()

        self.initialized = True

    # -------------------------------------------------------------------------
    def perform_arg_parser_late(self):
        """Execute some actions after parsing the command line parameters."""
        if self.args.user:
            user = self.args.user.strip()
            if user:
                self.cfg.ddns_user = user

        if self.args.password:
            self.cfg.ddns_pwd = self.args.password

        if self.args.all_domains:
            self.cfg.all_domains = True
        elif self.args.domains:
            self.cfg.domains = []
            for domain in self.args.domains:
                self.cfg.domains.append(domain)

    # -------------------------------------------------------------------------
    def _run(self):

        LOG.info(_('Starting {a!r}, version {v!r} ...').format(
            a=self.appname, v=self.version))

        if self.cfg.all_domains:
            self.update_all()
        else:
            self.get_current_addresses()
            for domain in self.cfg.domains:
                self.last_update_timestamp = None
                self.get_last_update(domain)
                self.update_domain(domain)
        self.empty_line()

        LOG.info(_('Ending {a!r}.').format(
            a=self.appname, v=self.version))

    # -------------------------------------------------------------------------
    def pre_run(self):
        """Execute some actions before the main routine."""
        if self.verbose > 1:
            LOG.debug(_('Actions before running.'))

        if not self.cfg.all_domains and not self.cfg.domains:
            msg = _('No domains to update given, but the option all domains is deactivated.')
            LOG.error(msg)
            self.exit(6)

        # try:
        #     self.verify_working_dir()
        # except WorkDirError as e:
        #     LOG.error(str(e))
        #     self.exit(3)

    # -------------------------------------------------------------------------
    def get_current_addresses(self):
        """Get the current addresses."""
        self.current_ipv4_address = None
        current_address_v4 = self.get_my_ipv(4)
        my_ip_v4 = None
        if current_address_v4:
            try:
                my_ip_v4 = ipaddress.ip_address(current_address_v4)
                self.current_ipv4_address = my_ip_v4
                LOG.info(_('Found current {t} address {a}.').format(t='IPv4', a=my_ip_v4))
            except ValueError as e:
                msg = _('Address {a!r} seems not to be a valid {w} address: {e}').format(
                    a=current_address_v4, w='IPv4', e=e)
                LOG.error(msg)
        else:
            LOG.error(_('Got no public {} address.').format('IPv4'))
        self.current_ipv4_address = my_ip_v4

        self.current_ipv6_address = None
        current_address_v6 = self.get_my_ipv(6)
        my_ip_v6 = None
        if current_address_v6:
            try:
                my_ip_v6 = ipaddress.ip_address(current_address_v6)
                self.current_ipv6_address = my_ip_v6
                LOG.info(_('Found current {t} address {a}.').format(t='IPv6', a=my_ip_v6))
            except ValueError as e:
                msg = _('Address {a!r} seems not to be a valid {w} address: {e}').format(
                    a=current_address_v6, w='IPv6', e=e)
                LOG.error(msg)
        else:
            LOG.error(_('Got no public {} address.').format('IPv5'))
        self.current_ipv6_address = my_ip_v6

        if not self.cfg.all_domains:
            for domain in self.cfg.domains:
                addresses = self.resolve_address(domain)
                self.cur_resolved_addresses[domain] = addresses

        LOG.info(_('Currently configured dynamic addresses:') + '\n' + pp(
            self.cur_resolved_addresses))

    # -------------------------------------------------------------------------
    def get_last_update(self, domain):
        """Try to get the timestamp of the last update of the domain."""
        update_status = UpdateDdnsStatus(
            appname=self.appname, verbose=self.verbose, simulate=self.simulate,
            domain=domain, workdir=self.cfg.working_dir)

        if not update_status.filename_abs.exists():
            LOG.info(_('Did not found update status file {!r}.').format(
                str(update_status.filename_abs)))
            return

        try:
            update_status.read_status()
        except Exception as e:
            msg = _('{c} - could not evaluate update status file {f!r}: {e}').format(
                c=e.__class__.__name__, f=str(update_status.filename_abs), e=e)
            LOG.error(msg)
            return

        LOG.debug(_('Last update was at {dt} with status {st!r}.').format(
            dt=update_status.update_date.isoformat(' '), st=update_status.status_code))
        self.last_update_timestamp = update_status.timestamp

    # -------------------------------------------------------------------------
    def check_for_update_domain(self, domain):
        """Return, whether a domain should be updated on DDNSS."""
        do_update = False

        if self.cfg.protocol in ('any', 'ipv4'):
            if self.current_ipv4_address:
                if self.current_ipv4_address not in self.cur_resolved_addresses[domain]:
                    do_update = True
            else:
                for addr in self.cur_resolved_addresses[domain]:
                    if addr.version == 4:
                        do_update = True

        if self.cfg.protocol in ('any', 'ipv6'):
            if self.current_ipv6_address:
                if self.current_ipv6_address not in self.cur_resolved_addresses[domain]:
                    do_update = True
            else:
                for addr in self.cur_resolved_addresses[domain]:
                    if addr.version == 6:
                        do_update = True

        if self.last_update_timestamp is None:
            do_update = True
        elif self.last_update_timestamp > 0:
            timediff = time.time() - self.last_update_timestamp
            if self.verbose:
                delta = datetime.timedelta(seconds=timediff)
                LOG.debug(_('Last update of domain {dom!r} is {delta} ago.').format(
                    dom=domain, delta=delta))
            if timediff >= self.forced_update_interval:
                do_update = True

        return do_update

    # -------------------------------------------------------------------------
    def update_domain(self, domain):
        """Update an IPv4 addresses of the given domain."""
        self.empty_line()
        LOG.debug(_('Checking the need for updating the given domain {!r}.').format(domain))

        do_update = self.check_for_update_domain(domain)

        if not do_update:
            if self.force:
                LOG.info(_(
                    'Updating the DDNS records of domain {!r}, although if they seems not '
                    'to be changed.').format(domain))
            else:
                LOG.info(_('Update of domain {!r} is not necessary.').format(domain))
                return
        else:
            LOG.info(_('Updating the DDNS records of domain {!r}.').format(domain))

        url = self.cfg.upd_url

        args = []
        args_out = []

        arg = 'user=' + quote(self.cfg.ddns_user)
        args.append(arg)
        args_out.append(arg)

        arg = 'pwd=' + quote(self.cfg.ddns_pwd)
        args.append(arg)
        args_out.append('pwd=******')

        arg = 'host=' + quote(domain)
        args.append(arg)
        args_out.append(arg)

        if self.cfg.protocol in ('any', 'ipv4') and self.current_ipv4_address:
            arg = 'ip=' + quote(str(self.current_ipv4_address))
            args.append(arg)
            args_out.append(arg)

        if self.cfg.protocol in ('any', 'ipv6') and self.current_ipv6_address:
            arg = 'ip6=' + quote(str(self.current_ipv6_address))
            args.append(arg)
            args_out.append(arg)

        if self.cfg.with_mx:
            args.append('mx=1')
            args.append(arg)
            args_out.append(arg)

        url_out = url + '?' + '&'.join(args_out)
        url += '?' + '&'.join(args)
        LOG.debug('Update-URL: {}'.format(url_out))
        # LOG.debug('Update-URL: {}'.format(url))

        if self.simulate:
            self.empty_line()
            LOG.info(_('Simulation mode, update of domain {!r} will not be sended.').format(
                domain))

            return True

        self.empty_line()
        try:
            resp = self.perform_request(url, return_json=False)
        except DdnsAppError as e:
            LOG.error(str(e))
            return None

        response = resp[0]
        status_code = resp[1]
        status_text = resp[2]

        msg = _('No response from {}.').format('DDNSS')
        if response:
            msg = _('Response from {}:').format('DDNSS')

        msg_status = _('Status code: {c}, status text: {r!r}.').format(
            c=status_code, r=status_text)

        if self.quiet:
            LOG.info(msg + '\n' + msg_status + '\n' + response)
        else:
            if response:
                text_len = len(msg)
                print(self.colored(msg, 'CYAN'))
                self.line(text_len, color='CYAN')
                print(response)
            else:
                print(self.colored(msg, 'CYAN'))

        update_status = UpdateDdnsStatus(
            appname=self.appname, verbose=self.verbose, simulate=self.simulate,
            domain=domain, workdir=self.cfg.working_dir,
            status_code=status_code, status_text=status_text,
        )
        if self.verbose > 3:
            LOG.debug('UpdateDdnsStatus object:\n' + pp(update_status.as_dict()))

        update_status.write_status()

        return True

    # -------------------------------------------------------------------------
    def update_all(self):
        """Update all domains at DDNSS with found dynamic external addresses."""
        self.empty_line()
        LOG.info(_('Update all domains at {} with found dynamic external addresses ...').format(
            'DDNSS'))

        url = self.cfg.upd_url

        args = []
        args_out = []

        arg = 'user=' + quote(self.cfg.ddns_user)
        args.append(arg)
        args_out.append(arg)

        arg = 'pwd=' + quote(self.cfg.ddns_pwd)
        args.append(arg)
        args_out.append('pwd=******')

        arg = 'host=all'
        args.append(arg)
        args_out.append(arg)

        if self.cfg.protocol in ('any', 'ipv4') and self.current_ipv4_address:
            arg = 'ip=' + quote(str(self.current_ipv4_address))
            args.append(arg)
            args_out.append(arg)

        if self.cfg.protocol in ('any', 'ipv6') and self.current_ipv6_address:
            arg = 'ip6=' + quote(str(self.current_ipv6_address))
            args.append(arg)
            args_out.append(arg)

        if self.cfg.with_mx:
            args.append('mx=1')
            args.append(arg)
            args_out.append(arg)

        url_out = url + '?' + '&'.join(args_out)
        url += '?' + '&'.join(args)
        LOG.debug('Update-URL: {}'.format(url_out))
        # LOG.debug('Update-URL: {}'.format(url))

        if self.simulate:
            self.empty_line()
            LOG.info(_('Simulation mode, update of all domains will not be sended.'))

            return True

        self.empty_line()
        try:
            resp = self.perform_request(url, return_json=False)
        except DdnsAppError as e:
            LOG.error(str(e))
            return None

        response = resp[0]
        status_code = resp[1]
        status_text = resp[2]

        msg = _('No response from {}.').format('DDNSS')
        if response:
            msg = _('Response from {}:').format('DDNSS')

        msg_status = _('Status code: {c}, status text: {r!r}.').format(
            c=status_code, r=status_text)

        if self.quiet:
            LOG.info(msg + '\n' + msg_status + '\n' + response)
        else:
            if response:
                text_len = len(msg)
                print(self.colored(msg, 'CYAN'))
                self.line(text_len, color='CYAN')
                print(response)
            else:
                print(self.colored(msg, 'CYAN'))

        return True


# =============================================================================
if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
