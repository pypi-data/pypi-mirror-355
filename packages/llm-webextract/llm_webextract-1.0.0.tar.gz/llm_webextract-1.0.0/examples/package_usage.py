#!/usr/bin/env python3
"""
WebExtract Package Usage Examples

This file demonstrates how to use WebExtract as an installed package.
"""

# First, install the package:
# pip install webextract

import webextract
from webextract import WebExtractor, ConfigBuilder, ConfigProfiles


def basic_usage():
    """Basic usage examples."""
    print("🌐 WebExtract Package Examples")
    print("=" * 50)
    
    # Method 1: Quick extraction with defaults
    print("\n1. Quick extraction:")
    result = webextract.quick_extract("https://example.com")
    if result:
        print(f"   Title: {result.content.title}")
        print(f"   Confidence: {result.confidence:.2f}")
    
    # Method 2: Using WebExtractor class
    print("\n2. Using WebExtractor class:")
    extractor = WebExtractor()
    result = extractor.extract("https://example.com")
    if result:
        print(f"   Topics: {result.structured_info.get('topics', [])}")


def configuration_examples():
    """Configuration examples."""
    print("\n" + "="*50)
    print("🔧 Configuration Examples")
    print("="*50)
    
    # Builder pattern configuration
    config = (ConfigBuilder()
              .with_model("llama3:8b")
              .with_custom_prompt("Extract key facts and contact information")
              .with_timeout(60)
              .with_content_limit(8000)
              .build())
    
    extractor = WebExtractor(config)
    print("✅ Custom configuration created")
    
    # Pre-built profiles
    news_extractor = WebExtractor(ConfigProfiles.news_scraping())
    research_extractor = WebExtractor(ConfigProfiles.research_papers())
    ecommerce_extractor = WebExtractor(ConfigProfiles.ecommerce())
    
    print("✅ Profile-based extractors created")


def llm_provider_examples():
    """Different LLM provider examples."""
    print("\n" + "="*50)
    print("🤖 LLM Provider Examples")
    print("="*50)
    
    # Note: These require API keys
    
    # OpenAI example (requires API key)
    print("OpenAI configuration:")
    openai_config = (ConfigBuilder()
                     .with_openai(api_key="your-openai-key", model="gpt-4")
                     .with_custom_prompt("Extract structured data as JSON")
                     .build())
    print("✅ OpenAI config created")
    
    # Anthropic example (requires API key)
    print("Anthropic configuration:")
    anthropic_config = (ConfigBuilder()
                       .with_anthropic(api_key="your-anthropic-key", model="claude-3-sonnet-20240229")
                       .with_content_limit(10000)
                       .build())
    print("✅ Anthropic config created")
    
    # Quick functions for different providers
    print("\nQuick functions:")
    print("webextract.extract_with_openai(url, api_key)")
    print("webextract.extract_with_anthropic(url, api_key)")


def adaptive_extraction():
    """Smart extraction that adapts based on URL."""
    print("\n" + "="*50)
    print("🎯 Adaptive Extraction")
    print("="*50)
    
    class SmartExtractor:
        def __init__(self):
            self.news_config = ConfigProfiles.news_scraping()
            self.docs_config = ConfigProfiles.documentation()
            self.ecommerce_config = ConfigProfiles.ecommerce()
            self.research_config = ConfigProfiles.research_papers()
        
        def extract_smart(self, url: str):
            """Extract with model selection based on URL patterns."""
            url_lower = url.lower()
            
            if any(pattern in url_lower for pattern in ['news', 'article', 'blog']):
                print(f"🗞️  Using news extraction for: {url}")
                extractor = WebExtractor(self.news_config)
            elif any(pattern in url_lower for pattern in ['github.com', 'docs.', 'documentation']):
                print(f"📚 Using documentation extraction for: {url}")
                extractor = WebExtractor(self.docs_config)
            elif any(pattern in url_lower for pattern in ['shop', 'store', 'product', 'buy']):
                print(f"🛒 Using e-commerce extraction for: {url}")
                extractor = WebExtractor(self.ecommerce_config)
            elif any(pattern in url_lower for pattern in ['arxiv', 'scholar', 'research', 'paper']):
                print(f"🔬 Using research extraction for: {url}")
                extractor = WebExtractor(self.research_config)
            else:
                print(f"🌐 Using default extraction for: {url}")
                extractor = WebExtractor()
            
            return extractor.extract(url)
    
    # Example usage
    smart = SmartExtractor()
    print("Created adaptive extractor")
    
    # Simulate different URL types
    example_urls = [
        "https://news.bbc.co.uk/some-article",
        "https://docs.python.org/library/",
        "https://amazon.com/product/123",
        "https://arxiv.org/paper/123"
    ]
    
    for url in example_urls:
        print(f"\nProcessing: {url}")
        # In real usage, you would call: smart.extract_smart(url)
        print("  → Would select appropriate extraction strategy")


def environment_config():
    """Environment-based configuration."""
    print("\n" + "="*50)
    print("🌍 Environment Configuration")
    print("="*50)
    
    print("Set these environment variables:")
    print("export WEBEXTRACT_MODEL='llama3:8b'")
    print("export WEBEXTRACT_REQUEST_TIMEOUT='45'")
    print("export WEBEXTRACT_MAX_CONTENT='8000'")
    print("export WEBEXTRACT_LLM_PROVIDER='ollama'")
    print("export WEBEXTRACT_LLM_BASE_URL='http://localhost:11434'")
    
    # Load config from environment
    from webextract.config.settings import WebExtractConfig
    env_config = WebExtractConfig.from_env()
    print(f"\n✅ Environment config loaded:")
    print(f"   Model: {env_config.llm.model_name}")
    print(f"   Provider: {env_config.llm.provider}")
    print(f"   Timeout: {env_config.scraping.request_timeout}s")


def main():
    """Run all examples."""
    try:
        basic_usage()
        configuration_examples()
        llm_provider_examples()
        adaptive_extraction()
        environment_config()
        
        print("\n" + "="*50)
        print("✅ All examples completed successfully!")
        print("🚀 You're ready to use WebExtract!")
        print("="*50)
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure WebExtract is installed: pip install webextract")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Check your configuration and try again")


if __name__ == "__main__":
    main() 