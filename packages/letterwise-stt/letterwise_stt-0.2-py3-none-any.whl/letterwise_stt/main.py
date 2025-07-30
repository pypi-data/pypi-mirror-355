from letterwise_stt import STTPhonemeExtractor, WordReconstructor

extractor = STTPhonemeExtractor()
reconstructor = WordReconstructor()

print("🎙 Speak something clearly into the mic. Ctrl+C to quit.\n")

try:
    for letters in extractor.listen_letters_live():
        reconstructed = reconstructor.reconstruct(letters)
        print(f"🧠 Letters: {letters} → Words: {reconstructed}")
except KeyboardInterrupt:
    print("\n🛑 Stopped.")
