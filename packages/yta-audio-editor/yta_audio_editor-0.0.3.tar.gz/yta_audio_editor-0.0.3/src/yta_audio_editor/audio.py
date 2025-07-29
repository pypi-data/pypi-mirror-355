"""
Module to hold the main Audio class that is
capable of obtaining information, modifying
it, applying filters, etc.

The audio isusually presented in 2 columns
format, but depending on the library who is
handling the numpy array, the 2D information
can be different. The 'soundfile' library 
uses the (n_samples, n_channels) format while
the 'librosa' (mono = False) uses the 
(n_channels, n_samples) format.

TODO: Check the 'util.valid_audio(y)' within
the 'librosa' lib because it seems interesting
to validate a numpy audio array.
"""
from yta_validation.parameter import ParameterValidator
from yta_validation import PythonValidator
from yta_programming.decorators.requires_dependency import requires_dependency
from typing import Union

import numpy as np
import librosa


class Audio:
    """
    Class to represent and wrap a sound that is
    a numpy array to be able to work with it in
    an easy way.
    """

    @property
    def number_of_channels(
        self
    ) -> int:
        """
        The number of channels of the audio.
        """
        shape = self.audio.shape

        return (
            1
            if len(shape) == 1 else
            shape[1]
        )

    @property
    def number_of_samples(
        self
    ) -> int:
        """
        The number of samples in the audio.
        """
        return self.audio.shape[0]
    
    @property
    def duration(
        self
    ) -> int:
        """
        The duration of the audio in seconds, which
        is calculated by applying the number of
        samples divided by the sample rate:

        - number_of_samples / sample_rate
        """
        return self.number_of_samples / self.sample_rate

    @property
    def is_mono(
        self
    ) -> bool:
        """
        Check if the audio is mono (includes
        only one channel) or not.
        """
        return self.number_of_channels == 1
    
    @property
    def is_stereo(
        self
    ) -> bool:
        """
        Check if the audio is stereo (includes
        two channels) or not.
        """
        return self.number_of_channels == 2
    
    @property
    def as_mono(
        self
    ) -> 'np.ndarray':
        """
        Get the audio forced to be mono. If the
        audio is not mono it is obtained by
        averaging samples across channels.
        """
        return (
            self.audio
            if self.is_mono else
            librosa.to_mono(self.audio.T)
        )
    
    # Other properties below
    @property
    def min(
        self
    ):
        """
        Get the min value of the audio.
        """
        return np.min(np.abs(self.audio))

    @property
    def max(
        self
    ):
        """
        Get the max value of the audio.
        """
        return np.max(np.abs(self.audio))
    
    @property
    def inverted(
        self
    ) -> np.ndarray:
        """
        Get the audio but inverted as an horizontal mirror.

        TODO: Wtf is this (?)
        """
        return -self.audio
    
    @property
    def reversed(
        self
    ) -> np.ndarray:
        """
        Get the audio but reversed.
        """
        return self.audio[::-1]
    
    @property
    def normalized(
        self
    ) -> np.ndarray:
        """
        Get the audio but normalized, which means that its
        maximum value is 1.0.
        """
        max_val = np.max(np.abs(self.data))
        if max_val > 0:
            self.data /= max_val

    def __init__(
        self,
        audio: Union['np.ndarray', str],
        sample_rate: Union[int, None] = None
    ):
        # 1. Process a filename
        if PythonValidator.is_string(audio):
            # TODO: Use 'try-catch' or validate audio file
            # sr=None preserves the original sample rate
            audio, sample_rate = librosa.load(audio, sr = sample_rate)
            self.sample_rate = sample_rate

        # TODO: Process 'AudioClip', etc...
        # 2. Process a numpy array
        # TODO: Handle the type and process the input
        # TODO: Set the accepted input types
        # TODO: What about the sample rate (?)
        self.audio: Union['np.ndarray'] = audio
        """
        The audio numpy array once that has been read
        according to the input.
        """
        self.sample_rate = sample_rate
        """
        The sample rate of the audio. If you force this
        value pay attention because the result could be
        unexpected if it is not an accurate value.
        """

        if (
            not self.is_mono and
            not self.is_stereo
        ):
            raise Exception('The format is unexpected, no mono nor stereo audio.')
        
    def trimmed(
        self,
        start: Union[float, None],
        end: Union[float, None]
    ) -> 'Audio':
        """
        Get a new instance with the audio array modified.
        """
        self.audio = self.trim(start, end)

        return self

    def trim(
        self,
        start: Union[float, None],
        end: Union[float, None]
    ) -> 'np.ndarray':
        """
        Get the audio trimmed from the provided 'start'
        to the also given 'end'.
        """
        ParameterValidator.validate_positive_number('start', start, do_include_zero = True)
        ParameterValidator.validate_positive_number('end', end, do_include_zero = True)

        start = (
            0
            if start is None else
            start
        )
        end = (
            self.duration
            if end is None else
            end
        )

        return self.audio[int(start * self.sample_rate):int(end * self.sample_rate)]
        
    # TODO: This is for an audio frame, not necessary for
    # the whole audio, but an audio is also an audio
    # frame
    def change_audio_volume(
        self,
        audio_frame: np.ndarray,
        factor: int = 100
    ):
        """
        Change the 'audio_frame' volume by applying the
        given 'factor'.

        Based on:
        https://github.com/Zulko/moviepy/blob/master/moviepy/audio/fx/MultiplyVolume.py
        """
        # TODO: Apply the limit better
        ParameterValidator.validate_mandatory_int('factor', factor)

        factors_array = np.full(self.number_of_samples, factor)

        return (
            np.multiply(
                audio_frame,
                factors_array
            )
            if self.is_mono else
            np.multiply(
                audio_frame,
                factors_array[:, np.newaxis]
            )
            # if self.is_stereo == 2:
        )
    
    @requires_dependency('soundfile', 'yta_audio_editor', 'soundfile')
    def save(
        self,
        filename: str
    ):
        """
        Write the audio to a file with the given
        'filename'.
        """
        import soundfile as sf

        sf.write(filename, self.data, self.sample_rate)

    # TODO: This 'sounddevice' library is not very stable
    # nor working always... and playing the sound is not
    # an important need now...
    # @requires_dependency('sounddevice', 'yta_audio_editor', 'sounddevice')
    # def play(
    #     self
    # ):
    #     """
    #     Play the audio until it finishes.
    #     """
    #     import sounddevice as sd

    #     sd.play(self.data, self.sample_rate)
    #     sd.wait()

    """
    Filters below. You can find 'with_' and 'apply_'
    methods below. The 'with_' returns a copy of the
    numpy array modified, but touching not the
    original audio, and the 'apply_' methods modify
    the original audio instance (and the values of 
    the original array).
    """
    # TODO: Some filtering methods below
    def with_lowpass(
        self
    ) -> 'np.ndarray':
        """
        Get the audio modified by applying a simple
        lowpass filter.
        """
        from yta_audio_editor.filters import Filters

        return Filters.low_pass(self.audio.copy())

    def apply_lowpass(
        self
    ) -> 'np.ndarray':
        """
        Modify the audio in the instance with the one
        after the low pass effect is applied.
        """
        self.audio = self.with_lowpass()

        return self.audio
    
    def with_fadeout(
        self,
        duration: float
    ):
        """
        Get the audio with a fade out effect applied. This
        method does not modify the original audio but 
        returns the audio modified.
        """
        from yta_audio_editor.filters import Filters

        return Filters.fadeout(self.audio.copy(), self.sample_rate, duration)
    
    def apply_fadeout(
        self
    ) -> 'np.ndarray':
        """
        Modify the audio instance by applying a fade
        out filter and return the audio modified.
        """
        self.audio = self.with_fadeout()

        return self.audio
    
    def with_fadein(
        self,
        duration: float
    ):
        """
        Get the audio with a fade in effect applied. This
        method does not modify the original audio but 
        returns the audio modified.
        """
        from yta_audio_editor.filters import Filters

        return Filters.fadein(self.audio.copy(), self.sample_rate, duration)
    
    def apply_fadein(
        self
    ) -> 'np.ndarray':
        """
        Modify the audio instance by applying a fade
        in filter and return the audio modified.
        """
        self.audio = self.with_fadein()

        return self.audio
    
    # TODO: Other modifying methods below
    def with_time_strech(
        self,
        rate: float = 0.5
    ):
        """
        Get the audio with a time stretch effect
        applied, which means changing the audio 
        duration without changing the pitch. This
        method does not modify the original audio but 
        returns the audio modified.

        TODO: Explain the 'rate' better.
        """
        from yta_audio_editor.filters import Filters

        return Filters.time_stretch(self.audio.copy(), rate)
    
    def apply_time_stretch(
        self,
        rate: float = 0.5
    ):
        """
        Modify the audio instance by applying a time
        stretch filter, which means changing the audio
        duration without changing the pitch, and
        return the audio modified.
        """
        from yta_audio_editor.filters import Filters

        audio, sample_rate = Filters.time_stretch(self.audio, rate)

        self.audio = audio
        self.sample_rate = sample_rate

        return self.audio
    
    def with_pitch_shift(
        self,
        n_steps: int
    ):
        """
        Get the audio with a pitch shift effect applied,
        which means changing the pitch but not the audio
        duration. This method does not modify the
        original audio but returns the audio modified.

        TODO: Explain 'n_steps' better.
        """
        from yta_audio_editor.filters import Filters

        return Filters.pitch_shift(self.audio.copy(), self.sample_rate, n_steps)
    
    def apply_pitch_shift(
        self,
        audio: 'np.ndarray',
        n_steps: int
    ):
        """
        Modify the audio instance by applying a pitch
        shifting filter, which means changing the pitch
        without changing the audio duration, and return
        the audio modified.
        """
        from yta_audio_editor.filters import Filters

        audio, sample_rate = Filters.pitch_shift(self.audio, self.sample_rate, n_steps)

        self.audio = audio
        self.sample_rate = sample_rate

        return self.audio
    
    def with_fft(
        self
    ):
        """
        Get the audio with a fft effect applied, which
        means looking for the Fourier spectrum per
        channel. This method does not modify the
        original audio but returns the audio modified.
        """
        from yta_audio_editor.filters import Filters

        return Filters.fft(self.audio.copy())

    def apply_fft(
        self
    ):
        """
        Modify the audio instance by applying an fft
        filter, which means looking for the Fourier
        spectrum per channel, and return the audio
        modified.
        """
        from yta_audio_editor.filters import Filters

        self.audio = Filters.fft(self.audio)

        return self.audio