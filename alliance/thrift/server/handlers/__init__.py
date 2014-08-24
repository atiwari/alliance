import abc

from alliance.thrift.service.ttypes import SessionTKT

class HandlerBase(object):
    @abc.abstractmethod
    def handle(self, t_request, **kwargs):
        raise NotImplementedError
