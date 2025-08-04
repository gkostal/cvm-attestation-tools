#!/usr/bin/env python3
# test_api.py
#
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Simple test script for the CVM Attestation Web API.
"""

import requests
import json
import sys
import argparse

# API base URL
BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_attestation_endpoint(endpoint_path, test_name, vm_type):
    """Test an attestation endpoint."""
    print(f"\nTesting {test_name}...")
    
    # Set endpoint based on test type
    if "Guest" in test_name:
        endpoint_url = "https://sharedeus.eus.attest.azure.net/attest/AzureGuest?api-version=2020-10-01"
    elif "Platform" in test_name:
        endpoint_url = "https://sharedeus.eus.attest.azure.net/attest/SevSnpVm?api-version=2022-08-01"
    else:  # Hardware Evidence
        endpoint_url = ""
    
    # Set isolation type based on VM type
    isolation_type = "SEV_SNP" if vm_type == "CVM" else "TRUSTED_LAUNCH"
    
    # Sample request data
    test_data = {
        "endpoint": endpoint_url,
        "isolation_type": isolation_type,
        "claims": {"test": "data"}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint_path}",
            headers={"Content-Type": "application/json"},
            json=test_data
        )
        
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Success: {result.get('success', 'N/A')}")
            
            if 'error' in result:
                print(f"Error: {result['error']}")
            
            # Print token if present and successful
            if result.get('success') and 'token' in result:
                print(f"Token: {result['token']}")
            
            # Print evidence if present and successful
            if result.get('success') and 'evidence' in result:
                print(f"Evidence: {result['evidence']}")
            
            if 'logs' in result and result['logs']:
                print("Logs:")
                for log in result['logs'][-20:]:
                    print(f"  {log}")
            
            return response.status_code < 400
            
        except json.JSONDecodeError:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"{test_name} failed: {e}")
        return False

def test_swagger_docs():
    """Test that Swagger documentation is available."""
    print("\nTesting Swagger documentation...")
    try:
        response = requests.get(f"{BASE_URL}/swagger/")
        print(f"Status: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Swagger test failed: {e}")
        return False

def main():
    """Run all tests."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="CVM Attestation Web API Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""":
Examples:
  python test_api.py --vm-type CVM     # Test all CVM functionality
  python test_api.py --vm-type TVM     # Test TVM functionality (guest attestation only)
        """
    )
    parser.add_argument(
        '--vm-type',
        choices=['CVM', 'TVM'],
        required=True,
        help='VM type to test: CVM (Confidential VM) or TVM (Trusted VM)'
    )
    
    args = parser.parse_args()
    vm_type = args.vm_type
    
    print(f"CVM Attestation Web API Test Suite - {vm_type} Mode")
    print("=" * 50)
    
    # Define tests based on VM type
    if vm_type == "CVM":
        tests = [
            ("Health Check", test_health_check),
            ("Swagger Docs", test_swagger_docs),
            ("Guest Attestation", lambda: test_attestation_endpoint("/api/v1/attest/guest", "Guest Attestation", vm_type)),
            ("Platform Attestation", lambda: test_attestation_endpoint("/api/v1/attest/platform", "Platform Attestation", vm_type)),
            ("Hardware Evidence", lambda: test_attestation_endpoint("/api/v1/hardware-evidence", "Hardware Evidence", vm_type)),
        ]
    else:  # TVM
        tests = [
            ("Health Check", test_health_check),
            ("Swagger Docs", test_swagger_docs),
            ("Guest Attestation", lambda: test_attestation_endpoint("/api/v1/attest/guest", "Guest Attestation", vm_type)),
        ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("All tests passed!")
        sys.exit(0)
    else:
        print("Some tests failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()