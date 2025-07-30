from setuptools import setup, find_packages

setup(
    name="modelshub",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-google-genai>=0.0.5",
        "langchain-openai>=0.0.2",
        "langchain-groq>=0.0.1",
        "langchain-anthropic>=0.0.1",
        "python-dotenv>=1.0.0",
    ],
    author="Munakala Bharath",
    author_email="bharathmunakala22@gmail.com",
    description="A unified interface for various LLM providers",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/modelshub",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
) 