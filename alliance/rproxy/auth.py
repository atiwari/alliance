import base64

from oslo.config import cfg

from alliance.thrift.service.ttypes import TokenRequest
from alliance.tclient import alliance_client
from alliance.thrift.service.ttypes import AException
from alliance.common import crypto_utils
from alliance.common import dtos
from alliance.common import utils
#from alliance.common import exception
#from alliance.common.exception import ErrorCode
#from alliance.model import repositories
#from alliance.model import models
from alliance.common import resource

import json
LOG = utils.getLogger(__name__)
CONF = cfg.CONF

class AuthResource(object):

    def __init__(self, allianceClient=None, cloud_id_self=None):
        self.cloud_id_self = cloud_id_self
        self.allianceClient = allianceClient
        self.aes_crypto = crypto_utils.AESCrypto()
        self.json_encoder = utils.JsonEncoder()

    def _wrap_token_dto(self, cloud_id, auth_token_dto):
        session = resource.PartnerResource().getSession(cloud_id)
        key_dto = dtos.KeyDTO(key=base64.b64decode(session.session_key))
        return self.aes_crypto.encrypt(self.json_encoder.encode(auth_token_dto), key_dto)

    def _unwrap_token_dto(self, cloud_id, auth_token_dto_ENC):
        session = resource.PartnerResource().getSession(cloud_id)
        key_dto = dtos.KeyDTO(key=base64.b64decode(session.session_key))
        return json.loads(self.aes_crypto.decrypt(auth_token_dto_ENC, key_dto))

    def validate_uuid_token_hard(self, cloud_id_target, token_id):
        token_dto = dtos.AuthTokenDTO()
        token_dto.cloud_id = cloud_id_target
        token_dto.token_id = token_id
        token_dto.token_type = dtos.TokenType.UUID

        token_request = TokenRequest()
        token_request.cloud_id = self.cloud_id_self
        token_request.request_data = self._wrap_token_dto(cloud_id_target, token_dto)

        token_response = self.allianceClient.client().validateTokenHard(token_request)
        if token_response.response_data:
            token_json = self._unwrap_token_dto(cloud_id_target, token_response.response_data)
        return dtos.AuthTokenDTO(token_json)


    def validate_uuid_token_soft(self, token_id):
        pass

    def get_token(self, username, passwd, project_name=None, project_id=None):
        pass

if __name__ == '__main__':
    try:
        """Quick test code"""
        cloud_id_target = 'my-east-cloud-or-dc'
        alliance_client = alliance_client.AllianceClient(cloud_id_target='my-east-cloud-or-dc')
        authResource = AuthResource(allianceClient=alliance_client, cloud_id_self='my-west-cloud-or-dc')
        auth_response = authResource.validate_uuid_token_hard(cloud_id_target, "ff8ff5ee85da44ddb1137f9ad40bd17d")
        print auth_response.validation_code
    except AException as e:
        print e