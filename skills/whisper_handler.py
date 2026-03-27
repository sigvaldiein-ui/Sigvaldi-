import torch
import os
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline

class MimirWhisper:
    def __init__(self):
        print("👂 Hleð Whisper-large-v3 á GPU... (Hreint borð skv. SOP)")
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

        model_id = "openai/whisper-large-v3"

        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_id, 
            torch_dtype=self.torch_dtype, 
            low_cpu_mem_usage=True, 
            use_safetensors=True
        )
        self.model.to(self.device)
        self.processor = AutoProcessor.from_pretrained(model_id)

        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=self.model,
            tokenizer=self.processor.tokenizer,
            feature_extractor=self.processor.feature_extractor,
            max_new_tokens=128,
            chunk_length_s=30,
            batch_size=16,
            torch_dtype=self.torch_dtype,
            device=self.device,
        )
        print("✅ Whisper (v3) er klár á GPU.")

    def transcribe(self, audio_path):
        """Tekur hljóðskrá og skilar nákvæmum íslenskum texta."""
        if not os.path.exists(audio_path):
            return "❌ Villa: Hljóðskrá fannst ekki."
            
        print(f"🎤 Mímir hlustar á: {audio_path}")
        
        result = self.pipe(
            audio_path, 
            generate_kwargs={"language": "icelandic", "task": "transcribe"}
        )
        return result["text"].strip()

if __name__ == "__main__":
    whisper = MimirWhisper()
    print("🚀 Kerfið er tilbúið í hljóðgreiningu.")
