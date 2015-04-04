#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Gary Burton
# Copyright (C) 2009-2010  Nick Hall
# Copyright (C) 2009       Benny Malengier
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
TreeModel for the GRAMPS Person tree.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
from html import escape

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# set up logging
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger(__name__)

#-------------------------------------------------------------------------
#
# GRAMPS modules
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
from gramps.gen.lib import (Name, EventRef, EventType, EventRoleType,
                            FamilyRelType, ChildRefType, NoteType)
from gramps.gen.display.name import displayer as name_displayer
from gramps.gen.display.place import displayer as place_displayer
from gramps.gen.datehandler import format_time, get_date, get_date_valid
from .lru import LRU
from .flatbasemodel import FlatBaseModel
from .treebasemodel import TreeBaseModel
from gramps.gen.config import config
from gramps.gen.const import GRAMPS_LOCALE as glocale

#-------------------------------------------------------------------------
#
# COLUMN constants
#
#-------------------------------------------------------------------------
COLUMN_ID     = 1
COLUMN_GENDER = 2
COLUMN_NAME   = 3
COLUMN_DEATH  = 5
COLUMN_BIRTH  = 6
COLUMN_EVENT  = 7
COLUMN_FAMILY = 8
COLUMN_PARENT = 9
COLUMN_NOTES  = 16
COLUMN_CHANGE = 17
COLUMN_TAGS   = 18
COLUMN_PRIV   = 19

invalid_date_format = config.get('preferences.invalid-date-format')

#-------------------------------------------------------------------------
#
# PeopleBaseModel
#
#-------------------------------------------------------------------------
class PeopleBaseModel(object):
    """
    Basic Model interface to handle the PersonViews
    """
    _GENDER = [ _('female'), _('male'), _('unknown') ]

    def __init__(self, db):
        """
        Initialize the model building the initial data
        """
        self.db = db
        self.gen_cursor = db.get_person_cursor
        self.map = db.get_raw_person_data

        self.fmap = [
            self.column_name,
            self.column_id,
            self.column_gender,
            self.column_birth_day,
            self.column_birth_place,
            self.column_death_day,
            self.column_death_place,
            self.column_spouse,
            self.column_parents,
            self.column_marriages,
            self.column_children,
            self.column_todo,
            self.column_private,
            self.column_tags,
            self.column_change,
            self.column_tag_color,
            ]
            
        self._column_types = [str, str, str, str, str, str, str, str, int, int,
                              int, int, str, str, str, str, str, int, int, int,
                              str]

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_name(data)
        row[1] = self.column_id(data)
        row[2] = self.column_gender(data)
        bsortval, bdate, bplace = self._get_data(data, 'birth')
        row[3] = bdate
        row[4] = bplace
        dsortval, ddate, dplace = self._get_data(data, 'death')
        row[5] = ddate
        row[6] = dplace
        row[7] = self.column_spouse(data)
        row[8] = self.column_parents(data)
        row[9] = self.column_marriages(data)
        row[10] = self.column_children(data)
        row[11] = self.column_todo(data)
        row[12] = self.column_private(data)
        row[13] = self.column_tags(data)
        row[14] = self.column_change(data)
        row[15] = self.column_tag_color(data)
        row[16] = self.sort_name(data)
        row[17] = bsortval
        row[18] = dsortval
        row[19] = self.sort_change(data)
        row[20] = handle
        return row

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        self.db = None
        self.gen_cursor = None
        self.map = None
        self.fmap = None

    def color_column(self):
        """
        Return the color column.
        """
        return 15

    def total(self):
        """
        Total number of items.
        """
        return self.db.get_number_of_people()

    def sort_name(self, data):
        return name_displayer.raw_sorted_name(data[COLUMN_NAME])

    def column_name(self, data):
        return name_displayer.raw_display_name(data[COLUMN_NAME])

    def column_private(self, data):
        if data[COLUMN_PRIV]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''
    
    def column_spouse(self, data):
        spouses_names = ""
        for family_handle in data[COLUMN_FAMILY]:
            family = self.db.get_family_from_handle(family_handle)
            for spouse_id in [family.get_father_handle(),
                              family.get_mother_handle()]:
                if not spouse_id:
                    continue
                if spouse_id == data[0]:
                    continue
                spouse = self.db.get_person_from_handle(spouse_id)
                if spouses_names:
                    spouses_names += ", "
                spouses_names += name_displayer.display(spouse)
        return spouses_names

    def column_id(self, data):
        return data[COLUMN_ID]

    def sort_change(self,data):
        return data[COLUMN_CHANGE]

    def column_change(self, data):
        return format_time(data[COLUMN_CHANGE])

    def column_gender(self, data):
        return PeopleBaseModel._GENDER[data[COLUMN_GENDER]]

    def column_birth_day(self, data):
        return self._get_data(data, 'birth')[1]

    def column_birth_place(self, data):
        return self._get_data(data, 'birth')[2]

    def column_death_day(self, data):
        return self._get_data(data, 'death')[1]

    def column_death_place(self, data):
        return self._get_data(data, 'death')[2]

    def _get_data(self, data, event_type):
        if event_type == 'birth':
            index = data[COLUMN_BIRTH]
            fallbacks = [EventType.BAPTISM, EventType.CHRISTEN]
        else:
            index = data[COLUMN_DEATH]
            fallbacks = [EventType.BURIAL, EventType.CREMATION,
                         EventType.CAUSE_DEATH]
        if index != -1:
            try:
                local = data[COLUMN_EVENT][index]

                b = EventRef()
                b.unserialize(local)
                event = self.db.get_event_from_handle(b.ref)

                sortval = event.get_date_object().get_sort_value()
                date_str = get_date(event)
                if date_str != "":
                    retval = cgi.escape(date_str)
                if not get_date_valid(event):
                    retval = invalid_date_format % retval
                place_title = place_displayer.display_event(self.db, event)
                if place_title:
                    place_title = "<i>%s</i>" % cgi.escape(place_title)
                return (sortval, retval, place_title)

            except:
                return (0, '', '')
        
        for event_ref in data[COLUMN_EVENT]:
            er = EventRef()
            er.unserialize(event_ref)
            event = self.db.get_event_from_handle(er.ref)
            etype = event.get_type()
            date_str = get_date(event)
            if (etype in fallbacks
                and er.get_role() == EventRoleType.PRIMARY
                and date_str != ""):

                sortval = event.get_date_object().get_sort_value()
                retval = "<i>%s</i>" % cgi.escape(date_str)
                if not get_date_valid(event):
                    retval = invalid_date_format % retval
                place_title = place_displayer.display_event(self.db, event)
                if place_title:
                    place_title = "<i>%s</i>" % cgi.escape(place_title)
                return (sortval, retval, place_title)

        return (0, '', '')

    def column_parents(self, data):
        parents = 0
        if data[COLUMN_PARENT]:
            family = self.db.get_family_from_handle(data[COLUMN_PARENT][0])
            if family.get_father_handle():
                parents += 1
            if family.get_mother_handle():
                parents += 1
        return parents

    def column_marriages(self, data):
        marriages = 0
        for family_handle in data[COLUMN_FAMILY]:
            family = self.db.get_family_from_handle(family_handle)
            if int(family.get_relationship()) == FamilyRelType.MARRIED:
                marriages += 1
        return marriages

    def column_children(self, data):
        children = 0
        for family_handle in data[COLUMN_FAMILY]:
            family = self.db.get_family_from_handle(family_handle)
            for child_ref in family.get_child_ref_list():
                if (child_ref.get_father_relation() == ChildRefType.BIRTH and 
                    child_ref.get_mother_relation() == ChildRefType.BIRTH):
                    children += 1
        return children

    def column_todo(self, data):
        todo = 0
        for note_handle in data[COLUMN_NOTES]:
            note = self.db.get_note_from_handle(note_handle)
            if int(note.get_type()) == NoteType.TODO:
                todo += 1
        return todo

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

class PersonListModel(PeopleBaseModel, FlatBaseModel):
    """
    Listed people model.
    """
    def __init__(self, db, search=None, skip=set()):
        PeopleBaseModel.__init__(self, db)
        FlatBaseModel.__init__(self, db, search, skip)

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        PeopleBaseModel.destroy(self)
        FlatBaseModel.destroy(self)

class PersonTreeModel(PeopleBaseModel, TreeBaseModel):
    """
    Hierarchical people model.
    """
    def __init__(self, db, search=None, skip=set()):

        PeopleBaseModel.__init__(self, db)
        TreeBaseModel.__init__(self, db, search, skip)

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        PeopleBaseModel.destroy(self)
        self.number_items = None
        TreeBaseModel.destroy(self)

    def _set_base_data(self):
        """See TreeBaseModel, we also set some extra lru caches
        """
        self.number_items = self.db.get_number_of_people

    def get_tree_levels(self):
        """
        Return the headings of the levels in the hierarchy.
        """
        return [_('Group As'), _('Name')]

    def add_row(self, handle, data):
        """
        Add nodes to the node map for a single person.

        handle      The handle of the gramps object.
        data        The object data.
        """
        ngn = name_displayer.name_grouping_data
        
        name_data = data[COLUMN_NAME]
        group_name = ngn(self.db, name_data)

        #if group_name not in self.group_list:
            #self.group_list.append(group_name)
            #self.add_node(None, group_name, group_name, None)
            
        if group_name is not None:
            if group_name not in self.handle2iter:
                row = [group_name, None, None, None, None, None, None,
                       None, None, None, None, None, None, None, None,
                       '#000000000000', None, None, None, None, None]
                self.handle2iter[group_name] = self.append(None, row)
            parent_iter = self.handle2iter[group_name]
        else:
            parent_iter = None
        row = self._get_row(data, handle)
        self.handle2iter[handle] = self.append(parent_iter, row)

