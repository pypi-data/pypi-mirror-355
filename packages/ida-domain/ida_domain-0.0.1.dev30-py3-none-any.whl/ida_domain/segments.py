from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import ida_segment

from .decorators import check_db_open, decorate_all_methods

if TYPE_CHECKING:
    from .database import Database


@decorate_all_methods(check_db_open)
class Segments:
    """
    Provides access to segment-related operations in the IDA database.
    """

    def __init__(self, database: 'Database'):
        """
        Constructs a segments handler for the given database.

        Args:
            database: Reference to the active IDA database.
        """
        self.m_database = database

    def get_at(self, ea: int) -> Optional[object]:
        """
        Retrieves the segment that contains the given address.

        Args:
            ea: The effective address to search.

        Returns:
            A pointer to the containing segment, or None if none found.
        """
        return ida_segment.getseg(ea)

    def get_name(self, segment: object) -> str:
        """
        Retrieves the name of the given segment.

        Args:
            segment: Pointer to the segment.

        Returns:
            The segment name as a string, or an empty string if unavailable.
        """
        if segment is None:
            return ''
        return ida_segment.get_segm_name(segment)

    def set_name(self, segment: object, name: str) -> bool:
        """
        Renames a segment.

        Args:
            segment: Pointer to the segment to rename.
            name: The new name to assign to the segment.

        Returns:
            True if the rename operation succeeded, false otherwise.
        """
        if segment is None:
            return False
        return ida_segment.set_segm_name(segment, name)

    def get_all(self):
        """
        Retrieves an iterator over all segments in the database.

        Returns:
            A SegmentsIterator instance.
        """
        for current_index in range(0, ida_segment.get_segm_qty()):
            seg = ida_segment.getnseg(current_index)
            if seg:
                yield seg

    # Additional Python-friendly properties
    def get_label(self, segment: object) -> str:
        """Alias for get_name to match SWIG extension pattern."""
        return self.get_name(segment)
