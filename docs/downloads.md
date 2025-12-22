# Downloads

Download ArthSaarthi for your platform.

## Desktop Application (v1.0.0)

Self-contained desktop app with embedded database - no server setup required.

| Platform | Architecture | Download |
|----------|--------------|----------|
| **Windows** | x64 (Intel/AMD) | [ArthSaarthi-1.0.0-win-x64.exe](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.0.0/ArthSaarthi-1.0.0-win-x64.exe) |
| **macOS** | Apple Silicon (M1/M2/M3) | [ArthSaarthi-1.0.0-mac-arm64.dmg](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.0.0/ArthSaarthi-1.0.0-mac-arm64.dmg) |
| **macOS** | Intel | [ArthSaarthi-1.0.0-mac-x64.dmg](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.0.0/ArthSaarthi-1.0.0-mac-x64.dmg) |
| **Linux** | x64 | [ArthSaarthi-1.0.0-linux-x64.AppImage](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.0.0/ArthSaarthi-1.0.0-linux-x64.AppImage) |
| **Linux** | ARM64 | [ArthSaarthi-1.0.0-linux-arm64.AppImage](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.0.0/ArthSaarthi-1.0.0-linux-arm64.AppImage) |

[View all releases on GitHub →](https://github.com/aashishbhanawat/ArthSaarthi/releases)

---

## Docker Images

For self-hosted server deployment with multi-user support.

### Quick Start

```bash
# Pull images
docker pull aashishbhanawat/arthsaarthi-backend:latest
docker pull aashishbhanawat/arthsaarthi-frontend:latest

# Or use Docker Compose
curl -O https://raw.githubusercontent.com/aashishbhanawat/ArthSaarthi/main/docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

### Image Details

| Image | Architectures | Tags |
|-------|---------------|------|
| [arthsaarthi-backend](https://hub.docker.com/r/aashishbhanawat/arthsaarthi-backend) | amd64, arm64 | `latest`, `v1.0.0` |
| [arthsaarthi-frontend](https://hub.docker.com/r/aashishbhanawat/arthsaarthi-frontend) | amd64, arm64 | `latest`, `v1.0.0` |

### Requirements

- Docker 20.10+
- Docker Compose v2+
- PostgreSQL 15+ (external or via compose)
- Redis 7+ (external or via compose)

See [Installation Guide](installation_guide.md) for detailed setup instructions.

---

## System Requirements

### Desktop App
- **Windows:** Windows 10 or later (x64)
- **macOS:** macOS 11 (Big Sur) or later
- **Linux:** Ubuntu 20.04+ or equivalent (glibc 2.31+)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 500MB for application + data storage

### Server Mode
- **CPU:** 2 cores minimum
- **RAM:** 4GB minimum
- **Disk:** 10GB+ for database and cache
