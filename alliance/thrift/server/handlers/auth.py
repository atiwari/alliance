
import base64
import json

from . import HandlerBase
from alliance.thrift.service.ttypes import TokenResponse
from alliance.common import utils
from alliance.common.exception import ErrorCode
from alliance.common import dtos
from alliance.common import crypto_utils
from alliance.common import resource
from alliance.lproxy import keystone
from alliance.model import repositories

LOG = utils.getLogger(__name__)

class AuthHandler(HandlerBase):
    def __init__(self, cloud_id_self=None):
        self.aes_crypto = crypto_utils.AESCrypto()
        self.partner_repo = repositories.PartnerRepo()
        self.partner_session_repo = repositories.PartnerSession()
        self.cloud_id_self = cloud_id_self
        self.json_encoder = utils.JsonEncoder()

    def _wrap_token_dto(self, cloud_id, auth_token_dto):
        session = resource.PartnerResource().getSession(cloud_id)
        key_dto = dtos.KeyDTO(key=base64.b64decode(session.session_key))
        return self.aes_crypto.encrypt(self.json_encoder.encode(auth_token_dto), key_dto)

    def _unwrap_token_dto(self, cloud_id, auth_token_dto_ENC):
        session = resource.PartnerResource().getSession(cloud_id)
        key_dto = dtos.KeyDTO(key=base64.b64decode(session.session_key))
        return json.loads(self.aes_crypto.decrypt(auth_token_dto_ENC, key_dto))

    def handle(self, t_request, **kwargs):

        if t_request.cloud_id:
            try:
                auth_token_dto_json = self._unwrap_token_dto(t_request.cloud_id, t_request.request_data)
                auth_token_dto = dtos.AuthTokenDTO(auth_token_dto_json)
                if auth_token_dto:
                    try:
                        token = keystone.KeystoneProxy().validate_token(auth_token_dto.token_id)
                        #decorate token to add resources 
                        auth_token_dto.cloud_id = self.cloud_id_self
                        auth_token_dto.token_str = token
                        auth_token_dto.validation_code = dtos.ValidationCode.VALID
                    except Exception as e:
                        auth_token_dto.validation_code = dtos.ValidationCode.INVALID
                        auth_token_dto.details = e.message
            except Exception as e:
                auth_token_dto = dtos.AuthTokenDTO()
                auth_token_dto.cloud_id = self.cloud_id_self
                auth_token_dto.validation_code = dtos.ValidationCode.INDETERMINATE
                auth_token_dto.details = e.message

            token_response = TokenResponse()
            token_response.cloud_id = self.cloud_id_self
            token_response.response_data = self._wrap_token_dto(t_request.cloud_id, auth_token_dto)
            return token_response
