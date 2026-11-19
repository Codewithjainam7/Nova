"""
Skill: desktop_tidy
Description: Scans the user desktop for unorganized files and categorizes them.
"""
import os

def run(target_dir=None, **kwargs):
    if not target_dir:
        target_dir = os.path.expanduser("~/Desktop")
    
    if not os.path.exists(target_dir):
        return {"status": "ERROR", "message": f"Directory not found: {target_dir}"}
        
    files = [f for f in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, f))]
    extensions = {}
    for f in files:
        ext = os.path.splitext(f)[1].lower() or "no_ext"
        extensions[ext] = extensions.get(ext, 0) + 1
        
    return {
        "status": "SUCCESS",
        "total_files": len(files),
        "extension_breakdown": extensions,
        "preview": files[:8]
    }
