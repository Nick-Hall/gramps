#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009-2010  Nick Hall
# Copyright (C) 2009       Benny Malengier
# Copyright (C) 2010       Gary Burton
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
Place Model.
"""
#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import logging
_LOG = logging.getLogger(__name__)

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
from gramps.gen.lib import Place, PlaceType
from gramps.gen.datehandler import format_time
from gramps.gen.utils.place import conv_lat_lon
from gramps.gen.display.place import displayer as place_displayer
from .flatbasemodel import FlatBaseModel
from .treebasemodel import TreeBaseModel

#-------------------------------------------------------------------------
#
# internationalization
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# PlaceBaseModel
#
#-------------------------------------------------------------------------
class PlaceBaseModel(object):

    def __init__(self, db):
        self.gen_cursor = db.get_place_cursor
        self.map = db.get_raw_place_data
        self.fmap = [
            self.column_name,
            self.column_id,
            self.column_title,
            self.column_type,
            self.column_code,
            self.column_latitude,
            self.column_longitude,
            self.column_private,
            self.column_tags,
            self.column_change,
            self.column_tag_color
            ]

        self._column_types = [str, str, str, str, str, str, str, str, str, str,
                              str, str, str, int, str]

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_name(data)
        row[1] = self.column_id(data)
        row[2] = self.column_title(data)
        row[3] = self.column_type(data)
        row[4] = self.column_code(data)
        row[5] = self.column_latitude(data)
        row[6] = self.column_longitude(data)
        row[7] = self.column_private(data)
        row[8] = self.column_tags(data)
        row[9] = self.column_change(data)
        row[10] = self.column_tag_color(data)
        row[11] = self.sort_latitude(data)
        row[12] = self.sort_longitude(data)
        row[13] = self.sort_change(data)
        row[14] = handle
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
        return 10

    def total(self):
        """
        Total number of items.
        """
        return self.db.get_number_of_places()

    def column_title(self, data):
        place = Place()
        place.unserialize(data)
        return place_displayer.display(self.db, place)

    def column_name(self, data):
        return str(data[6][0])

    def column_longitude(self, data):
        if not data[3]:
            return ''
        value = conv_lat_lon('0', data[3], format='DEG')[1]
        if not value:
            return _("Error in format")
        return value

    def column_latitude(self, data):
        if not data[4]:
            return ''
        value = conv_lat_lon(data[4], '0', format='DEG')[0]
        if not value:
            return _("Error in format")
        return value

    def sort_longitude(self, data):
        if not data[3]:
            return ''
        value = conv_lat_lon('0', data[3], format='ISO-DMS') if data[3] else ''
        if not value:
             return _("Error in format")
        return value

    def sort_latitude(self, data):
        if not data[4]:
            return ''
        value = conv_lat_lon(data[4], '0', format='ISO-DMS') if data[4] else ''
        if not value:
            return _("Error in format")
        return value 

    def column_id(self, data):
        return data[1]

    def column_type(self, data):
        return str(PlaceType(data[8]))

    def column_code(self, data):
        return data[9]

    def column_private(self, data):
        if data[17]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''
    
    def sort_change(self, data):
        return data[15]
    
    def column_change(self, data):
        return format_time(data[15])

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
        for handle in data[16]:
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
        tag_list = list(map(self.get_tag_name, data[16]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))

#-------------------------------------------------------------------------
#
# PlaceListModel
#
#-------------------------------------------------------------------------
class PlaceListModel(PlaceBaseModel, FlatBaseModel):
    """
    Flat place model.  (Original code in PlaceBaseModel).
    """
    def __init__(self, db, search=None, skip=set()):

        PlaceBaseModel.__init__(self, db)
        FlatBaseModel.__init__(self, db, search, skip)

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        PlaceBaseModel.destroy(self)
        FlatBaseModel.destroy(self)

#-------------------------------------------------------------------------
#
# PlaceTreeModel
#
#-------------------------------------------------------------------------
class PlaceTreeModel(PlaceBaseModel, TreeBaseModel):
    """
    Hierarchical place model.
    """
    def __init__(self, db, search=None, skip=set()):

        PlaceBaseModel.__init__(self, db)
        TreeBaseModel.__init__(self, db, search, skip)

    def destroy(self):
        """
        Unset all elements that can prevent garbage collection
        """
        PlaceBaseModel.destroy(self)
        self.number_items = None
        TreeBaseModel.destroy(self)

    def _set_base_data(self):
        """See TreeBaseModel, for place, most have been set in init of
        PlaceBaseModel
        """
        self.number_items = self.db.get_number_of_places
        self.gen_cursor = self.db.get_place_tree_cursor

    def get_tree_levels(self):
        """
        Return the headings of the levels in the hierarchy.
        """
        return [_('Country'), _('State'), _('County'), _('Place')]

    def add_row(self, handle, data):
        """
        Add nodes to the node map for a single place.

        handle      The handle of the gramps object.
        data        The object data.
        """
        if len(data[5]) > 0:
            parent = data[5][0][0]
        else:
            parent = None

        if parent:
            parent_iter = self.handle2iter.get(parent)
        else:
            parent_iter = None
        row = self._get_row(data, handle)
        self.handle2iter[handle] = self.append(parent_iter, row)
