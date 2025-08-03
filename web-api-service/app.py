# app.py
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import sys
import os
import json
import base64
from typing import Optional

# Add the cvm-attestation directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cvm-attestation'))

from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields, Namespace
from flask_cors import CORS

from AttestationClient import AttestationClient, AttestationClientParameters, Verifier, HardwareEvidence
from src.Isolation import IsolationType
from memory_logger import MemoryLogger


# Create Flask app
app = Flask(__name__)
CORS(app)

# Create Flask-RESTX API
api = Api(
    app,
    version='1.0',
    title='CVM Attestation API',
    description='REST API for CVM Attestation operations',
    doc='/swagger/'
)

# Create namespace
ns = Namespace('api/v1', description='Attestation operations')
api.add_namespace(ns)

# Define models for Swagger documentation
attestation_request_model = api.model('AttestationRequest', {
    'endpoint': fields.String(required=True, description='Attestation endpoint URL'),
    'isolation_type': fields.String(required=True, description='Isolation type', 
                                   enum=['TDX', 'SEV_SNP', 'TRUSTED_LAUNCH', 'UNDEFINED']),
    'claims': fields.Raw(required=False, description='Optional user claims')
})

attestation_response_model = api.model('AttestationResponse', {
    'success': fields.Boolean(description='Whether the operation was successful'),
    'token': fields.String(description='Attestation token (if successful)'),
    'error': fields.String(description='Error message (if failed)'),
    'logs': fields.List(fields.String, description='Log messages from the operation')
})

hardware_evidence_response_model = api.model('HardwareEvidenceResponse', {
    'success': fields.Boolean(description='Whether the operation was successful'),
    'evidence': fields.Raw(description='Hardware evidence data (if successful)'),
    'error': fields.String(description='Error message (if failed)'),
    'logs': fields.List(fields.String, description='Log messages from the operation')
})


def map_isolation_type(isolation_type_str: str) -> IsolationType:
    """Map string to IsolationType enum."""
    mapping = {
        'TDX': IsolationType.TDX,
        'SEV_SNP': IsolationType.SEV_SNP,
        'TRUSTED_LAUNCH': IsolationType.TRUSTED_LAUNCH,
        'UNDEFINED': IsolationType.UNDEFINED
    }
    
    if isolation_type_str not in mapping:
        raise ValueError(f"Invalid isolation type: {isolation_type_str}. "
                        f"Supported types: {list(mapping.keys())}")
    
    return mapping[isolation_type_str]


def create_attestation_client(endpoint: str, isolation_type_str: str, claims: Optional[dict] = None) -> tuple:
    """Create an AttestationClient instance and return it along with the logger."""
    try:
        # Create memory logger
        logger = MemoryLogger()
        
        # Map isolation type
        isolation_type = map_isolation_type(isolation_type_str)
        
        # Create parameters (verifier is always MAA, api_key is always None)
        parameters = AttestationClientParameters(
            endpoint=endpoint,
            verifier=Verifier.MAA,
            isolation_type=isolation_type,
            claims=claims,
            api_key=None
        )
        
        # Create client
        client = AttestationClient(logger, parameters)
        
        return client, logger, None
        
    except Exception as e:
        logger = MemoryLogger()
        logger.error(f"Failed to create attestation client: {str(e)}")
        return None, logger, str(e)


def handle_bytes_response(response_data, logger: MemoryLogger) -> dict:
    """Handle response data that might be bytes."""
    try:
        if isinstance(response_data, bytes):
            # Try to decode as UTF-8 string first
            try:
                decoded = response_data.decode('utf-8')
                return {
                    'success': True,
                    'token': decoded,
                    'logs': logger.get_logs()
                }
            except UnicodeDecodeError:
                # If it's not valid UTF-8, return as base64
                encoded = base64.b64encode(response_data).decode('utf-8')
                return {
                    'success': True,
                    'token': encoded,
                    'logs': logger.get_logs()
                }
        elif isinstance(response_data, str):
            return {
                'success': True,
                'token': response_data,
                'logs': logger.get_logs()
            }
        else:
            return {
                'success': True,
                'token': str(response_data),
                'logs': logger.get_logs()
            }
    except Exception as e:
        logger.error(f"Error handling response: {str(e)}")
        return {
            'success': False,
            'error': f"Error processing response: {str(e)}",
            'logs': logger.get_logs()
        }


@ns.route('/attest/guest')
class AttestGuest(Resource):
    @ns.expect(attestation_request_model)
    @ns.marshal_with(attestation_response_model)
    def post(self):
        """Attest the guest (hardware and guest evidence)."""
        try:
            data = request.get_json()
            
            if not data:
                return {
                    'success': False,
                    'error': 'Request body must be JSON',
                    'logs': []
                }, 400
            
            # Validate required fields
            if 'endpoint' not in data or 'isolation_type' not in data:
                return {
                    'success': False,
                    'error': 'Missing required fields: endpoint, isolation_type',
                    'logs': []
                }, 400
            
            endpoint = data['endpoint']
            isolation_type = data['isolation_type']
            claims = data.get('claims')
            
            # Create attestation client
            client, logger, error = create_attestation_client(endpoint, isolation_type, claims)
            
            if error:
                return {
                    'success': False,
                    'error': error,
                    'logs': logger.get_logs()
                }, 400
            
            # Perform guest attestation
            try:
                result = client.attest_guest()
                
                if result is None:
                    return {
                        'success': False,
                        'error': 'Guest attestation failed - no token received',
                        'logs': logger.get_logs()
                    }, 500
                
                return handle_bytes_response(result, logger)
                
            except Exception as e:
                logger.error(f"Guest attestation failed: {str(e)}")
                return {
                    'success': False,
                    'error': f'Guest attestation failed: {str(e)}',
                    'logs': logger.get_logs()
                }, 500
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'logs': []
            }, 500


@ns.route('/attest/platform')
class AttestPlatform(Resource):
    @ns.expect(attestation_request_model)
    @ns.marshal_with(attestation_response_model)
    def post(self):
        """Attest the platform (hardware evidence only)."""
        try:
            data = request.get_json()
            
            if not data:
                return {
                    'success': False,
                    'error': 'Request body must be JSON',
                    'logs': []
                }, 400
            
            # Validate required fields
            if 'endpoint' not in data or 'isolation_type' not in data:
                return {
                    'success': False,
                    'error': 'Missing required fields: endpoint, isolation_type',
                    'logs': []
                }, 400
            
            endpoint = data['endpoint']
            isolation_type = data['isolation_type']
            claims = data.get('claims')
            
            # Create attestation client
            client, logger, error = create_attestation_client(endpoint, isolation_type, claims)
            
            if error:
                return {
                    'success': False,
                    'error': error,
                    'logs': logger.get_logs()
                }, 400
            
            # Perform platform attestation
            try:
                result = client.attest_platform()
                
                if result is None:
                    return {
                        'success': False,
                        'error': 'Platform attestation failed - no token received',
                        'logs': logger.get_logs()
                    }, 500
                
                return handle_bytes_response(result, logger)
                
            except Exception as e:
                logger.error(f"Platform attestation failed: {str(e)}")
                return {
                    'success': False,
                    'error': f'Platform attestation failed: {str(e)}',
                    'logs': logger.get_logs()
                }, 500
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'logs': []
            }, 500


@ns.route('/hardware-evidence')
class GetHardwareEvidence(Resource):
    @ns.expect(attestation_request_model)
    @ns.marshal_with(hardware_evidence_response_model)
    def post(self):
        """Get hardware evidence."""
        try:
            data = request.get_json()
            
            if not data:
                return {
                    'success': False,
                    'error': 'Request body must be JSON',
                    'logs': []
                }, 400
            
            # Validate required fields
            if 'endpoint' not in data or 'isolation_type' not in data:
                return {
                    'success': False,
                    'error': 'Missing required fields: endpoint, isolation_type',
                    'logs': []
                }, 400
            
            endpoint = data['endpoint']
            isolation_type = data['isolation_type']
            claims = data.get('claims')
            
            # Create attestation client
            client, logger, error = create_attestation_client(endpoint, isolation_type, claims)
            
            if error:
                return {
                    'success': False,
                    'error': error,
                    'logs': logger.get_logs()
                }, 400
            
            # Get hardware evidence
            try:
                evidence = client.get_hardware_evidence()
                
                if evidence is None:
                    return {
                        'success': False,
                        'error': 'Failed to get hardware evidence',
                        'logs': logger.get_logs()
                    }, 500
                
                # Convert hardware evidence to JSON-serializable format
                evidence_data = {
                    'type': evidence.type,
                    'hardware_report': base64.b64encode(evidence.hardware_report).decode('utf-8'),
                    'runtime_data': base64.b64encode(evidence.runtime_data).decode('utf-8')
                }
                
                return {
                    'success': True,
                    'evidence': evidence_data,
                    'logs': logger.get_logs()
                }
                
            except Exception as e:
                logger.error(f"Failed to get hardware evidence: {str(e)}")
                return {
                    'success': False,
                    'error': f'Failed to get hardware evidence: {str(e)}',
                    'logs': logger.get_logs()
                }, 500
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'logs': []
            }, 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {'status': 'healthy'}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)