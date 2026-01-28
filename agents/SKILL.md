---
name: hirebase-cli
description: Interact with the Hirebase Jobs API via command line. Search jobs and companies, get detailed information, and retrieve shareable links. Use when the user asks about job searches, hiring data, company lookups, or needs job/company information to share.
---

# Hirebase CLI

Command line tool for interacting with the Hirebase Jobs API. Designed for agents to search, explore, and share job and company data.

## Prerequisites

```bash
export HIREBASE_API_URL="https://api.hirebase.org"
export HIREBASE_API_KEY="your-api-key"
```

## Agent Workflow

The CLI is designed for a **search → get details → share** workflow:

### 1. Search (Discover Data)

Search returns lists with **slugs** for further exploration:

```bash
# Search jobs
hirebase jobs search --keywords "Python" --locations "San Francisco, CA, US"

# Search companies
hirebase companies search --query "AI startup"
```

Output includes:
- **Slugs**: Use these to get more details (e.g., `company_slug`, `job_slug`)
- **IDs**: Alternative identifiers for API calls
- **Links**: Hirebase URLs for sharing

### 2. Get Details (Explore Further)

Use slugs or IDs from search results to get full information:

```bash
# Get job details by ID
hirebase jobs get <job_id>

# Get job by slugs
hirebase jobs get-by-slug <company_slug> <job_slug>

# Get company details (includes jobs)
hirebase companies get <company_slug>
```

Detail views include:
- Full descriptions and requirements
- All metadata (salary, location, technologies, etc.)
- **Hirebase links** for sharing
- **Application links** for jobs
- **CLI hints** for related commands

### 3. Share (Communicate Data)

When sharing job or company info with users, include:
- **Hirebase link**: `https://www.hirebase.org/company/{company_slug}/job/{job_slug}`
- **Application link**: Direct apply URL (for jobs)
- Key details: title, company, salary, location, requirements

## Quick Reference

| Command | Purpose |
|---------|---------|
| `hirebase --version` | Show CLI version |
| `hirebase search <query>` | Quick job search shortcut |
| `hirebase jobs search` | Search jobs with filters |
| `hirebase jobs get <id>` | Get full job details by ID |
| `hirebase jobs get-by-slug <company> <job>` | Get job by slugs |
| `hirebase companies search` | Search companies |
| `hirebase companies get <slug>` | Get company details + jobs |
| `hirebase companies jobs <slug>` | List all jobs at a company |
| `hirebase blog list` | List blog articles (shows slug + ID) |
| `hirebase blog get <slug>` | Get article by slug |
| `hirebase blog create` | Create a new article |
| `hirebase blog update <id>` | Update article by ID |
| `hirebase blog delete <id>` | Delete article by ID |
| `hirebase scraper events` | Query scraper events |
| `hirebase health` | Check API health status |

## Jobs Commands

### Search Jobs

```bash
hirebase jobs search \
  --titles "Software Engineer,Data Scientist" \
  --keywords "Python,AWS" \
  --company "Startup,AI" \
  --locations "San Francisco, California, United States" \
  --days 30 \
  --sort relevance \
  --order desc \
  --limit 10
```

**Options:**
- `-t, --titles`: Job titles (comma-separated)
- `-k, --keywords`: Search keywords (comma-separated)
- `-c, --company`: Company keywords (comma-separated)
- `-l, --locations`: Location filter (see Location Formats below)
- `-d, --days`: Posted within N days
- `-s, --sort`: Sort by: `relevance` or `date_posted` (default: relevance)
- `-o, --order`: Sort order: `asc` or `desc` (default: desc)
- `-p, --page`: Page number
- `--limit`: Results per page (max 100)
- `-f, --full-info`: Show all fields (type, technologies, etc.)
- `-j, --json`: Output raw JSON

### Get Job Details

```bash
# By ID (from search results)
hirebase jobs get 6958cfd211e2763c3491ef8b

# By slugs (from search results)
hirebase jobs get-by-slug scale-ai software-engineer-infrastructure-security
```

Returns full job info including:
- Hirebase link for sharing
- Application link
- Salary, location, requirements
- Company slug for further exploration

## Companies Commands

### Search Companies

```bash
hirebase companies search \
  --names "Scale AI,OpenAI,Anthropic" \
  --keywords "AI,machine learning,startup" \
  --industries "Tech, Software & IT Services"
```

**Options:**
- `-n, --names`: Company names to search for (comma-separated)
- `-k, --keywords`: Keywords to search for (comma-separated)
- `-l, --location`: Location filter
- `-i, --industries`: Industries (comma-separated)
- `--subindustries`: Subindustries (comma-separated)
- `-t, --types`: Company types (comma-separated)
- `--job-board`: Filter by job board source
- `-p, --page`: Page number
- `--limit`: Results per page (max 100)
- `-j, --json`: Output raw JSON

### Get Company Details

```bash
hirebase companies get nextdoor
```

Returns:
- Company info (description, size, industries)
- Hirebase company link
- LinkedIn link
- Sample of current job listings
- Slugs for CLI commands

### Get Company Jobs

```bash
hirebase companies jobs motherduck
```

## Blog Commands

Manage blog articles. Use **slugs** to get articles, **IDs** to update them.

### List Articles

```bash
hirebase blog list
hirebase blog list --status published
hirebase blog list --category "Career Advice"
hirebase blog list --tag "jobs"
hirebase blog list --limit 20
```

**Options:**
- `-s, --status`: Filter by status (draft, published)
- `-c, --category`: Filter by category
- `-t, --tag`: Filter by tag
- `--skip`: Number of articles to skip
- `-l, --limit`: Number of articles to return (default 10)

Output shows both **slug** (for get) and **ID** (for update).

### Get Article

```bash
hirebase blog get test-article
```

### Create Article

```bash
hirebase blog create \
  --title "Job Search Tips" \
  --slug "job-search-tips" \
  --author "John Doe" \
  --content-file article.md \
  --image "https://example.com/image.jpg" \
  --category "Career Advice" \
  --tags "jobs,career,tips" \
  --status published \
  --featured
```

**Required options:**
- `-t, --title`: Article title
- `-s, --slug`: URL slug (used in article URL)
- `-a, --author`: Author name
- `--image`: Featured image URL
- `--category`: Article category
- Content: Use `--content "markdown..."` or `--content-file article.md`

**Optional options:**
- `--tags`: Comma-separated tags
- `--status`: `draft` (default) or `published`
- `--featured`: Mark as featured article
- `--meta-title`: SEO meta title (defaults to title)
- `--meta-description`: SEO meta description
- `--og-image`: Open Graph image URL (defaults to image)

### Update Article

Update by **ID** (get the ID from `hirebase blog list`):

```bash
hirebase blog update 6860d187ebeef99a0a84a35b --title "Updated Title"
hirebase blog update 6860d187ebeef99a0a84a35b --status published
hirebase blog update 6860d187ebeef99a0a84a35b --content-file new-content.md
```

### Delete Article

Delete by **ID** (get the ID from `hirebase blog list`):

```bash
# With confirmation prompt
hirebase blog delete 6860d187ebeef99a0a84a35b

# Skip confirmation
hirebase blog delete 6860d187ebeef99a0a84a35b --force
```

## Scraper Commands

Monitor and query scraper events.

### Query Scraper Events

```bash
hirebase scraper events \
  --spider greenhouse \
  --status COMPLETED \
  --start 7d \
  --limit 20
```

**Options:**
- `-s, --spider`: Filter by spider name (e.g., greenhouse, lever, ashby)
- `--status`: Filter by scraper status (see below)
- `--start`: Start time filter (ISO format or relative: `1d`, `1h`, `30m`, `1w`). Default: 90 days.
- `--end`: End time filter (ISO format or relative). Omit for no time limit.
- `--close-reason`: Filter by close reason
- `--min-items`: Minimum items scraped
- `--pid`: Process ID filter
- `--server`: Server name filter
- `-l, --limit`: Number of results (default 10)
- `-f, --full-info`: Show all fields
- `-j, --json`: Output raw JSON

**Scraper Status Values:**

| Status | Description |
|--------|-------------|
| `RUNNING` | Scraper is currently active |
| `COMPLETED` | Scraper finished successfully |
| `STOPPED` | Scraper was manually stopped |
| `FAILED` | Scraper encountered a fatal error |
| `INTERRUPTED` | Scraper was interrupted (e.g., system restart) |
| `ZOMBIE_CRASHED` | Scraper liveness check failed and completion deadline was exceeded |

**Examples:**

```bash
# Check currently running scrapers (no time limit)
hirebase scraper events --status RUNNING

# Find ALL failed scrapers (no time limit)
hirebase scraper events --status FAILED --limit 100

# Find failed scrapers in the last 24 hours
hirebase scraper events --status FAILED --start 1d

# Check greenhouse scraper completions this week
hirebase scraper events --spider greenhouse --status COMPLETED --start 7d

# Find all scrapers that crashed (no time limit)
hirebase scraper events --status ZOMBIE_CRASHED --limit 100
```

## Health Check

Verify the API is online and get the current version:

```bash
hirebase health
hirebase health --json
```

## Location Formats

```bash
# Simple
--locations "San Francisco, California, United States"

# Key-value
--locations "city:San Francisco,region:CA,country:US"

# JSON (for multiple)
--locations '[{"city": "SF", "region": "CA", "country": "US"}]'
```

## Output Formats

- **Default**: ASCII tables with key info + slugs + links
- `-f, --full-info`: Show all available fields
- `-j, --json`: Raw JSON for programmatic use

## Example Agent Session

```bash
# 1. User asks for Python jobs in SF
hirebase jobs search --keywords "Python" -l "San Francisco, CA, US" --days 7

# 2. Agent sees interesting job, gets details using ID from results
hirebase jobs get 6958cfd211e2763c3491ef8b

# 3. Agent wants to know more about the company
hirebase companies get scale-ai

# 4. Agent shares with user:
#    - Job title & company
#    - Hirebase link: https://www.hirebase.org/company/scale-ai/job/software-engineer
#    - Apply link: (direct application URL)
#    - Key requirements and salary
```

## Important Notes

- **Slugs are stable identifiers**: Use `company_slug` and `job_slug` for reliable lookups
- **Links are for sharing**: Include Hirebase URLs when communicating job/company info to users
- **IDs for updates**: Blog articles require IDs for update/delete operations
- **JSON for integration**: Use `--json` when you need structured data for processing
- **Pagination**: Use `--page` and `--limit` to navigate through large result sets
- **Full info**: Use `-f, --full-info` to see all available fields in table output

## Error Handling

If a command fails, the CLI returns exit code 1 with an error message. Common issues:
- Missing environment variables (`HIREBASE_API_URL`, `HIREBASE_API_KEY`)
- Invalid API key or network issues
- Resource not found (invalid slug or ID)
