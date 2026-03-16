# Comandos cURL para APIs do Organizations Agent

Este documento contém todos os comandos cURL para as APIs utilizadas no Organizations Agent.

## Variáveis de Ambiente

Antes de executar os comandos, defina as seguintes variáveis:

```bash
BASE_URL="https://weni.vtexcommercestable.com.br"
ACCOUNT_NAME="weni"
LOCALE="pt-BR"
VTEX_APP_KEY="vtexappkey-weni-VKJIJA"
VTEX_APP_TOKEN="MDYNKIKTIMMVTBS"
EMAIL="usuario@exemplo.com"
PASSWORD="senha123"
```

---

## 1. Authentication Tool

### 1.1. Obter Token de Autenticação

**Endpoint:** `GET /api/vtexid/pub/authentication/start`

**Descrição:** Obtém o token de autenticação necessário para validar credenciais.

```bash
curl -X GET \
  "${BASE_URL}/api/vtexid/pub/authentication/start?scope=${ACCOUNT_NAME}&locale=${LOCALE}" \
  -H "Accept: application/json"
```

**Resposta esperada:**
```json
{
  "authenticationToken": "token_aqui"
}
```

### 1.2. Enviar Access Key (Comentado no código)

**Endpoint:** `POST /api/vtexid/pub/authentication/accesskey/send`

**Descrição:** Envia access key usando o token de autenticação (método comentado no código).

```bash
curl -X POST \
  "${BASE_URL}/api/vtexid/pub/authentication/accesskey/send" \
  -H "Accept: application/json" \
  -F "authenticationToken=${AUTH_TOKEN}" \
  -F "email=${EMAIL}"
```

---

## 2. Validate Credentials Tool

### 2.1. Validar Credenciais do Usuário

**Endpoint:** `POST /api/vtexid/pub/authentication/classic/validate`

**Descrição:** Valida as credenciais (email e senha) do usuário usando o token de autenticação.

```bash
curl -X POST \
  "${BASE_URL}/api/vtexid/pub/authentication/classic/validate" \
  -H "Accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=${EMAIL}" \
  -d "password=${PASSWORD}" \
  -d "authenticationToken=${AUTH_TOKEN}"
```

**Resposta esperada:**
```json
{
  "authCookie": {
    "name": "VtexIdclientAutCookie",
    "value": "cookie_value_aqui"
  },
  "accountAuthCookie": {
    "name": "VtexIdclientAutCookie_ACCOUNT",
    "value": "account_cookie_value_aqui"
  },
  "userId": "user_id_aqui"
}
```

### 2.2. Buscar Organizações por Email (GraphQL)

**Endpoint:** `POST /_v/private/graphql/v1`

**Descrição:** Busca todas as organizações associadas a um email específico.

```bash
curl -X POST \
  "${BASE_URL}/_v/private/graphql/v1" \
  -H "Content-Type: application/json" \
  -H "Vtex-api-appkey: ${VTEX_APP_KEY}" \
  -H "Vtex-api-apptoken: ${VTEX_APP_TOKEN}" \
  -d '{
    "query": "query getOrganizationsByEmail($email: String!) { getOrganizationsByEmail(email: $email) @context(provider: \"vtex.b2b-organizations-graphql@0.x\") { id clId costId orgId roleId role { id name slug } organizationName organizationStatus costCenterName } }",
    "variables": {
      "email": "'${EMAIL}'"
    }
  }'
```

**Resposta esperada:**
```json
{
  "data": {
    "getOrganizationsByEmail": [
      {
        "id": "user_org_id",
        "clId": "client_id",
        "costId": "cost_center_id",
        "orgId": "organization_id",
        "roleId": "role_id",
        "role": {
          "id": "role_id",
          "name": "Sales Representative",
          "slug": "sales-representative"
        },
        "organizationName": "Nome da Organização",
        "organizationStatus": "active",
        "costCenterName": "Nome do Cost Center"
      }
    ]
  }
}
```

### 2.3. Buscar Price Tables de uma Organização (GraphQL)

**Endpoint:** `POST /api/io/_v/public/graphql/v1`

**Descrição:** Busca as price tables disponíveis para uma organização específica.

```bash
ORGANIZATION_ID="organization_id_aqui"

curl -X POST \
  "${BASE_URL}/api/io/_v/public/graphql/v1" \
  -H "VTEX-API-AppKey: ${VTEX_APP_KEY}" \
  -H "VTEX-API-AppToken: ${VTEX_APP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetOrganizationById($id: ID) { getOrganizationById(id: $id) @context(provider: \"vtex.b2b-organizations-graphql\") { priceTables } }",
    "variables": {
      "id": "'${ORGANIZATION_ID}'"
    }
  }'
```

**Resposta esperada:**
```json
{
  "data": {
    "getOrganizationById": {
      "priceTables": ["pamplona-fidelidade", "default"]
    }
  }
}
```

---

## 3. Select Organization Tool

### 3.1. Buscar Detalhes da Organização por ID (GraphQL)

**Endpoint:** `POST /api/io/_v/public/graphql/v1`

**Descrição:** Obtém detalhes completos de uma organização específica, incluindo collections, price tables, sales channel e cost centers.

```bash
ORGANIZATION_ID="organization_id_aqui"

curl -X POST \
  "${BASE_URL}/api/io/_v/public/graphql/v1" \
  -H "VTEX-API-AppKey: ${VTEX_APP_KEY}" \
  -H "VTEX-API-AppToken: ${VTEX_APP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query GetOrganizationById($id: ID) { getOrganizationById(id: $id) @context(provider: \"vtex.b2b-organizations-graphql\") { id name status collections { id name } priceTables salesChannel costCenters } }",
    "variables": {
      "id": "'${ORGANIZATION_ID}'"
    }
  }'
```

**Resposta esperada:**
```json
{
  "data": {
    "getOrganizationById": {
      "id": "organization_id",
      "name": "Nome da Organização",
      "status": "active",
      "collections": [
        {
          "id": "collection_id",
          "name": "Nome da Collection"
        }
      ],
      "priceTables": ["pamplona-fidelidade", "default"],
      "salesChannel": "2",
      "costCenters": ["cost_center_id_1", "cost_center_id_2"]
    }
  }
}
```

### 3.2. Criar Sessão

**Endpoint:** `POST /api/sessions`

**Descrição:** Cria uma sessão para o usuário com os dados da organização selecionada, incluindo cookies de autenticação, organização, cost center, price table e user ID.

```bash
AUTH_COOKIE_NAME="VtexIdclientAutCookie"
AUTH_COOKIE_VALUE="auth_cookie_value_aqui"
ACCOUNT_AUTH_COOKIE_NAME="VtexIdclientAutCookie_ACCOUNT"
ACCOUNT_AUTH_COOKIE_VALUE="account_auth_cookie_value_aqui"
COST_CENTER_ID="cost_center_id_aqui"
ORGANIZATION_ID="organization_id_aqui"
PRICE_TABLE_ID="pamplona-fidelidade"
USER_ID="user_id_aqui"

curl -X POST \
  "${BASE_URL}/api/sessions" \
  -H "Accept: application/json" \
  -H "Cookie: ${AUTH_COOKIE_NAME}=${AUTH_COOKIE_VALUE};${ACCOUNT_AUTH_COOKIE_NAME}=${ACCOUNT_AUTH_COOKIE_VALUE}" \
  -H "Content-Type: application/json" \
  -d '{
    "public": {
      "authCookie": {
        "value": "'${AUTH_COOKIE_VALUE}'"
      },
      "storefront-permissions": {
        "organization": {
          "value": "'${ORGANIZATION_ID}'"
        },
        "costcenter": {
          "value": "'${COST_CENTER_ID}'"
        },
        "priceTables": {
          "value": "'${PRICE_TABLE_ID}'"
        },
        "userId": {
          "value": "'${USER_ID}'"
        }
      }
    }
  }'
```

**Resposta esperada:**
```json
{
  "sessionToken": "session_token_aqui",
  "segmentToken": "segment_token_aqui"
}
```

---

## Fluxo Completo de Exemplo

Aqui está um exemplo de como executar o fluxo completo:

```bash
# 1. Obter token de autenticação
AUTH_TOKEN=$(curl -s -X GET \
  "${BASE_URL}/api/vtexid/pub/authentication/start?scope=${ACCOUNT_NAME}&locale=${LOCALE}" \
  -H "Accept: application/json" | jq -r '.authenticationToken')

# 2. Validar credenciais
AUTH_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/api/vtexid/pub/authentication/classic/validate" \
  -H "Accept: application/json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=${EMAIL}" \
  -d "password=${PASSWORD}" \
  -d "authenticationToken=${AUTH_TOKEN}")

# Extrair cookies e user ID
AUTH_COOKIE_NAME=$(echo $AUTH_RESPONSE | jq -r '.authCookie.name')
AUTH_COOKIE_VALUE=$(echo $AUTH_RESPONSE | jq -r '.authCookie.value')
ACCOUNT_AUTH_COOKIE_NAME=$(echo $AUTH_RESPONSE | jq -r '.accountAuthCookie.name')
ACCOUNT_AUTH_COOKIE_VALUE=$(echo $AUTH_RESPONSE | jq -r '.accountAuthCookie.value')
USER_ID=$(echo $AUTH_RESPONSE | jq -r '.userId')

# 3. Buscar organizações
ORGS_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/_v/private/graphql/v1" \
  -H "Content-Type: application/json" \
  -H "Vtex-api-appkey: ${VTEX_APP_KEY}" \
  -H "Vtex-api-apptoken: ${VTEX_APP_TOKEN}" \
  -d "{\"query\": \"query getOrganizationsByEmail(\$email: String!) { getOrganizationsByEmail(email: \$email) @context(provider: \\\"vtex.b2b-organizations-graphql@0.x\\\") { id clId costId orgId roleId role { id name slug } organizationName organizationStatus costCenterName } }\", \"variables\": {\"email\": \"${EMAIL}\"}}")

# Extrair primeira organização (exemplo)
ORGANIZATION_ID=$(echo $ORGS_RESPONSE | jq -r '.data.getOrganizationsByEmail[0].orgId')
COST_CENTER_ID=$(echo $ORGS_RESPONSE | jq -r '.data.getOrganizationsByEmail[0].costId')

# 4. Buscar price tables da organização
PRICE_TABLES_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/api/io/_v/public/graphql/v1" \
  -H "VTEX-API-AppKey: ${VTEX_APP_KEY}" \
  -H "VTEX-API-AppToken: ${VTEX_APP_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"query GetOrganizationById(\$id: ID) { getOrganizationById(id: \$id) @context(provider: \\\"vtex.b2b-organizations-graphql\\\") { priceTables } }\", \"variables\": {\"id\": \"${ORGANIZATION_ID}\"}}")

PRICE_TABLE_ID=$(echo $PRICE_TABLES_RESPONSE | jq -r '.data.getOrganizationById.priceTables[0]')

# 5. Criar sessão
SESSION_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/api/sessions" \
  -H "Accept: application/json" \
  -H "Cookie: ${AUTH_COOKIE_NAME}=${AUTH_COOKIE_VALUE};${ACCOUNT_AUTH_COOKIE_NAME}=${ACCOUNT_AUTH_COOKIE_VALUE}" \
  -H "Content-Type: application/json" \
  -d "{\"public\": {\"authCookie\": {\"value\": \"${AUTH_COOKIE_VALUE}\"}, \"storefront-permissions\": {\"organization\": {\"value\": \"${ORGANIZATION_ID}\"}, \"costcenter\": {\"value\": \"${COST_CENTER_ID}\"}, \"priceTables\": {\"value\": \"${PRICE_TABLE_ID}\"}, \"userId\": {\"value\": \"${USER_ID}\"}}}}")

echo "Session Token: $(echo $SESSION_RESPONSE | jq -r '.sessionToken')"
echo "Segment Token: $(echo $SESSION_RESPONSE | jq -r '.segmentToken')"
```

---

## Notas Importantes

1. **Autenticação**: Todas as requisições GraphQL requerem `VTEX-API-AppKey` e `VTEX-API-AppToken` nos headers.

2. **Cookies**: A criação de sessão requer os cookies de autenticação obtidos na validação de credenciais.

3. **GraphQL**: As queries GraphQL devem ser enviadas como JSON no body da requisição POST.

4. **Account Name**: O `account_name` é extraído automaticamente da `BASE_URL` (ex: `https://weni.vtexcommercestable.com.br` → `weni`).

5. **Price Tables**: As price tables são buscadas automaticamente para cada organização no fluxo de validação de credenciais.


