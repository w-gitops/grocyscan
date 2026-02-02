# Appendix F: n8n Integration

## F.1 Overview

GrocyScan provides two n8n community nodes:
1. **GrocyScan Node** - Regular node for workflow automation
2. **GrocyScan Tool** - AI Agent tool for intelligent automation

## F.2 Node Package Structure

```
n8n-nodes-grocyscan/
├── package.json
├── credentials/
│   └── GrocyScanApi.credentials.ts
├── nodes/
│   └── GrocyScan/
│       ├── GrocyScan.node.ts       # Regular node
│       ├── GrocyScanTool.node.ts   # AI Agent tool
│       ├── GenericFunctions.ts
│       └── descriptions/
│           ├── ScanDescription.ts
│           ├── ProductDescription.ts
│           └── LocationDescription.ts
└── icons/
    └── grocyscan.svg
```

## F.3 Credentials

```typescript
// credentials/GrocyScanApi.credentials.ts
export class GrocyScanApi implements ICredentialType {
  name = 'grocyScanApi';
  displayName = 'GrocyScan API';
  
  properties: INodeProperties[] = [
    {
      displayName: 'Base URL',
      name: 'baseUrl',
      type: 'string',
      default: 'http://localhost:3334',
    },
    {
      displayName: 'API Key',
      name: 'apiKey',
      type: 'string',
      typeOptions: { password: true },
    },
  ];

  authenticate: IAuthenticateGeneric = {
    type: 'generic',
    properties: {
      headers: { 'X-API-Key': '={{$credentials.apiKey}}' },
    },
  };
}
```

## F.4 Regular Node Operations

### Scan Resource
- **Lookup** - Look up product by barcode
- **Add to Inventory** - Scan and add product
- **Batch Lookup** - Multiple barcodes at once

### Product Resource
- **Get All** - List products
- **Get** - Get by ID
- **Search** - Search by name
- **Create** - Create new product
- **Get Expiring** - Products expiring soon

### Location Resource
- **Get All** - List locations
- **Get** - Get by code
- **Create** - Create location

### Job Resource
- **Get All** - List jobs
- **Retry** - Retry failed job
- **Cancel** - Cancel pending job

## F.5 AI Agent Tool

```typescript
// GrocyScanTool.node.ts
export class GrocyScanTool implements INodeType {
  description: INodeTypeDescription = {
    displayName: 'GrocyScan Tool',
    name: 'grocyScanTool',
    group: ['transform'],
    codex: {
      categories: ['AI'],
      subcategories: { AI: ['Tools'] },
    },
    inputs: [],
    outputs: [NodeConnectionType.AiTool],
    properties: [
      {
        displayName: 'Available Tools',
        name: 'availableTools',
        type: 'multiOptions',
        default: ['lookupBarcode', 'searchProducts', 'getExpiringProducts'],
        options: [
          { name: 'Lookup Barcode', value: 'lookupBarcode' },
          { name: 'Search Products', value: 'searchProducts' },
          { name: 'Add to Inventory', value: 'addToInventory' },
          { name: 'Get Expiring Products', value: 'getExpiringProducts' },
          { name: 'List Locations', value: 'listLocations' },
        ],
      },
    ],
  };
}
```

## F.6 Example Workflows

### Daily Expiration Alert

```json
{
  "name": "GrocyScan Daily Expiration Alert",
  "nodes": [
    {
      "name": "Daily at 8am",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": { "interval": [{ "field": "hours", "hour": 8 }] }
      }
    },
    {
      "name": "Get Expiring Products",
      "type": "n8n-nodes-grocyscan.grocyScan",
      "parameters": {
        "resource": "product",
        "operation": "getExpiring",
        "days": 7
      }
    },
    {
      "name": "Send Email Alert",
      "type": "n8n-nodes-base.emailSend",
      "parameters": {
        "subject": "Items expiring soon"
      }
    }
  ]
}
```

### AI Grocery Assistant

```json
{
  "name": "GrocyScan AI Assistant",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook"
    },
    {
      "name": "AI Agent",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "agent": "toolsAgent",
        "systemMessage": "You are a helpful grocery inventory assistant."
      }
    },
    {
      "name": "GrocyScan Tool",
      "type": "n8n-nodes-grocyscan.grocyScanTool",
      "parameters": {
        "availableTools": [
          "lookupBarcode",
          "searchProducts",
          "getExpiringProducts"
        ]
      }
    }
  ]
}
```

## F.7 Installation

```bash
# Install from npm
npm install n8n-nodes-grocyscan

# Or in n8n UI:
# Settings > Community Nodes > Install > n8n-nodes-grocyscan
```

## F.8 Publishing

```bash
# Build and publish
npm run build
npm run lint
npm publish

# Submit to n8n Creator Portal
# https://creators.n8n.io
```

---

## Navigation

- **Previous:** [Appendix E - User Documentation](appendix-e-user-documentation.md)
- **Back to:** [README](README.md)
