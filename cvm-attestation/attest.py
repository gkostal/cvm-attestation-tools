# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from base64 import urlsafe_b64encode, urlsafe_b64decode, b64decode
import json
import click
from src.report_parser import *
from AttestationClient import *
from src.OsInfo import OsInfo
from src.Logger import Logger
from src.measurements import get_measurements
from src.Isolation import IsolationType
from AttestationTypes import *
import os

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def encrypt(key, plaintext, associated_data):
    # Generate a random 96-bit IV.
    iv = os.urandom(12)

    # Construct an AES-GCM Cipher object with the given key and a
    # randomly generated IV.
    encryptor = Cipher(
        algorithms.AES(key),
        modes.GCM(iv),
    ).encryptor()

    # associated_data will be authenticated but not encrypted,
    # it must also be passed in on decryption.
    encryptor.authenticate_additional_data(associated_data)

    # Encrypt the plaintext and get the associated ciphertext.
    # GCM does not require padding.
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    return (iv, ciphertext, encryptor.tag)

def base64url_encode(data):
  return str(urlsafe_b64encode(data).rstrip(b'='), "utf-8")

# Function to encode a string to base64url
def base64url_encode_string(input_string):
    # Convert string to bytes
    bytes_to_encode = input_string.encode('utf-8')
    # Perform base64 encoding
    base64_bytes = b64encode(bytes_to_encode)
    # Convert to base64url by replacing '+' with '-' and '/' with '_'
    base64url_bytes = base64_bytes.replace(b'+', b'-').replace(b'/', b'_')
    # Return the base64url encoded string
    return base64url_bytes.decode('utf-8').rstrip('=')


def parse_config_file(filename):
  with open(filename, 'r') as json_file:
    # Parse the JSON data
    data = json.load(json_file)
  return data


IsolationTypeLookup = {
  'maa_tdx': IsolationType.TDX,
  'maa_snp': IsolationType.SEV_SNP,
  'ita': IsolationType.TDX,
  'default': IsolationType.UNDEFINED
}


AttestationProviderLookup = {
  'maa_tdx': Verifier.MAA,
  'maa_snp': Verifier.MAA,
  'ita': Verifier.ITA,
  'default': Verifier.UNDEFINED
}


@click.command()
@click.option('--c', type=str)
def main(c):

  try:
    # create a new console logger
    logger = Logger('logger').get_logger()
    logger.info("Attestation started...")
    logger.info(c)

    # creates an attestation parameters based on user's config
    config_json = parse_config_file(c)
    provider_tag = config_json['attestation_provider']
    endpoint = config_json['attestation_url']
    api_key = config_json['api_key']
    isolation_type = IsolationType.get(provider_tag, IsolationType['default'])
    provider = Verifier.get(provider_tag, Verifier['default'])
    client_parameters = AttestationClientParameters(endpoint, provider, isolation_type, api_key) 


    # PCR values for Linux Guest
    LINUX_PCR_LIST = [0, 1, 2, 3, 4, 5, 6, 7]
    WINDOWS_PCR_LIST = [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14]

    attestation_client = AttestationClient(logger, client_parameters)
    attestation_client.attest_platform()
  except Exception as e:
    logger.info('Exception in attest: ', e)


  # # Extract data from HCL report
  # hcl_report = tpm_wrapper.get_hcl_report(config_json['claims'])
  # report_type = extract_report_type(hcl_report)
  # runtime_data = extract_runtime_data(hcl_report)
  # hw_report = extract_hw_report(hcl_report)

  # # Set request data based on the platform
  # encoded_report = base64url_encode(hw_report)
  # encoded_runtime_data = base64url_encode(runtime_data)
  # encoded_token = ""
  # encoded_hw_evidence = ""
  # if report_type == 'tdx':
  #   isolation_type = IsolationType.TDX
  #   encoded_hw_evidence = src.imds.get_td_quote(encoded_report)
  # elif report_type == 'snp':
  #   isolation_type = IsolationType.SEV_SNP
  #   cert_chain = src.imds.get_vcek_certificate()
  #   snp_report = {
  #     'SnpReport': encoded_report,
  #     'VcekCertChain': base64url_encode(cert_chain)
  #   }
  #   snp_report = json.dumps(snp_report)
  #   snp_report = bytearray(snp_report.encode('utf-8'))
  #   encoded_hw_evidence = base64url_encode(snp_report)
  # else:
  #   logger.info('error')

  # aik_cert = tpm_wrapper.get_aik_cert()
  # aik_pub = tpm_wrapper.get_aik_pub()
  # pcr_quote, sig = tpm_wrapper.get_pcr_quote(LINUX_PCR_LIST)
  # pcr_values = tpm_wrapper.get_pcr_values(LINUX_PCR_LIST)
  # key = tpm_wrapper.get_ephemeral_key(LINUX_PCR_LIST)
  # tpm_info = TpmInfo(aik_cert, aik_pub, pcr_quote, sig, pcr_values, key)

  # os_info = OsInfo("Linux")
  # tcg_logs = get_measurements("Linux")
  # isolation = IsolationInfo(isolation_type, encoded_report, runtime_data, cert_chain)
  # param = GuestAttestationParameters(os_info, tcg_logs, tpm_info, isolation)
  # # logger.info(param.toJson())

  # request = {
  #   "AttestationInfo": base64url_encode_string(param.toJson())
  # }
  # # logger.info(request)

  # # Verify hardware evidence
  # encoded_response = src.verifier.verify_guest_evidence({
  #   'evidence': request,
  #   'endpoint': config_json['attestation_url']
  # })

  # # Print claims
  # # try:
  # logger.info('Parsing encoded token...')

  # # decode the response
  # response = urlsafe_b64decode(encoded_response).decode('utf-8')
  # response = json.loads(response)

  # # parse encrypted inner key
  # encrypted_inner_key = response['EncryptedInnerKey']
  # encrypted_inner_key_decoded = b64decode(bytes(json.dumps(encrypted_inner_key), 'utf-8'))

  # # parse Encryption Parameters
  # encryption_params_json = response['EncryptionParams']
  # iv = b64decode(bytes(json.dumps(encryption_params_json['Iv']), 'utf-8'))

  # auth_data = response['AuthenticationData']
  # auth_data = b64decode(bytes(json.dumps(auth_data), 'utf-8'))

  # decrypted_inner_key = \
  #   tpm_wrapper.decrypt_with_ephemeral_key(encrypted_inner_key_decoded, LINUX_PCR_LIST)

  # # parse the encrypted token
  # encrypted_jwt = response['Jwt']
  # encrypted_jwt = b64decode(bytes(json.dumps(encrypted_jwt), 'utf-8'))

  # # Your AES key
  # key = decrypted_inner_key

  # # Create an AESGCM object with the generated key
  # aesgcm = AESGCM(key)

  # # Now `ciphertext` contains the encrypted data and the authentication tag

  # try:
  #   logger.info('Decrypting JWT...')

  #   associated_data = bytearray(b'Transport Key')

  #   # NOTE: authentication data is part of the cipher's last 16 bytes
  #   cipher_message = encrypted_jwt + auth_data

  #   # Decrypt the token using the same key, nonce, and associated data
  #   decrypted_data = aesgcm.decrypt(iv, cipher_message, bytes(associated_data))
  #   logger.info("Decrypted JWT Successfully.")
  #   logger.info('TOKEN:')
  #   logger.info(decrypted_data.decode('utf-8'))
  # except Exception as e:
  #     exception_message = "Decryption failed:" + str(e)
  #     logger.info(exception_message)

    # claims = jwt.decode(encoded_token, options={"verify_signature": False})

    # src.verifier.print_token_claims(claims, config_json['attestation_provider'])
  # except Exception as e:
  #   logger.info('Exception: ', e)

if __name__ == "__main__":
  main()