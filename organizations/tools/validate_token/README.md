# Validate Authentication Token Tool

## Description
Tool responsible for validating the authentication token provided by the user after receiving it via email. This is the second step of the VTEX two-step authentication process.

## Functionality
This tool validates the access token provided by the user and returns complete authentication information, including session cookies and user data necessary for subsequent operations.

## Parameters

### Input
- **email** (string, required): User email address
  - Example: `"user@company.com"`
  - Contact field: `true`
- **auth_token** (string, required): Authentication token returned by the `authentication` tool
  - Example: `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
  - Contact field: `true`
- **user_token** (string, required): Token that the user received via email
  - Example: `"123456"`
  - Contact field: `true`

### Required Credentials
- **BASE_URL**: VTEX store base URL (ex: `https://weni.vtexcommercestable.com.br`)
- **LOCALE**: Localization for authentication process (ex: `pt-BR`)

## Response

The tool returns complete authentication information:

```json
{
  "authStatus": "Success",
  "promptMFA": false,
  "lastAttemptAvailable": null,
  "clientToken": null,
  "authCookie": {
    "Name": "VtexIdclientAutCookie_pamplonase",
    "Value": "eyJhbGciOiJFUzI1NiIsImtpZCI6IkRENTc5NUVDNkUxN0RBNjI4NjFDMDc4MTMwRkQyMEIzNDNEQkQzOTEiLCJ0eXAiOiJqd3QifQ..."
  },
  "accountAuthCookie": {
    "Name": "VtexIdclientAutCookie_84e6c2a3-f623-4761-b701-5337eb28e11a",
    "Value": "eyJhbGciOiJFUzI1NiIsImtpZCI6IkRENTc5NUVDNkUxN0RBNjI4NjFDMDc4MTMwRkQyMEIzNDNEQkQzOTEiLCJ0eXAiOiJqd3QifQ..."
  },
  "expiresIn": 86399,
  "userId": "ea757ea6-b48d-4bd9-885f-8c5a0fdaa147",
  "phoneNumber": null,
  "scope": null
}
```

### Response Fields
- **authStatus**: Authentication status ("Success" or "Failed")
- **promptMFA**: Indicates if multi-factor authentication is required
- **lastAttemptAvailable**: Information about last attempt
- **clientToken**: Client token (if applicable)
- **authCookie**: Main authentication cookie
  - **Name**: Cookie name
  - **Value**: Cookie JWT value
- **accountAuthCookie**: Account authentication cookie
  - **Name**: Account cookie name
  - **Value**: Account cookie JWT value
- **expiresIn**: Expiration time in seconds
- **userId**: Unique authenticated user ID
- **phoneNumber**: Phone number (if available)
- **scope**: Permission scope

## Internal Process

1. **Account Name Extraction**: Obtains account name from BASE_URL
2. **Token Validation**: Sends user token for validation
3. **Response Processing**: Extracts authentication data
4. **Cookie Formatting**: Organizes cookies for later use

## API Used

### Endpoint
```
{BASE_URL}/api/vtexid/pub/authentication/accesskey/validate
```

### Method
POST (multipart/form-data)

### Headers
- `Accept`: application/json

### Data Sent
- `authenticationToken`: Internal authentication token
- `email`: User email
- `accessKey`: Token provided by user (received via email)

## Use Cases
- Validation of access tokens sent via email
- Obtaining session cookies for authenticated operations
- Retrieving authenticated user information
- Preparing data for B2B session creation

## Error Handling

### Invalid or Expired Token
```json
{
  "message": "Invalid or expired token"
}
```

### Data Required for Next Steps
The data returned by this tool is essential for:
- **create_session**: Cookies and userId are necessary
- **Manager**: authCookie, accountAuthCookie and userId must be forwarded

## Dependencies
- `requests` module for HTTP calls
- `re` module for regular expressions

## Authentication Flow
1. **authentication** → Sends token via email
2. **validate_token** (this tool) → Validates token and returns authentication data
3. **create_session** → Uses data from this tool to create session

## Security
- JWT tokens contain encrypted information
- Cookies have defined expiration time
- Validation happens on VTEX server
- Sensitive data is handled securely

## Manager Integration
**Data to be forwarded to manager:**
- `authCookie.Name` and `authCookie.Value`
- `accountAuthCookie.Name` and `accountAuthCookie.Value`
- `userId`

This data will be used later in session creation.