"""
Common utilities for Alliance.
"""

import time
import uuid
import os
import six
import json
import datetime
from alliance.openstack.common import timeutils
from alliance.thrift.service.ttypes import SessionTKT
from oslo.config import cfg

import alliance.openstack.common.log as logging
from alliance.common import dtos 


host_opts = [
    cfg.StrOpt('host_href', default='http://localhost:9311'),
]

CONF = cfg.CONF
CONF.register_opts(host_opts)


# Current API version
API_VERSION = 'v1'


def hostname_for_refs(keystone_id=None, resource=None):
    """Return the HATEOS-style return URI reference for this service."""
    ref = ['{0}/{1}'.format(CONF.host_href, API_VERSION)]
    if not keystone_id:
        return ref[0]
    ref.append('/' + keystone_id)
    if resource:
        ref.append('/' + resource)
    return ''.join(ref)

def getLogger(name):
    return logging.getLogger(name)

class JsonEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__


class TimeKeeper(object):
    """Keeps track of elapsed times and then allows for dumping a summary to
    logs. This class can be used to profile a method as a fine grain level.
    """

    def __init__(self, name, logger=None):
        self.logger = logger or getLogger(__name__)
        self.name = name
        self.time_start = time.time()
        self.time_last = self.time_start
        self.elapsed = []

    def mark(self, note=None):
        """Mark a moment in time, with an optional note as to what is
        occurring at the time.
        :param note: Optional note
        """
        time_curr = time.time()
        self.elapsed.append((time_curr, time_curr - self.time_last, note))
        self.time_last = time_curr

    def dump(self):
        """Dump the elapsed time(s) to log."""
        self.logger.debug("Timing output for '{0}'".format(self.name))
        for timec, timed, note in self.elapsed:
            self.logger.debug("    time current/elapsed/notes:"
                              "{0:.3f}/{1:.0f}/{2}".format(timec,
                                                           timed * 1000.,
                                                           note))
        time_current = time.time()
        total_elapsed = time_current - self.time_start
        self.logger.debug("    Final time/elapsed:"
                          "{0:.3f}/{1:.0f}".format(time_current,
                                                   total_elapsed * 1000.))


def generate_uuid():
    return str(uuid.uuid4())

def get_key_rsa_keys(cloud_id):

        key_dir = os.path.abspath(os.path.join(os.path.dirname( __file__ ),
                                               '../..', ('etc/keys/%s/' %cloud_id)))
        key_dto = dtos.KeyDTO(passphrase='alliance',
                                     public_key_file=os.path.join(key_dir,'id_rsa.pub'),
                                     private_key_file=os.path.join(key_dir,'id_rsa')) 
        return key_dto

def iso2datetime(iso_time):
            """Convert ISO formatted string to datetime."""
            if isinstance(iso_time, six.string_types):
                iso_time = timeutils.parse_isotime(iso_time.strip())
                return timeutils.normalize_time(iso_time)

def is_valid_session(partner_session):
    now = datetime.datetime.now()
    delta = now - partner_session.valid_till
    sec_delta = 24*60*60*delta.days + delta.seconds + delta.microseconds/1000000.
    if sec_delta < 0:
        return True
    return False
    #raise exception.AllianceException('session expired')