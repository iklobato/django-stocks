# Testing the Django Challenge

This guide will help you test the Django Challenge implementation with both services.

## Current Setup

1. **API Service**: Running on port 8000
   - URL: http://localhost:8000
   - Entry point for users
   - Handles authentication, history, and statistics

2. **Stock Service**: Running on port 8001
   - URL: http://localhost:8001
   - Internal service that fetches stock data
   - Called by the API service

## Testing with the HTTP Client

Use the provided `requests.http` file with either:
- VS Code REST Client extension
- JetBrains HTTP Client

The file contains requests for both services:
- API service tests (authentication, stock queries, history, stats)
- Stock service direct tests

## API Service Endpoints

### GET / - API Documentation
Shows available endpoints and how to use them.

### GET /stock?q=SYMBOL
Get stock data for the specified symbol.
- Requires: `q` parameter with stock code
- Example: `/stock?q=aapl.us`
- Authentication: Basic or Token (if configured)

### GET /history
Get history of stock queries for the current user.
- Authentication: Required

### GET /stats
Get the top 5 most requested stocks.
- Authentication: Admin privileges required

## Stock Service Endpoints

### GET /stock
Internal endpoint to fetch stock data from Stooq.com
- Parameters:
  - `stock_code` - The stock symbol
  - `q` - Alternative name for stock code
  - `symbol` - Another alternative name
- Example: `/stock?stock_code=aapl.us`
- No authentication required

## Troubleshooting

### API Service Issues
- 400 Bad Request: Missing `q` parameter in `/stock`
- 401 Unauthorized: Authentication required
- 403 Forbidden: Insufficient permissions (for `/stats`)
- 500 Internal Server Error: Check if stock service is running

### Stock Service Issues
- 400 Bad Request: Missing stock code parameter
- 404 Not Found: Invalid stock symbol
- 500 Internal Server Error: Problem with external Stooq API

## Manual Testing with curl

### API Service

1. Get API Documentation:
```bash
curl http://localhost:8000/
```

2. Get Stock Data (with Basic Auth):
```bash
curl -u username:password http://localhost:8000/stock?q=aapl.us
```

3. Get History (with Basic Auth):
```bash
curl -u username:password http://localhost:8000/history
```

4. Get Stats (admin only):
```bash
curl -u admin:admin123 http://localhost:8000/stats
```

### Stock Service

1. Get Stock Data:
```bash
curl http://localhost:8001/stock?stock_code=aapl.us
```

2. Test with Different Parameters:
```bash
curl http://localhost:8001/stock?q=aapl.us
curl http://localhost:8001/stock?symbol=aapl.us
```