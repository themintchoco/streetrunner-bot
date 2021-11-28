import functools
import itertools
import math

from colour import Color


class ColorEffect:
    animated = False

    def __init__(self, *color, duration=1, **kwargs):
        self.duration = duration
        self.alpha = kwargs.pop('alpha', 1)

        if isinstance(color[0], Color):
            self.color = color
        else:
            self.color = (Color(*color, **kwargs),)

    def __getitem__(self, t):
        return self.color[0]

    def __iter__(self):
        for i in range(self.duration):
            yield self[i]

    def rgba(self, color):
        if isinstance(color, int):
            color = self[color]

        return tuple(int(i * 255) for i in (*color.rgb, self.alpha))


class ColorEffectBlink(ColorEffect):
    animated = True

    def __getitem__(self, t):
        return self.color[round(self.time_function(t) // (1 / len(self.color)))]

    def time_function(self, t):
        return t / self.duration


class ColorEffectUnicorn(ColorEffect):
    animated = True

    def __getitem__(self, t):
        return self.spectrum[round(min(self.time_function(t) * 100 * (len(self.color) - 1), len(self.spectrum) - 1))]

    @functools.cached_property
    def spectrum(self):
        return list(itertools.chain(*(self.color[i].range_to(self.color[i + 1], 100)
                                      for i in range(len(self.color) - 1)))) if len(self.color) > 1 else [self.color[0]]

    def time_function(self, t):
        return t / self.duration


class ColorEffectBreathe(ColorEffectUnicorn):
    def __init__(self, *color, inhale_rate=1.4, exhale_rate=1.4, **kwargs):
        super().__init__(*color, **kwargs)
        self.inhale_rate = inhale_rate
        self.exhale_rate = exhale_rate

    def time_function(self, t):
        return min(math.e ** (self.inhale_rate * t / self.duration) - 1,
                   math.e ** (-self.exhale_rate * (t / self.duration - 1)) - 1,
                   1)
