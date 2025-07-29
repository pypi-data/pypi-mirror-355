from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .config import LargeScaleChangeModel


class LargeScaleChangeException(Exception):
    """
    Can be raised to indicate this is a large-scale change,
    often triggered by a diff so large the platform complains about it.
    """

    def __init__(self, large_scale_change: "LargeScaleChangeModel" = None) -> None:
        super().__init__("Large scale change detected")
        self.large_scale_change = large_scale_change
