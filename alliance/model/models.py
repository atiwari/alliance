# Copyright (c) 2013-2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Defines database models for Alliance
"""
import six

import sqlalchemy as sa
from sqlalchemy.ext import compiler
from sqlalchemy.ext import declarative
from sqlalchemy import orm
from sqlalchemy.orm import collections as col
from sqlalchemy import types as sql_types

from alliance.common import exception
from alliance.common import utils
from alliance.openstack.common import jsonutils as json
from alliance.openstack.common import timeutils

LOG = utils.getLogger(__name__)
BASE = declarative.declarative_base()


# Allowed entity states
class States(object):
    PENDING = 'PENDING'
    ACTIVE = 'ACTIVE'
    ERROR = 'ERROR'

    @classmethod
    def is_valid(cls, state_to_test):
        """Tests if a state is a valid one."""
        return state_to_test in cls.__dict__

class TrustStatus(object):
    DRAFT = 'DRAFT'
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'

    @classmethod
    def is_valid(cls, state_to_test):
        """Tests if a state is a valid one."""
        return state_to_test in cls.__dict__

class AllianceRole(object):
    DRAFT = 'DRAFT'
    ACTIVE = 'ACTIVE'
    EXPIRED = 'EXPIRED'

    @classmethod
    def is_valid(cls, state_to_test):
        """Tests if a state is a valid one."""
        return state_to_test in cls.__dict__

@compiler.compiles(sa.BigInteger, 'sqlite')
def compile_big_int_sqlite(type_, compiler, **kw):
    return 'INTEGER'


class JsonBlob(sql_types.TypeDecorator):
    """JsonBlob is custom type for fields
        which need to store JSON text
    """

    impl = sa.Text

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class ModelBase(object):
    """Base class for Nova and Alliance Models."""
    __table_args__ = {'mysql_engine': 'InnoDB'}
    __table_initialized__ = False
    __protected_attributes__ = set([
        "created_at", "updated_at", "deleted_at", "deleted"])

    id = sa.Column(sa.String(36), primary_key=True,
                   default=utils.generate_uuid)

    created_at = sa.Column(sa.DateTime, default=timeutils.utcnow,
                           nullable=False)
    updated_at = sa.Column(sa.DateTime, default=timeutils.utcnow,
                           nullable=False, onupdate=timeutils.utcnow)
    deleted_at = sa.Column(sa.DateTime)
    deleted = sa.Column(sa.Boolean, nullable=False, default=False)

    status = sa.Column(sa.String(20), nullable=False, default=States.PENDING)

    def save(self, session=None):
        """Save this object."""
        # import api here to prevent circular dependency problem
        import alliance.model.repositories
        session = session or alliance.model.repositories.get_session()
        session.add(self)
        session.flush()

    def delete(self, session=None):
        """Delete this object."""
        import alliance.model.repositories
        session = session or alliance.model.repositories.get_session()
        self.deleted = True
        self.deleted_at = timeutils.utcnow()
        self.save(session=session)

        self._do_delete_children(session)

    def _do_delete_children(self, session):
        """Sub-class hook: delete children relationships."""
        pass

    def update(self, values):
        """dict.update() behaviour."""
        for k, v in values.iteritems():
            self[k] = v

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(orm.object_mapper(self).sa.Columns)
        return self

    def next(self):
        n = next(self._i).name
        return n, getattr(self, n)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        return self.__dict__.items()

    def to_dict(self):
        return self.__dict__.copy()

    def to_dict_fields(self):
        created_at = self.created_at.isoformat() if self.created_at \
            else self.created_at

        updated_at = self.updated_at.isoformat() if self.updated_at \
            else self.updated_at

        """Returns a dictionary of just the db fields of this entity."""
        dict_fields = {'created': created_at,
                       'updated': updated_at,
                       'status': self.status}
        if self.deleted_at:
            dict_fields['deleted'] = self.deleted_at.isoformat()
        if self.deleted:
            dict_fields['is_deleted'] = True
        dict_fields.update(self._do_extra_dict_fields())
        return dict_fields

    def _do_extra_dict_fields(self):
        """Sub-class hook method: return dict of fields."""
        return {}

    def _iso_to_datetime(self, expiration):
        """Convert ISO formatted string to datetime."""
        if isinstance(expiration, six.string_types):
            expiration_iso = timeutils.parse_isotime(expiration.strip())
            expiration = timeutils.normalize_time(expiration_iso)

        return expiration


class Partner(BASE, ModelBase):
    """Represents a participating cloud partner.
    """

    __tablename__ = 'partners'

    cloud_id = sa.Column(sa.String(255), primary_key=True)
    name = sa.Column(sa.String(255))
    role = sa.Column(sa.Enum('SELF','PROVIDER', 'CONSUMER','PROVCONS', name='roles'))
    trust_status = sa.Column(sa.Enum('DRAFT','ACTIVE', 'EXPIRED', name='status'))
    trust_since = sa.Column(sa.DateTime, default=None)
    trust_till = sa.Column(sa.DateTime, default=None)

    sessions = orm.relationship("PartnerSession", backref="partners")
    
    __table_args__ = (sa.UniqueConstraint('cloud_id', name='_cloud_id_uc'),)

    def __init__(self, parsed_request=None):
        """Creates Partner from a dict."""
        super(Partner, self).__init__()

        if parsed_request:
            self.cloud_id = parsed_request.get('cloud_id')
            self.name = parsed_request.get('name')
            self.role = parsed_request.get('role')
            self.trust_status = parsed_request.get('trust_status')
            self.trust_since = self._iso_to_datetime(parsed_request.get
                                               ('trust_since'))
            self.trust_till = self._iso_to_datetime(parsed_request.get
                                               ('trust_till'))
            self.status = States.ACTIVE

    def _do_extra_dict_fields(self):
        """Sub-class hook method: return dict of fields."""
        return {'id': self.id,
                'cloud_id': self.cloud_id,
                'name': self.name or self.id,
                'role': self.role,
                'trust_status': self.trust_status,
                'trust_since': self.trust_since.isoformat() if self.trust_since
                    else self.trust_since,
                'trust_till': self.trust_till.isoformat() if self.trust_till
                    else self.trust_till}

class PartnerSession(BASE, ModelBase):
    """Represents a participating cloud partner.
    """

    __tablename__ = 'partner_session'

    cloud_id = sa.Column(sa.String(36), sa.ForeignKey('partners.cloud_id'))
    session_key = sa.Column(sa.String(255), nullable=False)
    login_time = sa.Column(sa.DateTime, default=None)
    valid_till = sa.Column(sa.DateTime, default=None)

    __table_args__ = (sa.UniqueConstraint('cloud_id', name='_cloud_id_uc'),)

# Keep this tuple synchronized with the models in the file
MODELS = [Partner, PartnerSession]


def register_models(engine):
    """Creates database tables for all models with the given engine."""
    LOG.debug("Models: {0}".format(repr(MODELS)))
    for model in MODELS:
        model.metadata.create_all(engine)


def unregister_models(engine):
    """Drops database tables for all models with the given engine."""
    for model in MODELS:
        model.metadata.drop_all(engine)
