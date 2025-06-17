#!/usr/bin/env -S uv run -s
# this_file: src/vexylicon/utils/svg_processor.py
"""SVG DOM manipulation utilities using lxml.

This module provides safe XML parsing and manipulation functions
for SVG documents. All operations use proper DOM manipulation
rather than string replacement to ensure robustness.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

# SVG namespace
SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"

# Note: lxml doesn't support registering default namespace with empty prefix
# We'll handle namespaces during serialization instead


class SVGProcessor:
    """Handles SVG document parsing and manipulation using lxml."""

    def __init__(self, svg_content: str | Path):
        """Initialize with SVG content or file path.

        Args:
            svg_content: SVG string or path to SVG file

        Raises:
            etree.XMLSyntaxError: If SVG is malformed
        """
        if isinstance(svg_content, Path):
            with open(svg_content, "rb") as f:
                self.tree = etree.parse(f)
        else:
            self.tree = etree.fromstring(svg_content.encode("utf-8"))
            if not isinstance(self.tree, etree._Element):
                msg = "Failed to parse SVG content"
                raise ValueError(msg)

        self.root = self.tree if isinstance(self.tree, etree._Element) else self.tree.getroot()

    def ns(self, tag: str) -> str:
        """Return namespaced tag for SVG elements.

        Args:
            tag: Element tag name (e.g., 'path', 'g')

        Returns:
            Fully qualified tag with namespace
        """
        return f"{{{SVG_NS}}}{tag}"

    def find_by_id(self, element_id: str) -> etree._Element | None:
        """Find element by ID attribute.

        Args:
            element_id: ID to search for

        Returns:
            Element if found, None otherwise
        """
        return self.root.find(f".//*[@id='{element_id}']")

    def find_all(self, tag: str) -> list[etree._Element]:
        """Find all elements with given tag.

        Args:
            tag: Tag name (without namespace)

        Returns:
            List of matching elements
        """
        return self.root.findall(f".//{self.ns(tag)}")

    def get_defs(self, create: bool = True) -> etree._Element | None:
        """Get or create the <defs> element.

        Args:
            create: Whether to create if missing

        Returns:
            The defs element, or None if not found and create=False
        """
        defs = self.root.find(self.ns("defs"))
        if defs is None and create:
            defs = etree.SubElement(self.root, self.ns("defs"))
            # Move defs to the beginning
            self.root.insert(0, defs)
        return defs

    def create_element(self, tag: str, **attrs) -> etree._Element:
        """Create a new SVG element with attributes.

        Args:
            tag: Element tag name
            **attrs: Element attributes

        Returns:
            New element
        """
        elem = etree.Element(self.ns(tag))
        for key, value in attrs.items():
            if key == "href":
                # Handle xlink:href for compatibility
                elem.set(f"{{{XLINK_NS}}}href", str(value))
                elem.set("href", str(value))  # Also set modern href
            else:
                elem.set(key, str(value))
        return elem

    def add_gradient(self, gradient_type: str, gradient_id: str, stops: list[dict], **attrs) -> etree._Element:
        """Add a gradient definition to the SVG.

        Args:
            gradient_type: 'linear' or 'radial'
            gradient_id: ID for the gradient
            stops: List of stop definitions with offset, color, opacity
            **attrs: Additional gradient attributes (x1, y1, cx, cy, etc.)

        Returns:
            The created gradient element
        """
        defs = self.get_defs()

        tag = "linearGradient" if gradient_type == "linear" else "radialGradient"
        gradient = self.create_element(tag, id=gradient_id, gradientUnits="userSpaceOnUse", **attrs)

        for stop in stops:
            stop_elem = self.create_element("stop", offset=str(stop["offset"]), stop_color=stop["color"])
            if "opacity" in stop:
                stop_elem.set("stop-opacity", str(stop["opacity"]))
            gradient.append(stop_elem)

        defs.append(gradient)
        return gradient

    def duplicate_element(self, elem: etree._Element, new_id: str) -> etree._Element:
        """Create a deep copy of an element with a new ID.

        Args:
            elem: Element to duplicate
            new_id: New ID for the copy

        Returns:
            The duplicated element
        """
        new_elem = etree.fromstring(etree.tostring(elem))
        new_elem.set("id", new_id)
        return new_elem

    def get_path_data(self, elem: etree._Element) -> str:
        """Extract path data from a path or use element.

        Handles both direct path elements and use elements that
        reference path definitions.

        Args:
            elem: Path or use element

        Returns:
            Path data string, or empty string if not found
        """
        if elem.tag.endswith("path"):
            return elem.get("d", "")
        if elem.tag.endswith("use"):
            # Get the href attribute
            href = elem.get("href") or elem.get(f"{{{XLINK_NS}}}href", "")
            if href.startswith("#"):
                ref_id = href[1:]  # Remove the #
                ref_elem = self.find_by_id(ref_id)
                if ref_elem is not None and ref_elem.tag.endswith("path"):
                    return ref_elem.get("d", "")
        return ""

    def to_string(self, pretty_print: bool = True) -> str:
        """Convert the SVG tree back to a string.

        Args:
            pretty_print: Whether to format with indentation

        Returns:
            SVG as string
        """
        # First get the string without XML declaration
        svg_str = etree.tostring(self.root, encoding="unicode", pretty_print=pretty_print)
        # Add XML declaration manually
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{svg_str}'

    def write(self, output_path: Path, pretty_print: bool = True) -> None:
        """Write the SVG to a file.

        Args:
            output_path: Where to save the SVG
            pretty_print: Whether to format with indentation
        """
        output_path.write_text(self.to_string(pretty_print), encoding="utf-8")
