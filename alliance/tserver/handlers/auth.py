
import base64
import json

from . import HandlerBase
from . import HandleCommand
from alliance.thrift.service.ttypes import TokenResponse
from alliance.common import utils
from alliance.common.exception import ErrorCode
from alliance.common import exception
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

    def _wrap_dto(self, cloud_id, dto):
        session = resource.PartnerResource().getSession(cloud_id)
        if utils.is_valid_session(session):
            key_dto = dtos.KeyDTO(key=base64.b64decode(session.session_key))
            return self.aes_crypto.encrypt(self.json_encoder.encode(dto), key_dto)
        else:
            #Server has to just throw, no need get session  
            raise exception.InvalidSession(code=ErrorCode.SESSION_KEY_INVALID, message="session not valid")

    def _unwrap_dto(self, cloud_id, dto_ENC):
        session = resource.PartnerResource().getSession(cloud_id)
        if utils.is_valid_session(session):
            key_dto = dtos.KeyDTO(key=base64.b64decode(session.session_key))
            return json.loads(self.aes_crypto.decrypt(dto_ENC, key_dto))
        else:
            #Server has to just throw, no need get session
            raise exception.InvalidSession(code=ErrorCode.SESSION_KEY_INVALID, message="session not valid")

    def handle(self, t_request, command=None, **kwargs):
        
        if command == HandleCommand.VALIDATE_TOKEN_HARD:
            return self._handle_validate_token_hard(t_request)
        elif command == HandleCommand.AUTHENTICATE:
            return self._handle_authenticate(t_request)
        else:
            return None
    
    def _handle_authenticate(self, t_request, **kwargs):
        if t_request.cloud_id:
            auth_dto_json = self._unwrap_dto(t_request.cloud_id, t_request.request_data)
            auth_dto = dtos.AuthDTO(auth_dto_json)
            if auth_dto:
                try:
                    token = keystone.KeystoneProxy().create_token(username=auth_dto.username,
                                                                  password=auth_dto.password,
                                                                  project_name=auth_dto.project_name,
                                                                  project_domain_id=auth_dto.project_domain_id,
                                                                  user_domain_id=auth_dto.user_domain_id)
                    #decorate token to add resources
                    auth_token_dto = dtos.AuthTokenDTO()
                    #auth_token_dto.cloud_id = self.cloud_id_self
                    auth_token_dto.token_str = token
                    auth_token_dto.token_type = dtos.TokenType.UUID
                    auth_token_dto.opr_code = dtos.OprCode.OK
                except Exception as e:
                    auth_token_dto = dtos.AuthTokenDTO()
                    #auth_token_dto.cloud_id = self.cloud_id_self
                    auth_token_dto.opr_code = dtos.OprCode.INDETERMINATE
                    auth_token_dto.details = e.message

            token_response = TokenResponse()
            token_response.cloud_id = self.cloud_id_self
            token_response.response_data = self._wrap_dto(t_request.cloud_id, auth_token_dto)

            return token_response


    def _handle_validate_token_hard(self, t_request, **kwargs):
        if t_request.cloud_id:
            try:
                auth_token_dto_json = self._unwrap_dto(t_request.cloud_id, t_request.request_data)
                auth_token_dto = dtos.AuthTokenDTO(auth_token_dto_json)
                if auth_token_dto:
                    try:
                        token = keystone.KeystoneProxy().validate_token(auth_token_dto.token_id)
                        #decorate token to add resources 
                        #auth_token_dto.cloud_id = self.cloud_id_self
                        auth_token_dto.token_str = token
                        auth_token_dto.opr_code = dtos.OprCode.VALID
                    except Exception as e:
                        auth_token_dto.opr_code = dtos.OprCode.INVALID
                        auth_token_dto.details = e.message
            except Exception as e:
                auth_token_dto = dtos.AuthTokenDTO()
                #auth_token_dto.cloud_id = self.cloud_id_self
                auth_token_dto.opr_code = dtos.OprCode.INDETERMINATE
                auth_token_dto.details = e.message

            token_response = TokenResponse()
            token_response.cloud_id = self.cloud_id_self
            token_response.response_data = self._wrap_dto(t_request.cloud_id, auth_token_dto)
            return token_response
