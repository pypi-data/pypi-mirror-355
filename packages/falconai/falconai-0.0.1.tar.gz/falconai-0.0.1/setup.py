from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    description = f.read()


setup(
    name='falconai',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'litellm',
        'langchain_community',
        'beautifulsoup4',
        'docx2txt',
        'bs4',
        'pyttsx3',
        'browser-use',
        'playwright',
        'duckduckgo-search',
        'langchain-openai',
        'langchain-anthropic',
        'langchain-google-genai',
        'httpx',
        'duckduckgo_search',
        'duckai',
        'crawl4ai',
        'mcp-use',
        'pypdf',
        'youtube-transcript-api',
        'langchain-groq',
        'langchain-xai',
        'langchain-deepseek',
        'langchain-community'
    ],
    long_description=description,
    long_description_content_type='text/markdown'
)
