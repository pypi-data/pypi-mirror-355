<div align="center">

# 🚀 Vibetest Use

[![PyPI version](https://badge.fury.io/py/vibetest-use.svg)](https://badge.fury.io/py/vibetest-use)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Actions](https://github.com/im47cn/vibetest-use/workflows/Tests/badge.svg)](https://github.com/im47cn/vibetest-use/actions)

**🤖 AI-Powered Multi-Agent Website Testing Platform**

*Autonomous browser agents that intelligently test your websites for bugs, accessibility issues, and user experience problems*

[📦 Installation](#-installation) • [🚀 Quick Start](#-quick-start) • [📖 Usage](#-usage) • [🎯 Examples](#-examples) • [🔧 Configuration](#-configuration)

</div>

---

## ✨ What is Vibetest Use?

**Vibetest Use** is a cutting-edge **Model Control Protocol (MCP)** server that orchestrates multiple intelligent browser agents to comprehensively test your websites. Powered by Google's Gemini AI and advanced browser automation, it provides enterprise-grade testing capabilities through a simple, intuitive interface.

### 🎯 Key Features

- 🤖 **Multi-Agent Testing**: Deploy multiple AI agents simultaneously for comprehensive coverage
- 🧠 **AI-Powered Analysis**: Gemini 2.0 Flash provides intelligent bug detection and reporting
- 🌐 **Universal Compatibility**: Test any website - production, staging, or localhost
- ♿ **Accessibility Testing**: Automated WCAG compliance checking
- 🔗 **Link Validation**: Comprehensive broken link detection
- 📱 **Responsive Testing**: Cross-device compatibility validation
- 🎨 **UI/UX Analysis**: Visual regression and user experience assessment
- 📊 **Detailed Reporting**: Comprehensive test results with actionable insights

https://github.com/user-attachments/assets/9558d051-78bc-45fd-8694-9ac80eaf9494

---

## 📦 Installation

### Recommended: Using uvx (fastest)

[uvx](https://github.com/astral-sh/uv) is the fastest way to run Python tools without installation conflicts:

```bash
# Run vibetest-use directly (no installation needed)
uvx vibetest-use

# Or install globally for repeated use
uvx --global vibetest-use
```

**Why uvx?**
- ⚡ **Instant execution** - No virtual environment setup
- 🔒 **Isolated dependencies** - No conflicts with your system
- 🚀 **Always latest version** - Automatically uses the newest release

### Alternative: Using pip

```bash
pip install vibetest-use
```

### Prerequisites

- **Python 3.11+** - Modern Python version required
- **Google API Key** - For Gemini AI integration ([Get yours here](https://aistudio.google.com/app/apikey))
- **MCP-Compatible IDE** - Claude Desktop, Cursor, or any MCP-enabled environment

---

## 🚀 Quick Start

### Option 1: Claude Desktop (Recommended)

```bash
# Add MCP server via Claude CLI
claude mcp add vibetest-use vibetest-use -e GOOGLE_API_KEY="your_api_key"

# Verify connection
claude
> /mcp
  ⎿  MCP Server Status
     • vibetest-use: ✅ connected
```

### Option 2: Cursor IDE

1. **Open Cursor Settings** → **MCP** → **Add Server**
2. **Configure the server:**

```json
{
  "mcpServers": {
    "vibetest-use": {
      "command": "vibetest-use",
      "env": {
        "GOOGLE_API_KEY": "your_api_key"
      }
    }
  }
}
```

3. **Restart Cursor** and start testing!

### Option 3: Manual Installation

```bash
# Clone and install from source
git clone https://github.com/im47cn/vibetest-use.git
cd vibetest-use
pip install -e .

# Run directly
export GOOGLE_API_KEY="your_api_key"
vibetest-use
```

---

## 📖 Usage

### Basic Commands

Once configured, you can start testing with simple natural language commands:

```
🌐 Test any website
> Test my website with vibetest-use: https://example.com

🏠 Test localhost development
> Run vibetest-use on localhost:3000

🚀 Advanced testing with multiple agents
> Run a headless vibetest-use on localhost:8080 with 10 agents

🔍 Focused accessibility testing
> Test accessibility issues with vibetest-use on my staging site: https://staging.myapp.com
```

### Advanced Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| **URL** | Any website URL | `https://example.com`, `localhost:3000` |
| **Agent Count** | Number of testing agents (1-20) | `5 agents`, `10 agents` |
| **Mode** | Headless or visual testing | `headless`, `non-headless` |
| **Focus** | Specific testing areas | `accessibility`, `links`, `ui` |

---

## 🎯 Examples

### E-commerce Site Testing
```
> Test my e-commerce site with 8 agents focusing on checkout flow: https://mystore.com
```

### Mobile App Testing
```
> Run responsive testing on my mobile app: https://app.example.com
```

### Accessibility Audit
```
> Perform comprehensive accessibility testing on localhost:3000 with detailed reporting
```

### Performance Testing
```
> Test loading performance and user experience on https://mysite.com with 5 agents
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Required
export GOOGLE_API_KEY="your_gemini_api_key"

# Optional
export BROWSER_USE_LOGGING_LEVEL="INFO"
export ANONYMIZED_TELEMETRY="false"
```

### Advanced MCP Configuration

For enterprise deployments, you can customize the MCP server configuration:

```json
{
  "mcpServers": {
    "vibetest-use": {
      "command": "vibetest-use",
      "env": {
        "GOOGLE_API_KEY": "your_api_key",
        "MAX_AGENTS": "10",
        "DEFAULT_TIMEOUT": "30",
        "HEADLESS_MODE": "true"
      }
    }
  }
}
```

---

## 🎬 Full Demo

https://github.com/user-attachments/assets/6450b5b7-10e5-4019-82a4-6d726dbfbe1f

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/im47cn/vibetest-use.git
cd vibetest-use
pip install -e ".[dev]"
pytest
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Powered by [Browser Use](https://github.com/browser-use/browser-use) - Advanced browser automation
- Built with [Google Gemini AI](https://ai.google.dev/) - Intelligent analysis and reporting
- Supports [Model Control Protocol](https://modelcontextprotocol.io/) - Seamless AI integration

---

<div align="center">

**Made with ❤️ for developers who care about quality**

[⭐ Star us on GitHub](https://github.com/im47cn/vibetest-use) • [🐛 Report Issues](https://github.com/im47cn/vibetest-use/issues) • [💬 Join Discussions](https://github.com/im47cn/vibetest-use/discussions)

</div>
