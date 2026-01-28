# Hirebase CLI

Command line interface for interacting with the [Hirebase API](https://docs.hirebase.org/).

## Installation

```bash
# Clone and install in development mode
cd hirebase-cli
pip install -e .

# Or install directly
pip install hirebase-cli
```

## Configuration

Set the following environment variables:

```bash
export HIREBASE_API_URL="https://api.hirebase.org"
export HIREBASE_API_KEY="your-api-key"
```

Or create a `.env` file in your working directory:

```env
HIREBASE_API_URL=https://api.hirebase.org
HIREBASE_API_KEY=your-api-key
```

## Usage

### Quick Start

```bash
# Check version
hirebase --version

# Check API health
hirebase health

# Quick job search
hirebase search "Software Engineer" -l "San Francisco, CA, US"
```

### Jobs

```bash
# Search for jobs
hirebase jobs search --titles "Software Engineer,Data Scientist" \
  --keywords "Python,AWS" \
  --locations "San Francisco, California, United States" \
  --days 30

# Get job by ID
hirebase jobs get 6958cfd211e2763c3491ef8b

# Get job by company and job slug
hirebase jobs get-by-slug scale-ai software-engineer-infrastructure-security

# Show full information
hirebase jobs search --titles "Engineer" --full-info

# Output as JSON
hirebase jobs search --titles "Engineer" --json
```

### Companies

```bash
# Search companies
hirebase companies search --name "Scale AI"
hirebase companies search --industries "Tech, Software & IT Services"
hirebase companies search --query "AI startup" --location "San Francisco, CA, US"

# Get jobs from a company
hirebase companies jobs motherduck
```

### Blog

```bash
# List articles
hirebase blog list
hirebase blog list --full-info

# Get article by slug
hirebase blog get test-article

# Create article
hirebase blog create \
  --title "My Article" \
  --slug "my-article" \
  --author "John Doe" \
  --content-file article.md \
  --image "https://example.com/image.jpg" \
  --category "Career Advice" \
  --tags "jobs,career,tips" \
  --status published

# Update article
hirebase blog update ARTICLE_ID --title "Updated Title" --status published
```

### Scraper Admin

```bash
# Query scraper events (last 24 hours by default)
hirebase scraper events

# Filter by spider name and status
hirebase scraper events --spider greenhouse --status finished

# Use relative time filters
hirebase scraper events --start 7d  # Last 7 days
hirebase scraper events --start 1h  # Last hour
```

### Output Options

All commands support:

- `--full-info` / `-f`: Show all fields in table output
- `--json` / `-j`: Output raw JSON response
- `--help`: Show command help

### Location Formats

Locations can be specified in multiple formats:

```bash
# Simple comma-separated
--location "San Francisco, California, United States"

# Key-value format
--location "city:San Francisco,region:California,country:United States"

# JSON format
--location '{"city": "San Francisco", "region": "California", "country": "United States"}'
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT License - see LICENSE file for details.
