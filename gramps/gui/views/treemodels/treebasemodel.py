#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2009       Gary Burton
# Copyright (C) 2009-2011  Nick Hall
# Copyright (C) 2009-2012  Benny Malengier
# Copyright (C) 2011       Tim G L lyons
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
# gui/views/treemodels/treebasemodel.py

"""
This module provides the model that is used for all hierarchical treeviews.
"""

#-------------------------------------------------------------------------
#
# Standard python modules
#
#-------------------------------------------------------------------------
import time
import logging

_LOG = logging.getLogger(__name__)

#-------------------------------------------------------------------------
#
# GTK modules
#
#-------------------------------------------------------------------------
from gi.repository import Gtk

#-------------------------------------------------------------------------
#
# Gramps modules
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext
import gramps.gui.widgets.progressdialog as progressdlg
from gramps.gen.filters import SearchFilter, ExactSearchFilter

#-------------------------------------------------------------------------
#
# TreeBaseModel
#
#-------------------------------------------------------------------------
class TreeBaseModel(Gtk.TreeStore):
    """
    The base class for all hierarchical treeview models.
    
    Creation:
    db     :   the database
    search :  the search that must be shown
    skip   :  values not to show
    """
    def __init__(self, db, search=None, skip=set()):

        Gtk.TreeStore.__init__(self)
        self.set_column_types(self._column_types)

        cput = time.clock()

        self.db = db
        self.skip = skip
        self.handle2iter = {}

        self._set_base_data()
        self.set_search(search)
        self.rebuild_data()

        _LOG.debug(self.__class__.__name__ + ' __init__ ' +
                    str(time.clock() - cput) + ' sec')

    def destroy(self):
        """
        Unset all elements that prevent garbage collection
        """
        self.db = None
        self.rebuild_data = None
        self.search = None

    def set_search(self, search):
        """
        Change the search function that filters the data in the model. 
        When this method is called, make sure:
        # you call self.rebuild_data() to recalculate what should be seen 
          in the model
        # you reattach the model to the treeview so that the treeview updates
          with the new entries
        """
        if search:
            if search[0] == 1: # Filter
                #following is None if no data given in filter sidebar
                self.search = search[1]
                self.rebuild_data = self._rebuild_filter
            elif search[0] == 0: # Search
                if search[1]: # Search from topbar in columns
                    # we have search[1] = (index, text_unicode, inversion)
                    col = search[1][0]
                    text = search[1][1]
                    inv = search[1][2]
                    func = lambda x: self.fmap[col](x)
                    if search[2]:
                        self.search = ExactSearchFilter(func, text, inv)
                    else:
                        self.search = SearchFilter(func, text, inv)
                else:
                    self.search = None
                self.rebuild_data = self._rebuild_search
            else: # Fast Filter
                self.search = search[1]
                self.rebuild_data = self._rebuild_search
        else:
            self.search = None
            self.rebuild_data = self._rebuild_filter

    def displayed(self):
        """
        Return the number of rows displayed.
        """
        return len(self)
        
    def total(self):
        """
        Return the total number of rows without a filter or search condition.
        """
        return 0

    def color_column(self):
        """
        Return the color column.
        """
        return None

    def _rebuild_search(self):
        """ function called when view must be build, given a search text
            in the top search bar
        """
        self.clear()
        self.handle2iter = {}
        if self.db.is_open():
            if self.search is not None:
                for key, data in self.gen_cursor():
                    handle = key.decode('utf8')
                    if (self.search.match(data, self.db) 
                        and handle not in self.skip):
                        self.add_row(handle, data)
            else:
                for key, data in self.gen_cursor():
                    handle = key.decode('utf8')
                    if handle not in self.skip:
                        self.add_row(handle, data)

    def _rebuild_filter(self):
        """ function called when view must be build, given filter options
            in the filter sidebar
        """
        self.clear()
        self.handle2iter = {}
        if self.db.is_open():
            if self.search is not None:
                dlist = self.search.apply(self.db)
                for key, data in self.gen_cursor():
                    if key in dlist:
                        handle = key.decode('utf8')
                        if handle not in self.skip:
                            self.add_row(handle, data)
            else:
                for key, data in self.gen_cursor():
                    handle = key.decode('utf8')
                    if handle not in self.skip:
                        self.add_row(handle, data)

    def _get_row(self, data, handle):
        row = []
        for col, col_func in enumerate(self.fmap):
            if col_func is not None:
                row.append(col_func(data))
            else:
                row.append('')
        row.append(handle)
        return row

    def get_tree_levels(self):
        """
        Return the headings of the levels in the hierarchy.
        """
        raise NotImplementedError
        
    def add_row(self, handle, data):
        """
        Add a row to the model.  In general this will add more then one node by
        using the add_node method.
        """
        raise NotImplementedError

    def add_row_by_handle(self, handle):
        """
        Add a row to the model.
        """
        self.add_row(handle, self.map(handle))

    def delete_row_by_handle(self, handle):
        """
        Delete a row from the model.
        """
        iter = self.get_iter_from_handle(handle)
        self.remove(iter)
        del self.handle2iter[handle]

    def update_row_by_handle(self, handle):
        """
        Update a row in the model.
        """
        iter = self.get_iter_from_handle(handle)
        self.set_row(iter, self.__get_row(self.map(handle), handle))

    def get_iter_from_handle(self, handle):
        """
        Get the iter for a gramps handle.
        """
        return self.handle2iter.get(handle)

    def get_handle_from_iter(self, iter):
        """
        Get the gramps handle for an iter.
        """
        return self.get_value(iter, len(self._column_types) - 1)
