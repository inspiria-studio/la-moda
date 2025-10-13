# Search Products Tool

## Description
Tool responsible for searching products in VTEX Intelligent Search based on product names provided by the user, applying regionalization and B2B segmentation.

## Functionality
This tool performs intelligent product search using the VTEX Intelligent Search API, enabling:
- Search for multiple products simultaneously
- Application of B2B segmentation (vtex_segment)
- Product regionalization
- Extraction of detailed product information (price, specifications, variations)

## Parameters

### Input
- **product_names** (array, required): List of product names to search for
  - Example: `["nescau", "coffee", "sugar"]`
- **vtex_segment** (string, required): B2B segmentation token provided by the manager
  - Example: `"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`

### Required Credentials
- **BASE_URL**: VTEX store base URL (ex: `https://pamplonase.myvtex.com`)
- **STORE_URL**: Store URL (ex: `https://weni.com.br`)

## Response

The tool returns a list of found products with the following structure:

```json
[
  {
    "sku_id": "797",
    "sku_name": "Nescau Chocolate Powder 800g Free 100g",
    "variations": [],
    "price": 10,
    "description": "Nescau® 2.0 is the Nestlé® chocolate drink that everyone loves...",
    "brand": "Nescau",
    "specification_groups": [
      {
        "name": "allSpecifications",
        "specifications": [
          {
            "name": "sellerId",
            "values": ["1"]
          }
        ]
      }
    ]
  }
]
```

### Response Fields
- **sku_id**: Unique SKU ID in VTEX
- **sku_name**: Complete product/SKU name
- **variations**: Product variations (color, size, etc.)
- **price**: Product price
- **description**: Detailed product description (truncated to 200 characters)
- **brand**: Product brand
- **specification_groups**: Technical specification groups of the product

## Internal Process

1. **Parameter Parsing**: Converts string or array of products into processable list
2. **Intelligent Search**: For each product, makes API call to VTEX
3. **Data Extraction**: Processes API response extracting relevant information
4. **Price Formatting**: Obtains prices from `sellers[0].commertialOffer.Price` structure
5. **Final Structuring**: Organizes data in standardized format for return

## Search URL
```
{BASE_URL}/api/io/_v/api/intelligent-search/product_search/?query={product_name}&simulationBehavior=regionalize1p
```

## Headers Used
- `vtex-segment`: B2B segmentation token
- `Accept`: application/json

## Use Cases
- Product search by name for B2B customers
- Regionalized price consultation
- Technical product specifications retrieval
- Available variations listing

## Limitations
- Returns up to 3 variations per product
- Description limited to 200 characters
- Maximum of 2 specification groups with 2 specifications each

## Debug Logs
The tool generates informative logs about:
- Search URL used
- Number of SKUs found
- Response size in bytes/KB/MB
