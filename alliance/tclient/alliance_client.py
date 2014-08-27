from thrift import Thrift
from thrift.transport import TSocket
from thrift.transport import TTransport
from thrift.protocol import TCompactProtocol

from alliance.common import utils
from alliance.thrift.service import AllianceService


LOG = utils.getLogger(__name__)

class AllianceClient():
    """
        By default we are assuming that alliance
        server is running locally.
        Which is not the correct assumption.
    """
    def __init__(self, cloud_id_target=None, endpoint='localhost', port=9441):
        """Using cloud_id_target we have to find the
        alliance endpoints
        """
        LOG.debug('alliance client for %s' %cloud_id_target)
        # Make socket
        self.tsocket = TSocket.TSocket(endpoint, port)
        # Buffering is critical. Raw sockets are very slow
        #self.transport = TTransport.TBufferedTransport(self.transport)
        self.transport = TTransport.TFramedTransport(self.tsocket)
        # Wrap in a protocol
        self.protocol = TCompactProtocol.TCompactProtocol(self.transport)

    def open(self):
        try:
            # Connect!
            if self.transport.isOpen():
                pass
            else:
                self.transport.open()
        except Thrift.TException, tx:
            print '%s' % (tx.message)

    def close(self):
        try:
            if self.transport.isOpen():
                # Close!
                self.transport.close()
        except Thrift.TException, tx:
            print '%s' % (tx.message)

    def client(self):
        try:
            self.open()
            # Create a client to use the protocol encoder
            client = AllianceService.Client(self.protocol)
        except Thrift.TException, tx:
            print '%s' % (tx.message)

        return client