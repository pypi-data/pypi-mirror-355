# 🌐 WebExtract

AI-powered web content extraction using Large Language Models. Extract structured information from any webpage with the power of local or cloud-based LLMs.

## ✨ What does it do?

Transform any webpage into structured data:

1. **🌐 Smart Scraping** - Uses Playwright for reliable scraping of modern websites
2. **🤖 AI Processing** - Leverages LLMs (Ollama, OpenAI, Anthropic) for intelligent content analysis  
3. **📊 Structured Output** - Extracts topics, entities, sentiment, summaries, and key information
4. **🎯 Configurable** - Flexible configuration for different use cases and LLM providers

Perfect for researchers, developers, and anyone who needs to extract meaningful information from web content.

## 🚀 Quick Start

### Installation

```bash
# Install the package
pip install webextract

# For specific LLM providers (optional)
pip install webextract[openai]    # For OpenAI GPT models
pip install webextract[anthropic] # For Anthropic Claude models  
pip install webextract[all]       # For all providers

# Install browser dependencies
playwright install chromium
```

### Basic Usage

```python
import webextract

# Simple extraction with defaults (requires Ollama)
result = webextract.quick_extract("https://example.com")
print(result.structured_info)

# With OpenAI
result = webextract.extract_with_openai(
    "https://news.bbc.co.uk", 
    api_key="sk-..."
)

# With Anthropic  
result = webextract.extract_with_anthropic(
    "https://example.com",
    api_key="sk-ant-..."
)
```

### Command Line Interface

```bash
# Extract with default settings
webextract extract "https://example.com"

# Pretty formatted output
webextract extract "https://example.com" --format pretty

# Custom model and prompt
webextract extract "https://example.com" \
  --model llama3:8b \
  --prompt "Focus on extracting contact information and key facts"

# Test your setup
webextract test
```

## 💡 Features

🌐 **Modern Web Scraping** - Uses Playwright for reliable scraping of modern websites, including SPAs and JavaScript-heavy sites

🛡️ **Robust & Reliable** - Handles errors gracefully, retries failed requests, and works with anti-bot measures

🧠 **Smart Extraction** - Uses your local LLM to understand content and extract meaningful information

⚡ **Fast & Efficient** - Optimized for speed with intelligent content processing and browser automation

🎨 **Beautiful Output** - Clean JSON or rich terminal formatting

🔧 **Highly Configurable** - Customize everything from timeouts to extraction prompts

📊 **Built-in Monitoring** - Confidence scores and performance metrics included

## 🎯 Usage Examples

### Python API

```python
from webextract import WebExtractor, ConfigBuilder, ConfigProfiles

# Method 1: Simple usage
extractor = WebExtractor()
result = extractor.extract("https://example.com")

# Method 2: Custom configuration  
config = (ConfigBuilder()
          .with_model("llama3:8b")
          .with_custom_prompt("Extract key facts and figures")
          .with_timeout(60)
          .build())

extractor = WebExtractor(config)
result = extractor.extract("https://example.com")

# Method 3: Use pre-built profiles
news_extractor = WebExtractor(ConfigProfiles.news_scraping())
research_extractor = WebExtractor(ConfigProfiles.research_papers())
ecommerce_extractor = WebExtractor(ConfigProfiles.ecommerce())

# Method 4: Different LLM providers
openai_config = (ConfigBuilder()
                 .with_openai(api_key="sk-...", model="gpt-4")
                 .build())

anthropic_config = (ConfigBuilder()
                   .with_anthropic(api_key="sk-ant-...", model="claude-3-sonnet-20240229")
                   .build())
```

### Command Line Usage

```bash
# Basic extraction
webextract extract "https://example.com"

# Save to file with pretty formatting
webextract extract "https://example.com" \
  --format pretty \
  --output results.json

# Custom model and settings
webextract extract "https://example.com" \
  --model llama3:8b \
  --max-content 8000 \
  --prompt "Focus on extracting technical information"

# Test connection
webextract test

# Show version
webextract version
```

### Environment Configuration

```bash
# Set via environment variables
export WEBEXTRACT_MODEL="llama3:8b"
export WEBEXTRACT_REQUEST_TIMEOUT="45"
export WEBEXTRACT_MAX_CONTENT="8000"
export WEBEXTRACT_LLM_PROVIDER="ollama"
export WEBEXTRACT_LLM_BASE_URL="http://localhost:11434"
```

## 🛠 Configuration

You can customize the behavior using environment variables:

```bash
export OLLAMA_BASE_URL="http://localhost:11434"
export DEFAULT_MODEL="gemma3:27b"
export REQUEST_TIMEOUT="30"
export MAX_CONTENT_LENGTH="5000"
export REQUEST_DELAY="1.0"
```

Or modify `config/settings.py` directly.

## 📋 What Gets Extracted?

The LLM analyzes web content and extracts:

- **Topics & Themes** - Main subjects discussed
- **Entities** - People, organizations, locations mentioned
- **Key Points** - Important takeaways and facts
- **Sentiment** - Overall tone (positive/negative/neutral)
- **Summary** - Concise overview of the content
- **Metadata** - Title, description, important links
- **Category** - Content classification
- **Important Dates** - Key dates mentioned in the content

## 🏗 Project Structure

```
webextract/
├── src/
│   ├── models.py          # Data structures
│   ├── scraper.py         # Playwright-based web scraping
│   ├── llm_client.py      # Ollama integration
│   └── extractor.py       # Main coordination
├── config/
│   └── settings.py        # Configuration
├── examples/
│   └── basic_usage.py     # Code examples
├── main.py               # CLI interface
└── requirements.txt      # Dependencies
```

## 🚀 Technical Highlights

- **Browser Automation**: Uses Playwright for reliable, modern web scraping
- **Dynamic Content**: Handles JavaScript-rendered content and SPAs
- **Smart Rate Limiting**: Respects website resources with configurable delays
- **Error Recovery**: Comprehensive retry logic with exponential backoff
- **Resource Management**: Proper browser lifecycle management
- **Anti-Detection**: Rotates user agents and uses realistic browser behavior

## 🤝 Contributing

Found a bug? Have an idea? Contributions are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Ollama](https://ollama.ai/) for local LLM processing
- Uses [Playwright](https://playwright.dev/) for modern web scraping
- HTML parsing with [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- CLI powered by [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)

---

**⭐ If this tool helps you, consider giving it a star!** 