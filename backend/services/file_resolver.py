"""
File Resolver Service for ADA.
Searches user workspace, Downloads, Documents, and Desktop to locate
referenced files (e.g. resumes, spreadsheets, documents, reports) by fuzzy keyword matching
and recency sorting.
"""

import os
import re
from typing import Optional, Dict, Any, List

def find_latest_user_file(query_text: str) -> Optional[Dict[str, Any]]:
    """
    Searches user directories (Downloads, Documents, Desktop, Workspace) for a file
    matching the query description (e.g. "devisri resume", "latest resume", "financial report"),
    sorted by matching relevance and recency (modification time).
    """
    search_dirs = [
        os.path.expanduser(r"~\Downloads"),
        os.path.expanduser(r"~\Documents"),
        r"C:\Users\Jainam\OneDrive\Documents",
        r"C:\Users\Jainam\OneDrive\Desktop",
        os.path.expanduser(r"~\Desktop"),
        r"D:\ANTIGRAVITY PROJECTS\Transfer_To_New_Laptop\NOVA_AI\workspace",
    ]

    # Clean query into matching tokens
    clean = re.sub(
        r'\b(?:open|upload|the|latest|one|and|also|keep|it|i|want|to|work|my|file|document|folder|for|me|in|antigravity|now|only|chrome|docs|there|bakcgorund|background|not|on|screen|meant|that)\b',
        ' ',
        query_text,
        flags=re.IGNORECASE
    )
    tokens = [w.lower().strip() for w in clean.split() if len(w.strip()) > 1]

    is_resume_query = any(k in query_text.lower() for k in ["resume", "cv", "biodata"])

    allowed_exts = {
        ".pdf", ".docx", ".doc", ".txt", ".xlsx", ".xls", ".pptx", ".ppt",
        ".csv", ".png", ".jpg", ".jpeg", ".md", ".json", ".zip"
    }

    scored_files: List[Dict[str, Any]] = []
    seen = set()

    for sdir in search_dirs:
        if not os.path.exists(sdir):
            continue
        try:
            for root, dirs, files in os.walk(sdir):
                # Search up to 2 sub-levels
                rel = os.path.relpath(root, sdir)
                if rel != "." and len(rel.split(os.sep)) > 2:
                    continue
                if any(skip in root.lower() for skip in [".git", "node_modules", ".venv", "__pycache__", "appdata"]):
                    continue

                for fname in files:
                    fpath = os.path.join(root, fname)
                    if fpath in seen or not os.path.isfile(fpath):
                        continue
                    seen.add(fpath)

                    fname_lower = fname.lower()
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in allowed_exts:
                        continue

                    score = 0
                    for tok in tokens:
                        if tok in fname_lower:
                            score += 10
                            # Bonus if token matches as an exact word or prefix
                            if f"_{tok}" in fname_lower or f"{tok}_" in fname_lower or f" {tok}" in fname_lower or fname_lower.startswith(tok):
                                score += 5

                    if is_resume_query:
                        if "resume" in fname_lower or "cv" in fname_lower:
                            score += 8
                        # If query has specific name tokens like "devisri"
                        if "devisri" in query_text.lower() and "devisri" in fname_lower:
                            score += 20
                        elif "devi" in query_text.lower() and "devi" in fname_lower:
                            score += 15

                    # Prefer Word docs or PDFs for resumes
                    if is_resume_query and ext in [".pdf", ".docx"]:
                        score += 5

                    if score > 0:
                        try:
                            mtime = os.path.getmtime(fpath)
                            scored_files.append({
                                "score": score,
                                "mtime": mtime,
                                "path": fpath,
                                "filename": fname,
                                "extension": ext
                            })
                        except Exception:
                            pass
        except Exception:
            continue

    if not scored_files:
        return None

    # Sort: highest score first, then newest file (highest mtime) first
    scored_files.sort(key=lambda x: (x["score"], x["mtime"]), reverse=True)
    return scored_files[0]
