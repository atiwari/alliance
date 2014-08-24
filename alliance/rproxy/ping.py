from alliance.thrift.service.ttypes import SessionTKT
from alliance.thrift.service.ttypes import AException

from alliance.common import dtos
from alliance.common import crypto_utils
from alliance.common import exception
from alliance.tclient import alliance_client

from alliance.openstack.common import gettextutils as u

class PingResource(object):

    def __init__(self, allianceClient=None):
        self.allianceClient = allianceClient or alliance_client.AllianceClient()
    
    def ping(self):
        session_ticket = SessionTKT()
        session_ticket.cloud_id = "helion-west-cloud-dc"
        session_ticket.signature = "dsdsdsdsdsd"
        try:
            ping_response = self.allianceClient.client().ping(session_ticket)
            print ping_response.response
        except AException as e:
            print e.code
        finally:
            self.allianceClient.close()




"""Quick test code"""
pinghelper = PingResource()
pinghelper.ping()
