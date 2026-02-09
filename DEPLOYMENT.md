# Deployment Information

## Backend Deployment

**Server:** 94.131.85.176

### API Endpoints

- **HTTPS (Production):** https://94.131.85.176
- **HTTP (redirects to HTTPS):** http://94.131.85.176
- **Swagger Documentation:** https://94.131.85.176/docs
- **API Base URL:** https://94.131.85.176/api/v1

### SSL Certificate

The server uses a self-signed SSL certificate. When accessing from a browser for the first time, you'll need to accept the security exception.

### CORS Configuration

The following origins are allowed:
- http://localhost:3000
- http://localhost:8000
- https://edu-stream-mu.vercel.app
- https://94.131.85.176
- http://94.131.85.176

## Frontend Configuration

### Environment Variables for Frontend

Set the following environment variable in your frontend project (Vercel):

```bash
NEXT_PUBLIC_API_BASE_URL=https://94.131.85.176/api/v1
# or
VITE_API_BASE_URL=https://94.131.85.176/api/v1
```

### Example API Usage

```javascript
// In your API client/config
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'https://94.131.85.176/api/v1';

// Example requests
fetch(`${API_BASE_URL}/courses/`)
fetch(`${API_BASE_URL}/materials`)
fetch(`${API_BASE_URL}/auth/login`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ email, password })
})
```

## Important Notes

1. **HTTPS Required:** The backend is configured to use HTTPS. Make sure all API requests use `https://` protocol.

2. **Self-Signed Certificate:** Since we're using a self-signed certificate, you might need to:
   - Accept the certificate in your browser before making API calls
   - Or configure your frontend to allow self-signed certificates in development

3. **Direct IP Access:** Currently using IP address (94.131.85.176). For production, consider:
   - Setting up a domain name
   - Using Let's Encrypt for a valid SSL certificate

## Server Access

```bash
# SSH Access
ssh -i ssh-key-1770638448815 baltabek@94.131.85.176

# View logs
sudo docker compose logs app -f

# Restart services
sudo docker compose restart app

# Check status
sudo docker compose ps
```

## Troubleshooting

### CORS Errors

If you get CORS errors:
1. Check that your frontend origin is listed in the CORS_ORIGINS environment variable
2. Restart the backend: `sudo docker compose restart app`

### SSL Certificate Warnings

If you get SSL certificate warnings:
- This is expected with self-signed certificates
- For development: accept the certificate in your browser
- For production: set up a domain and use Let's Encrypt

### API Not Responding

1. Check if services are running: `sudo docker compose ps`
2. Check logs: `sudo docker compose logs app --tail 50`
3. Check nginx status: `sudo systemctl status nginx`
4. Verify ports are open: `ss -tlnp | grep -E '(80|443)'`
