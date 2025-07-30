from .splv_encoder_py import *

import numpy as np
from pydub import AudioSegment

def _pydub_audio_from_file(self, file):
    frames = AudioSegment.from_file(file).raw_data
    self.accept_audio_frames(np.frombuffer(frames, np.int8))

SPLVencoder.pydub_audio_from_file = _pydub_audio_from_file