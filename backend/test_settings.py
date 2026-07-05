import asyncio
import pytest
from backend.settings.schema import SettingItem, SettingsCategory
from backend.settings.core import SettingsSystem

@pytest.mark.asyncio
async def test_settings_initialization_and_crud():
    system = SettingsSystem()
    await system.initialize("user_profile_1")
    
    assert system.active_profile.profile_id == "user_profile_1"
    
    # Update a setting
    item = SettingItem(key="theme", category=SettingsCategory.APPEARANCE, value="dark")
    await system.update_setting(item)
    
    # Retrieve the setting
    val = await system.get_setting("theme")
    assert val == "dark"

@pytest.mark.asyncio
async def test_settings_validation_failure():
    system = SettingsSystem()
    await system.initialize("user_profile_2")
    
    # Invalid setting (None value)
    item = SettingItem(key="font_size", category=SettingsCategory.APPEARANCE, value=None)
    with pytest.raises(ValueError):
        await system.update_setting(item)

@pytest.mark.asyncio
async def test_settings_backup():
    system = SettingsSystem()
    await system.initialize("user_profile_3")
    
    backup_id = await system.backup_active_profile()
    assert "backup_user_profile_3" in backup_id

if __name__ == "__main__":
    asyncio.run(test_settings_initialization_and_crud())
    asyncio.run(test_settings_validation_failure())
    asyncio.run(test_settings_backup())
    print("ALL SETTINGS TESTS PASSED")
