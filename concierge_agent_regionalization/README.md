# Product Concierge B2B Agent

## Overview
The **Product Concierge B2B** is an intelligent agent specialized in providing personalized product recommendations for B2B customers, utilizing intelligent search with regionalization and specific segmentation.

## Objective
Assist B2B users in product discovery and consultation, offering detailed information about prices, technical specifications, and variations, always considering regional and organizational segmentation settings.

## Key Features
- ✅ Intelligent product search by name
- ✅ B2B segmentation application
- ✅ Product and price regionalization
- ✅ Related product suggestions
- ✅ Detailed information (prices, specifications, variations)
- ✅ Automatic extraction of SKU IDs and Seller IDs

## User Journey

### 1. Product Request
**User:** "I need to find Nescau chocolate powder"

**Agent:** Collects additional information such as:
- Desired size
- Specific brand
- Color or style (if applicable)
- Other preferences

### 2. Intelligent Search
**Internal Process:**
- Agent requests `vtex_segment` from manager
- Executes search using `search_product` tool
- Applies automatic regionalization
- Filters results by B2B segmentation

### 3. Results Presentation
**Return to User:**
```
🔍 I found the following products:

📦 Nescau Chocolate Powder 800g Free 100g
   💰 Price: $10.00
   🏢 Brand: Nescau
   📋 SKU ID: 797
   🏪 Seller ID: 1
   📝 Description: Nescau® 2.0 is the Nestlé® chocolate drink that everyone loves...
```

### 4. Related Suggestions
**Agent:** Always suggests related products after finding the requested item:
- "You might also be interested in coffee, sugar, or powdered milk"
- Presents complementary products from the same category

### 5. Information for Manager
**Data Forwarded:**
- SKU ID of all found products
- Seller ID of each product
- Segmentation information used

## Tools Used

### search_product
- **Function:** Search products in VTEX Intelligent Search
- **Input:** List of product names + vtex_segment
- **Output:** Detailed list of products with prices and specifications

## Required Configurations

### Credentials
- **BASE_URL**: VTEX store URL (ex: `https://pamplonase.myvtex.com`)
- **STORE_URL**: Final store URL (ex: `https://weni.com.br`)

### Manager Parameters
- **vtex_segment**: B2B segmentation token (required for all searches)

## Typical Use Cases

### 1. Simple Search
```
User: "I want coffee"
Agent: Searches coffee products → Returns options with regionalized prices
```

### 2. Specific Search
```
User: "I need Pilão brand coffee, 500g size"
Agent: Searches with specific filters → Returns exact products
```

### 3. Product Not Found
```
User: "I want a very specific product"
Agent: "I didn't find that product. Would you like to search for another type?"
```

### 4. Detailed Information
```
User: "Give me more details about this product"
Agent: Provides technical specifications, available variations, prices
```

## Advanced Features

### Regionalization
- Region-adjusted prices
- Regional product availability
- Specific delivery configurations

### B2B Segmentation
- Differentiated corporate prices
- B2B-exclusive products
- Personalized price tables

### Search Intelligence
- Semantic similarity search
- Automatic product suggestions
- Automatic term correction

## Limitations
- Requires `vtex_segment` to function correctly
- Dependent on VTEX Intelligent Search configuration
- Limited to products registered in the platform

## Data Flow
```
User → Agent → Manager (vtex_segment) → VTEX API → Processing → User
                ↓
            Manager (SKU IDs + Seller IDs)
```

## Performance Metrics
- Search response time
- Result relevance
- Suggestion conversion rate
- User satisfaction with recommendations

## Integration with Other Agents
- **Organizations Agent**: To obtain organizational configurations
- **User Authentication**: For authenticated sessions
- **Checkout Agents**: For order completion

## Best Practices
1. **Always** request vtex_segment before search
2. **Always** forward SKU IDs to manager
3. **Always** suggest related products
4. **Always** be polite and helpful
5. **Never** invent unavailable information

## Error Handling
- Search without results: Suggests alternative search
- API error: Informs temporary problem
- Invalid segment: Requests new token from manager