'''
Created on Aug 6, 2014

@author: atiwari
'''
import os
from oslo.config import cfg
#from keystoneclient.v2_0 import client as v2client
from keystoneclient.v3 import client as v3client 
from keystoneclient.middleware import auth_token 

from alliance.common import config

os.environ['no_proxy'] = 'localhost,127.0.0.0/8,127.0.1.1,127.0.1.1*,local.home'

CONF = cfg.CONF
opt_keystone_group = cfg.OptGroup(name='keystone', title='Config for keystone server')

keystone_opts = [
cfg.StrOpt('auth_host', default='localhost',
                help=('default auth_host')),
cfg.IntOpt('admin_port', default=35357,
                help=('default pulic_port')),
cfg.IntOpt('public_port', default=5000,
                help=('default public_port port')),
cfg.StrOpt('admin_tenant_name', default='service',
                help=('default admin_tenant_name')),
cfg.StrOpt('auth_protocol', default='http',
                help=('default auth_protocol')),
cfg.StrOpt('admin_user', default='lbadmin',
                help=('default admin_user')),
cfg.StrOpt('admin_password', default='changeit',
                help=('default admin_password')),
cfg.StrOpt('auth_version', default='v3.0',
                help=('default version')),
cfg.StrOpt('log_name', default='alliance',
                help=('default log_name')),
cfg.BoolOpt('include_service_catalog', default=False,
                help=('default include_service_catalog'))
                ]

CONF.register_group(opt_keystone_group)
CONF.register_opts(keystone_opts, opt_keystone_group)
config.parse_args()

class KeystoneProxy(object):

    def __init__(self, username='barbican',
                 password='orange',
                 tenant_name='service',
                 auth_url='http://localhost:35357/v3',
                 debug=True, **kwargs):

        self.keystone = v3client.Client(username='barbican',
                                      password='orange',
                                      tenant_name='service',
                                      auth_url='http://localhost:35357/v3',
                                      debug=True)

    def validate_token(self, token_id,
                       project_id=None,
                       project_name=None):
        if token_id:
            return auth_token.AuthProtocol(None, CONF.keystone).verify_uuid_token(token_id, retry=True)

    def validate_token_soft(self, token_id=None):
        try:
            if self.validate_token(token_id):
                return True
            else:
                return False
        except Exception:
            return False

    def create_token(self, auth_url='http://localhost:35357/v3',
                     username=None,
                     password=None,
                     project_name=None,
                     project_domain_id=None,
                     user_domain_id=None):
        
        #This is not the best impl
        aclient = v3client.Client(auth_url=auth_url,
                                  username=username,
                                  password=password,
                                  project_name=project_name,
                                  project_domain_id=project_domain_id,
                                  user_domain_id=user_domain_id)
        return aclient.get_raw_token_from_identity_service(auth_url=auth_url,
                                                           username=username,
                                                           password=password,
                                                           project_name=project_name,
                                                           project_domain_id=project_domain_id,
                                                           user_domain_id=user_domain_id)
        
    
    def delete_token(self, token_id=None):
        pass
        #no v3 client api

    def get_service(self, service_id=None):
        if service_id:
            return self.keystone.services.get(service_id)
        else:
            return self.keystone.services.list()

    def get_endpoints(self, service=None, interface=None, region=None, enabled=None):
            return self.keystone.endpoints.list(service, interface, region, enabled)

    def create_project(self, project_name=None, owner=None):
        #print self.keystone.tenants.list()
        tenant = self.keystone.tenants.create(tenant_name=project_name,
                                              description="project for %s" %owner,
                                              enabled=True)
        tenant.delete()


if __name__ == '__main__':
    ks_proxy = KeystoneProxy()
    #ks_proxy.create_project("arvind", "arvind")
    #print ks_proxy.get_service('f17fe3f0648440229f42cd101c2360d2')
    #print ks_proxy.get_endpoints(service='57b17d5dd86d47a8a635271cf2a9ee8f')
    #print ks_proxy.get_service('57b17d5dd86d47a8a635271cf2a9ee8f')
    print ks_proxy.validate_token_soft('18cf348c2634498d837fdd0e381862df')
    #print ks_proxy.create_token(username='lbuser',
    #                      password='changeit',
    #                      auth_url='http://localhost:35357/v3',
    #                      project_name='lbaas-user-project01',
    #                      project_domain_id='f7894f7eab9a463a990eb6dd6f13bda4',
    #                      user_domain_id='f7894f7eab9a463a990eb6dd6f13bda4')
    #ks_proxy.delete_token(token_id='18cf348c2634498d837fdd0e381862df')
    