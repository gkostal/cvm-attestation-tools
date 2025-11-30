# snp_utils.py
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import json
from src.encoder import Encoder


class SnpFormatter:
    """Utility class for formatting SEV-SNP hardware evidence."""
    
    @staticmethod
    def format_snp_evidence(snp_report: bytes, vcek_cert_chain: bytes) -> str:
        """
        Format SEV-SNP hardware evidence with VCEK certificate chain.
        
        Creates a JSON structure containing both the SNP report and VCEK cert chain,
        then encodes it as base64url for attestation.
        
        Args:
            snp_report: Raw SNP hardware report bytes
            vcek_cert_chain: VCEK certificate chain bytes
            
        Returns:
            Base64url encoded JSON string containing:
            {
                "SnpReport": "<base64url_encoded_report>",
                "VcekCertChain": "<base64url_encoded_cert_chain>"
            }
        """
        hardware_evidence = {
            'SnpReport': Encoder.base64url_encode(snp_report),
            'VcekCertChain': Encoder.base64url_encode(vcek_cert_chain)
        }
        hardware_evidence_json = json.dumps(hardware_evidence)
        hardware_evidence_bytes = bytearray(hardware_evidence_json.encode('utf-8'))
        return Encoder.base64url_encode(hardware_evidence_bytes)
