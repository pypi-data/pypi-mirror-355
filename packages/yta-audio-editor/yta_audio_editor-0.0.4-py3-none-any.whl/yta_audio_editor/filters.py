"""
Filters that are applied to a numpy array that 
represents a sound.

Info: When we are modifying an audio, we can
do it channel by channel or setting it as a
mono audio before modifying it. If you have
a guitar in the left channel, applying a 
filter channel by channel will keep it only
in the left channel, but if you turn it into
a mono audio to modify it, the guitar will 
be now in both because they were mixed to be
modified.

TODO: Maybe move this class to a specific class
that contains the effects that can be applied 
to an audio.
"""
from yta_validation.parameter import ParameterValidator
from yta_programming.decorators.requires_dependency import requires_dependency

import numpy as np
import librosa


class Filters:
    """
    Class to group all the audio filters that can
    be applied to the numpy array audio by using
    the static methods we define here.
    """

    @requires_dependency('scipy', 'yta_audio_editor', 'scipy')
    def _apply_filter(
        audio: 'np.ndarray',
        sample_rate: int,
        number_of_channels: int,
        order: int = 5,
        cut_off: float = 0.5,
        btype: str = 'low'
    ) -> 'np.ndarray':
        """
        *For internal use only*

        Apply a filter.

        TODO: Explain this method and the parameters
        """
        from scipy.signal import butter, lfilter

        # TODO: What is this 'nyq' var for and why is
        # it always the same (?)
        nyq = 0.5 * sample_rate
        # Why do we use this 'normal_cut_off' var (?)
        normal_cut_off = (cut_off / nyq)
        b, a = butter(order, normal_cut_off, btype = btype)
        # We need a copy to preserve the original
        audio = audio.copy()
        for ch in range(number_of_channels):
            audio[:, ch] = lfilter(b, a, audio[:, ch])

        return audio
    
    @requires_dependency('scipy', 'yta_audio_editor', 'scipy')
    @staticmethod
    def low_pass(
        audio: 'np.ndarray',
        sample_rate: int,
        number_of_channels: int,
    ) -> 'np.ndarray':
        """
        Apply a low pass filter in the given 'audio'.
        """
        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        ParameterValidator.validate_mandatory_positive_int('sample_rate', sample_rate)
        ParameterValidator.validate_mandatory_positive_int('number_of_channels', number_of_channels)
        # The original code was like this:
        # b, a = butter(4, 0.2, btype = 'low')
        # return lfilter(b, a, audio)
    
        return Filters._apply_filter(
            audio = audio,
            sample_rate = sample_rate,
            number_of_channels = number_of_channels,
            order = 4,
            cut_off = 0.4,
            btype = 'low'
        )

    @staticmethod
    def fadein(
        audio: 'np.ndarray',
        sample_rate: int,
        duration: float
    ) -> 'np.ndarray':
        """
        Apply a fade in effect.
        """
        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        ParameterValidator.validate_mandatory_positive_int('sample_rate', sample_rate)
        ParameterValidator.validate_mandatory_positive_float('duration', duration)

        number_of_samples = int(duration * sample_rate)
        fade = np.linspace(0, 1, number_of_samples)

        # TODO: Is this modifying the original by
        # reference? Maybe force a copy of it (?)
        audio[:number_of_samples] = audio[:number_of_samples] * fade[:, np.newaxis]
        
        return audio

    @staticmethod
    def fadeout(
        audio: 'np.ndarray',
        sample_rate: int,
        duration: float
    ) -> 'np.ndarray':
        """
        Apply a fade out effect.
        """
        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        ParameterValidator.validate_mandatory_positive_int('sample_rate', sample_rate)
        ParameterValidator.validate_mandatory_positive_float('duration', duration)

        number_of_samples = int(duration * sample_rate)
        fade = np.linspace(1, 0, number_of_samples)

        # TODO: Is this modifying the original by
        # reference? Maybe force a copy of it (?)
        audio[-number_of_samples:] = audio[-number_of_samples:] * fade[:, np.newaxis]

        return audio
    
    def reverb(
        audio: 'np.ndarray',
        impulse_response
    ):
        # TODO: Set the 'impulse_response' type
        from scipy.signal import fftconvolve

        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        # TODO: Validate 'impulse_response'

        return fftconvolve(audio, impulse_response, mode = 'full')
    
    # TODO: Maybe this below is not a filter
    def mute(
        audio: 'np.ndarray',
        sample_rate: int,
        start: float,
        end: float
    ):
        """
        Mute the part of the audio delimited by the
        given 'start' and 'end' time seconds.
        """
        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        ParameterValidator.validate_mandatory_positive_int('sample_rate', sample_rate)
        # TODO: Validate 'start' and 'end'

        audio[int(start * sample_rate):int(end * sample_rate)] = 0

        return audio
    
    # TODO: Maybe this below is not a filter
    def resample(
        audio: 'np.ndarray',
        original_sample_rate: int,
        new_sample_rate: int
    ):
        """
        Resample the given 'audio' to the new provided
        'new_sample_rate'.
        """
        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        ParameterValidator.validate_mandatory_positive_int('original_sample_rate', original_sample_rate)
        ParameterValidator.validate_mandatory_positive_int('new_sample_rate', new_sample_rate)

        return librosa.resample(audio, orig_sr = original_sample_rate, target_sr = new_sample_rate)
    
    # TODO: Maybe this below is not a filter
    def loop(
        audio: 'np.ndarray',
        times: int
    ):
        ParameterValidator.validate_mandatory_instance_of('audio', audio, 'np.ndarray')
        ParameterValidator.validate_mandatory_positive_int('times', times)

        return np.tile(audio, times)

    def distortion(
        audio: 'np.ndarray',
        threshold: float = 0.5
    ):
        # TODO: Explain this better and how the 'threshold'
        # affects to the effect
        return np.clip(audio, -threshold, threshold)
    
    def fft(
        audio: 'np.ndarray'
    ):
        """
        Get the magnitude of the Fourier spectrum per
        channel.
        """
        # TODO: Why per channel? Is it ok (?)
        return np.abs(np.fft.rfft(audio, axis = 0))
    
    def time_stretch(
        audio: 'np.ndarray',
        rate
    ):
        """
        Modify the duration of the audio but keeping 
        the pitch intact.

        This filter modifies the audio numpy array but
        also the number of samples so be careful.

        TODO: Explain what is the 'rate' parameter for.
        """
        y_stretched = librosa.effects.time_stretch(audio, rate)

        audio = y_stretched[:, np.newaxis]
        number_of_samples = audio.shape[0]

        # TODO: Not nice return...
        return audio, number_of_samples
    
    def pitch_shift(
        audio: 'np.ndarray',
        sample_rate: int,
        n_steps: int
    ):
        """
        Modify the pitch of the audio without modifying
        the audio duration, applying the effect to the
        audio as if it was a mono audio.

        This filter modifies the audio numpy array but
        also the number of samples so be careful.

        TODO: Explain what is the 'n_steps' parameter for.
        """
        y = librosa.to_mono(audio.T)
        y_shifted = librosa.effects.pitch_shift(y, sample_rate, n_steps)

        audio = y_shifted[:, np.newaxis]
        number_of_samples = audio.shape[0]

        # TODO: Not nice return...
        return audio, number_of_samples
    
"""
TODO: Keep going with more complex audio effects
"""