# Organizations Agent

## Overview
The **Organizations Agent** is responsible for assisting B2B users in selecting and configuring organizations for making purchases, managing the organizational choice process and commercial parameter configuration.

## Objective
Facilitate the user's decision about which organization to use for their purchases, providing detailed information about available organizations, roles, cost centers, and price tables.

## Key Features
- ✅ User organization listing
- ✅ Detailed role and permission information
- ✅ Cost center configuration
- ✅ Price table selection
- ✅ Organizational data management
- ✅ Purchase process preparation

## User Journey

### 1. Purchase Process Initiation
**User:** "I want to make a purchase"

**Agent:** "To proceed with your purchase, I need to know which organization you want to use. I'll search for your available organizations."

### 2. Email Request
**Agent:** Requests user email from manager to search organizations

### 3. Organization Search
**Internal Process:**
- Executes `get_organizations` with provided email
- Obtains complete list of user organizations
- Extracts role and permission information

### 4. Organization Presentation
**Return to User:**
```
🏢 Your available organizations:

1. 📋 Leo's Market
   🆔 ID: 0bc8734c-68cf-11f0-b37f-d6298c939021
   👤 Role: Sales Representative
   🏪 Cost Center: Maceio
   📊 Status: Active

2. 📋 Boni Supermarkets
   🆔 ID: 84d56f1b-db18-11ee-8452-0affc1c2d6e9
   👤 Role: Sales Admin
   🏪 Cost Center: Curitiba
   📊 Status: Active

Which organization would you like to use?
```

### 5. Organization Selection
**User:** "I want to use Leo's Market organization"

**Internal Process:**
- Executes `select_organization` with organization ID
- Obtains detailed organization configurations

### 6. Detailed Organizational Information
**Return to User:**
```
✅ Selected organization: Leo's Market

📋 Your information:
   👤 User ID: 2b0da4c8-695c-11f0-b37f-eccc49142a1c
   🏪 Cost Center ID: 261e955b-68cf-11f0-b37f-c4c78f24e134
   🏢 Organization ID: 0bc8734c-68cf-11f0-b37f-d6298c939021
   🛒 Sales Channel: 2
   📊 Price Tables: ["pamplona-fidelidade", "default"]

Which price table would you like to use?
```

### 7. Final Configuration
**User:** Selects price table

**Agent:** Confirms configuration and forwards all data to manager

## Tools Used

### get_organizations
- **Function:** Search organizations by user email
- **Input:** User email
- **Output:** List of organizations with roles and permissions

### select_organization
- **Function:** Obtain specific organization details
- **Input:** Organization ID
- **Output:** Detailed configurations (channels, price tables, etc.)

## Required Configurations

### Credentials
- **BASE_URL**: VTEX store URL (ex: `https://weni.vtexcommercestable.com.br`)
- **VTEX_APP_KEY**: VTEX application key (confidential)
- **VTEX_APP_TOKEN**: VTEX application token (confidential)

### Manager Parameters
- **User email**: Required to search organizations

## Typical Use Cases

### 1. User with Multiple Organizations
```
Scenario: User belongs to several companies
Process: List all → User chooses → Configure parameters
```

### 2. User with One Organization
```
Scenario: User has only one organization
Process: Show organization → Confirm → Configure automatically
```

### 3. User with Different Roles
```
Scenario: User has different roles in organizations
Process: Show specific role for each organization
```

### 4. Price Table Configuration
```
Scenario: Organization has multiple tables
Process: List options → User chooses → Apply configuration
```

## Data Forwarded to Manager

### After get_organizations:
- Complete list of organizations
- ID and name of each organization
- User role name for each organization

### After select_organization:
- **userId**: User ID in organization
- **costId**: Cost center ID
- **orgId**: Organization ID
- **salesChannel**: Sales channel
- **priceTables**: Available price tables
- **collectionId**: Collection ID (if exists)

## Data Flow
```
Manager (email) → get_organizations → Org List → User
                                          ↓
User (choice) → select_organization → Detailed Data → Manager
                                          ↓
                                    Price Table Configuration
```

## Integration with Other Agents

### User Authentication Agent
- Receives organizational data for session creation
- Uses orgId, costId to configure B2B session

### Product Concierge Agent
- Uses organizational configurations for search
- Applies specific price tables

### Checkout Agents
- Uses organizational data for processing
- Applies specific commercial rules

## Organization States
- **active**: Active and available organization
- **inactive**: Inactive organization (not listed)

## Common Role Types
- **sales-representative**: Sales representative
- **sales-admin**: Sales administrator
- **buyer**: Buyer
- **approver**: Order approver

## Error Handling

### No Organizations Found
```
"I didn't find organizations for this email. 
Check if the email is correct or contact support."
```

### API Error
```
"Temporary error searching organizations. 
Try again in a few moments."
```

### Invalid Organization
```
"Organization not found or inactive. 
Select a valid organization from the list."
```

## Advanced Configurations

### Multiple Cost Centers
- User can have access to several centers
- System allows specific selection

### Dynamic Price Tables
- Prices can vary by organization
- Automatic configuration based on selection

### Specific Sales Channels
- Each organization can have its own channel
- Affects product availability

## Best Practices
1. **Always** request email from manager
2. **Always** show user role
3. **Always** confirm selection before proceeding
4. **Always** ask about price table
5. **Never** assume configurations without confirmation

## Security and Permissions
- User only sees organizations they have access to
- Roles determine specific permissions
- Organizational data is protected by authentication