import mock
import datetime
from oslo.config import cfg
import sqlalchemy.orm as sa_orm
import testtools

from alliance.common import exception
from alliance.model import models
from alliance.model import repositories


class WhenCleaningRepositoryPagingParameters(testtools.TestCase):

    def setUp(self):
        super(WhenCleaningRepositoryPagingParameters, self).setUp()
        self.CONF = cfg.CONF

    def test_parameters_not_assigned(self):
        """The cleaner should use defaults when params are not specified."""
        clean_offset, clean_limit = repositories.clean_paging_values()

        self.assertEqual(clean_offset, 0)
        self.assertEqual(clean_limit, self.CONF.default_limit_paging)

    def test_limit_as_none(self):
        """When Limit is set to None it should use the default limit."""
        offset = 0
        clean_offset, clean_limit = repositories.clean_paging_values(
            offset_arg=offset,
            limit_arg=None)

        self.assertEqual(clean_offset, offset)
        self.assertIsNotNone(clean_limit)

    def test_offset_as_none(self):
        """When Offset is set to None it should use an offset of 0."""
        limit = self.CONF.default_limit_paging
        clean_offset, clean_limit = repositories.clean_paging_values(
            offset_arg=None,
            limit_arg=limit)

        self.assertIsNotNone(clean_offset)
        self.assertEqual(clean_limit, limit)

    def test_limit_as_uncastable_str(self):
        """When Limit cannot be cast to an int, expect the default."""
        clean_offset, clean_limit = repositories.clean_paging_values(
            offset_arg=0,
            limit_arg='boom')
        self.assertEqual(clean_offset, 0)
        self.assertEqual(clean_limit, self.CONF.default_limit_paging)

    def test_offset_as_uncastable_str(self):
        """When Offset cannot be cast to an int, it should be zero."""
        limit = self.CONF.default_limit_paging
        clean_offset, clean_limit = repositories.clean_paging_values(
            offset_arg='boom',
            limit_arg=limit)
        self.assertEqual(clean_offset, 0)
        self.assertEqual(clean_limit, limit)

    def test_limit_is_less_than_one(self):
        """Offset should default to 1."""
        limit = -1
        clean_offset, clean_limit = repositories.clean_paging_values(
            offset_arg=1,
            limit_arg=limit)
        self.assertEqual(clean_offset, 1)
        self.assertEqual(clean_limit, 1)

    def test_limit_ist_too_big(self):
        """Limit should max out at configured value."""
        limit = self.CONF.max_limit_paging + 10
        clean_offset, clean_limit = repositories.clean_paging_values(
            offset_arg=1,
            limit_arg=limit)
        self.assertEqual(clean_limit, self.CONF.max_limit_paging)
"""
    def test_should_raise_exception_create_kek_datum_with_null_name(self):
        repositories._ENGINE = mock.MagicMock()
        tenant = mock.MagicMock(id="1")
        plugin_name = None
        suppress_exception = False
        session = mock.MagicMock()
        session.query.side_effect = sa_orm.exc.NoResultFound()

        kek_repo = repositories.KEKDatumRepo()
        self.assertRaises(exception.BarbicanException,
                          kek_repo.find_or_create_kek_datum, tenant,
                          plugin_name, suppress_exception, session)

    def test_should_raise_exception_create_kek_datum_with_empty_name(self):
        repositories._ENGINE = mock.MagicMock()
        tenant = mock.MagicMock(id="1")
        plugin_name = ""
        suppress_exception = False
        session = mock.MagicMock()
        session.query.side_effect = sa_orm.exc.NoResultFound()

        kek_repo = repositories.KEKDatumRepo()
        self.assertRaises(exception.BarbicanException,
                          kek_repo.find_or_create_kek_datum, tenant,
                          plugin_name, suppress_exception, session)
"""

class WhenTestingParterRepo(testtools.TestCase):

    def setUp(self):
        super(WhenTestingParterRepo, self).setUp()
        self.CONF = cfg.CONF
        self.partner_repo = repositories.PartnerRepo()

        self.parsed_secret_self = {'cloud_id': 'hp-helion-east-cloud-dc',
                      'name': 'hp-helion-east-cloud-dc',
                      'role': 'SELF',
                      'trust_status': 'ACTIVE',
                      'trust_since': datetime.datetime.now().isoformat(),
                      'trust_till': datetime.datetime.now().isoformat()}

        self.parsed_secret = {'cloud_id': 'hp-helion-west-cloud-dc',
                      'name': 'hp-helion-west-cloud-dc',
                      'role': 'PROVIDER',
                      'trust_status': 'ACTIVE',
                      'trust_since': datetime.datetime.now().isoformat(),
                      'trust_till': datetime.datetime.now().isoformat()}
        
    def test_should_pass(self):
        self_cloud = models.Partner(self.parsed_secret_self)
        self.partner_repo.create_from(self_cloud)

        partner_cloud = models.Partner(self.parsed_secret)
        self.partner_repo.create_from(partner_cloud)

class WhenTestingParterSessionRepo(testtools.TestCase):

    def setUp(self):
        super(WhenTestingParterSessionRepo, self).setUp()
        self.CONF = cfg.CONF
        self.partner_session_repo = repositories.PartnerSession()
        self.partner_session = models.PartnerSession()
        self.partner_session.cloud_id =  'hp-helion-west-cloud-dc'
        self.partner_session.session_key = 'hp-helion-west-cloud-dc'
        self.now = datetime.datetime.now()
        self.nowp10 = datetime.datetime.now() + datetime.timedelta(hours=10)
        self.partner_session.login_time = self.now
        self.partner_session.valid_till = self.nowp10
        self.partner_session.status = models.States.ACTIVE

    def test_should_pass(self):
        #create ps1
        self.partner_session_repo.create_from(self.partner_session)
        #create ps2
        self.partner_session = models.PartnerSession()
        self.partner_session.cloud_id =  'hp-helion-east-cloud-dc'
        self.partner_session.session_key = 'hp-helion-west-cloud-dc'
        self.partner_session.login_time = self.now
        self.partner_session.valid_till = self.nowp10
        self.partner_session.status = models.States.ACTIVE
        
        self.partner_session_repo.create_from(self.partner_session)