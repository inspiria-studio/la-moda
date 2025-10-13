# Compartilhamento de Tokens VTEX - Sistema La Moda

## 🔑 **Visão Geral**

O sistema utiliza dois tokens principais para autenticação e segmentação: **`vtex_session`** e **`vtex_segment`**. Estes tokens são gerados pelo **Organizations Agent** e compartilhados com os outros agentes através do **Manager**.

---

## 📋 **Tipos de Tokens**

### **1. vtex_session (Session Token)**
- **Propósito**: Token de sessão JWT que identifica o usuário autenticado
- **Conteúdo**: Informações de sessão, expiração, usuário ID
- **Uso**: Autenticação em operações que requerem identificação do usuário

### **2. vtex_segment (Segment Token)**
- **Propósito**: Token de segmentação B2B que contém informações comerciais
- **Conteúdo**: Organização, centro de custo, tabela de preços, canal de venda
- **Uso**: Aplicação de regras comerciais específicas (preços, produtos, regionalização)

---

## 🔄 **Fluxo de Compartilhamento**

### **FASE 1: Geração dos Tokens (Organizations Agent)**

```
1. Usuário solicita autenticação
   ↓
2. Organizations Agent → send_token (email)
   ↓
3. Usuário fornece token recebido
   ↓
4. Organizations Agent → validate_token
   ↓
5. Organizations Agent → select_organization
   ↓
6. GERAÇÃO DOS TOKENS:
   - sessionToken (vtex_session)
   - segmentToken (vtex_segment)
```

### **FASE 2: Compartilhamento via Manager**

```
Organizations Agent
    ↓ (retorna para manager)
Manager (armazena tokens)
    ↓ (compartilha quando solicitado)
Product Concierge B2B ← vtex_segment
    ↓ (retorna para manager)
Manager (armazena SKU IDs)
    ↓ (compartilha quando solicitado)
Checkout Agent ← vtex_session + vtex_segment
```

---

## 🎯 **Como Cada Agente Usa os Tokens**

### **1. Organizations Agent**
#### **Gera os Tokens:**
- **Input**: Dados de autenticação + organização selecionada
- **Process**: Cria sessão via API `/api/sessions`
- **Output**: `sessionToken` e `segmentToken`

```python
# Método create_session_token
def create_session_token(self, ...):
    json_data = {
        "public": {
            "authCookie": {"value": auth_cookie_value},
            "storefront-permissions": {
                "organization": {"value": organization_id},
                "costcenter": {"value": cost_center_id},
                "priceTables": {"value": price_table_id},
                "userId": {"value": user_id}
            }
        }
    }
    # Retorna: {"sessionToken": "...", "segmentToken": "..."}
```

#### **Instruções:**
- **"SEMPRE após o usuário selecionar a organização, VOCÊ DEVE retornar o vtex_segment e vtex_session para o usuário"**

---

### **2. Product Concierge B2B**
#### **Solicita vtex_segment:**
- **Input**: Nome do produto + `vtex_segment` (do manager)
- **Process**: Usa token no header Cookie para busca regionalizada
- **Output**: Produtos com preços e informações específicas da organização

```python
# Método intelligentSearch
def intelligentSearch(self, product_name, url, store_url, vtex_segment):
    headers = {
        "Cookie": f"vtex_segment={vtex_segment}"
    }
    # Busca produtos com segmentação B2B aplicada
```

#### **Instruções:**
- **"Always ask the manager for the vtex_segment"**
- **"After every product search, always send both the sku_id and sellerId to the manager"**

---

### **3. Checkout Agent**
#### **Usa Ambos os Tokens:**
- **Input**: Produtos + `vtex_session` + `vtex_segment` (do manager)
- **Process**: Cria carrinho com autenticação e segmentação
- **Output**: Carrinho criado com checkout_url

```python
# Método execute
def execute(self, context: Context):
    vtex_session = context.parameters.get("vtex_session", "")
    vtex_segment = context.parameters.get("vtex_segment", "")
    
    # Usa vtex_session para autenticação
    session_information = self.get_session_information(base_url, vtex_session)
    
    # Usa vtex_segment para segmentação
    self._add_items(..., vtex_session, vtex_segment)
```

#### **Instruções:**
- **"SEMPRE pergunte para o manager o VTEX_Session, Vtex_segment"**
- **"ALWAYS you receive checkout_url of tool create_cart, ALWAYS SEND THE CHECKOUT_URL TO MANAGER"**

---

## 🔄 **Fluxo Detalhado de Compartilhamento**

### **Passo 1: Organizações Agent Gera Tokens**
```yaml
Organizations Agent:
  - Recebe: email, token, organização, price_table
  - Processa: create_session_token()
  - Retorna para Manager:
    - sessionToken: "eyJhbGciOiJFUzI1NiIs..."
    - segmentToken: "eyJjYW1wYWlnbnMiOm51bGws..."
```

### **Passo 2: Manager Armazena e Compartilha**
```yaml
Manager:
  - Armazena: sessionToken, segmentToken
  - Aguarda solicitações dos outros agentes
  - Compartilha quando solicitado
```

### **Passo 3: Product Concierge Solicita vtex_segment**
```yaml
Product Concierge → Manager: "Preciso do vtex_segment"
Manager → Product Concierge: segmentToken
Product Concierge → VTEX API: Busca com segmentação
Product Concierge → Manager: sku_ids, seller_ids
```

### **Passo 4: Checkout Agent Solicita Ambos**
```yaml
Checkout Agent → Manager: "Preciso do vtex_session e vtex_segment"
Manager → Checkout Agent: sessionToken, segmentToken
Checkout Agent → VTEX API: Cria carrinho autenticado
Checkout Agent → Manager: orderform_id, checkout_url
```

---

## 📊 **Estrutura dos Tokens**

### **vtex_session (JWT)**
```json
{
  "header": {"alg": "ES256", "typ": "JWT"},
  "payload": {
    "account.id": [],
    "id": "8bd482fd-3ca8-4777-b7d2-a5c3d8f05a78",
    "version": 2,
    "sub": "session",
    "account": "session",
    "exp": 1756557418,
    "iat": 1755866218,
    "jti": "076876bb-f66c-44a8-9b57-df38e7f80863",
    "iss": "session/data-signer"
  }
}
```

### **vtex_segment (JWT)**
```json
{
  "payload": {
    "campaigns": null,
    "channel": "1",
    "priceTables": "pamplona-fidelidade",
    "regionId": null,
    "utm_campaign": null,
    "utm_source": null,
    "utm_campaign": null,
    "currencyCode": "BRL",
    "currencySymbol": "R$",
    "countryCode": "BRA",
    "cultureInfo": "pt-BR",
    "admin_cultureInfo": "pt-BR",
    "channelPrivacy": "public",
    "facets": "accesscontrollist=befeecfa4-db16-11ee-8452-0affc1c2d6e9;"
  }
}
```

---

## 🔒 **Segurança e Boas Práticas**

### **Regras de Segurança:**
1. **NUNCA** armazenar tokens em logs ou saídas visíveis
2. **SEMPRE** validar tokens antes de usar
3. **SEMPRE** solicitar tokens ao manager, nunca assumir valores
4. **SEMPRE** retornar dados estruturados para o manager

### **Fluxo de Validação:**
```
1. Agent solicita token ao Manager
2. Manager valida se token existe e é válido
3. Manager retorna token para Agent
4. Agent usa token em operação VTEX
5. Agent retorna resultado para Manager
```

---

## ⚠️ **Tratamento de Erros**

### **Token Inválido:**
```yaml
Erro: "Token inválido ou expirado"
Ação: Solicitar novo token ao Manager
Fallback: Redirecionar para Organizations Agent
```

### **Token Ausente:**
```yaml
Erro: "Token não fornecido"
Ação: Solicitar token ao Manager
Fallback: Não prosseguir com operação
```

### **Token Expirado:**
```yaml
Erro: "Sessão expirada"
Ação: Solicitar renovação de token
Fallback: Redirecionar para reautenticação
```

---

## 📈 **Monitoramento**

### **Métricas Importantes:**
- **Taxa de sucesso** na geração de tokens
- **Tempo de vida** dos tokens
- **Taxa de erro** por token inválido
- **Frequência de renovação** de tokens

### **Logs Essenciais:**
- Geração de tokens (sem expor conteúdo)
- Solicitações de tokens entre agentes
- Erros de validação de tokens
- Tempo de resposta das operações com tokens

---

## 🎯 **Resumo do Compartilhamento**

1. **Organizations Agent** → Gera e retorna tokens para Manager
2. **Manager** → Armazena e distribui tokens conforme solicitado
3. **Product Concierge** → Solicita `vtex_segment` para busca regionalizada
4. **Checkout Agent** → Solicita ambos os tokens para operações autenticadas
5. **Todos os Agentes** → Retornam dados estruturados para Manager

Este sistema garante que cada agente tenha acesso apenas aos tokens necessários para suas operações específicas, mantendo a segurança e a segmentação adequada do sistema B2B.

