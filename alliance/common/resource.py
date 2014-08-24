import json

from oslo.config import cfg

from alliance.common import dtos
from alliance.common import utils
from alliance.common import exception
from alliance.model import repositories

LOG = utils.getLogger(__name__)
CONF = cfg.CONF

class PartnerResource(object):

    def __init__(self):
        self.partner_repo = repositories.PartnerRepo()
        self.partner_session_repo = repositories.PartnerSession()
        self.json_encoder = utils.JsonEncoder()

    def getPartner(self, cloud_id_target):
        # Fetch the partner from DB
        partner = self.partner_repo.find_by_cloud_id(cloud_id_target)
        if not partner:
            raise exception.PartnerNotFound(cloud_id=self.cloud_id_target)
        LOG.debug('partner found for cloud_id %s', cloud_id_target)
        return partner

    def getPartnerSession(self, cloud_id_target):

        if self.getPartner(cloud_id_target):
            # Fetch session for the partner from DB
            try:
                partner_session = self.partner_session_repo.find_by_cloud_id(cloud_id_target)
                LOG.debug('session found in db for partner cloud_id %s', cloud_id_target)
            except exception.NotFound:
                partner_session = None
            return partner_session
        
    def getSession(self, cloud_id_target):

        if self.getPartner(cloud_id_target):
            # Fetch session for the partner from DB
            try:
                partner_session = self.partner_session_repo.find_by_cloud_id(cloud_id_target)
                LOG.debug('session found in db for partner cloud_id %s', cloud_id_target)
            except exception.NotFound:
                partner_session = None
            # If have a valid session, just return
            if partner_session:
                session_dto = dtos.SessionDTO()
                session_dto.cloud_id = cloud_id_target
                session_dto.session_key = partner_session.session_key
                session_dto.login_time = partner_session.login_time
                session_dto.valid_till = partner_session.valid_till
                LOG.debug('session in db is valid for partner cloud_id %s', cloud_id_target)
                return session_dto 

            return partner_session

    def isValidSession(self, session):
            return utils.is_valid_session(session)