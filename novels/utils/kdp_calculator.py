"""
KDP Cover Dimension Calculator.

Implements Amazon KDP's official formulas for:
  - eBook cover recommended resolution
  - Paperback full-cover dimensions (with bleed + spine)

Reference: https://kdp.amazon.com/en_US/help/topic/G200645690
"""

from dataclasses import dataclass
from typing import Optional
from novels.models.cover import PaperType, TrimSize

BLEED_IN = 0.125   # standard KDP bleed on each edge (inches)
PRINT_DPI = 300    # standard print DPI

# eBook recommended dimensions
EBOOK_WIDTH_PX  = 1600
EBOOK_HEIGHT_PX = 2560


@dataclass
class EbookDimensions:
    width_px: int
    height_px: int
    aspect_ratio: float
    file_size_kb_approx: int

    def to_dict(self) -> dict:
        return {
            'cover_type': 'ebook',
            'width_px': self.width_px,
            'height_px': self.height_px,
            'aspect_ratio': round(self.aspect_ratio, 4),
            'file_size_kb_approx': self.file_size_kb_approx,
            'notes': [
                f'Recommended: {self.width_px}×{self.height_px} px at 72 DPI',
                'Format: JPEG or TIFF, RGB color space',
                'Aspect ratio 1:1.6 (width:height)',
                'Maximum file size: 50 MB',
            ],
        }


@dataclass
class PaperbackDimensions:
    trim_width_in: float
    trim_height_in: float
    spine_width_in: float
    total_width_in: float
    total_height_in: float
    total_width_px: int
    total_height_px: int
    bleed_in: float
    dpi: int
    page_count: int
    paper_type: str
    trim_size: str

    def to_dict(self) -> dict:
        return {
            'cover_type': 'paperback',
            'trim_size': self.trim_size,
            'paper_type': self.paper_type,
            'page_count': self.page_count,
            'dpi': self.dpi,
            'bleed_in': self.bleed_in,
            'trim_width_in': round(self.trim_width_in, 4),
            'trim_height_in': round(self.trim_height_in, 4),
            'spine_width_in': round(float(self.spine_width_in), 4),
            'total_width_in': round(float(self.total_width_in), 4),
            'total_height_in': round(float(self.total_height_in), 4),
            'total_width_px': self.total_width_px,
            'total_height_px': self.total_height_px,
            'notes': [
                f'Full cover width: {round(float(self.total_width_in), 4)}" '
                f'= back ({self.trim_width_in}") + spine ({round(float(self.spine_width_in), 4)}") '
                f'+ front ({self.trim_width_in}") + bleed ({self.bleed_in * 2}")',
                f'Full cover height: {round(float(self.total_height_in), 4)}" '
                f'= trim ({self.trim_height_in}") + bleed ({self.bleed_in * 2}")',
                f'Canvas size: {self.total_width_px} × {self.total_height_px} px at {self.dpi} DPI',
                'Format: PDF (print-ready), RGB or CMYK',
                'Minimum 300 DPI required',
            ],
        }


def calc_ebook(
    width_px: int = EBOOK_WIDTH_PX,
    height_px: int = EBOOK_HEIGHT_PX,
) -> EbookDimensions:
    """Return eBook cover dimension spec."""
    aspect = height_px / width_px
    # Rough estimate: JPEG ~0.5 bit/px
    file_kb = int((width_px * height_px * 3) / 1024 / 4)
    return EbookDimensions(
        width_px=width_px,
        height_px=height_px,
        aspect_ratio=aspect,
        file_size_kb_approx=file_kb,
    )


def calc_paperback(
    trim_size: str,
    paper_type: str,
    page_count: int,
    dpi: int = PRINT_DPI,
    bleed_in: float = BLEED_IN,
) -> Optional[PaperbackDimensions]:
    """
    Calculate full-cover dimensions for a KDP paperback.

    Returns None if trim_size or paper_type is unknown.
    """
    if trim_size not in TrimSize.DIMENSIONS:
        return None
    if paper_type not in PaperType.SPINE_MULTIPLIER:
        return None

    trim_w, trim_h = TrimSize.DIMENSIONS[trim_size]
    multiplier = PaperType.SPINE_MULTIPLIER[paper_type]
    spine_w = page_count * multiplier

    # Full wrap dimensions
    total_w = bleed_in + trim_w + spine_w + trim_w + bleed_in
    total_h = bleed_in + trim_h + bleed_in

    return PaperbackDimensions(
        trim_width_in=trim_w,
        trim_height_in=trim_h,
        spine_width_in=spine_w,
        total_width_in=total_w,
        total_height_in=total_h,
        total_width_px=int(round(total_w * dpi)),
        total_height_px=int(round(total_h * dpi)),
        bleed_in=bleed_in,
        dpi=dpi,
        page_count=page_count,
        paper_type=paper_type,
        trim_size=trim_size,
    )


def get_trim_size_choices() -> list[dict]:
    return [{'value': v, 'label': l} for v, l in TrimSize.CHOICES]


def get_paper_type_choices() -> list[dict]:
    return [{'value': v, 'label': l} for v, l in PaperType.CHOICES]
