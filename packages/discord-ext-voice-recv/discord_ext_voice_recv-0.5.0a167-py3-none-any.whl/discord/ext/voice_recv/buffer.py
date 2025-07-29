# -*- coding: utf-8 -*-

from __future__ import annotations

import heapq
import logging
import threading

from .utils import gap_wrapped, add_wrapped


from typing import (
    TYPE_CHECKING,
    Protocol,
    TypeVar,
)

from .rtp import _PacketCmpMixin

if TYPE_CHECKING:
    from typing import Optional, List
    from .rtp import AudioPacket

__all__ = [
    'HeapJitterBuffer',
]


_T = TypeVar('_T')
PacketT = TypeVar('PacketT', bound=_PacketCmpMixin)


log = logging.getLogger(__name__)


class Buffer(Protocol[_T]):
    """The base class representing a simple buffer with no extra features."""

    # fmt: off
    def __len__(self) -> int: ...
    def push(self, item: _T) -> None: ...
    def pop(self) -> Optional[_T]: ...
    def peek(self) -> Optional[_T]: ...
    def flush(self) -> List[_T]: ...
    def reset(self) -> None: ...
    # fmt: on


# class RetainingBuffer(Buffer[_T], Protocol):
#     """A buffer that retains an arbitrary number of items."""

#     maxsize: int
#     prefsize: int
#     prefill: int


# class SortedBuffer(Buffer[_T], Protocol):
#     """A buffer that maintains a sorted internal state."""


# class WindowedBuffer(Buffer[_T], Protocol):
#     """A buffer with arbitrarily windowed output."""

#     window_start: float
#     window_end: float

#     # fmt: off
#     def pop(self) -> List[_T]: ...
#     def peek(self) -> Optional[List[_T]]: ...
#     def flush(self) -> List[List[_T]]: ...
#     # fmt: on


class BaseBuffer(Buffer[PacketT]):
    """A basic buffer."""

    def __init__(self):
        self._buffer: List[PacketT] = []

    def __len__(self) -> int:
        return len(self._buffer)

    def push(self, item: PacketT) -> None:
        self._buffer.append(item)

    def pop(self) -> Optional[PacketT]:
        return self._buffer.pop()

    def peek(self) -> Optional[PacketT]:
        return self._buffer[-1] if self._buffer else None

    def flush(self) -> List[PacketT]:
        buf = self._buffer.copy()
        self._buffer.clear()
        return buf

    def reset(self) -> None:
        self._buffer.clear()


# class RetensionBuffer(BaseBuffer[PacketT], RetainingBuffer):
#     def __init__(self, maxsize: int = 10, *, prefsize: int = 1, prefill: int = 1):
#         if maxsize < 1:
#             raise ValueError(f'maxsize ({maxsize}) must be greater than 0')

#         if not 0 <= prefsize <= maxsize:
#             raise ValueError(f'prefsize must be between 0 and maxsize ({maxsize})')

#         super().__init__()
#         self.maxsize: int = maxsize
#         self.prefsize: int = prefsize
#         self.prefill: int = prefill


class HeapJitterBuffer(BaseBuffer[PacketT]):
    """Push item in, pop items out"""

    _threshold: int = 10000

    def __init__(self, maxsize: int = 10, *, prefsize: int = 1, prefill: int = 1):
        if maxsize < 1:
            raise ValueError(f'maxsize ({maxsize}) must be greater than 0')

        if not 0 <= prefsize <= maxsize:
            raise ValueError(f'prefsize must be between 0 and maxsize ({maxsize})')

        self.maxsize: int = maxsize
        self.prefsize: int = prefsize
        self.prefill: int = prefill
        self._prefill: int = prefill

        self._last_tx_seq: int = -1

        self._has_item: threading.Event = threading.Event()
        # I sure hope I dont need to add a lock to this
        self._buffer: List[AudioPacket] = []

    def _push(self, packet: AudioPacket) -> None:
        heapq.heappush(self._buffer, packet)

    def _pop(self) -> AudioPacket:
        return heapq.heappop(self._buffer)

    def _get_packet_if_ready(self) -> Optional[AudioPacket]:
        return self._buffer[0] if len(self._buffer) > self.prefsize else None

    def _pop_if_ready(self) -> Optional[AudioPacket]:
        return self._pop() if len(self._buffer) > self.prefsize else None

    def _update_has_item(self) -> None:
        prefilled = self._prefill == 0
        packet_ready = len(self._buffer) > self.prefsize

        if not prefilled or not packet_ready:
            self._has_item.clear()
            return

        next_packet = self._buffer[0]
        sequential = add_wrapped(self._last_tx_seq, 1) == next_packet.sequence
        positive_seq = self._last_tx_seq >= 0

        # We have the next packet ready
        # OR we havent sent a packet out yet
        # OR the buffer is full
        if (sequential and positive_seq) or not positive_seq or len(self._buffer) >= self.maxsize:
            self._has_item.set()
        else:
            self._has_item.clear()

    def _cleanup(self) -> None:
        # Logging this is pointless until I fix the stale remote buffer issue
        # if len(self._buffer) > self.maxsize:
        #     log.debug("Buffer overfilled: %s > %s", len(self._buffer), self.maxsize)

        # drop oldest packets if buffer overfilled
        while len(self._buffer) > self.maxsize:
            packet = heapq.heappop(self._buffer)
            # log.debug("Dropped extra packet %s", packet)

    def push(self, packet: AudioPacket) -> bool:
        """
        Push a packet into the buffer.  If the packet would make the buffer
        exceed its maxsize, the oldest packet will be dropped.
        """

        seq = packet.sequence

        # for the gap between _last_tx_seq and the current one, a large gap is old, a small gap is new
        # the gap for old packets will generally be very large since they wrap all the way around
        if gap_wrapped(self._last_tx_seq, seq) > self._threshold and self._last_tx_seq != -1:
            log.debug("Dropping old packet %s", packet)
            return False

        self._push(packet)

        if self._prefill > 0:
            self._prefill -= 1

        self._cleanup()
        self._update_has_item()

        return True

    def pop(self, *, timeout: float | None = 0) -> Optional[AudioPacket]:
        """
        If timeout is a positive number, wait as long as timeout for a packet
        to be ready and return that packet, otherwise return None.
        """

        ok = self._has_item.wait(timeout)
        if not ok:
            return None

        if self._prefill > 0:
            return None

        # This function should actually be redundant but i'll leave it for now
        packet = self._pop_if_ready()

        if packet is not None:
            self._last_tx_seq = packet.sequence

        self._update_has_item()
        return packet

    def peek(self, *, all: bool = False) -> Optional[AudioPacket]:
        """
        Returns the next packet in the buffer only if it is ready, meaning it can
        be popped. When `all` is set to True, it returns the next packet, if any.
        """

        if not self._buffer:
            return None

        if all:
            return self._buffer[0]
        else:
            return self._get_packet_if_ready()

    def peek_next(self) -> Optional[AudioPacket]:
        """
        Returns the next packet in the buffer only if it is sequential.
        """

        packet = self.peek(all=True)

        if packet is None:
            return

        if packet.sequence == add_wrapped(self._last_tx_seq, 1) or self._last_tx_seq < 0:
            return packet

    def gap(self) -> int:
        """
        Returns the number of missing packets between the last packet to be
        popped and the currently held next packet.  Returns 0 otherwise.
        """

        if self._buffer and self._last_tx_seq > 0:
            return gap_wrapped(self._last_tx_seq, self._buffer[0].sequence)

        return 0

    def flush(self) -> List[AudioPacket]:
        """
        Return all remaining packets.
        """

        packets = sorted(self._buffer)
        self._buffer.clear()

        if packets:
            self._last_tx_seq = packets[-1].sequence

        self._prefill = self.prefill
        self._has_item.clear()

        return packets

    def reset(self) -> None:
        """
        Clear buffer and reset internal counters.
        """

        self._buffer.clear()
        self._has_item.clear()
        self._prefill = self.prefill
        self._last_tx_seq = -1


# class WindowBuffer(Generic[PacketT]):
#     def __init__(self, window_duration: float, *, time_func: Callable[[], float] = time.time):
#         self.window_duration: float = window_duration
#         self.time = time_func

#         self._buffer: List[Tuple[PacketT, float]] = []
#         self._start: float = 0
#         self._current_window: int = 1
#         self._lock = threading.Lock()

#         self.add_item = self._add_once

#     @property
#     def window_start(self) -> float:
#         return self._start + self._current_window * self.window_duration

#     @property
#     def window_end(self) -> float:
#         return self.window_start + self.window_duration

#     def _add_once(self, item: PacketT) -> None:
#         self._start = self.time()
#         self.add_item = self._add_item
#         return self.add_item(item)

#     def _add_item(self, item: PacketT) -> None:
#         with self._lock:
#             self._buffer.append((item, self.time()))

#     # stub
#     def add_item(self, item: PacketT) -> None:
#         pass

#     def reset(self) -> None:
#         with self._lock:
#             self._buffer.clear()
#             self._start = 0
#             self._current_window = 1
#             self.add_item = self._add_once

#     def get_last_window_number(self) -> int:
#         return self._current_window - 1

#     def get_window_number_at(self, when: Optional[float] = None) -> int:
#         # TODO: check to see if this logic is sane
#         return int(((when or self.time()) - self._start) / self.window_duration)

#     def get_time_until_current_window_end(self) -> float:
#         return self.window_end - self.time()

#     def get_next_window(self, *, skip_empty: bool = False) -> Sequence[PacketT]:
#         time.sleep(self.get_time_until_current_window_end())

#         with self._lock:
#             window = None
#             while not window:
#                 window = self._generate_window()
#                 self._current_window += 1
#                 if not skip_empty:
#                     break
#         return window

#     def _generate_window(self) -> List[PacketT]:
#         window = []

#         # I could just splice the list and not do this dumb copy but eh
#         for pair in self._buffer.copy():
#             item, when = pair
#             if self.window_start <= when < self.window_end:
#                 window.append(item)
#                 self._buffer.remove(pair)

#         return window

#     @classmethod
#     def sync(cls, *buffers: WindowBuffer, start_time: float) -> None:
#         for buffer in buffers:
#             buffer.reset()
#             buffer.add_item = buffer._add_item
#             buffer._start = start_time


# 1. Basic buffer with max size/retention capabilities
# 2. Sorted buffer?
# 3. Windowed buffer
# 4. Controller for grouping and syncing multiple buffers (for muxer etc)
