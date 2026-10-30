"""
Knowledge Extraction & Entity Enrichment Engine
Detects GitHub repositories, Claude Skills, AI tools, Books, URLs, emails, and code snippets.
"""
import re
from typing import Any
from pydantic import BaseModel, Field


GITHUB_REGEX = re.compile(r"https?://(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)", re.IGNORECASE)
URL_REGEX = re.compile(r"https?://(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?", re.IGNORECASE)
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
BOOK_REGEX = re.compile(r"(?:book|reading|read):\s*([^\n,]+)(?:by\s+([^\n,]+))?", re.IGNORECASE)


class ExtractedEntities(BaseModel):
    github_repos: list[dict[str, str]] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    emails: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    books: list[dict[str, str]] = Field(default_factory=list)
    ai_tools: list[str] = Field(default_factory=list)
    code_snippets: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class KnowledgeExtractor:
    KNOWN_AI_TERMS = [
        "claude skill", "claude code", "agent skill", "mcp server", "fastmcp",
        "langgraph", "langchain", "autogen", "crewai", "gemini flash",
        "gemini pro", "chatgpt", "gpt-4", "gemma", "ollama", "vllm"
    ]

    @classmethod
    def extract_from_text(cls, text: str) -> ExtractedEntities:
        if not text:
            return ExtractedEntities()

        entities = ExtractedEntities()

        # 1. GitHub Repositories
        seen_repos = set()
        for match in GITHUB_REGEX.finditer(text):
            owner, repo = match.group(1), match.group(2).rstrip(".,;")
            full_url = f"https://github.com/{owner}/{repo}"
            if full_url not in seen_repos:
                seen_repos.add(full_url)
                entities.github_repos.append({
                    "url": full_url,
                    "owner": owner,
                    "repo": repo,
                    "title": f"{owner}/{repo}"
                })

        # 2. General URLs
        for match in URL_REGEX.finditer(text):
            url = match.group(0).rstrip(".,;)")
            if not any(r["url"] == url for r in entities.github_repos):
                if url not in entities.urls:
                    entities.urls.append(url)

        # 3. Emails
        for match in EMAIL_REGEX.finditer(text):
            email = match.group(0)
            if email not in entities.emails:
                entities.emails.append(email)

        # 4. Phone numbers
        for match in PHONE_REGEX.finditer(text):
            phone = match.group(0).strip()
            if phone not in entities.phone_numbers:
                entities.phone_numbers.append(phone)

        # 5. AI Tools & Claude Skills
        text_lower = text.lower()
        for term in cls.KNOWN_AI_TERMS:
            if term in text_lower:
                entities.ai_tools.append(term.title())

        # 6. Books
        for line in text.splitlines():
            line_str = line.strip()
            if "book" in line_str.lower() or "author" in line_str.lower():
                match = BOOK_REGEX.search(line_str)
                if match:
                    title = match.group(1).strip()
                    author = (match.group(2) or "Unknown").strip()
                    entities.books.append({"title": title, "author": author})
                elif "by" in line_str and ("read" in line_str.lower() or "book" in line_str.lower()):
                    parts = line_str.split("by")
                    title = parts[0].replace("Book:", "").replace("book:", "").strip()
                    author = parts[1].strip() if len(parts) > 1 else "Unknown"
                    entities.books.append({"title": title, "author": author})

        # 7. Code snippets (lines starting with import, def, class, const, let, git, curl, pip)
        code_lines = []
        for line in text.splitlines():
            s = line.strip()
            if s.startswith(("import ", "from ", "def ", "class ", "git clone", "pip install", "curl ", "npm install", "const ", "let ")):
                code_lines.append(s)
        if code_lines:
            entities.code_snippets.append("\n".join(code_lines))

        # 8. Derive Tags
        tags = set()
        if entities.github_repos:
            tags.add("GitHub")
            tags.add("Open Source")
        if entities.ai_tools:
            tags.add("AI & Automation")
        if entities.books:
            tags.add("Books & Learning")
        if entities.code_snippets:
            tags.add("Programming")

        entities.tags = sorted(list(tags))
        return entities
