# OIDC / JWT Authentication

## Design

v0.4 keeps the MCP SDK as the HTTP bearer gate and replaces the v0.3 static-token verifier with an optional OIDC/JWT verifier.

Validation includes:

- JWT signature through JWKS
- configured algorithm allow-list
- issuer
- audience
- expiration
- subject
- application role mapping
- tenant claim extraction

An unrecognized role is rejected.

## Generic OIDC

```bash
export DPMCP_TRANSPORT=streamable-http
export DPMCP_AUTH_ENABLED=true
export DPMCP_AUTH_MODE=oidc

export DPMCP_AUTH_ISSUER_URL='https://idp.example.com/realms/data-platform'
export DPMCP_AUTH_RESOURCE_URL='https://mcp.example.com/mcp'
export DPMCP_OIDC_JWKS_URL='https://idp.example.com/realms/data-platform/protocol/openid-connect/certs'
export DPMCP_OIDC_AUDIENCE='data-platform-mcp'
export DPMCP_OIDC_ROLE_CLAIM='realm_access.roles'
export DPMCP_OIDC_TENANT_CLAIM='tenant'
export DPMCP_OIDC_CLIENT_ID_CLAIM='azp'
export DPMCP_OIDC_ROLE_MAP_JSON='{
  "data-platform-reader":"reader",
  "data-platform-analyst":"analyst",
  "data-platform-operator":"operator",
  "data-platform-admin":"admin"
}'
```

## Keycloak example

Recommended Keycloak setup:

1. Create a dedicated client/audience for the MCP resource server.
2. Define client or realm roles corresponding to reader/analyst/operator/admin.
3. Map the roles into the access token.
4. Add a tenant claim mapper if source isolation is enabled.
5. Configure the MCP server with the realm issuer and JWKS endpoint.

Keycloak commonly exposes realm roles at:

```text
realm_access.roles
```

## Microsoft Entra ID example

Typical Entra configuration:

```bash
export DPMCP_AUTH_ISSUER_URL='https://login.microsoftonline.com/<tenant-id>/v2.0'
export DPMCP_OIDC_JWKS_URL='https://login.microsoftonline.com/<tenant-id>/discovery/v2.0/keys'
export DPMCP_OIDC_AUDIENCE='api://<application-client-id>'
export DPMCP_OIDC_ROLE_CLAIM='roles'
export DPMCP_OIDC_TENANT_CLAIM='tid'
export DPMCP_OIDC_CLIENT_ID_CLAIM='azp'
export DPMCP_OIDC_ROLE_MAP_JSON='{
  "DataPlatform.Reader":"reader",
  "DataPlatform.Analyst":"analyst",
  "DataPlatform.Operator":"operator",
  "DataPlatform.Admin":"admin"
}'
```

Define Entra App Roles and assign users/service principals to those roles rather than treating arbitrary token scopes as server roles.

## Multi-tenancy

Enable tenant source isolation:

```bash
export DPMCP_TENANT_ENABLED=true
export DPMCP_TENANT_ALLOWED_SOURCES_JSON='{
  "tenant-a":["postgres"],
  "tenant-b":["vertica"],
  "platform-admin":["*"]
}'
```

Then:

```text
tenant-a + analyst
  -> PostgreSQL metadata/lineage/EXPLAIN allowed
  -> Vertica denied

tenant-b + operator
  -> Vertica allowed
  -> PostgreSQL denied
```

Role controls **what operation** is permitted. Tenant policy controls **which data source** is reachable.

## Static tokens

Static tokens remain available for local demos and integration testing:

```bash
DPMCP_AUTH_MODE=static
DPMCP_API_TOKENS_JSON='{
  "replace-me":{"client_id":"demo-agent","role":"reader","tenant":"tenant-a"}
}'
```

Do not use committed static secrets for production.
