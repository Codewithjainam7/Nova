import asyncio
import pytest
from backend.vision.schema import VisionPermissionLevel
from backend.vision.core import VisionEngine

@pytest.mark.asyncio
async def test_vision_full_analysis():
    engine = VisionEngine()
    
    mock_image = b"mock_image_bytes"
    result = await engine.analyze_screen(mock_image)
    
    assert engine.metrics.total_images_processed == 1
    assert result.full_text == "Mock OCR Text"
    assert len(result.boxes) == 2 # 1 from OCR, 1 from UI

@pytest.mark.asyncio
async def test_vision_permissions():
    # Set to READ_ONLY (cannot do desktop analysis)
    engine = VisionEngine(permission_level=VisionPermissionLevel.READ_ONLY)
    
    mock_image = b"mock_image_bytes"
    
    with pytest.raises(PermissionError):
        await engine.analyze_screen(mock_image)
        
    assert engine.metrics.failed_images == 1

@pytest.mark.asyncio
async def test_vision_recovery():
    engine = VisionEngine()
    
    # Mock a failure in the pipeline
    async def failing_pipeline(img):
        raise RuntimeError("Simulated OCR failure")
        
    engine.manager.pipeline.run_pipeline = failing_pipeline
    
    mock_image = b"mock_image_bytes"
    
    with pytest.raises(RuntimeError):
        await engine.analyze_screen(mock_image)
        
    assert engine.metrics.failed_images == 1

if __name__ == "__main__":
    asyncio.run(test_vision_full_analysis())
    asyncio.run(test_vision_permissions())
    asyncio.run(test_vision_recovery())
    print("ALL VISION TESTS PASSED")
