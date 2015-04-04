#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
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

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import logging
log = logging.getLogger(".")

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
from gramps.gen.datehandler import format_time
from .flatbasemodel import FlatBaseModel
from gramps.gen.const import GRAMPS_LOCALE as glocale

#-------------------------------------------------------------------------
#
# SourceModel
#
#-------------------------------------------------------------------------
class SourceModel(FlatBaseModel):

    def __init__(self, db, search=None, skip=set()):
        self.map = db.get_raw_source_data
        self.gen_cursor = db.get_source_cursor
        self.fmap = [
            self.column_title,
            self.column_id,
            self.column_author,
            self.column_abbrev,
            self.column_pubinfo,
            self.column_private,
            self.column_tags,
            self.column_change,
            self.column_tag_color
            ]

        self._column_types = [str, str, str, str, str, str, str, str, str, int,
                              str]

        FlatBaseModel.__init__(self, db, search, skip)

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_title(data)
        row[1] = self.column_id(data)
        row[2] = self.column_author(data)
        row[3] = self.column_abbrev(data)
        row[4] = self.column_pubinfo(data)
        row[5] = self.column_private(data)
        row[6] = self.column_tags(data)
        row[7] = self.column_change(data)
        row[8] = self.column_tag_color(data)
        row[9] = self.sort_change(data)
        row[10] = handle
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
        return 8

    def total(self):
        """
        Total number of items.
        """
        return self.db.get_number_of_sources()

    def column_title(self,data):
        return data[2]

    def column_author(self,data):
        return data[3]

    def column_abbrev(self,data):
        return data[7]

    def column_id(self,data):
        return data[1]

    def column_pubinfo(self,data):
        return data[4]

    def column_private(self, data):
        if data[12]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''

    def column_change(self,data):
        return format_time(data[8])
    
    def sort_change(self,data):
        return data[8]

    def get_tag_name(self, tag_handle):
        """
        Return the tag name from the given tag handle.
        """
        return self.db.get_tag_from_handle(tag_handle).get_name()
        
    def column_tag_color(self, data):
        """
        Return the tag color.
        """
        tag_color = "#000000000000"
        tag_priority = None
        for handle in data[11]:
            tag = self.db.get_tag_from_handle(handle)
            if tag:
                this_priority = tag.get_priority()
                if tag_priority is None or this_priority < tag_priority:
                    tag_color = tag.get_color()
                    tag_priority = this_priority
        return tag_color

    def column_tags(self, data):
        """
        Return the sorted list of tags.
        """
        tag_list = list(map(self.get_tag_name, data[11]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))
