from typing import Union, final
from time import monotonic, sleep

Clock_attr = dict()

@final
class Clock:

    __slots__ = ()

    def __new__(cls) -> 'Clock':
        if not isinstance(Clock_attr.get('instance', None), Clock):
            Clock_attr['instance'] = super().__new__(cls)

        Clock_attr['last_tick'] = monotonic()
        Clock_attr['time_elapsed'] = 0.0
        Clock_attr['raw_time'] = 0.0
        Clock_attr['fps'] = 0.0

        return Clock_attr['instance']

    def tick(self, framerate: Union[int, float]) -> float:
        current_time = monotonic()
        elapsed_time = current_time - Clock_attr['last_tick']

        if framerate > 0:
            min_frame_time = 1 / framerate
            if elapsed_time < min_frame_time:
                sleep(min_frame_time - elapsed_time)

        current_time = monotonic()

        Clock_attr['fps'] = 1 / (current_time - Clock_attr['last_tick']) if current_time != Clock_attr['last_tick'] else 0.0
        Clock_attr['time_elapsed'] = current_time - Clock_attr['last_tick']
        Clock_attr['raw_time'] = elapsed_time
        Clock_attr['last_tick'] = current_time

        return Clock_attr['time_elapsed']

    def get_time(self) -> float:
        return Clock_attr['time_elapsed']

    def get_rawtime(self) -> float:
        return Clock_attr['raw_time']

    def get_fps(self) -> float:
        return Clock_attr['fps']