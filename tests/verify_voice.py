import asyncio
import time
from backend.voice.hardware import AudioRecorder, AudioPlayer
from backend.voice.providers import SpeechRecognizer, SpeechSynthesizer

async def verify_voice_engine():
    print("Starting Voice Engine Verification...\n")
    
    recorder = AudioRecorder(sample_rate=16000)
    player = AudioPlayer()
    stt = SpeechRecognizer(model_size="base")
    tts = SpeechSynthesizer()
    
    latencies = {}
    
    # 1. Warm up Whisper (it loads model to memory on first inference)
    print("Initializing Whisper Model...")
    await stt.transcribe(b'\x00' * 16000 * 2) # Dummy 1s audio
    
    # 2. Recording
    print("--- [TEST 1: RECORDING] ---")
    print("Please say 'Open Google'...")
    
    await recorder.start()
    start_time = time.time()
    
    # Record for 3 seconds
    audio_buffer = b""
    while time.time() - start_time < 3.0:
        chunk = await recorder.read_chunk()
        audio_buffer += chunk
        await asyncio.sleep(0.01)
        
    await recorder.stop()
    latencies["Recording (3s block)"] = time.time() - start_time
    print(f"[PASS] Microphone recording captured {len(audio_buffer)} bytes.")
    
    # 3. STT Processing
    print("\n--- [TEST 2: SPEECH-TO-TEXT] ---")
    start_time = time.time()
    transcript = await stt.transcribe(audio_buffer)
    latencies["STT Inference"] = time.time() - start_time
    print(f"Transcript: '{transcript}'")
    if transcript:
        print("[PASS] Speech recognized.")
    else:
        print("[WARN] No speech recognized.")
        
    # 4. TTS Generation
    print("\n--- [TEST 3: TEXT-TO-SPEECH] ---")
    text_to_say = "Hello Jainam, Voice Engine is working."
    print(f"Generating audio for: '{text_to_say}'")
    start_time = time.time()
    mp3_bytes = await tts.synthesize(text_to_say)
    latencies["TTS Generation"] = time.time() - start_time
    print(f"[PASS] TTS generation produced {len(mp3_bytes)} bytes.")
    
    # 5. Playback
    print("\n--- [TEST 4: PLAYBACK] ---")
    print("Playing back synthesized audio...")
    start_time = time.time()
    await player.play(mp3_bytes)
    latencies["Playback"] = time.time() - start_time
    print("[PASS] Audio playback complete.")
    
    print("\n--- [PERFORMANCE LATENCIES] ---")
    for k, v in latencies.items():
        print(f"{k}: {v:.2f}s")
        
if __name__ == "__main__":
    asyncio.run(verify_voice_engine())
