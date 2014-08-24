"""
Configuration setup for Alliance.
"""

import logging
import os

from oslo.config import cfg

#import alliance.version

CONF = cfg.CONF
CONF.import_opt('verbose', 'alliance.openstack.common.log')
CONF.import_opt('debug', 'alliance.openstack.common.log')
CONF.import_opt('log_dir', 'alliance.openstack.common.log')
CONF.import_opt('log_file', 'alliance.openstack.common.log')
CONF.import_opt('log_config_append', 'alliance.openstack.common.log')
CONF.import_opt('log_format', 'alliance.openstack.common.log')
CONF.import_opt('log_date_format', 'alliance.openstack.common.log')
CONF.import_opt('use_syslog', 'alliance.openstack.common.log')
CONF.import_opt('syslog_log_facility', 'alliance.openstack.common.log')

LOG = logging.getLogger(__name__)


def parse_args(args=None, usage=None, default_config_files=None):
    CONF(args=args,
         project='alliance',
         prog='alliance',
         version='poc.000',
         usage=usage,
         default_config_files=default_config_files)

    #CONF.pydev_debug_host = os.environ.get('PYDEV_DEBUG_HOST')
    #CONF.pydev_debug_port = os.environ.get('PYDEV_DEBUG_PORT')

"""
def setup_remote_pydev_debug():
    Required setup for remote debugging.

    if CONF.pydev_debug_host and CONF.pydev_debug_port:
        try:
            try:
                from pydev import pydevd
            except ImportError:
                import pydevd

            pydevd.settrace(CONF.pydev_debug_host,
                            port=int(CONF.pydev_debug_port),
                            stdoutToServer=True,
                            stderrToServer=True)
        except Exception:
            LOG.exception('Unable to join debugger, please '
                          'make sure that the debugger processes is '
                          'listening on debug-host \'%s\' debug-port \'%s\'.',
                          CONF.pydev_debug_host, CONF.pydev_debug_port)
            raise
"""