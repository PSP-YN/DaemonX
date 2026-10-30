"""
Instagram Taxonomy Classifier across 22 Standardized Categories
"""
from daemonx.storage.schema import TAXONOMY_CATEGORIES


KEYWORD_CATEGORY_MAP = {
    "cat_ai_ml": ["ai", "machine learning", "deep learning", "llm", "neural network", "transformer", "model weights"],
    "cat_ai_agents": ["agent", "agents", "automation", "autonomous", "crewai", "langgraph", "agentic", "autogen"],
    "cat_claude": ["claude", "anthropic", "claude 3", "claude sonnet", "claude opus", "claude skill", "claude code"],
    "cat_chatgpt": ["chatgpt", "openai", "gpt-4", "gpt", "o1", "o3", "custom gpt"],
    "cat_gemini": ["gemini", "google ai", "deepmind", "gemma", "vertex ai"],
    "cat_mcp": ["mcp", "model context protocol", "mcp server", "fastmcp"],
    "cat_github": ["github", "github.com", "git clone", "repo", "repository", "open source repo"],
    "cat_opensource": ["open source", "foss", "floss", "self-hosted", "mit license", "apache 2.0"],
    "cat_tutorials": ["tutorial", "how to build", "step by step", "guide", "walkthrough", "learn to code"],
    "cat_webdev": ["web dev", "frontend", "backend", "react", "next.js", "vue", "javascript", "typescript", "css", "html"],
    "cat_mobiledev": ["android", "ios", "kotlin", "swift", "flutter", "react native", "mobile app"],
    "cat_cybersecurity": ["cybersecurity", "security", "pentest", "hacking", "vulnerability", "infosec", "exploit"],
    "cat_devtools": ["developer tool", "devtool", "terminal", "cli", "vscode", "ide", "debugger", "git"],
    "cat_books": ["book", "reading", "author", "pages", "read this book", "chapter"],
    "cat_self_improvement": ["habit", "mindset", "discipline", "focus", "growth", "self-improvement"],
    "cat_productivity": ["productivity", "notion", "workflow", "time management", "system", "efficient"],
    "cat_psychology": ["psychology", "mental model", "cognitive", "bias", "behavior"],
    "cat_business": ["business", "revenue", "saas", "sales", "marketing", "monetize", "mrr", "arr"],
    "cat_startup": ["startup", "founder", "venture", "pitch", "mvp", "product market fit"],
    "cat_education": ["education", "research paper", "arxiv", "learning", "study"],
}


class InstagramClassifier:
    @staticmethod
    def classify(text: str, caption: str = "", tags: list[str] | None = None) -> list[tuple[str, str]]:
        """
        Classifies reel content into one or more categories from the 22-category taxonomy.
        Returns list of (category_id, category_name) tuples.
        """
        combined = f"{text} {caption} {' '.join(tags or [])}".lower()
        matched = []

        cat_names = {cid: name for cid, name, _ in TAXONOMY_CATEGORIES}

        for cat_id, keywords in KEYWORD_CATEGORY_MAP.items():
            for kw in keywords:
                if kw in combined:
                    matched.append((cat_id, cat_names[cat_id]))
                    break

        if not matched:
            matched.append(("cat_useful", cat_names["cat_useful"]))

        return matched
