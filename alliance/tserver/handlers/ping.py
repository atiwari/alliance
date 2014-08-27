
from alliance.thrift.service.ttypes import PingResponse

from . import HandlerBase
from alliance.common import utils
from alliance.common.exception import ErrorCode
from alliance.common import exception
from alliance.model import repositories

LOG = utils.getLogger(__name__)

class PingHandler(HandlerBase):

    def __init__(self, cloud_id_self=None):
        self.cloud_id_self = cloud_id_self
        self.partner_repo = repositories.PartnerRepo()

    def handle(self, t_request, **kwargs):

        partner = self.partner_repo.find_by_cloud_id(t_request.cloud_id)
        if not partner:
            raise exception.PartnerNotFound(ErrorCode.PARTNER_NOT_FOUND,
                                            cloud_id=t_request.cloud_id)

        print "@@@@@@@@@ playing ping pong with %s", t_request.cloud_id
        pong = PingResponse()
        pong.cloud_id = self.cloud_id_self
        pong.response_data = 'pong'
        return pong