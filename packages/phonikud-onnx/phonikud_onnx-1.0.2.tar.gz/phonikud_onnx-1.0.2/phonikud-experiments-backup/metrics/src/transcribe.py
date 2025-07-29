import tempfile
from pathlib import Path
from pydub import AudioSegment
from pywhispercpp.model import Model
from huggingface_hub import hf_hub_download


class Transcriber:
    def __init__(self):
        model_path = hf_hub_download(
            repo_id="ivrit-ai/whisper-large-v3-turbo-ggml",
            filename="ggml-model.bin"
        )
        self.model = Model(model_path)

    def _prepare_audio(self, file: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        audio = AudioSegment.from_file(file)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(tmp_path, format="wav")
        return str(tmp_path)

    def transcribe(self, file: str, language='he'):
        normalized = self._prepare_audio(file)
        segs = self.model.transcribe(normalized, language=language)
        text = ' '.join(segment.text for segment in segs)
        Path(normalized).unlink(missing_ok=True)  # clean up the temp file
        return text
