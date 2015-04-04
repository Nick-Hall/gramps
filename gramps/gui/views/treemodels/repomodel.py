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
from gramps.gen.lib import Address, RepositoryType, Url, UrlType
from gramps.gen.datehandler import format_time
from .flatbasemodel import FlatBaseModel
from gramps.gen.const import GRAMPS_LOCALE as glocale
#-------------------------------------------------------------------------
#
# RepositoryModel
#
#-------------------------------------------------------------------------
class RepositoryModel(FlatBaseModel):

    def __init__(self, db, search=None, skip=set()):
        self.gen_cursor = db.get_repository_cursor
        self.map = db.get_raw_repository_data
        self.fmap = [
            self.column_name,
            self.column_id,
            self.column_type,
            self.column_home_url,
            self.column_street,
            self.column_locality,
            self.column_city,
            self.column_state,
            self.column_country,
            self.column_postal_code,
            self.column_email,
            self.column_search_url,
            self.column_private,
            self.column_tags,
            self.column_change,
            self.column_tag_color
            ]
        
        self._column_types = [str, str, str, str, str, str, str, str, str, str,
                              str, str, str, str, str, str, int, str]
        
        FlatBaseModel.__init__(self, db, search, skip)

    def _get_row(self, data, handle):
        row = [None] * len(self._column_types)
        row[0] = self.column_name(data)
        row[1] = self.column_id(data)
        row[2] = self.column_type(data)
        email, search, home = self._get_url(data)
        row[3] = home
        addr = self._get_address(data)
        row[4] = addr.get_street()
        row[5] = addr.get_locality()
        row[6] = addr.get_city()
        row[7] = addr.get_state()
        row[8] = addr.get_country()
        row[9] = addr.get_postal_code()
        row[10] = email
        row[11] = search
        row[12] = self.column_private(data)
        row[13] = self.column_tags(data)
        row[14] = self.column_change(data)
        row[15] = self.column_tag_color(data)
        row[16] = self.sort_change(data)
        row[17] = handle
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
        return 15

    def total(self):
        """
        Total number of items.
        """
        return self.db.get_number_of_repositories()

    def column_id(self,data):
        return data[1]

    def column_type(self,data):
        return str(RepositoryType(data[2]))

    def column_name(self,data):
        return data[3]

    def _get_address(self, data):
        addr = Address()
        if data[5]:
            addr.unserialize(data[5][0])
        return addr

    def column_city(self, data):
        return self._get_address(data).get_city()

    def column_street(self, data):
        return self._get_address(data).get_street()
        
    def column_locality(self, data):
        return self._get_address(data).get_locality()
    
    def column_state(self, data):
        return self._get_address(data).get_state()

    def column_country(self, data):
        return self._get_address(data).get_country()

    def column_postal_code(self, data):
        return self._get_address(data).get_postal_code()

    def column_phone(self, data):
        return self._get_address(data).get_phone()

    def _get_url(self, data):
        email = search = home = ''
        if data[6]:
            for i in data[6]:
                url = Url()
                url.unserialize(i)
                if url.get_type() == UrlType.EMAIL:
                    email = url.path
                elif url.get_type() == UrlType.WEB_SEARCH:
                    search = url.path
                elif url.get_type() == UrlType.WEB_HOME:
                    home = url.path
        return (email, search, home)

    def column_email(self, data):
        return self._get_url(data)[0]

    def column_search_url(self, data):
        return self._get_url(data)[1]
    
    def column_home_url(self, data):
        return self._get_url(data)[2]

    def column_private(self, data):
        if data[9]:
            return 'gramps-lock'
        else:
            # There is a problem returning None here.
            return ''

    def sort_change(self,data):
        return data[7]

    def column_change(self,data):
        return format_time(data[7])

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
        for handle in data[8]:
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
        tag_list = list(map(self.get_tag_name, data[8]))
        return ', '.join(sorted(tag_list, key=glocale.sort_key))
