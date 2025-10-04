# Complete Fly.io Tutorial

## Table of Contents
1. [What is Fly.io?](#what-is-flyio)
2. [Installation & Setup](#installation--setup)
3. [Basic Concepts](#basic-concepts)
4. [Your First App](#your-first-app)
5. [Configuration Files](#configuration-files)
6. [Deployment Process](#deployment-process)
7. [Domain Management](#domain-management)
8. [SSL Certificates](#ssl-certificates)
9. [Scaling & Monitoring](#scaling--monitoring)
10. [Database Integration](#database-integration)
11. [Advanced Features](#advanced-features)
12. [Troubleshooting](#troubleshooting)
13. [Best Practices](#best-practices)

## What is Fly.io?

Fly.io is a modern cloud platform that runs applications close to users globally. Key features:

- **Global Edge Deployment**: Deploy apps to multiple regions worldwide
- **Microservices Architecture**: Each app runs in isolated containers
- **Zero Config Networking**: Built-in private networking between services
- **Instant WireGuard VPN**: Secure access to your infrastructure
- **Hardware Isolation**: Apps run on dedicated hardware for better performance

### Why Choose Fly.io?
- ✅ Fast global deployment
- ✅ Developer-friendly CLI
- ✅ Docker-based deployments
- ✅ Built-in load balancing
- ✅ Competitive pricing
- ✅ Great for full-stack applications

## Installation & Setup

### 1. Install flyctl CLI

**Windows (PowerShell):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**macOS/Linux:**
```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Verify Installation
```bash
flyctl version
```

### 3. Sign Up & Login
```bash
flyctl auth signup  # Create new account
# OR
flyctl auth login   # Login to existing account
```

## Basic Concepts

### Applications
- **App**: A logical unit that can have multiple machines
- **Machine**: Individual containers running your code
- **Organization**: Groups apps and manages billing

### Regions
Popular regions:
- `ord` - Chicago, IL (US)
- `dfw` - Dallas, TX (US)
- `lax` - Los Angeles, CA (US)
- `lhr` - London, UK
- `nrt` - Tokyo, Japan
- `syd` - Sydney, Australia

### Resources
- **CPU**: Shared or dedicated CPU cores
- **Memory**: 256MB to 8GB RAM options
- **Storage**: Persistent volumes for data

## Your First App

### 1. Create a Simple HTML App

**Create directory:**
```bash
mkdir my-first-fly-app
cd my-first-fly-app
```

**Create index.html:**
```html
<!DOCTYPE html>
<html>
<head>
    <title>My First Fly App</title>
</head>
<body>
    <h1>Hello from Fly.io!</h1>
    <p>This is my first app deployed on Fly.io</p>
</body>
</html>
```

**Create Dockerfile:**
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 2. Launch the App
```bash
flyctl launch
```

This will:
- Scan your source code
- Detect the Dockerfile
- Ask configuration questions
- Create `fly.toml` config file
- Deploy your app

### 3. Access Your App
```bash
flyctl open
```

## Configuration Files

### fly.toml Structure
```toml
app = "my-app-name"
primary_region = "ord"

[build]
  # Build configuration

[http_service]
  internal_port = 80
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### Key Sections Explained

**App Settings:**
```toml
app = "unique-app-name"
primary_region = "ord"  # Primary deployment region
```

**HTTP Service:**
```toml
[http_service]
  internal_port = 80           # Port your app listens on
  force_https = true           # Redirect HTTP to HTTPS
  auto_stop_machines = true    # Stop idle machines
  auto_start_machines = true   # Start machines on traffic
  min_machines_running = 0     # Minimum running machines
```

**VM Configuration:**
```toml
[[vm]]
  cpu_kind = "shared"     # "shared" or "performance"
  cpus = 1               # Number of CPU cores
  memory_mb = 256        # Memory allocation
```

**Environment Variables:**
```toml
[env]
  NODE_ENV = "production"
  API_URL = "https://api.example.com"
```

**Health Checks:**
```toml
[http_service.checks]
  interval = "10s"
  grace_period = "5s"
  method = "GET"
  path = "/health"
  protocol = "http"
  timeout = "2s"
```

## Deployment Process

### 1. Basic Deployment
```bash
flyctl deploy
```

### 2. Deploy from Specific Directory
```bash
flyctl deploy --dockerfile /path/to/Dockerfile
```

### 3. Deploy with Build Args
```bash
flyctl deploy --build-arg NODE_ENV=production
```

### 4. Deploy to Specific Region
```bash
flyctl deploy --region ord
```

### 5. Check Deployment Status
```bash
flyctl status
flyctl logs
```

## Domain Management

### 1. Add Custom Domain
```bash
flyctl certs create example.com
flyctl certs create www.example.com
```

### 2. Check Certificate Status
```bash
flyctl certs list
flyctl certs show example.com
```

### 3. Get DNS Setup Instructions
```bash
flyctl certs setup example.com
```

### 4. Common DNS Configurations

**A Record (Root Domain):**
```
A    @ → [Your Fly.io IP]
AAAA @ → [Your Fly.io IPv6]
```

**CNAME (Subdomain):**
```
CNAME www → your-app.fly.dev
```

## SSL Certificates

### Automatic SSL
Fly.io automatically provides SSL certificates for:
- `your-app.fly.dev` (immediate)
- Custom domains (after DNS verification)

### Certificate Types
- **Let's Encrypt**: Free, automatic renewal
- **Custom**: Upload your own certificates

### Troubleshooting SSL
```bash
# Check certificate status
flyctl certs list

# View detailed certificate info
flyctl certs show example.com

# Force certificate renewal
flyctl certs setup example.com
```

## Scaling & Monitoring

### 1. Scale Machines
```bash
# Set number of machines
flyctl scale count 3

# Scale specific regions
flyctl scale count 2 --region ord
flyctl scale count 1 --region lhr
```

### 2. Scale Resources
```bash
# Scale VM resources
flyctl scale vm shared-cpu-1x --memory 512

# Available VM sizes
flyctl platform vm-sizes
```

### 3. Monitoring Commands
```bash
# View app status
flyctl status

# View logs
flyctl logs
flyctl logs --follow

# View metrics
flyctl metrics

# SSH into machine
flyctl ssh console
```

### 4. Auto-scaling Configuration
```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1
  max_machines_running = 10
```

## Database Integration

### 1. PostgreSQL
```bash
# Create PostgreSQL cluster
flyctl postgres create --name my-db

# Connect app to database
flyctl postgres attach --app my-app my-db
```

### 2. Redis
```bash
# Create Redis instance
flyctl redis create --name my-redis

# Get connection string
flyctl redis status my-redis
```

### 3. Database URLs
After attachment, Fly.io sets environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

### 4. Example Connection (Node.js)
```javascript
const { Pool } = require('pg');

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
});
```

## Advanced Features

### 1. Multiple Regions
```bash
# Deploy to multiple regions
flyctl regions add ord dfw lax

# Remove from region
flyctl regions remove sea

# List all regions
flyctl regions list
```

### 2. Volumes (Persistent Storage)
```bash
# Create volume
flyctl volumes create my_data --size 10 --region ord

# List volumes
flyctl volumes list

# Mount in fly.toml
```
```toml
[[mounts]]
  source = "my_data"
  destination = "/data"
```

### 3. Secrets Management
```bash
# Set secrets
flyctl secrets set DATABASE_PASSWORD=secret123
flyctl secrets set API_KEY=abc123

# List secrets (names only)
flyctl secrets list

# Unset secrets
flyctl secrets unset OLD_SECRET
```

### 4. WireGuard VPN
```bash
# Create WireGuard connection
flyctl wireguard create

# List connections
flyctl wireguard list

# Connect to private network
flyctl proxy 5432 -a my-db
```

### 5. Multiple Processes
```toml
[processes]
  web = "nginx -g 'daemon off;'"
  worker = "node worker.js"

[http_service]
  processes = ["web"]
```

## Troubleshooting

### Common Issues & Solutions

**1. Build Failures**
```bash
# Check build logs
flyctl logs --app my-app

# Build locally to test
docker build -t my-app .
docker run -p 8080:80 my-app
```

**2. Health Check Failures**
```bash
# Check machine status
flyctl status

# View detailed logs
flyctl logs --follow

# SSH into machine
flyctl ssh console
```

**3. SSL Certificate Issues**
```bash
# Check DNS configuration
nslookup example.com

# Verify certificate status
flyctl certs show example.com

# Re-setup certificate
flyctl certs setup example.com
```

**4. Connection Issues**
```bash
# Test connectivity
curl -I https://your-app.fly.dev

# Check machine health
flyctl status

# Restart all machines
flyctl machine restart
```

### Useful Debug Commands
```bash
# View app configuration
flyctl config show

# Check platform status
flyctl platform status

# View billing info
flyctl orgs show

# Get help for any command
flyctl help deploy
```

## Best Practices

### 1. Configuration
- ✅ Use environment variables for configuration
- ✅ Keep secrets in Fly.io secrets, not in code
- ✅ Set appropriate health checks
- ✅ Configure auto-scaling based on your needs

### 2. Docker Best Practices
- ✅ Use multi-stage builds to reduce image size
- ✅ Use specific base image tags (not `latest`)
- ✅ Add health check endpoints
- ✅ Run as non-root user when possible

### 3. Deployment
- ✅ Test locally before deploying
- ✅ Use staging environments
- ✅ Monitor logs during deployment
- ✅ Have rollback plan ready

### 4. Performance
- ✅ Deploy to regions close to your users
- ✅ Use appropriate VM sizes
- ✅ Enable gzip compression
- ✅ Implement caching strategies

### 5. Security
- ✅ Force HTTPS for web apps
- ✅ Use Fly.io secrets for sensitive data
- ✅ Keep dependencies updated
- ✅ Implement proper authentication

### 6. Cost Optimization
- ✅ Use auto-stop for low-traffic apps
- ✅ Right-size your VMs
- ✅ Monitor usage regularly
- ✅ Clean up unused resources

### Example Production-Ready fly.toml
```toml
app = "my-production-app"
primary_region = "ord"

[build]

[env]
  NODE_ENV = "production"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 2
  max_machines_running = 10

[http_service.checks]
  interval = "10s"
  grace_period = "5s"
  method = "GET"
  path = "/health"
  protocol = "http"
  timeout = "2s"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512

[[mounts]]
  source = "app_data"
  destination = "/app/data"
```

## Quick Reference

### Essential Commands
```bash
flyctl launch              # Create and deploy new app
flyctl deploy              # Deploy changes
flyctl status              # Check app status
flyctl logs                # View logs
flyctl open                # Open app in browser
flyctl ssh console         # SSH into machine
flyctl scale count 3       # Scale to 3 machines
flyctl secrets set KEY=val # Set secret
flyctl certs create domain # Add SSL certificate
```

### Configuration
```bash
flyctl config show         # View current config
flyctl regions list        # List all regions
flyctl platform vm-sizes   # List VM options
flyctl apps list          # List your apps
```

### Monitoring
```bash
flyctl status             # App overview
flyctl logs --follow      # Live logs
flyctl metrics            # Performance metrics
flyctl machine list       # List machines
```

---

## Summary

Fly.io provides a powerful, developer-friendly platform for deploying applications globally. Key advantages:

1. **Simple Deployment**: Docker-based with minimal configuration
2. **Global Scale**: Deploy to multiple regions easily  
3. **Auto-scaling**: Machines start/stop based on traffic
4. **Great Developer Experience**: Excellent CLI and documentation
5. **Cost Effective**: Pay only for what you use

Start with a simple app, then gradually explore advanced features like databases, multiple regions, and auto-scaling as your needs grow.

For more information, visit: https://fly.io/docs/