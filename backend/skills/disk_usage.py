"""
Skill: disk_usage
Description: disk_usage to return total and free disk space in GB
Auto-synthesized by NOVA on 2026-11-22 04:45:40
"""

"""
Skill: disk_usage
Purpose: Return total and free disk space in GB for a specified path.
"""
import shutil


def run(**kwargs):
    path = kwargs.get('path', '/')
    try:
        total_bytes, used_bytes, free_bytes = shutil.disk_usage(path)
        gb = 1024 ** 3
        return {
            'status': 'SUCCESS',
            'path': path,
            'total_gb': round(total_bytes / gb, 2),
            'free_gb': round(free_bytes / gb, 2),
            'used_gb': round(used_bytes / gb, 2)
        }
    except Exception as exc:
        return {
            'status': 'ERROR',
            'path': path,
            'message': str(exc)
        }
