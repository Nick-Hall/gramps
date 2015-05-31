#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2010       Nick Hall
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
_LOG = logging.getLogger(".gui.notemodel")

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
from gramps.gen.const import GRAMPS_LOCALE as glocale
from .flatbasemodel import FlatBaseModel
from gramps.gen.lib import (Note, NoteType, StyledText)

#-------------------------------------------------------------------------
#
# NoteModel
#
#-------------------------------------------------------------------------
class NoteModel(FlatBaseModel):
    """
    """
    def __init__(self, db, search=None, skip=set()):
        """Setup initial values for instance variables."""
        self.gen_cursor = db.get_note_cursor
        self.map = db.get_raw_note_data
        self.fmap = [
            self.column_preview,
            self.column_id,
            self.column_type,
            self.column_private,
            self.column_tags,
            self.column_change,
            self.column_tag_color
        ]

        self._column_types = [str, str, str, str, str, str, str, int, str]

        FlatBaseModel.__init__(self, db, search, skip)

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_preview(data)
        row[1] = self.column_id(data)
        row[2] = self.column_type(data)
        row[3] = self.column_private(data)
        row[4] = self.column_tags(data)
        row[5] = self.column_change(data)
        row[6] = self.column_tag_color(data)
        row[7] = self.sort_change(data)
        row[8] = handle
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
        return 6

    def total(self):
        """
        Total number of items.
        """
        return self.db.get_number_of_notes()

    def column_id(self, data):
        """Return the id of the Note."""
        return data[Note.POS_ID]

    def column_type(self, data):
        """Return the type of the Note in readable format."""
        return str(NoteType(data[Note.POS_TYPE]))

    def column_preview(self, data):
        """Return a shortend version of the Note's text."""
        #data is the encoding in the database, make it a unicode object
        #for universal work
        note = str(data[Note.POS_TEXT][StyledText.POS_TEXT])
        note = " ".join(note.split())
        if len(note) > 80:
            return note[:80] + "..."
        else:
            return note

    def column_private(self, data):
        if data[Note.POS_PRIVATE]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''

    def sort_change(self, data):
        return data[Note.POS_CHANGE]
    
    def column_change(self,data):
        return format_time(data[Note.POS_CHANGE])

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
        for handle in data[Note.POS_TAGS]:
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
        tag_list = list(map(self.get_tag_name, data[Note.POS_TAGS]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))
