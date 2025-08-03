#!/usr/bin/env python3
# run_server.py
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Development server runner for the CVM Attestation Web API.
"""

import os
import sys

# Add the cvm-attestation directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
cvm_attestation_dir = os.path.join(current_dir, '..', 'cvm-attestation')
sys.path.insert(0, cvm_attestation_dir)

from app import app

if __name__ == '__main__':
    print("Starting CVM Attestation Web API...")
    print("Swagger documentation available at: http://localhost:5000/swagger/")
    print("Health check available at: http://localhost:5000/health")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )