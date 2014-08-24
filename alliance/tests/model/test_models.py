import datetime
import testtools

from alliance.model import models


class WhenCreatingNewPartner(testtools.TestCase):
    def setUp(self):
        super(WhenCreatingNewPartner, self).setUp()
        self.parsed_secret = {'cloud_id': 'James_Bond_007',
                              'name': 'James_Bond_007',
                              'role': 'PROVIDER',
                              'trust_status': models.TrustStatus.DRAFT,
                              'trust_since': datetime.datetime.now().isoformat(),
                              'trust_till': datetime.datetime.now().isoformat()}

    def test_new_partner_is_created_from_dict(self):
        partner = models.Partner(self.parsed_secret)
        self.assertEqual(partner.cloud_id, self.parsed_secret['cloud_id'])
        self.assertEqual(partner.name, self.parsed_secret['name'])
        self.assertEqual(partner.role, self.parsed_secret['role'])
        self.assertEqual(partner.trust_status, self.parsed_secret['trust_status'])
        self.assertIsInstance(partner.trust_since, datetime.datetime)
        self.assertIsInstance(partner.trust_till, datetime.datetime)

