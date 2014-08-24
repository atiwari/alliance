/**
 * Copyright (c) Hewlett-Packard, Inc. 2004-2010. All rights reserved.
 */

include "AllianceType.thrift"


namespace java alliance.thrift.service
namespace cpp alliance.thrift.service
namespace py alliance.thrift.service

enum ARole {
  HOST = 1,
  GUEST = 2
}

enum CType {
  ENC = 1,
  SENC = 2
}

enum TokenType {
  UUID = 1,
  PKI = 2
}


exception AException {
  1: i32 code,
  2: string message,
  3: string detail
}

struct SessionTicket {
	1: string cloud_id,
	2: string signature
	3: string pki_data
}


struct Token {
	1: string signature
	2: string pki_data
}


service AllianceAsyncService {
  
  VTResponse push(1: SessionTicket sessionTicket, 2: VToken req) throws (1: AException  allEx)
 
}
