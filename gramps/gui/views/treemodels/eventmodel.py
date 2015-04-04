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
from html import escape
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
from gramps.gen.datehandler import format_time, get_date, get_date_valid
from gramps.gen.lib import Event, EventType
from gramps.gen.utils.db import get_participant_from_event
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.config import config
from .flatbasemodel import FlatBaseModel
from gramps.gen.const import GRAMPS_LOCALE as glocale

#-------------------------------------------------------------------------
#
# COLUMN constants
#
#-------------------------------------------------------------------------
COLUMN_HANDLE      = 0
COLUMN_ID          = 1
COLUMN_TYPE        = 2
COLUMN_DATE        = 3
COLUMN_DESCRIPTION = 4
COLUMN_PLACE       = 5
COLUMN_CHANGE      = 10
COLUMN_TAGS        = 11
COLUMN_PRIV        = 12

INVALID_DATE_FORMAT = config.get('preferences.invalid-date-format')

#-------------------------------------------------------------------------
#
# EventModel
#
#-------------------------------------------------------------------------
class EventModel(FlatBaseModel):

    def __init__(self, db, search=None, skip=set()):
        self.gen_cursor = db.get_event_cursor
        self.map = db.get_raw_event_data
        
        self.fmap = [
            self.column_description,
            self.column_id,
            self.column_type,
            self.column_date,
            self.column_place,
            self.column_private,
            self.column_tags,
            self.column_change,
            self.column_participant,
            self.column_tag_color
            ]
        self._column_types = [str, str, str, str, str, str, str, str, str, str,
                              int, int, str]

        FlatBaseModel.__init__(self, db, search, skip)

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_description(data)
        row[1] = self.column_id(data)
        row[2] = self.column_type(data)
        row[3] = self.column_date(data)
        row[4] = self.column_place(data)
        row[5] = self.column_private(data)
        row[6] = self.column_tags(data)
        row[7] = self.column_change(data)
        row[8] = self.column_participant(data)
        row[9] = self.column_tag_color(data)
        row[10] = self.sort_date(data)
        row[11] = self.sort_change(data)
        row[12] = handle
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
        return 9

    def total(self):
        """
        Total number of items.
        """
        return self.db.get_number_of_events()

    def column_description(self,data):
        return data[COLUMN_DESCRIPTION]

    def column_participant(self,data):
        return get_participant_from_event(self.db, data[COLUMN_HANDLE])
        
    def column_place(self,data):
        if data[COLUMN_PLACE]:
            event = Event()
            event.unserialize(data)
            return place_displayer.display_event(self.db, event)
        else:
            return ''

    def column_type(self,data):
        return str(EventType(data[COLUMN_TYPE]))

    def column_id(self,data):
        return data[COLUMN_ID]

    def column_date(self,data):
        if data[COLUMN_DATE]:
            event = Event()
            event.unserialize(data)
            date_str =  get_date(event)
            if date_str != "":
                retval = escape(date_str)
            if not get_date_valid(event):
                return INVALID_DATE_FORMAT % retval
            else:
                return retval
        return ''

    def sort_date(self,data):
        if data[COLUMN_DATE]:
            event = Event()
            event.unserialize(data)
            return event.get_date_object().get_sort_value()
        return 0

    def column_private(self, data):
        if data[COLUMN_PRIV]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''
    
    def sort_change(self,data):
        return data[COLUMN_CHANGE]

    def column_change(self,data):
        return format_time(data[COLUMN_CHANGE])

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
        for handle in data[COLUMN_TAGS]:
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
        tag_list = list(map(self.get_tag_name, data[COLUMN_TAGS]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))
