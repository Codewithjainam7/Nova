import asyncio
import pytest
from backend.release.schema import BuildType, ReleasePackageType, TelemetryData
from backend.release.core import ReleaseManager
from backend.release.versioning import VersionManager, MigrationManager
from backend.release.telemetry import CrashReporter, TelemetryManager
from backend.release.deployment import AutoUpdater, InstallerGenerator, PortableBuildGenerator, ReleaseValidator

@pytest.mark.asyncio
async def test_release_core_pipeline():
    manager = ReleaseManager()
    
    # 1. Build
    build_dir = await manager.builder.build(BuildType.PRODUCTION)
    assert "production" in build_dir
    
    # 2. Package
    pkg = await manager.packager.package(build_dir, ReleasePackageType.WINDOWS_INSTALLER)
    assert "windows_installer" in pkg
    
    # 3. Publish
    await manager.artifacts.publish(pkg)

@pytest.mark.asyncio
async def test_versioning_and_migration():
    vm = VersionManager()
    assert str(vm.current_version) == "1.0.0+release"
    assert "Release Notes" in vm.generate_release_notes()
    
    mig = MigrationManager()
    assert await mig.verify_compatibility("0.9.0", "1.0.0") is True

@pytest.mark.asyncio
async def test_telemetry_and_crash():
    # Crash
    cr = CrashReporter()
    report = await cr.generate_report(ValueError("Test"), "Kernel")
    assert report.subsystem == "Kernel"
    assert "Test" in report.stack_trace
    
    # Telemetry
    tm = TelemetryManager(opt_in=True)
    await tm.record_session(TelemetryData(session_id="session123", os_version="Windows 11", app_version="1.0.0"))
    
    tm_opt_out = TelemetryManager(opt_in=False)
    await tm_opt_out.record_session(TelemetryData(session_id="session456", os_version="Windows 11", app_version="1.0.0"))

@pytest.mark.asyncio
async def test_deployment_generators():
    updater = AutoUpdater()
    assert await updater.check_for_updates("1.0.0") is False
    await updater.rollback()
    
    installer = InstallerGenerator()
    assert await installer.generate("dist/") == "setup.exe"
    
    portable = PortableBuildGenerator()
    assert await portable.generate("dist/") == "portable.zip"
    
    validator = ReleaseValidator()
    assert await validator.validate_build("setup.exe") is True

if __name__ == "__main__":
    asyncio.run(test_release_core_pipeline())
    asyncio.run(test_versioning_and_migration())
    asyncio.run(test_telemetry_and_crash())
    asyncio.run(test_deployment_generators())
    print("ALL RELEASE TESTS PASSED")
