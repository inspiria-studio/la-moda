# Documentação dos Agentes - Sistema La Moda

## Visão Geral

Este documento apresenta uma análise detalhada dos três agentes principais do sistema La Moda: **Checkout Agent**, **Product Concierge B2B** e **Organizations Agent**. Cada agente possui funções específicas e trabalham em conjunto para fornecer uma experiência completa de compra B2B.

---

## 1. Checkout Agent (Agente de Finalização de Compra)

### 🎯 **Objetivo Principal**
Responsável por processar informações de pagamento e finalização de pedidos, criando carrinhos de compra e gerando links de checkout para os clientes.

### 🔧 **Funcionalidades Principais**

#### **Criação de Carrinho**
- Recebe informações de produtos no formato específico
- Cria carrinhos de compra personalizados
- Gera links de checkout únicos
- Gerencia `orderform_id` para rastreamento

#### **Gestão de Sessão**
- Requer tokens de sessão VTEX (`vtex_session`)
- Requer tokens de segmentação (`vtex_segment`)
- Mantém consistência entre operações

#### **Informações do Carrinho**
- Consulta detalhes de carrinhos existentes
- Fornece informações atualizadas sobre itens
- Suporte a dúvidas dos usuários sobre produtos no carrinho

### 🛠 **Ferramentas Disponíveis**

#### **create_cart**
- **Parâmetros:**
  - `product_items`: Array de produtos com ID, quantidade, preço e moeda
  - `orderform_id`: ID do formulário de pedido (opcional)
  - `vtex_session`: Token de sessão VTEX (obrigatório)
  - `vtex_segment`: Token de segmentação VTEX (obrigatório)

#### **get_cart_info**
- **Parâmetros:**
  - `orderform_id`: ID do formulário de pedido (obrigatório)

### 📋 **Regras de Negócio**
- **NUNCA** informa métodos de pagamento disponíveis
- **SEMPRE** envia `checkout_url` e `order_form_id` para o manager
- **SEMPRE** solicita tokens de sessão ao manager
- Não cria novos `orderform_id` se já existir um ativo
- Considera retornos como carrinhos criados, não pedidos finalizados

### 🔄 **Fluxo de Trabalho**
```
Produtos Recebidos → Validação de Tokens → Criação de Carrinho → 
Geração de Link → Envio para Manager → Consultas de Informação
```

---

## 2. Product Concierge B2B (Agente de Recomendação de Produtos)

### 🎯 **Objetivo Principal**
Especializado em oferecer recomendações personalizadas de produtos para clientes B2B, utilizando busca inteligente com regionalização e segmentação específica.

### 🔧 **Funcionalidades Principais**

#### **Busca Inteligente**
- Busca por nome de produtos
- Aplicação de segmentação B2B
- Regionalização de preços e produtos
- Sugestões de produtos relacionados

#### **Coleta de Informações**
- Extrai detalhes como tamanho, cor, estilo, marca
- Fornece informações técnicas detalhadas
- Apresenta variações disponíveis

#### **Recomendações Personalizadas**
- Sugere produtos complementares
- Considera preferências do usuário
- Aplica tabelas de preços específicas

### 🛠 **Ferramentas Disponíveis**

#### **search_product**
- **Parâmetros:**
  - `product_names`: Array de nomes de produtos
  - `vtex_segment`: Token de segmentação (obrigatório)

### 📋 **Regras de Negócio**
- **SEMPRE** solicita `vtex_segment` ao manager antes de buscar
- **SEMPRE** envia `sku_id` e `sellerId` para o manager
- **SEMPRE** sugere produtos relacionados após encontrar o solicitado
- **NUNCA** inventa informações indisponíveis
- **SEMPRE** é educado e prestativo

### 🔄 **Fluxo de Trabalho**
```
Solicitação do Usuário → Coleta de Detalhes → Solicitação de Token → 
Busca de Produtos → Regionalização → Apresentação de Resultados → 
Sugestões Relacionadas → Envio de IDs para Manager
```

### 🎨 **Exemplo de Interação**
```
Usuário: "Preciso encontrar Nescau em pó"
Agente: Coleta informações (tamanho, marca, etc.)
Agente: Busca produtos com regionalização
Agente: Apresenta resultados com preços regionalizados
Agente: Sugere produtos relacionados (café, açúcar, leite em pó)
Agente: Envia SKU IDs e Seller IDs para o manager
```

---

## 3. Organizations Agent (Agente de Organizações)

### 🎯 **Objetivo Principal**
Responsável por autenticar usuários e ajudá-los na seleção de organizações para realizar compras, gerenciando todo o fluxo desde a autenticação até a criação de sessão.

### 🔧 **Funcionalidades Principais**

#### **Autenticação por Email**
- Envio de tokens de autenticação via email
- Validação de tokens recebidos
- Gestão segura de credenciais

#### **Gestão de Organizações**
- Listagem de organizações disponíveis
- Detalhamento de roles e permissões
- Configuração de centros de custo
- Seleção de tabelas de preços

#### **Criação de Sessão**
- Combinação de seleção organizacional com criação de sessão
- Geração de tokens de sessão e segmentação
- Configuração de parâmetros comerciais

### 🛠 **Ferramentas Disponíveis**

#### **send_token**
- **Parâmetros:**
  - `email`: Endereço de email do usuário

#### **validate_token**
- **Parâmetros:**
  - `email`: Endereço de email do usuário
  - `auth_token`: Token de autenticação retornado
  - `user_token`: Token recebido pelo usuário

#### **select_organization**
- **Parâmetros:**
  - `organization_id`: ID da organização selecionada
  - `cost_center_id`: ID do centro de custo
  - `auth_cookie_name/value`: Cookies de autenticação
  - `account_auth_cookie_name/value`: Cookies da conta
  - `price_table_id`: ID da tabela de preços escolhida

### 📋 **Fluxo de Autenticação**

#### **PASSO 1 - Autenticação por Email**
1. Solicita email do usuário
2. Envia token via `send_token`
3. Informa ao usuário para verificar email

#### **PASSO 2 - Validação e Obtenção de Organizações**
1. Usuário fornece token recebido
2. Valida token com `validate_token`
3. Extrai dados de autenticação
4. Obtém lista de organizações automaticamente
5. Apresenta todas as organizações com detalhes

#### **PASSO 3 - Seleção e Criação de Sessão**
1. Usuário escolhe organização e tabela de preços
2. Executa `select_organization` com todos os parâmetros
3. Retorna dados completos da sessão

### 🔄 **Fluxo Completo**
```
Solicitação de Email → Envio de Token → Validação → 
Listagem de Organizações → Seleção → Criação de Sessão → 
Retorno de Tokens para Manager
```

### 🎨 **Exemplo de Interação**
```
Usuário: "Quero fazer uma compra"
Agente: "Para prosseguir, preciso do seu email"
Usuário: "usuario@empresa.com"
Agente: Envia token e solicita verificação de email
Usuário: "Recebi o token: 123456"
Agente: Valida token e apresenta organizações:
        - Leo's Market (Sales Representative)
        - Boni Supermarkets (Sales Admin)
Usuário: "Escolho Leo's Market"
Agente: "Qual tabela de preços deseja usar?"
Usuário: "pamplona-fidelidade"
Agente: Cria sessão e retorna tokens para manager
```

---

## 🔗 **Integração Entre Agentes**

### **Fluxo Completo do Sistema**
```
1. Organizations Agent → Autentica e seleciona organização
2. Product Concierge → Busca produtos com segmentação
3. Checkout Agent → Finaliza compra com carrinho
```

### **Dados Compartilhados**
- **vtex_session**: Token de sessão VTEX
- **vtex_segment**: Token de segmentação
- **sku_id**: Identificadores de produtos
- **sellerId**: IDs dos vendedores
- **orderform_id**: IDs dos formulários de pedido

### **Dependências**
- Organizations Agent fornece tokens para outros agentes
- Product Concierge fornece IDs de produtos para Checkout
- Checkout Agent finaliza o processo com carrinho criado

---

## 🛡️ **Segurança e Boas Práticas**

### **Medidas de Segurança**
- Tokens de autenticação via email
- Validação rigorosa de credenciais
- Proteção de informações sensíveis
- Controle de acesso baseado em roles

### **Boas Práticas Gerais**
- **SEMPRE** solicitar tokens necessários ao manager
- **SEMPRE** retornar dados estruturados
- **NUNCA** inventar informações indisponíveis
- **SEMPRE** manter interações educadas e profissionais
- **SEMPRE** seguir o fluxo sequencial estabelecido

### **Tratamento de Erros**
- Falhas de autenticação: Oferecer reenvio de token
- Produtos não encontrados: Sugerir alternativas
- Erros de API: Informar problemas temporários
- Dados inválidos: Solicitar informações corretas

---

## 📊 **Métricas e Monitoramento**

### **Checkout Agent**
- Taxa de criação de carrinhos
- Tempo de geração de links
- Taxa de conversão de checkout

### **Product Concierge B2B**
- Tempo de resposta de busca
- Relevância dos resultados
- Taxa de conversão de sugestões

### **Organizations Agent**
- Taxa de sucesso de autenticação
- Tempo de processamento de tokens
- Satisfação na seleção de organizações

---

Este sistema de agentes trabalha de forma integrada para proporcionar uma experiência completa e segura de compra B2B, desde a autenticação até a finalização do pedido, sempre considerando segmentação, regionalização e personalização para cada usuário e organização.

