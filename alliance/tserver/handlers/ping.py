
from alliance.thrift.service.ttypes import Pong

from . import HandlerBase
from alliance.common import utils
from alliance.common.exception import ErrorCode
from alliance.common import exception

LOG = utils.getLogger(__name__)

class PingHandler(HandlerBase):
    def __init__(self):
        pass

    def handle(self, t_request, **kwargs):
        print t_request.cloud_id
        pong = Pong()
        pong.response = "Hi " + t_request.cloud_id
        raise exception.PartnerNotFound(ErrorCode.PARTNER_NOT_FOUND, cloud_id=t_request.cloud_id)
        return pong