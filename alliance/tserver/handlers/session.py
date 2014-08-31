'''
Created on Jul 21, 2014

@author: atiwari
'''
import base64
import datetime
import json

from . import HandlerBase
from . import HandleCommand as command
from alliance.common import crypto_utils
from alliance.common import dtos
from alliance.common import utils
from alliance.common.exception import ErrorCode
from alliance.common import exception
from alliance.model import repositories
from alliance.model import models
from alliance.thrift.service.ttypes import SessionTKT

LOG = utils.getLogger(__name__)


class SessionHandler(HandlerBase):
    def __init__(self, cloud_id_self=None):
        self.aes_crypto = crypto_utils.AESCrypto()
        self.rsa_crypto = crypto_utils.RSACrypto()
        self.partner_repo = repositories.PartnerRepo()
        self.partner_session_repo = repositories.PartnerSession()
        self.cloud_id_self = cloud_id_self
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

    def handle(self, t_request, command=command.GET_SESSION, **kwargs):

        partner = self.partner_repo.find_by_cloud_id(t_request.cloud_id)

        if not partner:
            raise exception.PartnerNotFound(ErrorCode.PARTNER_NOT_FOUND,
                                            cloud_id=t_request.cloud_id)
        try:
            rsa_key_dto_self = utils.get_key_rsa_keys(self.cloud_id_self)
        except Exception as e:
            LOG.debug('pki config issue for self %s', self.cloud_id_self)
            raise exception.ConfigurationIssues(ErrorCode.CONFIG_ISSUES,
                                            cloud_id=t_request.cloud_id)
        try:
            rsa_key_dto_partner = utils.get_key_rsa_keys(t_request.cloud_id)
        except Exception as e:
            LOG.debug('pki config issue for partner  %s',t_request.cloud_id)
            raise exception.ConfigurationIssues(ErrorCode.CONFIG_ISSUES,
                                            cloud_id=t_request.cloud_id)

        try:
            # decrypt with self private_key
            session_dto_json = self.rsa_crypto.decrypt(t_request.pki_data,
                                                       rsa_key_dto_self)
        except Exception as e:
            raise exception.PartnerValidationFailed(ErrorCode.TKT_UNWRAP_FAILED,
                                                    "unable to unwrap data due to %s", e)

        session_dto_json = json.loads(session_dto_json)
        session_dto = dtos.SessionDTO(session_dto_json)

        try:
            partner_session = self.partner_session_repo.find_by_cloud_id(t_request.cloud_id)
        except exception.NotFound:
            partner_session = None

        #Last session key should match in case bootstrap or optimistic
        if session_dto.attempt_type == dtos.AttemptType.BOOTSTRAP:
            if partner.cloud_id == session_dto.session_key:
                data_to_validate = str(session_dto.session_key) + str(session_dto.login_time)
        elif session_dto.attempt_type == dtos.AttemptType.OPTIMISTIC:
            if partner_session.session_key == session_dto.session_key:
                data_to_validate = str(session_dto.session_key) + str(session_dto.login_time)
            else:
                raise exception.PartnerValidationFailed(ErrorCode.TKT_SESSION_KEY_MISMATCH,
                                                        "last session key does not match")
        elif session_dto.attempt_type == dtos.AttemptType.FALLBACK:
            data_to_validate = str(session_dto.session_key) + str(session_dto.login_time)
        else: 
            raise exception.PartnerValidationFailed(ErrorCode.TKT_AMBIGUEUS_SESSION_ATTEMPT,
                                                        "session attempt does not known")

        # validate with partner public_key
        try:
            is_valid_signature = self.rsa_crypto.verify_sign(data_to_validate,
                                                             t_request.signature,
                                                             rsa_key_dto_partner)
        except Exception:
            is_valid_signature = False

        if not is_valid_signature:
            LOG.debug("signature validation failed")
            raise exception.PartnerValidationFailed(ErrorCode.TKT_VERIFICATION_FAILED,
                                                    "signature validation failed")
        #generate session key
        session_key = base64.b64encode(self.aes_crypto.generate_key(256))

        if not partner_session:
            partner_session = models.PartnerSession()
        #Save session for this partner locally
        partner_session.cloud_id = partner.cloud_id
        partner_session.session_key = session_key
        partner_session.login_time = datetime.datetime.now()
        partner_session.valid_till = datetime.datetime.now() + datetime.timedelta(hours=10)
        self.partner_session_repo.save(partner_session)

        #build session dto
        session_dto.cloud_id = self.cloud_id_self
        session_dto.session_key = session_key
        session_dto.login_time = partner_session.login_time.isoformat()
        session_dto.valid_till = partner_session.valid_till.isoformat()
        
        session_response = self._build_session_tkt(session_dto, rsa_key_dto_self, rsa_key_dto_partner)
        #data to sign
        #data_to_sign = str(session_dto.session_key) + str(session_dto.login_time)
        #t_request = SessionTKT()
        #t_request.cloud_id = self.cloud_id_self
        #sign with self private_key
        #t_request.signature = self.rsa_crypto.sign(data_to_sign, rsa_key_dto_self)
        #Encrypt with partner public_key
        #t_request.pki_data = self.rsa_crypto.encrypt(self.json_encoder.encode(session_dto), rsa_key_dto_partner)

        return session_response


