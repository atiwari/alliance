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
Defines interface for DB access that Resource controllers may reference

TODO: The top part of this file was 'borrowed' from Glance, but seems
quite intense for sqlalchemy, and maybe could be simplified.
"""


import logging
import time
import uuid

from oslo.config import cfg

import sqlalchemy
#from sqlalchemy import or_
import sqlalchemy.orm as sa_orm

from alliance.common import exception
from alliance.common import utils
from alliance.model.migration import commands
from alliance.model import models
from alliance.openstack.common import gettextutils as u
from alliance.openstack.common import timeutils

LOG = utils.getLogger(__name__)


_ENGINE = None
_MAKER = None
_MAX_RETRIES = None
_RETRY_INTERVAL = None
BASE = models.BASE
sa_logger = None


db_opts = [
    cfg.IntOpt('sql_idle_timeout', default=3600),
    cfg.IntOpt('sql_max_retries', default=60),
    cfg.IntOpt('sql_retry_interval', default=1),
    cfg.BoolOpt('db_auto_create', default=True),
    cfg.StrOpt('sql_connection'),
    cfg.IntOpt('max_limit_paging', default=100),
    cfg.IntOpt('default_limit_paging', default=10),
]

CONF = cfg.CONF
#FIXME (atiwari): This should come from config
CONF.sql_connection = 'sqlite:////var/lib/alliance/alliance.sqlite'
CONF.register_opts(db_opts)
CONF.import_opt('debug', 'alliance.openstack.common.log')

_CONNECTION = None
_IDLE_TIMEOUT = None


def setup_db_env():
    """Setup configuration for database."""
    global sa_logger, _IDLE_TIMEOUT, _MAX_RETRIES, _RETRY_INTERVAL, _CONNECTION

    _IDLE_TIMEOUT = CONF.sql_idle_timeout
    _MAX_RETRIES = CONF.sql_max_retries
    _RETRY_INTERVAL = CONF.sql_retry_interval
    _CONNECTION = CONF.sql_connection
    LOG.debug("Sql connection = {0}".format(_CONNECTION))
    sa_logger = logging.getLogger('sqlalchemy.engine')
    if CONF.debug:
        sa_logger.setLevel(logging.DEBUG)


def configure_db():
    """Establish the database, create an engine if needed, and
    register the models.
    """
    setup_db_env()
    get_engine()


def get_session(autocommit=True, expire_on_commit=False):
    """Helper method to grab session."""
    global _MAKER
    if not _MAKER:
        get_engine()
        get_maker(autocommit, expire_on_commit)
        assert(_MAKER)
    session = _MAKER()
    return session


def get_engine():
    """Return a SQLAlchemy engine."""
    """May assign _ENGINE if not already assigned"""
    global _ENGINE, sa_logger, _CONNECTION, _IDLE_TIMEOUT, _MAX_RETRIES, \
        _RETRY_INTERVAL

    if not _ENGINE:
        if not _CONNECTION:
            raise exception.AllianceException('No _CONNECTION configured')

    #TODO(jfwood) connection_dict = sqlalchemy.engine.url.make_url(_CONNECTION)

        engine_args = {
            'pool_recycle': _IDLE_TIMEOUT,
            'echo': False,
            'convert_unicode': True}

        try:
            LOG.debug("Sql connection: {0}; Args: {1}".format(_CONNECTION,
                                                              engine_args))
            _ENGINE = sqlalchemy.create_engine(_CONNECTION, **engine_args)

        #TODO(jfwood): if 'mysql' in connection_dict.drivername:
        #TODO(jfwood): sqlalchemy.event.listen(_ENGINE, 'checkout',
        #TODO(jfwood):                         ping_listener)

            _ENGINE.connect = wrap_db_error(_ENGINE.connect)
            _ENGINE.connect()
        except Exception as err:
            msg = u._("Error configuring registry database with supplied "
                      "sql_connection. Got error: %s") % err
            LOG.exception(msg)
            raise

        sa_logger = logging.getLogger('sqlalchemy.engine')
        if CONF.debug:
            sa_logger.setLevel(logging.DEBUG)

        if CONF.db_auto_create:
            meta = sqlalchemy.MetaData()
            meta.reflect(bind=_ENGINE)
            tables = meta.tables
            if tables and 'alembic_version' in tables:
                # Upgrade the database to the latest version.
                LOG.info(u._('Updating schema to latest version'))
                commands.upgrade()
            else:
                # Create database tables from our models.
                LOG.info(u._('Auto-creating alliance registry DB'))
                models.register_models(_ENGINE)

                # Sync the alembic version 'head' with current models.
                commands.stamp()

        else:
            LOG.info(u._('not auto-creating alliance registry DB'))

    return _ENGINE


def get_maker(autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy sessionmaker."""
    """May assign __MAKER if not already assigned"""
    global _MAKER, _ENGINE
    assert _ENGINE
    if not _MAKER:
        _MAKER = sa_orm.sessionmaker(bind=_ENGINE,
                                     autocommit=autocommit,
                                     expire_on_commit=expire_on_commit)
    return _MAKER


def is_db_connection_error(args):
    """Return True if error in connecting to db."""
    # NOTE(adam_g): This is currently MySQL specific and needs to be extended
    #               to support Postgres and others.
    conn_err_codes = ('2002', '2003', '2006')
    for err_code in conn_err_codes:
        if args.find(err_code) != -1:
            return True
    return False


def wrap_db_error(f):
    """Retry DB connection. Copied from nova and modified."""
    def _wrap(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except sqlalchemy.exc.OperationalError as e:
            if not is_db_connection_error(e.args[0]):
                raise

            remaining_attempts = _MAX_RETRIES
            while True:
                LOG.warning(u._('SQL connection failed. %d attempts left.'),
                            remaining_attempts)
                remaining_attempts -= 1
                time.sleep(_RETRY_INTERVAL)
                try:
                    return f(*args, **kwargs)
                except sqlalchemy.exc.OperationalError as e:
                    if (remaining_attempts == 0 or not
                            is_db_connection_error(e.args[0])):
                        raise
                except sqlalchemy.exc.DBAPIError:
                    raise
        except sqlalchemy.exc.DBAPIError:
            raise
    _wrap.func_name = f.func_name
    return _wrap


def clean_paging_values(offset_arg=0, limit_arg=CONF.default_limit_paging):
    """Cleans and safely limits raw paging offset/limit values."""
    offset_arg = offset_arg or 0
    limit_arg = limit_arg or CONF.default_limit_paging

    try:
        offset = int(offset_arg)
        offset = offset if offset >= 0 else 0
    except ValueError:
        offset = 0

    try:
        limit = int(limit_arg)
        if limit < 1:
            limit = 1
        if limit > CONF.max_limit_paging:
            limit = CONF.max_limit_paging
    except ValueError:
        limit = CONF.default_limit_paging

    LOG.debug("Clean paging values limit={0}, offset={1}".format(
        limit, offset
    ))

    return offset, limit


class Repositories(object):
    """Convenient way to pass repositories around.

    Selecting a given repository has 3 choices:
       1) Use a specified repository instance via **kwargs
       2) Create a repository here if it is specified as None via **kwargs
       3) Just use None if no repository is specified
    """
    def __init__(self, **kwargs):
        if kwargs:
            # Enforce that either all arguments are non-None or else all None.
            test_set = set(kwargs.values())
            if None in test_set and len(test_set) > 1:
                raise NotImplementedError('No support for mixing None '
                                          'and non-None repository instances')

            # Only set properties for specified repositories.
            self._set_repo('partner_repo', PartnerRepo, kwargs)
            self._set_repo('partner_session_repo', PartnerSession, kwargs)

    def _set_repo(self, repo_name, repo_cls, specs):
        if specs and repo_name in specs:
            setattr(self, repo_name, specs[repo_name] or repo_cls())


class BaseRepo(object):
    """Base repository for the alliance entities.

    This class provides template methods that allow sub-classes to hook
    specific functionality as needed.
    """

    def __init__(self):
        LOG.debug("BaseRepo init...")
        configure_db()

    def get_session(self, session=None):
        LOG.debug("Getting session...")
        return session or get_session()

    def get(self, entity_id, keystone_id=None,
            force_show_deleted=False,
            suppress_exception=False, session=None):
        """Get an entity or raise if it does not exist."""
        session = self.get_session(session)

        try:
            query = self._do_build_get_query(entity_id,
                                             keystone_id, session)

            # filter out deleted entities if requested
            if not force_show_deleted:
                query = query.filter_by(deleted=False)

            entity = query.one()

        except sa_orm.exc.NoResultFound:
            LOG.exception("Not found for {0}".format(entity_id))
            entity = None
            if not suppress_exception:
                raise exception.NotFound("No %s found with ID %s"
                                         % (self._do_entity_name(), entity_id))

        return entity

    def create_from(self, entity):
        """Sub-class hook: create from entity."""
        start = time.time()  # DEBUG
        if not entity:
            msg = "Must supply non-None {0}.".format(self._do_entity_name)
            raise exception.Invalid(msg)

        if entity.id:
            msg = "Must supply {0} with id=None(i.e. new entity).".format(
                self._do_entity_name)
            raise exception.Invalid(msg)

        LOG.debug("Begin create from...")
        session = get_session()
        with session.begin():

            # Validate the attributes before we go any further. From my
            # (unknown Glance developer) investigation, the @validates
            # decorator does not validate
            # on new records, only on existing records, which is, well,
            # idiotic.
            values = self._do_validate(entity.to_dict())

            try:
                LOG.debug("Saving entity...")
                entity.save(session=session)
            except sqlalchemy.exc.IntegrityError:
                LOG.exception('Problem saving entity for create')
                raise exception.Duplicate("Entity ID %s already exists!"
                                          % values['id'])
        LOG.debug('Elapsed repo '
                  'create secret:{0}'.format(time.time() - start))  # DEBUG

        return entity

    def save(self, entity):
        """Saves the state of the entity.

        :raises NotFound if entity does not exist.
        """
        session = get_session()
        with session.begin():
            entity.updated_at = timeutils.utcnow()

            # Validate the attributes before we go any further. From my
            # (unknown Glance developer) investigation, the @validates
            # decorator does not validate
            # on new records, only on existing records, which is, well,
            # idiotic.
            self._do_validate(entity.to_dict())

            try:
                entity.save(session=session)
            except sqlalchemy.exc.IntegrityError:
                LOG.exception('Problem saving entity for update')
                raise exception.NotFound("Entity ID %s not found"
                                         % entity.id)

    def update(self, entity_id, values, purge_props=False):
        """Set the given properties on an entity and update it.

        :raises NotFound if entity does not exist.
        """
        return self._update(entity_id, values, purge_props)

    def delete_entity_by_id(self, entity_id, keystone_id):
        """Remove the entity by its ID."""

        session = get_session()
        with session.begin():

            entity = self.get(entity_id=entity_id, keystone_id=keystone_id,
                              session=session)

            try:
                entity.delete(session=session)
            except sqlalchemy.exc.IntegrityError:
                LOG.exception('Problem finding entity to delete')
                raise exception.NotFound("Entity ID %s not found"
                                         % entity_id)

    def _do_entity_name(self):
        """Sub-class hook: return entity name, such as for debugging."""
        return "Entity"

    def _do_create_instance(self):
        """Sub-class hook: return new entity instance (in Python, not in db).
        """
        return None

    def _do_build_get_query(self, entity_id, keystone_id, session):
        """Sub-class hook: build a retrieve query."""
        return None

    def _do_convert_values(self, values):
        """Sub-class hook: convert text-based values to target types for the
        database.
        """
        pass

    def _do_validate(self, values):
        """Sub-class hook: validate values.

        Validates the incoming data and raises an Invalid exception
        if anything is out of order.

        :param values: Mapping of entity metadata to check
        """
        status = values.get('status', None)
        if not status:
            #TODO(jfwood): I18n this!
            msg = "{0} status is required.".format(self._do_entity_name())
            raise exception.Invalid(msg)

        if not models.States.is_valid(status):
            msg = "Invalid status '{0}' for {1}.".format(
                status, self._do_entity_name())
            raise exception.Invalid(msg)

        return values

    def _update(self, entity_id, values, purge_props=False):
        """Used internally by update()

        :param values: A dict of attributes to set
        :param entity_id: If None, create the entity, otherwise,
                          find and update it
        """
        session = get_session()
        with session.begin():

            if entity_id:
                entity_ref = self.get(entity_id, session=session)
                values['updated_at'] = timeutils.utcnow()
            else:
                self._do_convert_values(values)
                entity_ref = self._do_create_instance()

            # Need to canonicalize ownership
            if 'owner' in values and not values['owner']:
                values['owner'] = None

            entity_ref.update(values)

            # Validate the attributes before we go any further. From my
            # (unknown Glance developer) investigation, the @validates
            # decorator does not validate
            # on new records, only on existing records, which is, well,
            # idiotic.
            self._do_validate(entity_ref.to_dict())
            self._update_values(entity_ref, values)

            try:
                entity_ref.save(session=session)
            except sqlalchemy.exc.IntegrityError:
                LOG.exception('Problem saving entity for _update')
                if entity_id:
                    raise exception.NotFound("Entity ID %s not found"
                                             % entity_id)
                else:
                    raise exception.Duplicate("Entity ID %s already exists!"
                                              % values['id'])

        return self.get(entity_ref.id)

    def _update_values(self, entity_ref, values):
        for k in values:
            if getattr(entity_ref, k) != values[k]:
                setattr(entity_ref, k, values[k])


class PartnerRepo(BaseRepo):
    """Repository for the Partner entity."""

    def _do_entity_name(self):
        """Sub-class hook: return entity name, such as for debugging."""
        return "Partner"

    def _do_create_instance(self):
        return models.Partner()

    def _do_build_get_query(self, entity_id, cloud_id, session):
        """Sub-class hook: build a retrieve query."""
        return session.query(models.Partner).filter_by(id=entity_id)

    def find_by_cloud_id(self, cloud_id, suppress_exception=False,
                            session=None):
        session = self.get_session(session)

        try:
            query = session.query(models.Partner).filter_by(cloud_id=cloud_id)
            entity = query.one()
        except sa_orm.exc.NoResultFound:
            LOG.exception("Problem getting Partner {0}".format(cloud_id))
            entity = None
            if not suppress_exception:
                raise exception.NotFound("No %s found with keystone-ID %s"
                                         % (self._do_entity_name(),
                                            cloud_id))
        return entity

class PartnerSession(BaseRepo):
        """Repository for the PartnerSession entity."""
        def _do_entity_name(self):
            """Sub-class hook: return entity name, such as for debugging."""
            return "PartnerSession"

        def _do_create_instance(self):
            return models.PartnerSession()

        def _do_build_get_query(self, entity_id, keystone_id, session):
            """Sub-class hook: build a retrieve query."""
            return session.query(models.PartnerSession
                                 ).filter_by(id=entity_id)

        def _do_validate(self, values):
            """Sub-class hook: validate values."""
            pass

        def find_by_cloud_id(self, cloud_id, suppress_exception=False,
                            session=None):
            session = self.get_session(session)
    
            try:
                query = session.query(models.PartnerSession).filter_by(cloud_id=cloud_id)
                entity = query.one()
            except sa_orm.exc.NoResultFound:
                LOG.exception("Problem getting PartnerSession {0}".format(cloud_id))
                entity = None
                if not suppress_exception:
                    raise exception.NotFound("No %s found with keystone-ID %s"
                                             % (self._do_entity_name(),
                                                cloud_id))
            return entity
