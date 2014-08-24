'''
Created on Jul 12, 2014

@author: atiwari
'''
from alliance.common import utils
from alliance.common import exception
from alliance.tserver.handlers.ping import PingHandler
from alliance.tserver.handlers.session import SessionHandler
from alliance.tserver.handlers.auth import AuthHandler
from alliance.thrift.service.ttypes import AException

LOG = utils.getLogger(__name__)

class AllianceProcessor:
    def __init__(self):
        pass

    def ping(self, session_ticket):
        print "--- ping (server)"
        return PingHandler(cloud_id_self="hp-helion-east-cloud-dc").handle(session_ticket)

    def getSession(self, session_ticket):
        print "--- getSession (server)"
        return SessionHandler(cloud_id_self="hp-helion-east-cloud-dc").handle(session_ticket)
        #except exception.AllianceException as ae:
        #    raise AException(ae.message)

    def validateTokenHard(self, token_request):
        print "--- validateTokenHard (server)"
        return AuthHandler(cloud_id_self="hp-helion-east-cloud-dc").handle(token_request)