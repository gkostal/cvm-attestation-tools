from flask import Flask, jsonify, request
from AttestationClient import AttestationClient, AttestationClientParameters, Verifier
from src.Logger import Logger
from src.Isolation import IsolationType

app = Flask(__name__)

# Initialize logger
logger = Logger("AttestationAPI").get_logger()

# Sample configuration for the AttestationClient
# Replace with actual configuration
endpoint = "https://sharedweu.weu.attest.azure.net/attest/SevSnpVm?api-version=2022-08-01"
api_key = ""
isolation_type = IsolationType.SEV_SNP
verifier = Verifier.MAA

# Initialize AttestationClient
client_params = AttestationClientParameters(endpoint, verifier, isolation_type, api_key=api_key)
attestation_client = AttestationClient(logger, client_params)

@app.route('/api/attest_platform', methods=['POST'])
def attest_platform():
    try:
        # Call the attest_platform method
        token = attestation_client.attest_platform()
        return jsonify({"token": token}), 200
    except Exception as e:
        logger.error(f"Error during attestation: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_hw_evidence', methods=['POST'])
def generate_hw_evidence():
    try:
        # Call the generate HW evidence method
        evidence = attestation_client.generate_hw_evidence()
        return evidence, 200
    except Exception as e:
        logger.error(f"Error during attestation: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
