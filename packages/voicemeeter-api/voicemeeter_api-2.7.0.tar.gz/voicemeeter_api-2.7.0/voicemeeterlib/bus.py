import time
from abc import abstractmethod
from enum import IntEnum
from math import log
from typing import Union

from . import kinds
from .iremote import IRemote
from .meta import bus_mode_prop, device_prop, float_prop

BusModes = IntEnum(
    'BusModes',
    'normal amix bmix repeat composite tvmix upmix21 upmix41 upmix61 centeronly lfeonly rearonly',
    start=0,
)


class Bus(IRemote):
    """
    Implements the common interface

    Defines concrete implementation for bus
    """

    @abstractmethod
    def __str__(self):
        pass

    @property
    def identifier(self) -> str:
        return f'bus[{self.index}]'

    @property
    def mute(self) -> bool:
        return self.getter('mute') == 1

    @mute.setter
    def mute(self, val: bool):
        self.setter('mute', 1 if val else 0)

    @property
    def mono(self) -> bool:
        return self.getter('mono') == 1

    @mono.setter
    def mono(self, val: bool):
        self.setter('mono', 1 if val else 0)

    @property
    def sel(self) -> bool:
        return self.getter('sel') == 1

    @sel.setter
    def sel(self, val: bool):
        self.setter('sel', 1 if val else 0)

    @property
    def label(self) -> str:
        return self.getter('Label', is_string=True)

    @label.setter
    def label(self, val: str):
        self.setter('Label', str(val))

    @property
    def gain(self) -> float:
        return round(self.getter('gain'), 1)

    @gain.setter
    def gain(self, val: float):
        self.setter('gain', val)

    @property
    def monitor(self) -> bool:
        return self.getter('monitor') == 1

    @monitor.setter
    def monitor(self, val: bool):
        self.setter('monitor', 1 if val else 0)

    def fadeto(self, target: float, time_: int):
        self.setter('FadeTo', f'({target}, {time_})')
        time.sleep(self._remote.DELAY)

    def fadeby(self, change: float, time_: int):
        self.setter('FadeBy', f'({change}, {time_})')
        time.sleep(self._remote.DELAY)


class BusEQ(IRemote):
    @classmethod
    def make(cls, remote, i):
        """
        Factory method for BusEQ.

        Returns a BusEQ class.
        """
        kls = (cls,)
        BusEQ_cls = type(
            'BusEQ',
            kls,
            {
                'channel': tuple(
                    BusEQCh.make(remote, i, j) for j in range(remote.kind.channels)
                )
            },
        )
        return BusEQ_cls(remote, i)

    @property
    def identifier(self) -> str:
        return f'Bus[{self.index}].eq'

    @property
    def on(self) -> bool:
        return self.getter('on') == 1

    @on.setter
    def on(self, val: bool):
        self.setter('on', 1 if val else 0)

    @property
    def ab(self) -> bool:
        return self.getter('ab') == 1

    @ab.setter
    def ab(self, val: bool):
        self.setter('ab', 1 if val else 0)


class BusEQCh(IRemote):
    @classmethod
    def make(cls, remote, i, j):
        """
        Factory method for Bus EQ channel.

        Returns a BusEQCh class.
        """
        kls = (cls,)
        BusEQCh_cls = type(
            'BusEQCh',
            kls,
            {
                'cell': tuple(
                    BusEQChCell(remote, i, j, k) for k in range(remote.kind.cells)
                )
            },
        )
        return BusEQCh_cls(remote, i, j)

    def __init__(self, remote, i, j):
        super().__init__(remote, i)
        self.channel_index = j

    @property
    def identifier(self) -> str:
        return f'Bus[{self.index}].eq.channel[{self.channel_index}]'


class BusEQChCell(IRemote):
    def __init__(self, remote, i, j, k):
        super().__init__(remote, i)
        self.channel_index = j
        self.cell_index = k

    @property
    def identifier(self) -> str:
        return f'Bus[{self.index}].eq.channel[{self.channel_index}].cell[{self.cell_index}]'

    @property
    def on(self) -> bool:
        return self.getter('on') == 1

    @on.setter
    def on(self, val: bool):
        self.setter('on', 1 if val else 0)

    @property
    def type(self) -> int:
        return int(self.getter('type'))

    @type.setter
    def type(self, val: int):
        self.setter('type', val)

    @property
    def f(self) -> float:
        return round(self.getter('f'), 1)

    @f.setter
    def f(self, val: float):
        self.setter('f', val)

    @property
    def gain(self) -> float:
        return round(self.getter('gain'), 1)

    @gain.setter
    def gain(self, val: float):
        self.setter('gain', val)

    @property
    def q(self) -> float:
        return round(self.getter('q'), 1)

    @q.setter
    def q(self, val: float):
        self.setter('q', val)


class PhysicalBus(Bus):
    @classmethod
    def make(cls, remote, i, kind):
        """
        Factory method for PhysicalBus.

        Returns a PhysicalBus class.
        """
        kls = (cls,)
        if kind.name == 'potato':
            EFFECTS_cls = _make_effects_mixin()
            kls += (EFFECTS_cls,)
        return type(
            'PhysicalBus',
            kls,
            {
                'device': BusDevice.make(remote, i),
            },
        )

    def __str__(self):
        return f'{type(self).__name__}{self.index}'


class BusDevice(IRemote):
    @classmethod
    def make(cls, remote, i):
        """
        Factory function for bus.device.

        Returns a BusDevice class of a kind.
        """
        DEVICE_cls = type(
            f'BusDevice{remote.kind}',
            (cls,),
            {
                **{
                    param: device_prop(param)
                    for param in [
                        'wdm',
                        'ks',
                        'mme',
                        'asio',
                    ]
                },
            },
        )
        return DEVICE_cls(remote, i)

    @property
    def identifier(self) -> str:
        return f'Bus[{self.index}].device'

    @property
    def name(self) -> str:
        return self.getter('name', is_string=True)

    @property
    def sr(self) -> int:
        return int(self.getter('sr'))


class VirtualBus(Bus):
    @classmethod
    def make(cls, remote, i, kind):
        """
        Factory method for VirtualBus.

        If basic kind subclass physical bus.

        Returns a VirtualBus class.
        """
        kls = (cls,)
        if kind.name == 'basic':
            return type(
                'VirtualBus',
                kls,
                {
                    'device': BusDevice.make(remote, i),
                },
            )
        elif kind.name == 'potato':
            EFFECTS_cls = _make_effects_mixin()
            kls += (EFFECTS_cls,)
        return type('VirtualBus', kls, {})

    def __str__(self):
        return f'{type(self).__name__}{self.index}'


class BusLevel(IRemote):
    def __init__(self, remote, index):
        super().__init__(remote, index)
        self.range = _make_bus_level_maps[remote.kind.name][self.index]

    def getter(self, mode):
        """
        Returns a tuple of level values for the channel.

        If observables thread running and level updates are subscribed to, fetch values from cache

        Otherwise call CAPI func.
        """

        def fget(x):
            return round(20 * log(x, 10), 1) if x > 0 else -200.0

        if not self._remote.stopped() and self._remote.event.ldirty:
            vals = self._remote.cache['bus_level'][self.range[0] : self.range[-1]]
        else:
            vals = [self._remote.get_level(mode, i) for i in range(*self.range)]

        return tuple(fget(val) for val in vals)

    @property
    def identifier(self) -> str:
        return f'Bus[{self.index}]'

    @property
    def all(self) -> tuple:
        return self.getter(3)

    @property
    def isdirty(self) -> bool:
        """
        Returns dirty status for this specific channel.

        Expected to be used in a callback only.
        """
        if not self._remote.stopped():
            return any(self._remote._bus_comp[self.range[0] : self.range[-1]])

    is_updated = isdirty


def make_bus_level_map(kind):
    return tuple((i, i + 8) for i in range(0, (kind.phys_out + kind.virt_out) * 8, 8))


_make_bus_level_maps = {kind.name: make_bus_level_map(kind) for kind in kinds.all}


def _make_bus_mode_mixin():
    """Creates a mixin of Bus Modes."""

    def identifier(self) -> str:
        return f'Bus[{self.index}].mode'

    def get(self) -> str:
        time.sleep(0.01)
        for i, val in enumerate(
            [
                self.amix,
                self.bmix,
                self.repeat,
                self.composite,
                self.tvmix,
                self.upmix21,
                self.upmix41,
                self.upmix61,
                self.centeronly,
                self.lfeonly,
                self.rearonly,
            ]
        ):
            if val:
                return BusModes(i + 1).name
        return 'normal'

    return type(
        'BusModeMixin',
        (IRemote,),
        {
            'identifier': property(identifier),
            **{mode.name: bus_mode_prop(mode.name) for mode in BusModes},
            'get': get,
        },
    )


def _make_effects_mixin():
    """creates an fx mixin"""
    return type(
        'FX',
        (),
        {
            **{
                f'return{param}': float_prop(f'return{param}')
                for param in ['reverb', 'delay', 'fx1', 'fx2']
            },
        },
    )


def bus_factory(is_phys_bus, remote, i) -> Union[PhysicalBus, VirtualBus]:
    """
    Factory method for buses

    Returns a physical or virtual bus subclass
    """
    BUS_cls = (
        PhysicalBus.make(remote, i, remote.kind)
        if is_phys_bus
        else VirtualBus.make(remote, i, remote.kind)
    )
    BUSMODEMIXIN_cls = _make_bus_mode_mixin()
    return type(
        f'{BUS_cls.__name__}{remote.kind}',
        (BUS_cls,),
        {
            'levels': BusLevel(remote, i),
            'mode': BUSMODEMIXIN_cls(remote, i),
            'eq': BusEQ.make(remote, i),
        },
    )(remote, i)


def request_bus_obj(phys_bus, remote, i) -> Bus:
    """
    Bus entry point. Wraps factory method.

    Returns a reference to a bus subclass of a kind
    """
    return bus_factory(phys_bus, remote, i)
