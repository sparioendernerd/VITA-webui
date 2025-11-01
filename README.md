# VITA - Vailen Industries Thematic AI ☕

**VITA (Vailen Industries Thematic AI)** is a powerful, coffee-inspired AI platform with first-class support for OpenAI, Ollama, and MCP (Model Context Protocol). Built on Open WebUI, VITA adds enhanced agentic capabilities and a warm, intuitive interface.

![VITA Demo](./demo.gif)

## What is VITA? ⭐

VITA stands for **Vailen Industries Thematic AI** - a fork of Open WebUI enhanced with:
- ☕ **Coffee-themed UI** - Warm, rich colors inspired by your favorite brew
- 🤖 **Agentic Workflows** - Orchestrate complex tasks with iterative tool execution
- 🔗 **MCP Integration** - Full Model Context Protocol support for agentic workflows
- 🚀 **Enhanced Features** - Multi-step tool execution and advanced AI capabilities

## Key Features ⭐

- ☕ **Coffee-Themed Interface**: A warm, inviting UI with rich coffee-inspired colors

- 🤖 **OpenAI-Compatible Support**: Direct integration with OpenAI models and compatible APIs
  - Optimized tool calling flows
  - Support for prompt caching and extended thinking
  - Streaming and non-streaming responses

- 🔗 **MCP (Model Context Protocol) Integration**: Full support for agentic workflows
  - Multi-step tool execution
  - Native integration with MCP tool use
  - Support for MCP resources and prompts

- 🚀 **Effortless Setup**: Install seamlessly using Docker or Kubernetes (kubectl, kustomize or helm) for a hassle-free experience with support for both `:ollama` and `:cuda` tagged images.

- 🤝 **Multi-Provider Support**: Effortlessly integrate OpenAI, Ollama, and OpenAI-compatible APIs. Customize API URLs to work with **LMStudio, GroqCloud, Mistral, OpenRouter, and more**.

- 🛡️ **Granular Permissions and User Groups**: By allowing administrators to create detailed user roles and permissions, we ensure a secure user environment. This granularity not only enhances security but also allows for customized user experiences, fostering a sense of ownership and responsibility amongst users.

- 🔄 **SCIM 2.0 Support**: Enterprise-grade user and group provisioning through SCIM 2.0 protocol, enabling seamless integration with identity providers like Okta, Azure AD, and Google Workspace for automated user lifecycle management.

- 📱 **Responsive Design**: Enjoy a seamless experience across Desktop PC, Laptop, and Mobile devices.

- 📱 **Progressive Web App (PWA) for Mobile**: Enjoy a native app-like experience on your mobile device with our PWA, providing offline access on localhost and a seamless user interface.

- ✒️🔢 **Full Markdown and LaTeX Support**: Elevate your LLM experience with comprehensive Markdown and LaTeX capabilities for enriched interaction.

- 🎤📹 **Hands-Free Voice/Video Call**: Experience seamless communication with integrated hands-free voice and video call features, allowing for a more dynamic and interactive chat environment.

- 🛠️ **Model Builder**: Easily create Ollama models via the Web UI. Create and add custom characters/agents, customize chat elements, and import models effortlessly.

- 🐍 **Native Python Function Calling Tool**: Enhance your LLMs with built-in code editor support in the tools workspace. Bring Your Own Function (BYOF) by simply adding your pure Python functions, enabling seamless integration with LLMs.

- 📚 **Local RAG Integration**: Dive into the future of chat interactions with groundbreaking Retrieval Augmented Generation (RAG) support. This feature seamlessly integrates document interactions into your chat experience. You can load documents directly into the chat or add files to your document library, effortlessly accessing them using the `#` command before a query.

- 🔍 **Web Search for RAG**: Perform web searches using providers like `SearXNG`, `Google PSE`, `Brave Search`, `serpstack`, `serper`, `Serply`, `DuckDuckGo`, `TavilySearch`, `SearchApi` and `Bing` and inject the results directly into your chat experience.

- 🌐 **Web Browsing Capability**: Seamlessly integrate websites into your chat experience using the `#` command followed by a URL. This feature allows you to incorporate web content directly into your conversations, enhancing the richness and depth of your interactions.

- 🎨 **Image Generation Integration**: Seamlessly incorporate image generation capabilities using options such as AUTOMATIC1111 API or ComfyUI (local), and OpenAI's DALL-E (external), enriching your chat experience with dynamic visual content.

- ⚙️ **Many Models Conversations**: Effortlessly engage with various models simultaneously, harnessing their unique strengths for optimal responses. Enhance your experience by leveraging a diverse set of models in parallel.

- 🔐 **Role-Based Access Control (RBAC)**: Ensure secure access with restricted permissions; only authorized individuals can access your models, and exclusive model creation/pulling rights are reserved for administrators.

- 🌐🌍 **Multilingual Support**: Experience VITA in your preferred language with our internationalization (i18n) support.

- 🧩 **Pipelines Plugin Support**: Seamlessly integrate custom logic and Python libraries into VITA using Pipelines Plugin Framework. Launch your Pipelines instance and explore endless possibilities including **Function Calling**, **Rate Limiting**, **Usage Monitoring**, **Live Translation**, **Toxic Message Filtering** and much more.

- 🌟 **Continuous Updates**: We are committed to improving VITA with regular updates, fixes, and new features.

## Quick Start 🚀

### Docker Setup

```bash
# With Ollama
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name vita \
  --restart always \
  ghcr.io/open-webui/open-webui:main

# Standalone (bring your own APIs)
docker run -d -p 3000:8080 \
  -v open-webui:/app/backend/data \
  --name vita \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

### Configuration

Set your API keys via environment variables:

```bash
# For OpenAI
export ENABLE_OPENAI_API=true
export OPENAI_API_KEY="sk-..."

# For Ollama (local)
export ENABLE_OLLAMA_API=true
export OLLAMA_API_BASE_URL="http://localhost:11434/api"
```

## VITA-Specific Features

### MCP Integration

Full Model Context Protocol support:
- Multi-step agentic workflows
- Tool execution with iteration controls
- Support for MCP resources and prompts
- OAuth 2.1 authentication for MCP servers

### Coffee Theme

A warm, inviting color scheme inspired by coffee:
- Rich espresso darks
- Creamy latte lights
- Smooth cappuccino accents
- Designed for extended coding and chat sessions

## Built On Open WebUI

VITA is built on the excellent [Open WebUI](https://github.com/open-webui/open-webui) project. We're grateful to the Open WebUI team and community for creating such a solid foundation.

### Changes from Open WebUI:
- Streamlined provider support (OpenAI + Ollama)
- MCP (Model Context Protocol) support
- Coffee-themed UI redesign
- Enhanced agentic capabilities

## Development

```bash
# Clone the repository
git clone https://github.com/sparioendernerd/VITA-webui.git
cd VITA-webui

# Install dependencies
npm install

# Set up Python backend
cd backend
pip install -r requirements.txt

# Run development server
npm run dev
```

## Contributing

VITA is a personal fork focused on MCP integration and several personal customizations. If you'd like to contribute to the base project, please visit [Open WebUI](https://github.com/open-webui/open-webui).

## License

VITA inherits the MIT License from Open WebUI. See LICENSE file for details.

## Acknowledgments

- **Open WebUI Team** - For the excellent foundation
- **Coffee** - For the inspiration ☕

---

**Powered by coffee and AI** ☕🤖
