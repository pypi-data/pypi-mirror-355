# ModelsHub

A unified interface for various Large Language Model (LLM) providers, making it easy to work with different LLM APIs in a consistent way.

## Installation

```bash
pip install modelshub
```

## Quick Start

```python
from modelshub import Gemini, OpenAI, Groq, Anthropic

# Initialize any model
model = Gemini(api_key="your-api-key")
# or
model = OpenAI(api_key="your-api-key")
# or
model = Groq(api_key="your-api-key")
# or
model = Anthropic(api_key="your-api-key")

# Use the model
response = model.generate("What is the capital of France?")
print(response)
```

## Features

- Unified interface for multiple LLM providers
- Easy to use and extend
- Production-ready implementation
- Consistent API across different providers
- Built on top of LangChain for maximum compatibility

## Supported Models

- Google Gemini
- OpenAI
- Groq
- Anthropic Claude
- (More coming soon!)

## Environment Variables

You can set your API keys as environment variables:

```bash
export GOOGLE_API_KEY="your-google-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export GROQ_API_KEY="your-groq-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 