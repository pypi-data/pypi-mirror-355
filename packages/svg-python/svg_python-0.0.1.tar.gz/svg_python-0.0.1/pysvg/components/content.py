from typing import Literal, Tuple
from pydantic import Field
from typing_extensions import override

from pysvg.schema import TransformConfig, BaseSVGConfig, Color, SVGCode
from pysvg.components.base import BaseSVGComponent


class TextConfig(BaseSVGConfig):
    """Geometry configuration for Text components"""

    x: float = Field(
        default=0, description="Text x position , central(default) or left-upper corner)"
    )
    y: float = Field(
        default=0, description="Text y position , central(default) or left-upper corner)"
    )
    text: str = Field(description="Text content to display")
    font_size: float = Field(default=12, ge=0, description="Font size")
    font_family: str = Field(default="Arial", description="Font family")
    color: Color = Field(default=Color("black"), description="Text color")
    text_anchor: Literal["start", "middle", "end"] = Field(
        default="middle", description="Text alignment"
    )
    dominant_baseline: Literal["auto", "middle", "hanging", "central"] = Field(
        default="central", description="Vertical text alignment"
    )


class ImageConfig(BaseSVGConfig):
    """Geometry configuration for Image components"""

    x: float = Field(default=0, description="Image x position")
    y: float = Field(default=0, description="Image y position")
    width: float = Field(default=100, ge=0, description="Image width")
    height: float = Field(default=100, ge=0, description="Image height")
    href: str = Field(description="Image path or URL")
    preserveAspectRatio: str = Field(
        default="xMidYMid meet", description="How to preserve aspect ratio"
    )


class SVGConfig(BaseSVGConfig):
    """Geometry configuration for SVG components"""

    x: float = Field(default=0, description="SVG x position")
    y: float = Field(default=0, description="SVG y position")
    width: float = Field(default=100, ge=0, description="SVG width")
    height: float = Field(default=100, ge=0, description="SVG height")
    svg_content: SVGCode = Field(description="Raw SVG component code")


class TextContent(BaseSVGComponent):
    """Text content component for SVG"""

    def __init__(self, config: TextConfig, transform: TransformConfig | None = None):
        super().__init__(config=config, transform=transform if transform else TransformConfig())

    @property
    def central_point(self) -> Tuple[float, float]:
        """Get the central point of the text"""
        raise NotImplementedError("TextContent does not have a central point")

    @override
    def to_svg_element(self) -> str:
        """Generate SVG text element"""
        attrs = [
            f'x="{self.config.x}"',
            f'y="{self.config.y}"',
            f'font-size="{self.config.font_size}"',
            f'font-family="{self.config.font_family}"',
            f'fill="{self.config.color.value}"',
            f'text-anchor="{self.config.text_anchor}"',
            f'dominant-baseline="{self.config.dominant_baseline}"',
        ]

        # Add transform if present
        if self.has_transform():
            transform_dict = self.transform.to_svg_dict()
            if "transform" in transform_dict and transform_dict["transform"] != "none":
                attrs.append(f'transform="{transform_dict["transform"]}"')

        return f"<text {' '.join(attrs)}>{self.config.text}</text>"


class ImageContent(BaseSVGComponent):
    """Image content component for SVG"""

    def __init__(self, config: ImageConfig, transform: TransformConfig | None = None):
        super().__init__(config=config, transform=transform if transform else TransformConfig())

    @property
    def central_point(self) -> Tuple[float, float]:
        """Get the central point of the image"""
        center_x = self.config.x + self.config.width / 2
        center_y = self.config.y + self.config.height / 2
        return (center_x, center_y)

    @override
    def to_svg_element(self) -> str:
        """Generate SVG image element"""
        attrs = [
            f'x="{self.config.x}"',
            f'y="{self.config.y}"',
            f'width="{self.config.width}"',
            f'height="{self.config.height}"',
            f'href="{self.config.href}"',
            f'preserveAspectRatio="{self.config.preserveAspectRatio}"',
        ]

        # Add transform if present
        if self.has_transform():
            transform_dict = self.transform.to_svg_dict()
            if "transform" in transform_dict and transform_dict["transform"] != "none":
                attrs.append(f'transform="{transform_dict["transform"]}"')

        return f"<image {' '.join(attrs)} />"


class SVGContent(BaseSVGComponent):
    """SVG content component for nested SVG"""

    def __init__(self, config: SVGConfig, transform: TransformConfig | None = None):
        super().__init__(config=config, transform=transform if transform else TransformConfig())

    @property
    def central_point(self) -> Tuple[float, float]:
        """Get the central point of the SVG"""
        center_x = self.config.x + self.config.width / 2
        center_y = self.config.y + self.config.height / 2
        return (center_x, center_y)

    @override
    def to_svg_element(self) -> str:
        """Generate nested SVG element"""
        attrs = [
            f'x="{self.config.x}"',
            f'y="{self.config.y}"',
            f'width="{self.config.width}"',
            f'height="{self.config.height}"',
            f'viewBox="0 0 {self.config.width} {self.config.height}"',
        ]

        # Add transform if present
        if self.has_transform():
            transform_dict = self.transform.to_svg_dict()
            if "transform" in transform_dict and transform_dict["transform"] != "none":
                attrs.append(f'transform="{transform_dict["transform"]}"')

        return f"<svg {' '.join(attrs)}>{self.config.svg_content}</svg>"
