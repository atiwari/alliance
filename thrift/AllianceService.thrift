/**
 * Copyright (c) Hewlett-Packard, Inc. 2004-2010. All rights reserved.
 */

# include "AllianceType.thrift"

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
  2: string message
}

struct SessionTKT {
	1: string cloud_id,
	2: string signature,
	3: string pki_data
}

struct PingRequest {
	1: string cloud_id,
	2: string request_data
}

struct PingResponse {
	1: string cloud_id,
	2: string response_data
}

struct TokenWrapper {
	1: string signature,
	2: string pki_data
}

struct TokenRequest {
	1: string cloud_id,
	2: string request_data
}

struct TokenResponse {
	1: string cloud_id,
	2: string response_data
}

struct ServiceRequest {
	1: string token_id,
	2: TokenType token_type
}

struct ServiceResponse {
	1: bool is_valid,
	2: string token_data
}

struct EndpointRequest {
	1: string token_id,
	2: TokenType token_type
}

struct EndpointResponse {
	1: bool is_valid,
	2: string token_data
}

struct ProvisioningRequest {
	1: string token_id,
	2: TokenType token_type
}

struct ProvisioningResponse {
	1: bool is_valid,
	2: string token_data
}

struct Notification {
	1: bool is_valid,
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

service AllianceService {

  SessionTKT getSession(1: SessionTKT SessionTKT) throws (1: AException allEx)

  PingResponse ping(1: PingRequest request) throws (1: AException allEx)  
  TokenResponse validateTokenHard(1: TokenRequest req) throws (1: AException  allEx)
  TokenResponse validateTokenSoft(1: TokenRequest req) throws (1: AException  allEx)

  ServiceResponse getServices(1: ServiceRequest req) throws (1: AException  allEx)
  EndpointResponse getEndpoints(1: EndpointRequest req) throws (1: AException  allEx)

  ProvisioningResponse provision(1: ProvisioningRequest req) throws (1: AException  allEx)

  oneway void pushToken(1: TokenWrapper req)
  oneway void popToken(1: TokenWrapper req)
  oneway void notifyX(1: Notification req)
}
