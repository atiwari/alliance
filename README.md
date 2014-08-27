alliance
========

Inter Cloud Resource Federation (Alliance)

***
This is work in progress please wait.
Documentations are not there. 
***

Project blue print and details
==============================
https://wiki.openstack.org/wiki/Inter_Cloud_Resource_Federation

Code organization
=================
```
alliance
    - common
        Common code used by server and client components.
    - lproxy 
        lproxy stands for 'local proxy', alliance server uses these proxies to get information from local services.
        e.g. Keystone for auth related calls, listing services and endpoints.
    - model
        Alliance models.
    - openstack
        OpenStack common code.
    - rpeoxy
        rproxy stands for 'remote proxy', clients can use these proxies to call alliance server running at other end.
        e.g. keystone can use these components to validate a uuid token from partner cloud. 
    - tclient
        This has classes to get thrift client and call remote procedure in partner cloud.
    - tests
        Some unit tests.
    - thrift
        Generated classes after compiling AllianceService.thrift
    - tserver
        This has server classes, currently it has implementation for synchronous server.
        later we will have another server for asynchronous request processing.  
        
        - handlers
            These are request handlers, server delegates the incoming requests to these handles.
```

Current features
================
1. Ping - To ping alliance service at other end.
2. Session - PKI key exchange is these but real communication will not be happening using PKI. Two partner has to handshake and decide on one key (session_key),    this key will be used for wrapping/unwrapping the request/response messages. 
3. validate uuid token across cloud

Working on
=========
Resource across cloud use case.

Help needed
===========
Where ever possible.
           
Why thrift
==========
1. Need RPC style calls.
2. Better performance.
3. Language independent.
4. Scale better.

Install thrift compiler
=======================
Note: This not mandatory

http://thrift.apache.org/tutorial/
Compile alliance interface file
===============================

go to project root and run.
thrift -out . --gen  py ./thrift/AllianceService.thrift 

to-copy-oslo-common
===================
python update.py ../alliance-master

How to play with it
==================

1. git clone https://github.com/arvindt7/alliance
2. pip install -r requirements.txt
3. pip install -r test-requirements.txt
4. to setup db. run WhenTestingPartnerRepo test from alliance/tests/model, this is kind of bootstrap script for now.
5. run the alliance server "alliance/tserver/alliance_server.py" has main block.
6. run "alliance/rproxy/ping.py"

    ```
    if you are getting "###### Fun playing ping, pong with my-east-cloud-or-dc" that means you are good. 
    ```
    
7. now run "alliance/rproxy/session.py", if you are getting below response that means you are good.

        ```
        my-east-cloud-or-dc
        rB6vxK/Wp9eBdjJRX21mn48xb3rXLfBwUrEjnyhhM08=
        2014-08-27 15:13:11.452498
        2014-08-28 01:13:11.452515
        ```

8. Start keystone server locally as per parameter in alliance.conf.
9. create a another user and get scoped token.
10. update "alliance/rproxy/auth.py" and run the same. you should see the auth response.

ssh-keygen -t rsa -C "my-east-cloud-or-dc"
ssh-keygen -t rsa -C "my-west-cloud-or-dc"

Note
====
1. Most of the codes are borrowed from Barbican code based (thanks to Barbican team), so do not surprise. 
2. Please excuse any typos in code. 
3. There is no setup.
4. No unit test coverage or functional test. 