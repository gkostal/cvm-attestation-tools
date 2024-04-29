# AttestationClient.py
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from enum import Enum
from src.OsInfo import OsInfo
from src.Isolation import IsolationType, IsolationInfo
from src.Logger import Logger
from src.ReportParser import ReportParser
from src.ImdsClient import ImdsClient
from src.AttestationProvider import MAAProvider, ITAProvider
from AttestationTypes import TpmInfo
from src.measurements import get_measurements
from src.Encoder import Encoder, urlsafe_b64decode
from tpm_wrapper import get_hcl_report, get_aik_cert, \
  get_aik_pub, get_pcr_quote, get_pcr_values, get_ephemeral_key, \
  decrypt_with_ephemeral_key

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# The version number of the attestation protocol between the client and the service.
PROTOCOL_VERSION = "2.0"


class GuestAttestationParameters:
  def __init__(self, os_info=None, tcg_logs=None, tpm_info=None, isolation=None):
    self.os_info = os_info
    self.tcg_logs = tcg_logs
    self.tpm_info = tpm_info
    self.isolation = isolation
  
  def toJson(self):
    return json.dumps({
      'AttestationProtocolVersion': PROTOCOL_VERSION,
      'OSType': Encoder.base64_encode_string(str(self.os_info.type)),
      'OSDistro': Encoder.base64_encode_string(self.os_info.distro_name),
      'OSVersionMajor': str(self.os_info.major_version),
      'OSVersionMinor': str(self.os_info.minor_version),
      'OSBuild': Encoder.base64_encode_string(self.os_info.build),
      'TcgLogs': Encoder.base64encode(self.tcg_logs),
      'ClientPayload': Encoder.base64_encode_string(""),
      'TpmInfo': self.tpm_info.get_values(),
      'IsolationInfo': self.isolation.get_values()
    })


class PlatformAttestationParameters:
  def __init__(self, hardware_report, runtime_data):
    self.hardware_report = hardware_report
    self.runtime_data = runtime_data


class Verifier(Enum):
  UNDEFINED = 0 # Undefined type
  MAA = 1       # Microsoft Attestation Service
  ITA = 2       # Intel Trusted Authority


class AttestationClientParameters:
  def __init__(self, endpoint: str, verifier: Verifier, isolation_type: IsolationType, claims = None, api_key = None):
    # Validate the isolation type
    if not isinstance(isolation_type, IsolationType):
      raise ValueError(f"Unsupported isolation type: {isolation_type}. Supported types: {list(IsolationType)}")
    
     # Validate the verifier
    if not isinstance(verifier, Verifier):
      raise ValueError(f"Unsupported isolation type: {verifier}. Supported types: {list(Verifier)}")

    self.endpoint = endpoint
    self.verifier = verifier
    self.api_key = api_key
    self.isolation_type = isolation_type
    self.user_claims = claims


class AttestationClient:
  def __init__(self, logger: Logger, parameters: AttestationClientParameters):
    verifier = parameters.verifier
    isolation_type = parameters.isolation_type
    endpoint = parameters.endpoint
    api_key = parameters.api_key

    self.parameters = parameters
    self.logger = logger

    self.provider = MAAProvider(logger,isolation_type,endpoint) if verifier == Verifier.MAA else ITAProvider(logger,isolation_type,endpoint, api_key) if verifier == Verifier.ITA else None
  
  def attest_guest(self):
    # try:
      imds_client = ImdsClient(self.logger)
      # Extract Hardware Report and Runtime Data
      hcl_report = get_hcl_report(self.parameters.user_claims)
      report_type = ReportParser.extract_report_type(hcl_report)
      runtime_data = ReportParser.extract_runtimes_data(hcl_report)
      hw_report = ReportParser.extract_hw_report(hcl_report)
      cert_chain = imds_client.get_vcek_certificate()

      # Set request data based on the platform
      encoded_report = Encoder.base64url_encode(hw_report)
      encoded_runtime_data = Encoder.base64url_encode(runtime_data)

      os_info = OsInfo()
      aik_cert = get_aik_cert()
      aik_pub = get_aik_pub()
      pcr_quote, sig = get_pcr_quote(os_info.pcr_list)
      pcr_values = get_pcr_values(os_info.pcr_list)
      key = get_ephemeral_key(os_info.pcr_list)
      tpm_info = TpmInfo(aik_cert, aik_pub, pcr_quote, sig, pcr_values, key)
      tcg_logs = get_measurements(os_info.type)
      isolation = IsolationInfo(self.parameters.isolation_type, hw_report, runtime_data, cert_chain)
      param = GuestAttestationParameters(os_info, tcg_logs, tpm_info, isolation)

      # Calls attestation provider with the guest evidence
      request = {
        "AttestationInfo": Encoder.base64url_encode_string(param.toJson())
      }
      encoded_response = self.provider.attest_guest(request)

      self.logger.info('Parsing encoded token...')

      # decode the response
      response = urlsafe_b64decode(encoded_response).decode('utf-8')
      response = json.loads(response)

      # parse encrypted inner key
      encrypted_inner_key = response['EncryptedInnerKey']
      encrypted_inner_key = json.dumps(encrypted_inner_key)
      encrypted_inner_key_decoded = Encoder.base64decode(encrypted_inner_key)

      # parse Encryption Parameters
      encryption_params_json = response['EncryptionParams']
      iv = json.dumps(encryption_params_json['Iv'])
      iv = Encoder.base64decode(iv)

      auth_data = response['AuthenticationData']
      auth_data = json.dumps(auth_data)
      auth_data = Encoder.base64decode(auth_data)

      decrypted_inner_key = \
        decrypt_with_ephemeral_key(encrypted_inner_key_decoded, os_info.pcr_list)
      print("HERE")

      # parse the encrypted token
      encrypted_jwt = response['Jwt']
      encrypted_jwt = json.dumps(encrypted_jwt)
      encrypted_jwt = Encoder.base64decode(encrypted_jwt)

      # Your AES key
      key = decrypted_inner_key

      # Create an AESGCM object with the generated key
      aesgcm = AESGCM(key)

      self.logger.info('Decrypting JWT...')

      associated_data = bytearray(b'Transport Key')

      # NOTE: authentication data is part of the cipher's last 16 bytes
      cipher_message = encrypted_jwt + auth_data

      # Decrypt the token using the same key, nonce, and associated data
      decrypted_data = aesgcm.decrypt(iv, cipher_message, bytes(associated_data))
      self.logger.info("Decrypted JWT Successfully.")
      self.logger.info('TOKEN:')
      self.logger.info(decrypted_data.decode('utf-8'))

      return decrypted_data
    # except Exception as e:
    #     exception_message = "Decryption failed:" + str(e)
    #     self.logger.info(exception_message)

  def attest_platform(self):
    self.logger.info('Attesting Platform Evidence...')

    isolation_type = self.parameters.isolation_type 

    # Extract Hardware Report and Runtime Data
    hcl_report = get_hcl_report(self.parameters.user_claims)
    report_type = ReportParser.extract_report_type(hcl_report)
    runtime_data = ReportParser.extract_runtimes_data(hcl_report)
    hw_report = ReportParser.extract_hw_report(hcl_report)

    # Set request data based on the platform
    encoded_report = Encoder.base64url_encode(hw_report)
    encoded_runtime_data = Encoder.base64url_encode(runtime_data)
    encoded_token = ""
    encoded_hw_evidence = ""

    imds_client = ImdsClient(self.logger)
    if report_type == 'tdx' and isolation_type == IsolationType.TDX:
      encoded_hw_evidence = imds_client.get_td_quote(encoded_report)
    elif report_type == 'snp' and isolation_type == IsolationType.SEV_SNP:
      cert_chain = imds_client.get_vcek_certificate()
      snp_report = {
        'SnpReport': encoded_report,
        'VcekCertChain': Encoder.base64url_encode(cert_chain)
      }
      snp_report = json.dumps(snp_report)
      snp_report = bytearray(snp_report.encode('utf-8'))
      encoded_hw_evidence = Encoder.base64url_encode(snp_report)
    else:
      self.logger.info('Invalid Hardware Report Type')

    # verify hardware evidence
    encoded_token = self.provider.attest_platform(encoded_hw_evidence, encoded_runtime_data)
    return encoded_token