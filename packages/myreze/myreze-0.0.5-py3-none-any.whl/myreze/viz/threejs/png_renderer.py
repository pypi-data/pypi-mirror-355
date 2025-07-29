from myreze.viz.threejs.threejs import ThreeJSRenderer
from typing import Dict, Any, Optional
import base64


@ThreeJSRenderer.register
class THREEPNGRenderer(ThreeJSRenderer):
    """Render PNG bytes for Three.js visualization."""

    def render(
        self, data: Dict[str, Any], params: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Render the data package as PNG bytes.

        Args:
            data: Data dictionary containing base64-encoded PNG data
            params: Optional rendering parameters (unused for PNG)

        Returns:
            PNG image as bytes
        """
        if params is None:
            params = {}

        # Extract base64-encoded PNG data from the data dictionary
        png_bytes_b64 = data.get("png_bytes")
        if png_bytes_b64 is None:
            raise ValueError("No 'png_bytes' data found in data dictionary")

        # Handle both single PNG and lists of PNGs
        if isinstance(png_bytes_b64, list):
            # For now, use the first PNG in the series
            # TODO: Could be extended to create animated PNG or multiple PNGs
            if len(png_bytes_b64) == 0:
                raise ValueError("Empty png_bytes list")

            # Decode the first base64 string back to bytes
            return base64.b64decode(png_bytes_b64[0])
        elif isinstance(png_bytes_b64, str):
            # Decode base64 string back to bytes
            return base64.b64decode(png_bytes_b64)
        else:
            # Handle bytes for backwards compatibility
            if isinstance(png_bytes_b64, bytes):
                return png_bytes_b64
            else:
                raise ValueError(
                    f"png_bytes must be base64 string or bytes, "
                    f"got {type(png_bytes_b64)}"
                )


@ThreeJSRenderer.register
class PNGTexture(THREEPNGRenderer):
    """Alias for THREEPNGRenderer to match usage in NWSRadarProduct."""

    pass
