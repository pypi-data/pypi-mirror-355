#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@summary: A module for providing a configuration.

@author: Frank Brehm
@contact: frank@brehm-online.com
@copyright: © 2025 by Frank Brehm, Berlin
"""
from __future__ import absolute_import

# Standard module
import codecs
import logging
from configparser import Error as ConfigParseError
try:
    import pathlib
except ImportError:
    import pathlib2 as pathlib

# Third party modules
import six
from six import StringIO
from six.moves import configparser

# Own modules
from . import DEFAULT_ENCODING
from .errors import ConfigError
from .obj import FbBaseObject
from .xlate import XLATOR

__version__ = '2.1.2'
LOG = logging.getLogger(__name__)

_ = XLATOR.gettext


# =============================================================================
class BaseConfiguration(FbBaseObject):
    """
    A base class for providing a configuration for the BaseConfiguration class.

    It provides also methods to read it from configuration files.
    """

    default_encoding = DEFAULT_ENCODING

    # -------------------------------------------------------------------------
    def __init__(
        self, appname=None, verbose=0, version=__version__, base_dir=None,
            encoding=DEFAULT_ENCODING, config_dir=None, config_file=None, initialized=False):
        """Initialise a BaseConfiguration object."""
        self._encoding = None
        self._config_dir = None
        self._config_file = None

        super(BaseConfiguration, self).__init__(
            appname=appname, verbose=verbose, version=version,
            base_dir=base_dir, initialized=False,
        )

        if encoding:
            self.encoding = encoding
        else:
            self.encoding = self.default_encoding

        if config_dir:
            self.config_dir = config_dir
        else:
            self._config_dir = self.base_dir.joinpath('etc')

        if config_file:
            self.config_file = config_file
        else:
            self._config_file = self.config_dir.joinpath(self.appname + '.ini')

        if initialized:
            self.initialized = True

    # -------------------------------------------------------------------------
    @property
    def encoding(self):
        """Return the encoding used to read config files."""
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        if not isinstance(value, str):
            msg = _(
                'Encoding {v!r} must be a {s!r} object, '
                'but is a {c!r} object instead.').format(
                v=value, s='str', c=value.__class__.__name__)
            raise TypeError(msg)

        encoder = codecs.lookup(value)
        self._encoding = encoder.name

    # -------------------------------------------------------------------------
    @property
    def config_dir(self):
        """Return the directory containing the configuration."""
        return self._config_dir

    @config_dir.setter
    def config_dir(self, value):
        if value is None:
            raise TypeError(_('A configuration directory may not be None.'))
        cdir = pathlib.Path(value)
        if cdir.exists():
            self._config_dir = cdir.resolve()
        else:
            self._config_dir = cdir

    # -------------------------------------------------------------------------
    @property
    def config_file(self):
        """Return the configuration file."""
        return self._config_file

    @config_file.setter
    def config_file(self, value):
        if value is None:
            raise TypeError(_('A configuration file may not be None.'))

        cfile = pathlib.Path(value)
        if cfile.exists():
            if not cfile.is_file():
                msg = _('Configuration file {!r} exists, but is not a regular file.').format(
                    str(cfile))
                raise ConfigError(msg)
            self._config_file = cfile.resolve()
            return
        cfile = self.config_dir.joinpath(cfile)
        if cfile.exists():
            if not cfile.is_file():
                msg = _('Configuration file {!r} exists, but is not a regular file.').format(
                    str(cfile))
                raise ConfigError(msg)
            self._config_file = cfile.resolve()
            return
        self._config_file = cfile

    # -------------------------------------------------------------------------
    def as_dict(self, short=True):
        """
        Transform the elements of the object into a dict.

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """
        res = super(BaseConfiguration, self).as_dict(short=short)
        res['default_encoding'] = self.default_encoding
        res['encoding'] = self.encoding
        res['config_dir'] = self.config_dir
        res['config_file'] = self.config_file

        return res

    # -------------------------------------------------------------------------
    def read(self, error_if_not_exists=False):
        """Read the configuration file."""
        if self.verbose > 2:
            LOG.debug(_('Searching for {!r} ...').format(self.config_file))
        if not self.config_file.exists():
            msg = _('Configuration file {!r} not found.').format(str(self.config_file))
            if error_if_not_exists:
                self.handle_error(msg, _('Configuration file error'))
            else:
                LOG.debug(msg)
            return

        open_opts = {}
        if six.PY3 and self.encoding:
            open_opts['encoding'] = self.encoding
            open_opts['errors'] = 'surrogateescape'

        if self.verbose > 1:
            LOG.debug(_('Reading {!r} ...').format(self.config_file))

        config = configparser.ConfigParser()
        try:
            with open(str(self.config_file), 'r', **open_opts) as fh:
                stream = StringIO('[default]\n' + fh.read())
                if six.PY2:
                    config.readfp(stream)
                else:
                    config.read_file(stream)
        except ConfigParseError as e:
            msg = _('Wrong configuration in {!r} found').format(str(self.config_file))
            msg += ': ' + str(e)
            self.handle_error(msg, _('Configuration parse error'))
            return

        self.eval_config(config)

    # -------------------------------------------------------------------------
    def eval_config(self, config):
        """Evaluate all found configuration options."""
        for section_name in config.sections():

            if section_name.lower() == 'default' or section_name.lower() == 'global':
                self.eval_config_global(config, section_name)
                continue

            self.eval_config_section(config, section_name)

    # -------------------------------------------------------------------------
    def eval_config_global(self, config, section_name):
        """Evaluate section [global] of configuration.

        May be overridden in descendant classes.
        """
        if self.verbose > 1:
            LOG.debug(_('Checking config section {!r} ...').format(section_name))

        for (key, value) in config.items(section_name):
            if key.lower() == 'verbose':
                val = int(value)
                if val > self.verbose:
                    self.verbose = val

    # -------------------------------------------------------------------------
    def eval_config_section(self, config, section_name):
        """Evaluate section with given name of configuration.

        Should be overridden in descendant classes.
        """
        pass


# =============================================================================

if __name__ == '__main__':

    pass

# =============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 list
