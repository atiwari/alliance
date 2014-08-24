
from oslo.config import cfg

from alliance.thrift.service.ttypes import SessionTKT
from alliance.thrift.service.ttypes import AException
from alliance.common import crypto_utils
from alliance.common import dtos
from alliance.common import utils
from alliance.common import exception
from alliance.common.exception import ErrorCode
from alliance.model import repositories
from alliance.model import models
from alliance.thrift.client import alliance_client

import json
LOG = utils.getLogger(__name__)
CONF = cfg.CONF

class SessionResource(object):

    def __init__(self, allianceClient=None, cloud_id_self=None):
        self.aes_crypto = crypto_utils.AESCrypto()
        self.rsa_crypto = crypto_utils.RSACrypto()
        self.partner_repo = repositories.PartnerRepo()
        self.partner_session_repo = repositories.PartnerSession()
        self.cloud_id_self = cloud_id_self or 'hp-helion-west-cloud-dc'
        self.allianceClient = allianceClient or alliance_client.AllianceClient()
        self.json_encoder = utils.JsonEncoder()

    def _build_session_tkt(self, session_dto, rsa_key_dto_self, rsa_key_dto_partner):
        # prepare session ticket to request a session
        session_ticket = SessionTKT()
        session_ticket.cloud_id = self.cloud_id_self
        session_ticket.pki_data = self.rsa_crypto.encrypt(self.json_encoder.encode(session_dto),
                                                          rsa_key_dto_partner)
        data_to_sign = str(session_dto.session_key) + str(session_dto.login_time)
        session_ticket.signature = self.rsa_crypto.sign(data_to_sign, 
            rsa_key_dto_self)
        return session_ticket

    def getSession(self, cloud_id_target=None):
        """
        Use PIK for get session
        """
        self.cloud_id_target = cloud_id_target
        # Fetch the partner from DB
        partner = self.partner_repo.find_by_cloud_id(self.cloud_id_target)

        if not partner:
            raise exception.PartnerNotFound(cloud_id=self.cloud_id_target)
        LOG.debug('partner found for cloud_id %s', self.cloud_id_target)
        # Fetch session for the partner fron DB
        try:
            partner_session = self.partner_session_repo.find_by_cloud_id(cloud_id_target)
            LOG.debug('session found in db for partner cloud_id %s', self.cloud_id_target)
        except exception.NotFound:
            partner_session = None

        # If have a valid session, just return
        if partner_session and utils.is_valid_session(partner_session):
            session_dto = dtos.SessionDTO()
            session_dto.cloud_id = cloud_id_target
            session_dto.session_key = partner_session.session_key
            session_dto.login_time = partner_session.login_time
            session_dto.valid_till = partner_session.valid_till
            LOG.debug('session in db is valid for partner cloud_id %s', self.cloud_id_target)
            return session_dto 

        #Now pull the PKI stuff
        rsa_key_dto_self = utils.get_key_rsa_keys(self.cloud_id_self)
        rsa_key_dto_partner = utils.get_key_rsa_keys(self.cloud_id_target)

        # first time login or session is expired
        session_dto = dtos.SessionDTO()
        session_dto.cloud_id = self.cloud_id_self
        if partner_session:
            session_dto.session_key = partner_session.session_key
            session_dto.login_time = partner_session.login_time.isoformat()
            session_dto.attempt_type = dtos.AttemptType.OPTIMISTIC
        else:
            #This will happen very first attempt to get session
            session_dto.session_key = self.cloud_id_self
            session_dto.attempt_type = dtos.AttemptType.BOOTSTRAP

        session_ticket = self._build_session_tkt(session_dto,
                                                 rsa_key_dto_self,
                                                 rsa_key_dto_partner)

        try:
            session_response = self.allianceClient.client().getSession(session_ticket)
        except AException as ae:
            # In this case try with fallback plan
            if ae.code == ErrorCode.TKT_SESSION_KEY_MISMATCH:
                session_dto.attempt_type = dtos.AttemptType.FALLBACK
                session_dto.session_key = utils.generate_uuid()
                session_dto.login_time = None
                session_ticket = self._build_session_tkt(session_dto,
                                                         rsa_key_dto_self,
                                                         rsa_key_dto_partner)
                session_response = self.allianceClient.client().getSession(session_ticket)

        if session_response.pki_data:
            # decrypt with self PK
            session_dto_json = self.rsa_crypto.decrypt(session_response.pki_data, rsa_key_dto_self)
            if session_dto_json:
                session_dto_json = json.loads(session_dto_json)
                session_dto = dtos.SessionDTO(session_dto_json)
                data_to_sign = str(session_dto.session_key) + str(session_dto.login_time)
                is_valid_signature = self.rsa_crypto.verify_sign(data_to_sign, session_response.signature, rsa_key_dto_partner)
                if is_valid_signature:
                    #save in db
                    if not partner_session:
                        partner_session = models.PartnerSession()

                    partner_session.cloud_id = session_dto.cloud_id
                    partner_session.session_key = session_dto.session_key
                    partner_session.login_time = utils.iso2datetime(session_dto.login_time)
                    partner_session.valid_till = utils.iso2datetime(session_dto.valid_till)
                    self.partner_session_repo.save(partner_session)

            return session_dto


if __name__ == '__main__':
    try:
        """Quick test code"""
        sessionHelper = SessionResource()
        cloud_id_target = 'hp-helion-east-cloud-dc'
        session_dto = sessionHelper.getSession(cloud_id_target)
        print session_dto.cloud_id
        print session_dto.session_key
        print session_dto.login_time
        print session_dto.valid_till
    
    except AException as e:
        print e

