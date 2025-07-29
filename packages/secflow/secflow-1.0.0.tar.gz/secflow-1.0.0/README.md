# 🛡️ SecFlow

**Enterprise Security Framework for DevSecOps Integration**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](https://pypi.org/project/secflow/)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> 🚀 **New**: Complete enterprise-ready security framework with advanced threat modeling, plugin system, and web interface!

## ✨ Features

### 🔌 **Plugin System**
- Extensible architecture with custom scanners
- Automatic plugin discovery and registration
- Version management and dependencies

### 📊 **Elasticsearch Integration**
- Centralized result storage and analytics
- Automatic index creation and mapping
- Ready-to-use Kibana dashboards

### 📬 **Multi-Channel Notifications**
- **Slack** - Rich formatting with attachments
- **Microsoft Teams** - Interactive cards
- **Email** - HTML/text notifications

### 🛡️ **Advanced Threat Modeling**
- Automatic codebase analysis
- STRIDE threat generation
- Mitigation recommendations
- JSON/YAML export

### 🌐 **Web Management Interface**
- Interactive dashboard
- REST API for integrations
- Real-time scan monitoring
- CORS support for frontends

### 🔍 **Security Scanners**
- **SAST**: Bandit, Semgrep, CodeQL
- **DAST**: OWASP ZAP, Nuclei
- **Secrets**: GitLeaks, TruffleHog
- **Dependencies**: Safety, Snyk
- **Infrastructure**: Checkov, Terrascan

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI
pip install secflow

# Or install from source
git clone https://github.com/WaiperOK/SecFlow.git
cd SecFlow
pip install -e .
```

### Basic Usage

```python
from pyseckit import SecFlow

# Initialize SecFlow
sf = SecFlow()

# Run security scan
results = sf.scan(target="./my-project")

# Generate threat model
threat_model = sf.generate_threat_model("./my-project")

# Start web interface
sf.start_web_interface(port=8080)
```

### CLI Usage

```bash
# Initialize configuration
secflow init

# Run comprehensive scan
secflow scan --target ./project --format json,html

# Start web interface
secflow web --port 8080

# Generate threat model
secflow threat-model --target ./project --output threats.json

# Test notifications
secflow test-notifications
```

## 📋 Configuration

Create `.secflow.yml` in your project root:

```yaml
# Core settings
project_name: "My Secure Project"
target_directories: ["."]

# Scanners configuration
scanners:
  bandit:
    enabled: true
    severity_threshold: "medium"
  semgrep:
    enabled: true
    rules: ["security", "owasp-top-10"]

# Integrations
elasticsearch:
  enabled: true
  hosts: ["localhost:9200"]

# Notifications
notifications:
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/..."
    channel: "#security"

# Web interface
web:
  enabled: true
  host: "0.0.0.0"
  port: 8080

# Plugins
plugins:
  discovery_paths: ["./plugins", "~/.secflow/plugins"]
```

## 🏗️ Architecture

```
SecFlow/
├── 📦 Core Modules
│   ├── pyseckit/core/          # Base functionality
│   ├── pyseckit/sast/          # Static analysis
│   ├── pyseckit/dast/          # Dynamic testing
│   ├── pyseckit/secret_scan/   # Secret detection
│   └── pyseckit/cloud/         # Infrastructure analysis
│
├── 🔌 Advanced Modules
│   ├── pyseckit/plugins/       # Plugin system
│   ├── pyseckit/integrations/  # External integrations
│   ├── pyseckit/threat_model/  # Threat modeling
│   └── pyseckit/web/           # Web interface
│
└── 📊 Outputs
    ├── reports/                # Generated reports
    ├── dashboards/             # Kibana dashboards
    └── threat_models/          # Threat models
```

## 🔌 Plugin Development

Create custom security scanners:

```python
from pyseckit.plugins import ScannerPlugin, PluginMetadata

class MyCustomScanner(ScannerPlugin):
    def __init__(self, config):
        metadata = PluginMetadata(
            name="my-scanner",
            version="1.0.0",
            description="Custom security scanner",
            author="Your Name"
        )
        super().__init__(config, metadata)
    
    def scan(self, target):
        # Your scanning logic here
        return scan_results
```

## 🌐 REST API

SecFlow provides a comprehensive REST API:

```bash
# System status
GET /api/status

# Start scan
POST /api/scan
{
  "target": "./project",
  "scanners": ["bandit", "semgrep"]
}

# Get results
GET /api/results/{scan_id}

# Generate threat model
POST /api/threat-model
{
  "target": "./project",
  "format": "json"
}
```

## 🚀 CI/CD Integration

### GitHub Actions

```yaml
name: SecFlow Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run SecFlow
        run: |
          pip install secflow
          secflow scan --target . --fail-on-critical
```

### GitLab CI

```yaml
security_scan:
  stage: test
  script:
    - pip install secflow
    - secflow scan --target . --format gitlab-sast
  artifacts:
    reports:
      sast: gl-sast-report.json
```

## 📊 Enterprise Features

- **Multi-tenant support** with role-based access
- **LDAP/SSO integration** for enterprise authentication
- **Compliance reporting** (SOC2, PCI-DSS, GDPR)
- **Custom rule engines** for organization-specific policies
- **Audit trails** and compliance tracking
- **High availability** deployment options

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🌟 Support

- 📖 **Documentation**: [Wiki](https://github.com/WaiperOK/SecFlow/wiki)
- 🐛 **Bug Reports**: [Issues](https://github.com/WaiperOK/SecFlow/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/WaiperOK/SecFlow/discussions)
- 📧 **Email**: team@secflow.dev

## 🏆 Acknowledgments

Built with ❤️ by the SecFlow team and contributors.

---

**⭐ Star us on GitHub if SecFlow helps secure your projects!** 