#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2006  Donald N. Allingham
# Copyright (C) 2009       Benny Malengier
# Copyright (C) 2010-2015  Nick Hall
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
This module provides the flat treemodel that is used for all flat treeviews.
"""

#-------------------------------------------------------------------------
#
# python modules
#
#-------------------------------------------------------------------------
import logging
import time

_LOG = logging.getLogger(__name__)
    
#-------------------------------------------------------------------------
#
# GNOME/GTK modules
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
# FlatBaseModel
#
#-------------------------------------------------------------------------
class FlatBaseModel(Gtk.ListStore):
    """
    The base class for all flat treeview models. 
    """
    def __init__(self, db, search=None, skip=set()):

        Gtk.ListStore.__init__(self)
        self.set_column_types(self._column_types)

        cput = time.clock()

        self.db = db
        self.skip = skip
        self.handle2iter = {}

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
                if self.search is None:
                    self.rebuild_data = self._rebuild_all
                else:
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
                    self.rebuild_data = self._rebuild_search
                else:
                    self.search = None
                    self.rebuild_data = self._rebuild_all
            else: # Fast Filter
                self.search = search[1]
                self.rebuild_data = self._rebuild_search
        else:
            self.search = None
            self.rebuild_data = self._rebuild_all

    def total(self):
        """
        Total number of items that maximally can be shown
        """
        return 0

    def displayed(self):
        """
        Number of items that are currently displayed
        """
        return len(self)

    def color_column(self):
        """
        Return the color column.
        """
        return None

    def apply_filter(self, pmon):
        items = self.total()
        status = progressdlg.LongOpStatus(msg=_("Applying Filter"),
                            total_steps=items, interval=items//10)
        pmon.add_op(status)
        dlist = self.search.apply(self.db, cb_progress=status.heartbeat)
        status.end()
        return dlist

    def _rebuild_search(self):
        """ function called when view must be build, given a search text
            in the top search bar
        """
        items = self.total()
        pmon = progressdlg.ProgressMonitor(progressdlg.GtkProgressDialog, 
                                            popup_time=2)
        status = progressdlg.LongOpStatus(msg=_("Building View"),
                            total_steps=items, interval=items//20, 
                            can_cancel=True)
        pmon.add_op(status)
        self.clear()
        self.handle2iter = {}
        if self.db.is_open():
            for key, data in self.gen_cursor():
                status.heartbeat()
                if status.should_cancel():
                    break
                handle = key.decode('utf8')
                if self.search.match(data, self.db):
                    if handle not in self.skip:
                        self._add(data, handle)
            if not status.was_cancelled():
                status.end()

    def _rebuild_filter(self):
        """ function called when view must be build, given filter options
            in the filter sidebar
        """
        self.clear()
        self.handle2iter = {}
        if self.db.is_open():
            items = self.total()
            pmon = progressdlg.ProgressMonitor(progressdlg.GtkProgressDialog, 
                                               popup_time=2)
            dlist = self.apply_filter(pmon)
            items = self.total()
            status = progressdlg.LongOpStatus(msg=_("Building View"),
                                total_steps=items, interval=items//10)
            pmon.add_op(status)
            for key, data in self.gen_cursor():
                status.heartbeat()
                if status.should_cancel():
                    break
                if key in dlist:
                    handle = key.decode('utf8')
                    if handle not in self.skip:
                        self._add(data, handle)
            if not status.was_cancelled():
                status.end()

    def _rebuild_all(self):
        items = self.total()
        pmon = progressdlg.ProgressMonitor(progressdlg.GtkProgressDialog, 
                                            popup_time=2)
        status = progressdlg.LongOpStatus(msg=_("Building View"),
                            total_steps=items, interval=items//20, 
                            can_cancel=True)
        pmon.add_op(status)
        self.clear()
        self.handle2iter = {}
        if self.db.is_open():
            for key, data in self.gen_cursor():
                status.heartbeat()
                if status.should_cancel():
                    break
                handle = key.decode('utf8')
                if handle not in self.skip:
                    self._add(data, handle)
            if not status.was_cancelled():
                status.end()

    def _get_row(self, data, handle):
        row = []
        for col, col_func in enumerate(self.fmap):
            row.append(col_func(data))
        row.append(handle)
        return row

    def _add(self, data, handle):
        row = self._get_row(data, handle)
        self.handle2iter[handle] = self.append(row)

    def add_row_by_handle(self, handle):
        """
        Add a row. This is called after object with handle is created.
        Row is only added if search/filter data is such that it must be shown
        """
        self._add(self.map(handle), handle)

    def delete_row_by_handle(self, handle):
        """
        Delete a row, called after the object with handle is deleted
        """
        iter = self.get_iter_from_handle(handle)
        self.remove(iter)
        del self.handle2iter[handle]

    def update_row_by_handle(self, handle):
        """
        Update a row, called after the object with handle is changed
        """
        iter = self.get_iter_from_handle(handle)
        self.set_row(iter, self._get_row(self.map(handle), handle))

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

class FastGroupAsFilter(object):

    def __init__(self, db, handle_list):
        self.db = db
        self.group_as = group_as

    def match(self, data, db):
        group_as = name_displayer.name_grouping_data(self.db, data[3])
        return group_as == self.group_as
