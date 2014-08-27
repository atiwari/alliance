'''
Created on Jul 12, 2014

@author: atiwari
'''
from alliance.common import exception
from alliance.common import utils
from alliance.thrift.service.ttypes import AException
from alliance.tserver.handlers.auth import AuthHandler
from alliance.tserver.handlers.ping import PingHandler
from alliance.tserver.handlers.session import SessionHandler


LOG = utils.getLogger(__name__)

class AllianceProcessor:
    def __init__(self):
        pass

    def getSession(self, session_ticket):
        print "--- getSession (server)"
        return SessionHandler(cloud_id_self="my-east-cloud-or-dc").handle(session_ticket)
        #except exception.AllianceException as ae:
        #    raise AException(ae.message)

    def ping(self, ping_request):
        print "--- ping (server)"
        return PingHandler(cloud_id_self="my-east-cloud-or-dc").handle(ping_request)

    def validateTokenHard(self, token_request):
        print "--- validateTokenHard (server)"
        return AuthHandler(cloud_id_self="my-east-cloud-or-dc").handle(token_request)

    def validateTokenSoft(self, token_request):
        print "--- validateTokenSoft (server)"
        exception.FeatureNotImplemented('validateTokenSoft')
        #return AuthHandler(cloud_id_self="my-east-cloud-or-dc").handle(token_request, validation_type='soft')
