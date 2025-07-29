# Wikipedia MCP Server

[![smithery badge](https://smithery.ai/badge/@Rudra-ravi/wikipedia-mcp)](https://smithery.ai/server/@Rudra-ravi/wikipedia-mcp)

A Model Context Protocol (MCP) server that retrieves information from Wikipedia to provide context to Large Language Models (LLMs). This tool helps AI assistants access factual information from Wikipedia to ground their responses in reliable sources.

![image](https://github.com/user-attachments/assets/e41382f7-111a-4105-97f3-7851c906843e)


## Overview

The Wikipedia MCP server provides real-time access to Wikipedia information through a standardized Model Context Protocol interface. This allows LLMs to retrieve accurate and up-to-date information directly from Wikipedia to enhance their responses.

## Verified By

[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/rudra-ravi-wikipedia-mcp-badge.png)](https://mseep.ai/app/rudra-ravi-wikipedia-mcp)

## Features

- **Search Wikipedia**: Find articles matching specific queries
- **Retrieve Article Content**: Get full article text with all information
- **Article Summaries**: Get concise summaries of articles
- **Section Extraction**: Retrieve specific sections from articles
- **Link Discovery**: Find links within articles to related topics
- **Related Topics**: Discover topics related to a specific article
- **Multi-language Support**: Access Wikipedia in different languages

## Installation

### From PyPI (Recommended)

The easiest way to install the Wikipedia MCP server is directly from PyPI:

```bash
pip install wikipedia-mcp
```

This will install the latest stable version.

### Installing via Smithery

To install wikipedia-mcp for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@Rudra-ravi/wikipedia-mcp):

```bash
npx -y @smithery/cli install @Rudra-ravi/wikipedia-mcp --client claude
```

### Using pipx (Recommended)

```bash
# Install pipx if you don't have it
sudo apt install pipx
pipx ensurepath

# Install the Wikipedia MCP server
pipx install git+https://github.com/rudra-ravi/wikipedia-mcp.git
```

### Using a virtual environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install the package
pip install git+https://github.com/rudra-ravi/wikipedia-mcp.git
```

### From source

```bash
# Clone the repository
git clone https://github.com/rudra-ravi/wikipedia-mcp.git
cd wikipedia-mcp

# Create a virtual environment
python3 -m venv wikipedia-mcp-env
source wikipedia-mcp-env/bin/activate

# Install in development mode
pip install -e .
```

## Usage

### Running the server

```bash
# If installed with pipx
wikipedia-mcp

# If installed in a virtual environment
source venv/bin/activate
wikipedia-mcp

# Specify transport protocol (default: stdio)
wikipedia-mcp --transport stdio  # For Claude Desktop
wikipedia-mcp --transport sse    # For HTTP streaming

# Specify language (default: en for English)
# wikipedia-mcp --language ja  # Example for Japanese
```

### Configuration for Claude Desktop

Add the following to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "wikipedia": {
      "command": "wikipedia-mcp"
    }
  }
}
```

Location of the configuration file:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%/Claude/claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

## Available MCP Tools

The Wikipedia MCP server provides the following tools for LLMs to interact with Wikipedia:

### `search_wikipedia`

Search Wikipedia for articles matching a query.

**Parameters:**
- `query` (string): The search term
- `limit` (integer, optional): Maximum number of results to return (default: 10)

**Returns:**
- A list of search results with titles, snippets, and metadata

### `get_article`

Get the full content of a Wikipedia article.

**Parameters:**
- `title` (string): The title of the Wikipedia article

**Returns:**
- Article content including text, summary, sections, links, and categories

### `get_summary`

Get a concise summary of a Wikipedia article.

**Parameters:**
- `title` (string): The title of the Wikipedia article

**Returns:**
- A text summary of the article

### `get_sections`

Get the sections of a Wikipedia article.

**Parameters:**
- `title` (string): The title of the Wikipedia article

**Returns:**
- A structured list of article sections with their content

### `get_links`

Get the links contained within a Wikipedia article.

**Parameters:**
- `title` (string): The title of the Wikipedia article

**Returns:**
- A list of links to other Wikipedia articles

### `get_related_topics`

Get topics related to a Wikipedia article based on links and categories.

**Parameters:**
- `title` (string): The title of the Wikipedia article
- `limit` (integer, optional): Maximum number of related topics (default: 10)

**Returns:**
- A list of related topics with relevance information

### `summarize_article_for_query`

Get a summary of a Wikipedia article tailored to a specific query.

**Parameters:**
- `title` (string): The title of the Wikipedia article
- `query` (string): The query to focus the summary on
- `max_length` (integer, optional): Maximum length of the summary (default: 250)

**Returns:**
- A dictionary containing the title, query, and the focused summary

### `summarize_article_section`

Get a summary of a specific section of a Wikipedia article.

**Parameters:**
- `title` (string): The title of the Wikipedia article
- `section_title` (string): The title of the section to summarize
- `max_length` (integer, optional): Maximum length of the summary (default: 150)

**Returns:**
- A dictionary containing the title, section title, and the section summary

### `extract_key_facts`

Extract key facts from a Wikipedia article, optionally focused on a specific topic within the article.

**Parameters:**
- `title` (string): The title of the Wikipedia article
- `topic_within_article` (string, optional): A specific topic within the article to focus fact extraction
- `count` (integer, optional): Number of key facts to extract (default: 5)

**Returns:**
- A dictionary containing the title, topic, and a list of extracted facts

## Example Prompts

Once the server is running and configured with Claude Desktop, you can use prompts like:

- "Tell me about quantum computing using the Wikipedia information."
- "Summarize the history of artificial intelligence based on Wikipedia."
- "What does Wikipedia say about climate change?"
- "Find Wikipedia articles related to machine learning."
- "Get me the introduction section of the article on neural networks from Wikipedia."

## MCP Resources

The server also provides MCP resources (similar to HTTP endpoints but for MCP):

- `search/{query}`: Search Wikipedia for articles matching the query
- `article/{title}`: Get the full content of a Wikipedia article
- `summary/{title}`: Get a summary of a Wikipedia article
- `sections/{title}`: Get the sections of a Wikipedia article
- `links/{title}`: Get the links in a Wikipedia article
- `summary/{title}/query/{query}/length/{max_length}`: Get a query-focused summary of an article
- `summary/{title}/section/{section_title}/length/{max_length}`: Get a summary of a specific article section
- `facts/{title}/topic/{topic_within_article}/count/{count}`: Extract key facts from an article

## Development

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/rudra-ravi/wikipedia-mcp.git
cd wikipedia-mcp

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the package in development mode
pip install -e .

# Install development and test dependencies
pip install -r requirements-dev.txt

# Run the server
wikipedia-mcp
```

### Project Structure

- `wikipedia_mcp/`: Main package
  - `__main__.py`: Entry point for the package
  - `server.py`: MCP server implementation
  - `wikipedia_client.py`: Wikipedia API client
  - `api/`: API implementation
  - `core/`: Core functionality
  - `utils/`: Utility functions
- `tests/`: Test suite
  - `test_basic.py`: Basic package tests
  - `test_cli.py`: Command-line interface tests
  - `test_server_tools.py`: Comprehensive server and tool tests

## Testing

The project includes a comprehensive test suite to ensure reliability and functionality.

### Test Structure

The test suite is organized in the `tests/` directory with the following test files:

- **`test_basic.py`**: Basic package functionality tests
- **`test_cli.py`**: Command-line interface and transport tests
- **`test_server_tools.py`**: Comprehensive tests for all MCP tools and Wikipedia client functionality

### Running Tests

#### Run All Tests
```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
python -m pytest tests/ -v

# Run tests with coverage
python -m pytest tests/ --cov=wikipedia_mcp --cov-report=html
```

#### Run Specific Test Categories
```bash
# Run only unit tests (excludes integration tests)
python -m pytest tests/ -v -m "not integration"

# Run only integration tests (requires internet connection)
python -m pytest tests/ -v -m "integration"

# Run specific test file
python -m pytest tests/test_server_tools.py -v
```

### Test Categories

#### Unit Tests
- **WikipediaClient Tests**: Mock-based tests for all client methods
  - Search functionality
  - Article retrieval
  - Summary extraction
  - Section parsing
  - Link extraction
  - Related topics discovery
- **Server Tests**: MCP server creation and tool registration
- **CLI Tests**: Command-line interface functionality

#### Integration Tests
- **Real API Tests**: Tests that make actual calls to Wikipedia API
- **End-to-End Tests**: Complete workflow testing

### Test Configuration

The project uses `pytest.ini` for test configuration:

```ini
[pytest]
markers =
    integration: marks tests as integration tests (may require network access)
    slow: marks tests as slow running

testpaths = tests
addopts = -v --tb=short
```

### Continuous Integration

All tests are designed to:
- Run reliably in CI/CD environments
- Handle network failures gracefully
- Provide clear error messages
- Cover edge cases and error conditions

### Adding New Tests

When contributing new features:

1. Add unit tests for new functionality
2. Include both success and failure scenarios
3. Mock external dependencies (Wikipedia API)
4. Add integration tests for end-to-end validation
5. Follow existing test patterns and naming conventions

## Troubleshooting

### Common Issues

- **Connection Error**: Ensure the command in claude_desktop_config.json is correct
- **Article Not Found**: Check the exact spelling of article titles
- **Rate Limiting**: Wikipedia API has rate limits; consider adding delays between requests
- **Large Articles**: Some Wikipedia articles are very large and may exceed token limits

## Understanding the Model Context Protocol (MCP)

The Model Context Protocol (MCP) is not a traditional HTTP API but a specialized protocol for communication between LLMs and external tools. Key characteristics:

- Uses stdio (standard input/output) or SSE (Server-Sent Events) for communication
- Designed specifically for AI model interaction
- Provides standardized formats for tools, resources, and prompts
- Integrates directly with Claude and other MCP-compatible AI systems

Claude Desktop acts as the MCP client, while this server provides the tools and resources that Claude can use to access Wikipedia information.

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Connect with the Author

- 🌐 Portfolio: [ravikumar-dev.me](https://ravikumar-dev.me)
- 📝 Blog: [Medium](https://medium.com/@Ravikumar-e)
- 💼 LinkedIn: [in/ravi-kumar-e](https://linkedin.com/in/ravi-kumar-e)
- 🐦 Twitter: [@Ravikumar_d3v](https://twitter.com/Ravikumar_d3v) 
