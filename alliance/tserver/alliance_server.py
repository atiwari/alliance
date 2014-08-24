from oslo.config import cfg

from alliance.openstack.common import log
from alliance.thrift.service import AllianceService
from alliance.tserver.processor import AllianceProcessor
from alliance.common import utils
from alliance.common import config

from thrift.transport import TSocket
from thrift.transport import TTransport
#from thrift.protocol import TBinaryProtocol
from thrift.protocol import TCompactProtocol
from thrift.server import TServer
#from thrift.server import TNonblockingServer

LOG = utils.getLogger(__name__)

#CONF = cfg.CONF

class AllianceThriftServer(object):
    """Alliance simple server."""
    def __init__(self, processor=None, t_socket=None,
                 t_transport_factory=None, t_protocol_factory=None, **kwargs):

        self.processor = (processor or AllianceProcessor())
        self.t_socket = (t_socket or TSocket.TServerSocket(host='localhost', port=9441))
        self.t_transport_factory = (t_transport_factory or TTransport.TFramedTransportFactory())
        self.t_protocol_factory = (t_protocol_factory or TCompactProtocol.TCompactProtocolFactory())
        self.server = TServer.TThreadPoolServer(processor, t_socket, t_transport_factory, t_protocol_factory)

    def start(self):
        print('-- Alliance Server (starting) --')
        self.server.serve()
    
    def stop(self):
        print('-- Alliance Server (stopped) --')


if __name__ == '__main__':

    CONF = cfg.CONF
    opt_tserver_group = cfg.OptGroup(name='tserver',
                         title='Config for thrift server')
    tserver_opts = [
    cfg.StrOpt('thriftServerHost', default='localhost',
                    help=('default server host')),
    cfg.IntOpt('thriftTcpPort', default=9441,
                    help=('default server port'))
                    ]

    CONF.register_group(opt_tserver_group)
    CONF.register_opts(tserver_opts, opt_tserver_group)
    
    config.parse_args()
    log.setup('alliance')

    handler = AllianceProcessor()
    processor = AllianceService.Processor(handler)
    t_socket = TSocket.TServerSocket(host=CONF.tserver.thriftServerHost,
                                     port=CONF.tserver.thriftTcpPort)
    t_transport_factory = TTransport.TFramedTransportFactory()
    t_protocol_factory = TCompactProtocol.TCompactProtocolFactory()

    alliance_server = AllianceThriftServer(processor, t_socket,
                                           t_transport_factory,
                                           t_protocol_factory)
    print "Starting server..."
    
    try:
        alliance_server.start()
    except KeyboardInterrupt:
        alliance_server.stop()
    except Exception as e:
        print e