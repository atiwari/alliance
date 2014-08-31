import abc

from alliance.thrift.service.ttypes import SessionTKT

class HandleCommand(object):
    GET_SESSION = 'get_session'
    PING = 'ping'
    VALIDATE_TOKEN_HARD = 'validate_token_hard'
    VALIDATE_TOKEN_SOFT = 'validate_token_soft'
    AUTHENTICATE = 'authenticate'
    REVOKE_TOKEN = 'revoke_token'
    GET_SERVICES = 'get_services'
    GET_ENDPOINTS = 'get_endpoints'

class HandlerBase(object):
    @abc.abstractmethod
    def handle(self, t_request, command=None, **kwargs):
        raise NotImplementedError

    @abc.abstractmethod
    def handle_async(self, t_request, command=None, **kwargs):
        raise NotImplementedError