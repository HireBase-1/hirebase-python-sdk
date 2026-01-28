"""Blog commands for the Hirebase CLI."""

import json
from typing import Optional
from datetime import datetime

import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm

from ..client import get_client, APIError
from ..formatters import (
    format_articles_table, format_article_detail,
    format_error, format_success, format_json, console
)

app = typer.Typer(name="blog", help="Manage blog articles")


@app.command("list")
def list_articles(
    status: Optional[str] = typer.Option(
        None, "--status", "-s",
        help="Filter by status: draft or published"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-c",
        help="Filter by category"
    ),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t",
        help="Filter by tag"
    ),
    skip: int = typer.Option(0, "--skip", help="Number of articles to skip"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of articles to return"),
    full_info: bool = typer.Option(
        False, "--full-info", "-f",
        help="Show full information for each article"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """List blog articles with optional filters."""
    try:
        client = get_client()
        result = client.list_articles(
            status=status,
            category=category,
            tag=tag,
            skip=skip,
            limit=limit,
        )
        
        if output_json:
            format_json(result)
        else:
            format_articles_table(result, full_info=full_info)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("get")
def get_article(
    slug: str = typer.Argument(..., help="Article slug to retrieve"),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Get a blog article by its slug."""
    try:
        client = get_client()
        result = client.get_article(slug)
        
        if output_json:
            format_json(result)
        else:
            format_article_detail(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("create")
def create_article(
    title: str = typer.Option(..., "--title", "-t", help="Article title"),
    slug: str = typer.Option(..., "--slug", "-s", help="URL slug"),
    author: str = typer.Option(..., "--author", "-a", help="Author name"),
    content: Optional[str] = typer.Option(
        None, "--content", "-c",
        help="Article content (markdown). Use @file.md to read from file"
    ),
    content_file: Optional[str] = typer.Option(
        None, "--content-file", "-cf",
        help="Path to file containing article content (markdown)"
    ),
    image_url: str = typer.Option(..., "--image", help="Featured image URL"),
    category: str = typer.Option(..., "--category", help="Article category"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
    meta_title: Optional[str] = typer.Option(None, "--meta-title", help="SEO meta title"),
    meta_description: Optional[str] = typer.Option(None, "--meta-description", help="SEO meta description"),
    og_image: Optional[str] = typer.Option(None, "--og-image", help="Open Graph image URL"),
    status: str = typer.Option("draft", "--status", help="Status: draft or published"),
    featured: bool = typer.Option(False, "--featured", help="Mark as featured article"),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Create a new blog article."""
    try:
        # Handle content from file
        article_content = content
        if content_file:
            with open(content_file, "r") as f:
                article_content = f.read()
        elif content and content.startswith("@"):
            with open(content[1:], "r") as f:
                article_content = f.read()
        
        if not article_content:
            format_error("Content is required. Use --content or --content-file")
            raise typer.Exit(1)
        
        # Calculate read time (rough estimate: 200 words per minute)
        word_count = len(article_content.split())
        time_to_read = max(1, word_count // 200)
        
        # Parse tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
        
        article_data = {
            "title": title,
            "slug": slug,
            "author": author,
            "content": article_content,
            "image_url": image_url,
            "time_to_read": time_to_read,
            "category": category,
            "tags": tag_list,
            "table_of_contents": [],
            "meta_title": meta_title or title,
            "meta_description": meta_description or "",
            "og_image": og_image or image_url,
            "status": status,
            "featured": featured,
        }
        
        client = get_client()
        result = client.create_article(article_data)
        
        if output_json:
            format_json(result)
        else:
            format_success(f"Article created: {result.get('slug', slug)}")
            format_article_detail(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        format_error(f"File not found: {e}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("update")
def update_article(
    article_id: str = typer.Argument(..., help="Article ID to update (from 'blog list')"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Article title"),
    author: Optional[str] = typer.Option(None, "--author", "-a", help="Author name"),
    content: Optional[str] = typer.Option(None, "--content", "-c", help="Article content (markdown)"),
    content_file: Optional[str] = typer.Option(None, "--content-file", "-cf", help="Path to content file"),
    image_url: Optional[str] = typer.Option(None, "--image", help="Featured image URL"),
    category: Optional[str] = typer.Option(None, "--category", help="Article category"),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    meta_title: Optional[str] = typer.Option(None, "--meta-title", help="SEO meta title"),
    meta_description: Optional[str] = typer.Option(None, "--meta-description", help="SEO meta description"),
    og_image: Optional[str] = typer.Option(None, "--og-image", help="Open Graph image URL"),
    status: Optional[str] = typer.Option(None, "--status", help="Status: draft or published"),
    featured: Optional[bool] = typer.Option(None, "--featured/--no-featured", help="Mark as featured"),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Update an existing blog article by ID.
    
    Get the article ID from 'hirebase blog list'. The full BlogArticle is required,
    so this command fetches the existing article first and merges your updates.
    """
    try:
        client = get_client()
        
        # First, fetch all articles to find the one with matching ID
        # (API doesn't have a get-by-id endpoint, so we need to search)
        articles = client.list_articles(limit=100)
        existing = None
        for article in articles:
            if article.get("_id") == article_id:
                existing = article
                break
        
        if not existing:
            format_error(f"Could not find article with ID: {article_id}")
            raise typer.Exit(1)
        
        # Handle content from file
        article_content = content
        if content_file:
            with open(content_file, "r") as f:
                article_content = f.read()
        elif content and content.startswith("@"):
            with open(content[1:], "r") as f:
                article_content = f.read()
        
        # Start with existing data and merge updates
        update_data = {
            "title": existing.get("title"),
            "slug": existing.get("slug"),
            "author": existing.get("author"),
            "content": existing.get("content"),
            "image_url": existing.get("image_url"),
            "time_to_read": existing.get("time_to_read", 1),
            "category": existing.get("category"),
            "tags": existing.get("tags", []),
            "table_of_contents": existing.get("table_of_contents", []),
            "meta_title": existing.get("meta_title"),
            "meta_description": existing.get("meta_description"),
            "og_image": existing.get("og_image"),
            "status": existing.get("status", "draft"),
            "featured": existing.get("featured", False),
            "view_count": existing.get("view_count", 0),
            "created_at": existing.get("created_at"),
            "published_at": existing.get("published_at"),
        }
        
        # Apply updates
        if title is not None:
            update_data["title"] = title
        if author is not None:
            update_data["author"] = author
        if article_content is not None:
            update_data["content"] = article_content
            word_count = len(article_content.split())
            update_data["time_to_read"] = max(1, word_count // 200)
        if image_url is not None:
            update_data["image_url"] = image_url
        if category is not None:
            update_data["category"] = category
        if tags is not None:
            update_data["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
        if meta_title is not None:
            update_data["meta_title"] = meta_title
        if meta_description is not None:
            update_data["meta_description"] = meta_description
        if og_image is not None:
            update_data["og_image"] = og_image
        if status is not None:
            update_data["status"] = status
            if status == "published" and not existing.get("published_at"):
                update_data["published_at"] = datetime.utcnow().isoformat()
        if featured is not None:
            update_data["featured"] = featured
        
        # Update timestamp
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = client.update_article(article_id, update_data)
        
        if output_json:
            format_json(result)
        else:
            format_success(f"Article updated: {existing.get('slug', article_id)}")
            format_article_detail(result)
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except FileNotFoundError as e:
        format_error(f"File not found: {e}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)


@app.command("delete")
def delete_article(
    article_id: str = typer.Argument(..., help="Article ID to delete (from 'blog list')"),
    force: bool = typer.Option(
        False, "--force", "-y",
        help="Skip confirmation prompt"
    ),
    output_json: bool = typer.Option(
        False, "--json", "-j",
        help="Output raw JSON response"
    ),
):
    """Delete a blog article by ID.
    
    Get the article ID from 'hirebase blog list'.
    """
    try:
        client = get_client()
        
        # First, find the article to show what will be deleted
        articles = client.list_articles(limit=100)
        article = None
        for a in articles:
            if a.get("_id") == article_id:
                article = a
                break
        
        if not article:
            format_error(f"Could not find article with ID: {article_id}")
            raise typer.Exit(1)
        
        # Confirm deletion unless --force is used
        if not force:
            console.print(f"\n[yellow]About to delete:[/yellow]")
            console.print(f"  Title: {article.get('title', 'N/A')}")
            console.print(f"  Slug: {article.get('slug', 'N/A')}")
            console.print(f"  Status: {article.get('status', 'N/A')}")
            console.print("")
            
            confirm = typer.confirm("Are you sure you want to delete this article?")
            if not confirm:
                console.print("[dim]Deletion cancelled.[/dim]")
                raise typer.Exit(0)
        
        result = client.delete_article(article_id)
        
        if output_json:
            format_json(result)
        else:
            format_success(f"Article deleted: {article.get('slug', article_id)}")
    
    except APIError as e:
        format_error(f"API Error: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        format_error(f"Error: {e}")
        raise typer.Exit(1)
