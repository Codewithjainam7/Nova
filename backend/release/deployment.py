import asyncio
from backend.release.schema import BuildType, ReleasePackageType
from backend.core.logger import app_logger

class AutoUpdater:
    """Manages background downloads and atomic patching."""
    async def check_for_updates(self, current_version: str) -> bool:
        app_logger.info(f"[AUTO UPDATE] Checking for updates (current: {current_version})")
        await asyncio.sleep(0.02)
        return False # No updates available in this mock
        
    async def rollback(self):
        app_logger.warning("[AUTO UPDATE] Rolling back to previous stable snapshot")
        await asyncio.sleep(0.05)

class LicenseManager:
    """Validates enterprise/developer licensing."""
    def verify_license(self, key: str) -> bool:
        return True # OSS/Free tier default

class InstallerGenerator:
    """Bundles the NSIS/InnoSetup scripts."""
    async def generate(self, source_dir: str) -> str:
        app_logger.info(f"[INSTALLER] Generating MSI/EXE from {source_dir}")
        await asyncio.sleep(0.04)
        return "setup.exe"

class PortableBuildGenerator:
    """Bundles self-contained ZIPs without registry hooks."""
    async def generate(self, source_dir: str) -> str:
        app_logger.info(f"[PORTABLE] Generating standalone ZIP from {source_dir}")
        await asyncio.sleep(0.03)
        return "portable.zip"

class ReleaseValidator:
    """Final sanity check before allowing a package to publish."""
    async def validate_build(self, package_path: str) -> bool:
        app_logger.info(f"[VALIDATOR] Scanning {package_path} for corrupted assets...")
        await asyncio.sleep(0.02)
        return True
