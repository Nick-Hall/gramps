#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2011       Tim G L Lyons, Nick Hall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

"""
CitationListModel class for GRAMPS.
"""

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".")
LOG = logging.getLogger(".citation")

#-------------------------------------------------------------------------
#
# GNOME/GTK modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from .flatbasemodel import FlatBaseModel
from .citationbasemodel import CitationBaseModel
from gramps.gen.datehandler import format_time

#-------------------------------------------------------------------------
#
# CitationListModel
#
#-------------------------------------------------------------------------
class CitationListModel(CitationBaseModel, FlatBaseModel):
    """
    Flat citation model.  (Original code in CitationBaseModel).
    """
    def __init__(self, db, search=None, skip=set()):
        self.map = db.get_raw_citation_data
        self.ff = None
        self.fmap = [
            self.citation_page,
            self.citation_id,
            self.citation_date,
            self.citation_confidence,
            self.citation_private,
            self.citation_tags,
            self.citation_change,
            self.citation_src_title,
            self.citation_src_id,
            self.citation_src_auth,
            self.citation_src_abbr,
            self.citation_src_pinfo,
            self.citation_src_private,
            self.citation_src_chan,
            self.citation_tag_color
            ]

        self._column_types = [str, str, str, str, str, str, str, str, str, str,
                              str, str, str, str, str, int, int, int, str]

        FlatBaseModel.__init__(self, db, search, skip)

    def gen_cursor(self):
        for key, data in self.db.get_citation_cursor():
            if self.ff and self.ff.match(data, self.db):
                yield key, data

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.citation_page(data)
        row[1] = self.citation_id(data)
        row[2] = self.citation_date(data)
        row[3] = self.citation_confidence(data)
        row[4] = self.citation_private(data)
        row[5] = self.citation_tags(data)
        row[6] = self.citation_change(data)
        source = self.db.get_source_from_handle(data[5])
        row[7] = source.get_title()
        row[8] = source.get_gramps_id()
        row[9] = source.get_author()
        row[10] = source.get_abbreviation()
        row[11] = source.get_publication_info()
        row[12] = 'gramps-lock' if source.get_privacy() else ''
        row[13] = format_time(source.change)
        row[14] = self.citation_tag_color(data)
        row[15] = self.citation_sort_date(data)
        row[16] = self.citation_sort_change(data)
        row[17] = source.change
        row[18] = handle
        return row

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        self.db = None
        self.gen_cursor = None
        self.map = None
        self.fmap = None
        FlatBaseModel.destroy(self)

    def color_column(self):
        """
        Return the color column.
        """
        return 14
