/**
 * Copyright (c) Hewlett-Packard, Inc. 2004-2010. All rights reserved.
 */


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

struct Pong {
	1: string response
}

struct TokenWrapper {
	1: string signature
	2: string pki_data
}

struct VTRequest {
	1: string token_id
	2: TokenType token_type
}

struct VTResponse {
	1: bool is_valid
	2: string token_data
}

struct ServiceRequest {
	1: string token_id
	2: TokenType token_type
}

struct ServiceResponse {
	1: bool is_valid
	2: string token_data
}

struct EndpointRequest {
	1: string token_id
	2: TokenType token_type
}

struct EndpointResponse {
	1: bool is_valid
	2: string token_data
}

struct ProvisioningRequest {
	1: string token_id
	2: TokenType token_type
}

struct ProvisioningResponse {
	1: bool is_valid
	2: string token_data
}

struct SignatureCredentials {
	1: string keyId,
	2: string keyType,
	3: string signatureMethod,
	4: string dataToSign,
	5: string signature
}

struct SigAuthRequest {
	1: SignatureCredentials credentials,
	2: map<string,string> params
}
