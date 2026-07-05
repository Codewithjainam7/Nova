import asyncio
import pytest
from backend.voice.core import VoiceEngine

@pytest.mark.asyncio
async def test_voice_listening_and_stt():
    engine = VoiceEngine()
    
    # Simulate start listening
    await engine.start_listening()
    assert engine.manager.recorder.is_recording is True
    
    # Simulate stopping mid-way just to check state
    await engine.stop_listening()
    assert engine.manager.recorder.is_recording is False

@pytest.mark.asyncio
async def test_wake_word_and_transcription():
    engine = VoiceEngine()
    await engine.start_listening()
    
    # Run the streaming STT simulation
    # The dummy recorder yields 1024 bytes -> VAD says yes -> STT stream yields 'partial... '
    # In core.py we check for wake word. Our dummy wake word is "NOVA", but STT yields "partial... "
    # We will inject "nova" manually to test the detector logic, but the actual transcribe loop uses the dummy stt.
    # We can just test the transcription completion for now.
    
    # Overwrite the STT dummy to include wake word
    async def mock_transcribe_stream(audio):
        yield "Hey NOVA, "
        yield "what is the weather?"
        engine.manager.recorder.is_recording = False # Stop the stream
        
    engine.manager.stt.transcribe_stream = mock_transcribe_stream
    
    transcript = await engine.transcribe_current_stream()
    
    assert engine.metrics.wake_word_hits > 0
    assert "Final" in transcript
    
    await engine.stop_listening()

@pytest.mark.asyncio
async def test_voice_synthesis():
    engine = VoiceEngine()
    
    await engine.start_listening() # Need active session to track state
    
    # TTS will play and transition state
    await engine.speak("Testing TTS playback.")
    
    session = engine.manager.session_manager.get_session()
    assert session.state.name == "IDLE"
    assert engine.metrics.avg_tts_latency_ms > 0
    
    await engine.stop_listening()

if __name__ == "__main__":
    asyncio.run(test_voice_listening_and_stt())
    asyncio.run(test_wake_word_and_transcription())
    asyncio.run(test_voice_synthesis())
    print("ALL VOICE TESTS PASSED")
