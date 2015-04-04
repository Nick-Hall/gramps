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
from gramps.gen.datehandler import displayer, format_time, get_date_valid
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.lib import EventRoleType, FamilyRelType
from .flatbasemodel import FlatBaseModel
from gramps.gen.utils.db import get_marriage_or_fallback
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale

invalid_date_format = config.get('preferences.invalid-date-format')

#-------------------------------------------------------------------------
#
# FamilyModel
#
#-------------------------------------------------------------------------
class FamilyModel(FlatBaseModel):

    def __init__(self, db, search=None, skip=set()):
        self.gen_cursor = db.get_family_cursor
        self.map = db.get_raw_family_data
        self.fmap = [
            self.column_id, 
            self.column_father, 
            self.column_mother, 
            self.column_type, 
            self.column_marriage, 
            self.column_private,
            self.column_tags,
            self.column_change, 
            self.column_tag_color,
            ]

        self._column_types = [str, str, str, str, str, str, str, str, str, str,
                              str, int, int, str]

        FlatBaseModel.__init__(self, db, search, skip)

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_id(data)
        row[1] = self.column_father(data)
        row[2] = self.column_mother(data)
        row[3] = self.column_type(data)
        row[4] = self.column_marriage(data)
        row[5] = self.column_private(data)
        row[6] = self.column_tags(data)
        row[7] = self.column_change(data)
        row[8] = self.column_tag_color(data)
        row[9] = self.sort_father(data)
        row[10] = self.sort_mother(data)
        row[11] = self.sort_marriage(data)
        row[12] = self.sort_change(data)
        row[13] = handle
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
        return self.db.get_number_of_families()

    def column_father(self, data):
        if data[2]:
            person = self.db.get_person_from_handle(data[2])
            return name_displayer.display_name(person.primary_name)
        else:
            return ""

    def sort_father(self, data):
        if data[2]:
            person = self.db.get_person_from_handle(data[2])
            return name_displayer.sorted_name(person.primary_name)
        else:
            return ""

    def column_mother(self, data):
        if data[3]:
            person = self.db.get_person_from_handle(data[3])
            return name_displayer.display_name(person.primary_name)
        else:
            return ""

    def sort_mother(self, data):
        if data[3]:
            person = self.db.get_person_from_handle(data[3])
            return name_displayer.sorted_name(person.primary_name)
        else:
            return ""

    def column_type(self, data):
        return str(FamilyRelType(data[5]))

    def column_marriage(self, data):
        family = self.db.get_family_from_handle(data[0])
        event = get_marriage_or_fallback(self.db, family, "<i>%s</i>")
        if event:
            if event.date.format:
                return event.date.format % displayer.display(event.date)
            elif not get_date_valid(event):
                return invalid_date_format % displayer.display(event.date)
            else:
                return "%s" % displayer.display(event.date)
        else:
            return ''

    def sort_marriage(self, data):
        family = self.db.get_family_from_handle(data[0])
        event = get_marriage_or_fallback(self.db, family)
        if event:
            return event.date.get_sort_value()
        else:
            return 0

    def column_id(self, data):
        return data[1]

    def column_private(self, data):
        if data[14]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''

    def sort_change(self, data):
        return data[12]
    
    def column_change(self, data):
        return format_time(data[12])

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
        for handle in data[13]:
            tag = self.db.get_tag_from_handle(handle)
            this_priority = tag.get_priority()
            if tag_priority is None or this_priority < tag_priority:
                tag_color = tag.get_color()
                tag_priority = this_priority
        return tag_color

    def column_tags(self, data):
        """
        Return the sorted list of tags.
        """
        tag_list = list(map(self.get_tag_name, data[13]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))
