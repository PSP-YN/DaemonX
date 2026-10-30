"""
SQLite Database Schema and FTS5 DDL
"""

SCHEMA_SQL = """
-- Media Items (Screenshots, Reels, Photos)
CREATE TABLE IF NOT EXISTS media_items (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,          -- 'screenshot', 'instagram_reel', 'image'
    original_path TEXT,
    device_path TEXT,
    sha256 TEXT UNIQUE,
    phash TEXT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    created_at REAL NOT NULL,
    processed_at REAL,
    status TEXT DEFAULT 'pending',      -- 'pending', 'processed', 'failed', 'quarantined'
    quarantine_path TEXT
);

-- Extracted Content (OCR, Captions, Summaries)
CREATE TABLE IF NOT EXISTS extracted_content (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    full_text TEXT,
    ocr_confidence REAL,
    caption TEXT,
    creator TEXT,
    source_url TEXT,
    summary TEXT,
    extracted_at REAL NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE
);

-- Resources (GitHub repositories, Claude Skills, Books, Tools, URLs)
CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    media_id TEXT,
    resource_type TEXT NOT NULL,        -- 'github_repo', 'claude_skill', 'book', 'url', 'tool'
    title TEXT NOT NULL,
    url TEXT,
    creator_or_author TEXT,
    description TEXT,
    metadata_json TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE SET NULL
);

-- Taxonomy Categories (22 core categories)
CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

-- Tags
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

-- Media Tags Mapping
CREATE TABLE IF NOT EXISTS media_tags (
    media_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    category_id TEXT,
    PRIMARY KEY (media_id, tag_id),
    FOREIGN KEY (media_id) REFERENCES media_items(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Processing Jobs (Tasks)
CREATE TABLE IF NOT EXISTS processing_jobs (
    id TEXT PRIMARY KEY,
    task_name TEXT NOT NULL,
    status TEXT NOT NULL,              -- 'pending', 'running', 'paused', 'completed', 'failed', 'cancelled'
    current_step INTEGER DEFAULT 0,
    total_steps INTEGER DEFAULT 0,
    state_json TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    completed_at REAL
);

-- Processing Errors
CREATE TABLE IF NOT EXISTS processing_errors (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    media_id TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    occurred_at REAL NOT NULL,
    FOREIGN KEY (job_id) REFERENCES processing_jobs(id) ON DELETE CASCADE
);

-- Cleanup Log
CREATE TABLE IF NOT EXISTS cleanup_log (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    action TEXT NOT NULL,              -- 'quarantine', 'restore', 'unsave', 'delete'
    original_path TEXT,
    quarantine_path TEXT,
    performed_at REAL NOT NULL,
    verified BOOLEAN DEFAULT 0,
    details TEXT
);

-- Audit Log
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    actor TEXT DEFAULT 'daemonx_agent',
    timestamp REAL NOT NULL,
    metadata_json TEXT
);

-- FTS5 Full-Text Search Virtual Table
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    media_id UNINDEXED,
    full_text,
    caption,
    creator,
    summary,
    resources,
    tags,
    tokenize = 'porter unicode61'
);

-- Triggers for FTS synchronization
CREATE TRIGGER IF NOT EXISTS trg_extracted_content_insert AFTER INSERT ON extracted_content
BEGIN
    INSERT INTO knowledge_fts (media_id, full_text, caption, creator, summary, resources, tags)
    VALUES (new.media_id, new.full_text, new.caption, new.creator, new.summary, '', '');
END;

CREATE TRIGGER IF NOT EXISTS trg_extracted_content_delete AFTER DELETE ON extracted_content
BEGIN
    DELETE FROM knowledge_fts WHERE media_id = old.media_id;
END;
"""

TAXONOMY_CATEGORIES = [
    ("cat_ai_ml", "AI and machine learning", "Foundational AI, deep learning, LLMs, neural networks"),
    ("cat_ai_agents", "AI agents and automation", "Autonomous agents, agentic workflows, multi-agent frameworks"),
    ("cat_claude", "Claude and Claude Skills", "Anthropic Claude models, prompts, skills, MCP adapters"),
    ("cat_chatgpt", "ChatGPT and GPT tools", "OpenAI ChatGPT, GPTs, prompts, OpenAI API integrations"),
    ("cat_gemini", "Gemini and Google AI", "Google Gemini, DeepMind, Gemma, Vertex AI tools"),
    ("cat_mcp", "MCP servers and agent frameworks", "Model Context Protocol servers, LangGraph, CrewAI, AutoGen"),
    ("cat_github", "GitHub repositories", "Open source GitHub software, libraries, repositories"),
    ("cat_opensource", "Open-source projects", "Self-hosted software, FLOSS, decentralized tools"),
    ("cat_tutorials", "Programming tutorials", "Code guides, software engineering walkthroughs"),
    ("cat_webdev", "Web development", "Frontend, backend, HTML, CSS, JavaScript, APIs, fullstack"),
    ("cat_mobiledev", "Mobile development", "Android, Kotlin, iOS, Swift, Flutter, React Native"),
    ("cat_cybersecurity", "Cybersecurity", "InfoSec, penetration testing, security tools, ethical hacking"),
    ("cat_devtools", "Developer tools", "IDE extensions, CLIs, terminal productivity, debuggers"),
    ("cat_books", "Books", "Technical, non-fiction, philosophy, self-development books"),
    ("cat_self_improvement", "Self-improvement", "Personal growth, mindset, habit formation"),
    ("cat_productivity", "Productivity", "Time management, workflow optimization, note-taking"),
    ("cat_psychology", "Psychology", "Cognitive psychology, mental models, behavioral science"),
    ("cat_business", "Business and entrepreneurship", "Founding companies, SaaS, marketing, sales"),
    ("cat_startup", "Startup ideas", "Product validation, venture concepts, market opportunities"),
    ("cat_education", "Education and research", "Academic papers, learning techniques, research tools"),
    ("cat_useful", "Other useful content", "Helpful life hacks, utilities, miscellaneous value"),
    ("cat_low_value", "Low-value or irrelevant content", "Memes, entertainment, spam, noise"),
]
