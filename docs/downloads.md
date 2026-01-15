# Downloads

Download ArthSaarthi for your platform.

## Desktop Application (v1.1.0)

Self-contained desktop app with embedded database - no server setup required.

| Platform | Architecture | Download |
|----------|--------------|----------|
| **Windows** | x64 (Intel/AMD) | [ArthSaarthi-Windows-x64-Setup-v1.1.0.exe](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.1.0/ArthSaarthi-Windows-x64-Setup-v1.1.0.exe) |
| **macOS** | Apple Silicon (M1/M2/M3) | [ArthSaarthi-macOS-arm64-v1.1.0.dmg](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.1.0/ArthSaarthi-macOS-arm64-v1.1.0.dmg) |
| **macOS** | Intel | [ArthSaarthi-macOS-x64-v1.1.0.dmg](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.1.0/ArthSaarthi-macOS-x64-v1.1.0.dmg) |
| **Linux** | x64 | [ArthSaarthi-Linux-x64-v1.1.0.AppImage](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.1.0/ArthSaarthi-Linux-x64-v1.1.0.AppImage) |
| **Linux** | ARM64 | [ArthSaarthi-Linux-arm64-v1.1.0.AppImage](https://github.com/aashishbhanawat/ArthSaarthi/releases/download/v1.1.0/ArthSaarthi-Linux-arm64-v1.1.0.AppImage) |

[View all releases on GitHub →](https://github.com/aashishbhanawat/ArthSaarthi/releases)

---

## Docker Images

For self-hosted server deployment with multi-user support.

### Quick Start

```bash
# Pull images
docker pull aashishbhanawat/arthsaarthi-backend:v1.1.0
docker pull aashishbhanawat/arthsaarthi-frontend:v1.1.0

# Or use Docker Compose
curl -O https://raw.githubusercontent.com/aashishbhanawat/ArthSaarthi/main/docker-compose.prod.yml
docker compose -f docker-compose.prod.yml up -d
```

### Image Details

| Image | Architectures | Tags |
|-------|---------------|------|
| [arthsaarthi-backend](https://hub.docker.com/r/aashishbhanawat/arthsaarthi-backend) | amd64, arm64 | `latest`, `v1.1.0`, `v1.0.0` |
| [arthsaarthi-frontend](https://hub.docker.com/r/aashishbhanawat/arthsaarthi-frontend) | amd64, arm64 | `latest`, `v1.1.0`, `v1.0.0` |

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
