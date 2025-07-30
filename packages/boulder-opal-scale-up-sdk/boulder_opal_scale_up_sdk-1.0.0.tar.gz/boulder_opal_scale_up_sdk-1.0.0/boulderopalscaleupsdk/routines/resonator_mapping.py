from pydantic import PrivateAttr

from boulderopalscaleupsdk.routines.common import Routine


class ResonatorMapping(Routine):
    """
    Parameters for running a resonator mapping routine.
    """

    _routine_name: str = PrivateAttr("resonator_mapping")

    feedlines: list[str]
