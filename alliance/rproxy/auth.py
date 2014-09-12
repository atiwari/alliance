import base64

from oslo.config import cfg

from alliance.thrift.service.ttypes import TokenRequest
from alliance.tclient import alliance_client
from alliance.thrift.service.ttypes import AException
from alliance.common import crypto_utils
from alliance.common import dtos
from alliance.common import utils
from alliance.rproxy import session
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

    def _wrap_dto(self, cloud_id, dto):
        #Client, If have invalid session grab new one
        session_dto = session.SessionResource(allianceClient= self.allianceClient,
                                              cloud_id_self=self.cloud_id_self).getSession(cloud_id)
        key_dto = dtos.KeyDTO(key=base64.b64decode(session_dto.session_key))
        return self.aes_crypto.encrypt(self.json_encoder.encode(dto), key_dto)

    def _unwrap_dto(self, cloud_id, dto_ENC):
        #Client, If have invalid session grab new one
        session_dto = session.SessionResource(allianceClient= self.allianceClient,
                                              cloud_id_self=self.cloud_id_self).getSession(cloud_id)
        key_dto = dtos.KeyDTO(key=base64.b64decode(session_dto.session_key))
        return json.loads(self.aes_crypto.decrypt(dto_ENC, key_dto))

    def validate_uuid_token_hard(self, cloud_id_target, token_id):
        token_dto = dtos.AuthTokenDTO()
        #token_dto.cloud_id = cloud_id_target
        token_dto.token_id = token_id
        token_dto.token_type = dtos.TokenType.UUID

        token_request = TokenRequest()
        token_request.cloud_id = self.cloud_id_self
        token_request.request_data = self._wrap_dto(cloud_id_target, token_dto)

        token_response = self.allianceClient.client().validateTokenHard(token_request)
        if token_response.response_data:
            token_json = self._unwrap_dto(cloud_id_target, token_response.response_data)
            print token_json
        return dtos.AuthTokenDTO(token_json)


    def validate_uuid_token_soft(self, token_id):
        pass

    def get_token(self, cloud_id_target, username=None,
                  password=None,
                  project_name=None,
                  project_id=None,
                  project_domain_id=None,
                  user_domain_id=None):

        auth_dto = dtos.AuthDTO()
        auth_dto.username = username
        auth_dto.password = password
        auth_dto.user_domain_id = user_domain_id
        auth_dto.project_id = project_id
        auth_dto.project_name = project_name
        auth_dto.project_domain_id = project_domain_id

        token_request = TokenRequest()
        token_request.cloud_id = self.cloud_id_self
        token_request.request_data = self._wrap_dto(cloud_id_target, auth_dto)

        token_response = self.allianceClient.client().authenticate(token_request)
        if token_response.response_data:
            auth_dto_json = self._unwrap_dto(cloud_id_target, token_response.response_data)
            print auth_dto_json
        return dtos.AuthTokenDTO(auth_dto_json)

if __name__ == '__main__':
    try:
        """Quick test code"""
        cloud_id_target = 'my-east-cloud-or-dc'
        alliance_client = alliance_client.AllianceClient(cloud_id_target='my-east-cloud-or-dc')
        authResource = AuthResource(allianceClient=alliance_client, cloud_id_self='my-west-cloud-or-dc')
        #auth_response = authResource.validate_uuid_token_hard(cloud_id_target, "5672e4ee84494993a829fe668e673c52")

        auth_response = authResource.get_token(cloud_id_target,
                                               username='lbuser',
                                               password='changeit',
                                               user_domain_id='f7894f7eab9a463a990eb6dd6f13bda4',
                                               project_name='lbaas-user-project01',
                                               project_domain_id='f7894f7eab9a463a990eb6dd6f13bda4')

        print auth_response.opr_code
    except AException as e:
        print e
