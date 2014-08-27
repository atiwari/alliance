from alliance.thrift.service.ttypes import PingRequest
from alliance.thrift.service.ttypes import AException
from alliance.tclient import alliance_client


class PingResource(object):
    """
    Alliance partners have to play Ping-Pong.
    This resource will help to check if the
    other party is up and running.
    """

    def __init__(self, allianceClient=None, cloud_id_self=None):
        self.allianceClient = allianceClient
        self.cloud_id_self = cloud_id_self

    def ping(self, cloud_id_target=None):
        request = PingRequest()
        request.cloud_id = self.cloud_id_self
        # In future we may need to make the ping request
        # message secure. Right now it is clear text.
        request.request_data = "ping" #can be any string
        try:
            ping_response = self.allianceClient.client().ping(request)
        except AException as e:
            print e.code
        finally:
            self.allianceClient.close()

        return ping_response


if __name__ == '__main__':
    try:
        """Quick test code"""
        cloud_id_target = 'my-east-cloud-or-dc'
        alliance_client = alliance_client.AllianceClient(cloud_id_target='my-east-cloud-or-dc')
        ping_resource = PingResource(allianceClient=alliance_client, cloud_id_self='my-west-cloud-or-dc')

        ping_response = ping_resource.ping(cloud_id_target)

        if ping_response and ping_response.response_data.lower() == 'pong' and ping_response.cloud_id == cloud_id_target:
            print ("###### Fun playing ping, pong with %s" %cloud_id_target)
        else:
            print ("###### No Pong from %s" %cloud_id_target)
    except AException as e:
        print e