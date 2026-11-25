"""
Web & Productivity Services Registry for ADA.
Provides canonical destination URLs, aliases, smart resolver logic,
and conversational noise filtering for natural speech-to-text queries.
"""

import re
import urllib.parse
from typing import Optional, Dict, Any, List, Tuple

class WebService:
    def __init__(
        self,
        service_id: str,
        name: str,
        canonical_url: str,
        aliases: List[str],
        category: str,
        new_item_url: Optional[str] = None,
        search_url_template: Optional[str] = None
    ):
        self.service_id = service_id
        self.name = name
        self.canonical_url = canonical_url
        self.aliases = sorted(aliases, key=len, reverse=True)  # Match longest aliases first
        self.category = category
        self.new_item_url = new_item_url
        self.search_url_template = search_url_template

# Canonical Registry of 40+ Web Services
SERVICES_REGISTRY: List[WebService] = [
    # Google Workspace & Productivity
    WebService(
        service_id="google_docs",
        name="Google Docs",
        canonical_url="https://docs.google.com",
        new_item_url="https://docs.new",
        aliases=["google docs", "google doc", "gdocs", "gdoc", "docs.google", "docs", "doc"],
        category="productivity"
    ),
    WebService(
        service_id="google_sheets",
        name="Google Sheets",
        canonical_url="https://sheets.google.com",
        new_item_url="https://sheets.new",
        aliases=["google sheets", "google sheet", "gsheets", "gsheet", "sheets.google", "sheets", "spreadsheet", "spreadsheets"],
        category="productivity"
    ),
    WebService(
        service_id="google_slides",
        name="Google Slides",
        canonical_url="https://slides.google.com",
        new_item_url="https://slides.new",
        aliases=["google slides", "google slide", "gslides", "slides.google", "slides", "presentation"],
        category="productivity"
    ),
    WebService(
        service_id="google_drive",
        name="Google Drive",
        canonical_url="https://drive.google.com",
        aliases=["google drive", "gdrive", "drive.google", "drive"],
        category="productivity"
    ),
    WebService(
        service_id="google_forms",
        name="Google Forms",
        canonical_url="https://forms.google.com",
        new_item_url="https://forms.new",
        aliases=["google forms", "google form", "gforms", "forms.google", "forms"],
        category="productivity"
    ),
    WebService(
        service_id="gmail",
        name="Gmail",
        canonical_url="https://mail.google.com",
        aliases=["gmail", "google mail", "email", "webmail", "mail.google"],
        category="communication"
    ),
    WebService(
        service_id="google_calendar",
        name="Google Calendar",
        canonical_url="https://calendar.google.com",
        new_item_url="https://cal.new",
        aliases=["google calendar", "google cal", "gcal", "calendar.google", "calendar"],
        category="productivity"
    ),
    WebService(
        service_id="google_meet",
        name="Google Meet",
        canonical_url="https://meet.google.com",
        new_item_url="https://meet.new",
        aliases=["google meet", "gmeet", "meet.google", "meet"],
        category="communication"
    ),
    WebService(
        service_id="google_keep",
        name="Google Keep",
        canonical_url="https://keep.google.com",
        new_item_url="https://keep.new",
        aliases=["google keep", "keep notes", "keep.google", "keep docs", "keep note", "keep"],
        category="productivity"
    ),
    WebService(
        service_id="google_maps",
        name="Google Maps",
        canonical_url="https://maps.google.com",
        aliases=["google maps", "google map", "gmaps", "maps.google", "maps"],
        category="navigation"
    ),
    WebService(
        service_id="google_photos",
        name="Google Photos",
        canonical_url="https://photos.google.com",
        aliases=["google photos", "gphotos", "photos.google"],
        category="media"
    ),
    WebService(
        service_id="google_translate",
        name="Google Translate",
        canonical_url="https://translate.google.com",
        aliases=["google translate", "gtranslate", "translate.google"],
        category="utility"
    ),

    # AI Platforms
    WebService(
        service_id="chatgpt",
        name="ChatGPT",
        canonical_url="https://chatgpt.com",
        aliases=["chatgpt", "chat gpt", "openai", "chat.openai.com"],
        category="ai"
    ),
    WebService(
        service_id="claude",
        name="Claude AI",
        canonical_url="https://claude.ai",
        aliases=["claude", "claude ai", "anthropic"],
        category="ai"
    ),
    WebService(
        service_id="gemini",
        name="Google Gemini",
        canonical_url="https://gemini.google.com",
        aliases=["gemini", "google gemini", "bard"],
        category="ai"
    ),
    WebService(
        service_id="perplexity",
        name="Perplexity AI",
        canonical_url="https://www.perplexity.ai",
        aliases=["perplexity", "perplexity ai"],
        category="ai"
    ),
    WebService(
        service_id="deepseek",
        name="DeepSeek",
        canonical_url="https://chat.deepseek.com",
        aliases=["deepseek", "deep seek", "deepseek ai"],
        category="ai"
    ),

    # Developer & Code Platforms
    WebService(
        service_id="github",
        name="GitHub",
        canonical_url="https://github.com",
        new_item_url="https://repo.new",
        aliases=["github", "git hub", "github.com"],
        category="developer"
    ),
    WebService(
        service_id="gitlab",
        name="GitLab",
        canonical_url="https://gitlab.com",
        aliases=["gitlab", "git lab"],
        category="developer"
    ),
    WebService(
        service_id="stackoverflow",
        name="Stack Overflow",
        canonical_url="https://stackoverflow.com",
        aliases=["stackoverflow", "stack overflow"],
        category="developer"
    ),
    WebService(
        service_id="huggingface",
        name="Hugging Face",
        canonical_url="https://huggingface.co",
        aliases=["huggingface", "hugging face", "hf.co"],
        category="developer"
    ),
    WebService(
        service_id="leetcode",
        name="LeetCode",
        canonical_url="https://leetcode.com",
        aliases=["leetcode", "leet code"],
        category="developer"
    ),
    WebService(
        service_id="replit",
        name="Replit",
        canonical_url="https://replit.com",
        aliases=["replit", "repl.it"],
        category="developer"
    ),

    # Design & Workspace
    WebService(
        service_id="notion",
        name="Notion",
        canonical_url="https://www.notion.so",
        aliases=["notion", "notion.so"],
        category="productivity"
    ),
    WebService(
        service_id="figma",
        name="Figma",
        canonical_url="https://www.figma.com",
        aliases=["figma", "figma.com"],
        category="design"
    ),
    WebService(
        service_id="canva",
        name="Canva",
        canonical_url="https://www.canva.com",
        aliases=["canva", "canva.com"],
        category="design"
    ),
    WebService(
        service_id="trello",
        name="Trello",
        canonical_url="https://trello.com",
        aliases=["trello"],
        category="productivity"
    ),
    WebService(
        service_id="miro",
        name="Miro",
        canonical_url="https://miro.com",
        aliases=["miro"],
        category="productivity"
    ),

    # Media & Social
    WebService(
        service_id="youtube",
        name="YouTube",
        canonical_url="https://www.youtube.com",
        search_url_template="https://www.youtube.com/results?search_query={query}",
        aliases=["youtube", "you tube", "yt"],
        category="media"
    ),
    WebService(
        service_id="youtube_music",
        name="YouTube Music",
        canonical_url="https://music.youtube.com",
        aliases=["youtube music", "yt music"],
        category="media"
    ),
    WebService(
        service_id="spotify_web",
        name="Spotify Web",
        canonical_url="https://open.spotify.com",
        aliases=["spotify web", "open spotify"],
        category="media"
    ),
    WebService(
        service_id="reddit",
        name="Reddit",
        canonical_url="https://www.reddit.com",
        aliases=["reddit", "reddit.com"],
        category="social"
    ),
    WebService(
        service_id="twitter_x",
        name="X / Twitter",
        canonical_url="https://x.com",
        aliases=["twitter", "x.com", "tweets"],
        category="social"
    ),
    WebService(
        service_id="linkedin",
        name="LinkedIn",
        canonical_url="https://www.linkedin.com",
        aliases=["linkedin", "linked in"],
        category="social"
    ),
    WebService(
        service_id="whatsapp_web",
        name="WhatsApp Web",
        canonical_url="https://web.whatsapp.com",
        aliases=["whatsapp web", "web whatsapp", "wa web"],
        category="communication"
    ),
    WebService(
        service_id="discord_web",
        name="Discord Web",
        canonical_url="https://discord.com/app",
        aliases=["discord web", "discord in browser"],
        category="communication"
    ),
    WebService(
        service_id="netflix",
        name="Netflix",
        canonical_url="https://www.netflix.com",
        aliases=["netflix"],
        category="media"
    ),
    WebService(
        service_id="prime_video",
        name="Prime Video",
        canonical_url="https://www.primevideo.com",
        aliases=["prime video", "amazon prime video"],
        category="media"
    ),
    WebService(
        service_id="amazon",
        name="Amazon",
        canonical_url="https://www.amazon.com",
        aliases=["amazon", "amazon.com"],
        category="shopping"
    ),
    WebService(
        service_id="tradingview",
        name="TradingView",
        canonical_url="https://www.tradingview.com",
        aliases=["tradingview", "trading view"],
        category="finance"
    ),
]


def clean_conversational_noise(query: str) -> str:
    """
    Strips conversational fluff, speech-to-text filler, personal reasons,
    and politeness prefixes/suffixes from a natural speech or chat transcript.
    Examples:
      - "open chrome and open google docs for me i hv to work" -> "open chrome and open google docs"
      - "open chrome and an dkeep docs me i hv to work there fast" -> "open chrome and keep docs"
      - "bro can you please open brave and go to youtube fast" -> "open brave and go to youtube"
      - "ada launch netflix right now" -> "launch netflix"
    """
    t = query.strip()

    # 1. Fix common Speech-To-Text artifacts
    stt_fixes = [
        (r'\ban\s+dkeep\b', 'and keep'),
        (r'\bdkeep\b', 'keep'),
        (r'\bg\s+docs\b', 'gdocs'),
        (r'\bg\s+sheets\b', 'gsheets'),
        (r'\bg\s+drive\b', 'gdrive'),
        (r'\bg\s+mail\b', 'gmail'),
        (r'\b(?:and\s+)+and\b', 'and'),
    ]
    for pattern, replacement in stt_fixes:
        t = re.sub(pattern, replacement, t, flags=re.IGNORECASE)

    # 2. Strip personal context, reasons, and filler clauses
    filler_patterns = [
        r'\b(?:for\s+me\s+to\s+work|for\s+me\s+i\s+have\s+to\s+work|for\s+me\s+i\s+hv\s+to\s+work|for\s+me\s+i\s+got\s+to\s+work|so\s+i\s+can\s+work|i\s+have\s+to\s+work|i\s+hv\s+to\s+work|i\s+need\s+to\s+work|i\s+got\s+to\s+work|i\s+want\s+to\s+work|i\s+wanna\s+work|want\s+to\s+work)\b',
        r'\b(?:i\s+am\s+working\s+in\s+antigravity\s+for\s+now|i\s+am\s+working\s+in\s+antigravity|working\s+in\s+antigravity\s+for\s+now|working\s+in\s+antigravity)\b',
        r'\b(?:and\s+keep\s+it\s+open|keep\s+it\s+open|and\s+keep\s+open|keep\s+open)\b',
        r'\b(?:and\s+keep)(?=\s+(?:and|open|also|$))\b',
        r'\b(?:me\s+i\s+have\s+to\s+work|me\s+i\s+hv\s+to\s+work|me\s+i\s+need\s+to\s+work|me\s+i\s+have\s+to|me\s+i\s+hv\s+to)\b',
        r'\b(?:there\s+fast|fast|quickly|asap|right\s+now|immediately|hurry\s+up|real\s+quick|urgently|for\s+now)\b',
        r'\b(?:for\s+me\s+to|for\s+me|for\s+myself|for\s+work)\b',
        r'\b(?:i\s+have\s+to|i\s+hv\s+to|i\s+need\s+to|i\s+want\s+to|i\s+wanna|i\s+got\s+to|so\s+that\s+i\s+can)\b',
        r'\b(?:there|in\s+there)\b(?=\s*$)',  # only 'there' at end of sentence
        r'\bme\b(?=\s*$)',  # trailing 'me'
    ]
    for pat in filler_patterns:
        t = re.sub(pat, ' ', t, flags=re.IGNORECASE)

    # 3. Strip leading politeness / assistant address
    prefix_patterns = [
        r'^\s*(?:hey|hi|hello|ok|okay)?\s*\b(?:ada|nova|bro|dude|boss|buddy|mate|listen)\b\s*',
        r'^\s*(?:can\s+you\s+please|could\s+you\s+please|would\s+you\s+please|will\s+you\s+please|please|pls|kindly)\s*',
        r'^\s*(?:can\s+you|could\s+you|would\s+you|will\s+you|help\s+me\s+to|help\s+me|go\s+ahead\s+and)\s*',
        r'^\s*(?:i\s+want\s+you\s+to|i\s+need\s+you\s+to|just)\s*',
    ]
    for pat in prefix_patterns:
        t = re.sub(pat, '', t, flags=re.IGNORECASE)

    # 4. Strip trailing politeness
    suffix_patterns = [
        r'\s*\b(?:please|pls|kindly|thank\s+you|thanks|bro|ada)\b\s*$',
    ]
    for pat in suffix_patterns:
        t = re.sub(pat, '', t, flags=re.IGNORECASE)

    # Clean double spaces
    t = ' '.join(t.split()).strip()
    return t


def resolve_web_service(query: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes a user's natural query to detect if they are directing ADA
    to navigate to a canonical web service or productivity app.

    Returns a dict with:
        - service_id: str
        - name: str
        - url: str
        - is_new_item: bool
    or None if no recognized web service matches.
    """
    clean_q = clean_conversational_noise(query).lower()

    # Pre-check for raw URLs explicitly entered (e.g. "open https://example.com" or "go to github.com")
    url_match = re.search(r'\b(https?://[^\s]+)\b', query)
    if url_match:
        raw_url = url_match.group(1).strip()
        return {
            "service_id": "direct_url",
            "name": raw_url,
            "url": raw_url,
            "is_new_item": False
        }

    domain_match = re.search(r'\b([a-zA-Z0-9-]+\.(?:com|org|io|net|so|ai|co|app|edu|gov))\b', clean_q)
    if domain_match:
        domain = domain_match.group(1).strip()
        full_url = f"https://{domain}"
        return {
            "service_id": domain.replace(".", "_"),
            "name": domain,
            "url": full_url,
            "is_new_item": False
        }

    # Check for "new document", "new doc", "new spreadsheet", "new sheet", "new presentation"
    is_create_new = any(
        phrase in clean_q for phrase in [
            "new doc", "new document", "blank doc", "create a doc", "make a doc",
            "new sheet", "new spreadsheet", "blank sheet", "create a sheet",
            "new slide", "new presentation", "create a slide", "blank presentation",
            "new repo", "new repository", "create repo", "new form"
        ]
    )

    # Check for "keep docs" voice artifact vs "google docs"
    if "keep docs" in clean_q:
        # User said "keep docs" -> strongly maps to Google Docs in natural dictation
        # (or Google Keep if preceded by "notes")
        if "notes" in clean_q:
            return {
                "service_id": "google_keep",
                "name": "Google Keep",
                "url": "https://keep.google.com",
                "is_new_item": False
            }
        return {
            "service_id": "google_docs",
            "name": "Google Docs",
            "url": "https://docs.google.com",
            "is_new_item": False
        }

    # Search against registered services
    for service in SERVICES_REGISTRY:
        for alias in service.aliases:
            # Word boundary check to prevent substring collisions
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, clean_q):
                target_url = service.canonical_url
                if is_create_new and service.new_item_url:
                    target_url = service.new_item_url

                return {
                    "service_id": service.service_id,
                    "name": service.name,
                    "url": target_url,
                    "is_new_item": is_create_new and bool(service.new_item_url)
                }

    return None


def extract_search_topic(query: str, browser_name: str = "") -> Tuple[str, str]:
    """
    Extracts the pure search topic from a search query, stripping browser mentions,
    search keywords, and filler noise.
    Returns:
        (clean_topic, search_url)
    """
    clean = clean_conversational_noise(query)
    # Remove browser mentions
    clean = re.sub(r'\b(?:in|on|using|with)\s+(?:brave|chrome|edge|firefox|browser)\b', ' ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(?:brave|chrome|edge|firefox|browser)\b', ' ', clean, flags=re.IGNORECASE)

    # Remove leading open / launch / go to phrases
    clean = re.sub(r'^\s*(?:open|launch|go\s+to)\s+', '', clean, flags=re.IGNORECASE)

    # Remove search command triggers
    clean = re.sub(r'^\s*(?:and\s+)?(?:search\s+google\s+for|search\s+for|search\s+web\s+for|search|google|look\s+up|find)\s+', ' ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(?:search\s+for|look\s+up|find|search)\b', ' ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\b(?:on\s+google|in\s+google|on\s+the\s+web|on\s+internet)\b', ' ', clean, flags=re.IGNORECASE)
    clean = re.sub(r'^\s*(?:and|then)\s+', '', clean, flags=re.IGNORECASE)

    clean_topic = ' '.join(clean.split()).strip()
    if clean_topic:
        encoded = urllib.parse.quote_plus(clean_topic)
        search_url = f"https://www.google.com/search?q={encoded}"
    else:
        clean_topic = "Google"
        search_url = "https://www.google.com"

    return clean_topic, search_url
