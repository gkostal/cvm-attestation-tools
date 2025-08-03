# CVM Attestation Web API

This Flask-based REST API provides web endpoints for the CVM attestation functionality.

## Features

- **REST API Endpoints**:
  - `POST /api/v1/attest/guest` - Attest guest evidence (hardware + guest)
  - `POST /api/v1/attest/platform` - Attest platform evidence (hardware only)
  - `POST /api/v1/hardware-evidence` - Get hardware evidence
  - `GET /health` - Health check

- **Swagger Documentation**: Available at `/swagger/`
- **Memory-based Logging**: All log messages are captured and returned in API responses
- **CORS Support**: Cross-origin requests are supported

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
python run_server.py
```

The API will be available at `http://localhost:5000`

## API Usage

### Request Format

All attestation endpoints expect a JSON payload with the following structure:

```json
{
  "endpoint": "https://your-attestation-endpoint.com",
  "isolation_type": "TDX",
  "claims": {
    "optional": "user claims"
  }
}
```

**Parameters:**
- `endpoint` (required): The attestation service endpoint URL
- `isolation_type` (required): One of `"TDX"`, `"SEV_SNP"`, `"TRUSTED_LAUNCH"`, or `"UNDEFINED"`
- `claims` (optional): Optional user claims object

### Response Format

All endpoints return a JSON response with the following structure:

```json
{
  "success": true,
  "token": "attestation-token-or-evidence-data",
  "logs": [
    "2024-01-01 12:00:00 - info - Starting attestation...",
    "2024-01-01 12:00:01 - info - Attestation completed"
  ]
}
```

**Fields:**
- `success`: Boolean indicating if the operation succeeded
- `token`: The attestation token (for attest endpoints) or evidence data (for hardware-evidence endpoint)
- `error`: Error message (present when `success` is `false`)
- `logs`: Array of log messages from the operation

### Examples

#### Attest Guest
```bash
curl -X POST http://localhost:5000/api/v1/attest/guest \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://your-maa-endpoint.com",
    "isolation_type": "TDX"
  }'
```

#### Attest Platform
```bash
curl -X POST http://localhost:5000/api/v1/attest/platform \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://your-maa-endpoint.com",
    "isolation_type": "SEV_SNP",
    "claims": {"custom": "data"}
  }'
```

#### Get Hardware Evidence
```bash
curl -X POST http://localhost:5000/api/v1/hardware-evidence \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://your-maa-endpoint.com",
    "isolation_type": "TDX"
  }'
```

## Configuration

The API is configured to:
- Always use MAA (Microsoft Attestation Service) as the verifier
- Not require an API key (always `None`)
- Capture all log messages in memory and return them in responses
- Support CORS for cross-origin requests

## Development

To run in development mode:
```bash
python run_server.py
```

The server will start with debug mode enabled and auto-reload on code changes.

## Docker

Build and run with Docker:
```bash
docker build -t cvm-attestation-api .
docker run -p 5000:5000 cvm-attestation-api
```

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid input)
- `500`: Internal server error (attestation failure)

All error responses include detailed error messages and log output for debugging.