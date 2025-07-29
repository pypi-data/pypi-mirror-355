from typing import Tuple
from typing_extensions import override

from pysvg.schema import AppearanceConfig, TransformConfig
from pysvg.components.base import BaseSVGComponent, BaseSVGConfig
from pydantic import Field


class LineConfig(BaseSVGConfig):
    """Geometry configuration for Line components."""

    x1: float = Field(default=0, description="Line start X coordinate")
    y1: float = Field(default=0, description="Line start Y coordinate")
    x2: float = Field(default=0, description="Line end X coordinate")
    y2: float = Field(default=0, description="Line end Y coordinate")

    @override
    def to_svg_dict(self) -> dict[str, str]:
        """Convert config parameters to SVG attributes dictionary."""
        attrs = super().to_svg_dict()
        attrs = {k: str(v) for k, v in attrs.items()}
        return attrs


class Line(BaseSVGComponent):
    """
    SVG Line Component
    """

    def __init__(
        self,
        config: LineConfig | None = None,
        appearance: AppearanceConfig | None = None,
        transform: TransformConfig | None = None,
    ):
        super().__init__(
            config=config if config is not None else LineConfig(),
            appearance=appearance if appearance is not None else AppearanceConfig(),
            transform=transform if transform is not None else TransformConfig(),
        )

    @property
    def central_point(self) -> Tuple[float, float]:
        """
        Get the central point of the line (midpoint).

        Returns:
            Tuple of (center_x, center_y) coordinates
        """
        center_x = (self.config.x1 + self.config.x2) / 2
        center_y = (self.config.y1 + self.config.y2) / 2
        return (center_x, center_y)

    def to_svg_element(self) -> str:
        """
        Generate complete SVG line element string

        Returns:
            XML string of SVG line element
        """
        attrs = {}
        attrs.update(self.config.to_svg_dict())
        attrs.update(self.appearance.to_svg_dict())
        attrs.update(self.transform.to_svg_dict())
        attr_strings = [f'{key}="{value}"' for key, value in attrs.items()]
        return f"<line {' '.join(attr_strings)} />"

    def get_bounding_box(self) -> Tuple[float, float, float, float]:
        """
        Get line's bounding box (without considering transformations)

        Returns:
            (min_x, min_y, max_x, max_y) bounding box coordinates
        """
        min_x = min(self.config.x1, self.config.x2)
        max_x = max(self.config.x1, self.config.x2)
        min_y = min(self.config.y1, self.config.y2)
        max_y = max(self.config.y1, self.config.y2)
        return (min_x, min_y, max_x, max_y)

    def get_length(self) -> float:
        """
        Calculate the length of the line

        Returns:
            Line length
        """
        import math

        dx = self.config.x2 - self.config.x1
        dy = self.config.y2 - self.config.y1
        return math.sqrt(dx**2 + dy**2)

    def get_slope(self) -> float | None:
        """
        Calculate the slope of the line

        Returns:
            Line slope, or None if the line is vertical
        """
        dx = self.config.x2 - self.config.x1
        if dx == 0:
            return None  # Vertical line
        dy = self.config.y2 - self.config.y1
        return dy / dx

    def get_angle(self) -> float:
        """
        Calculate the angle of the line in degrees

        Returns:
            Line angle in degrees (0-360)
        """
        import math

        dx = self.config.x2 - self.config.x1
        dy = self.config.y2 - self.config.y1
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        return angle_deg if angle_deg >= 0 else angle_deg + 360
