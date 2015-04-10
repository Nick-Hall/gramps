# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2009-2010  Nick Hall
# Copyright (C) 2011       Tim G L Lyons
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
Citation Tree View
"""

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
from gramps.plugins.view.citationlistview import CitationListView
from gramps.gui.views.treemodels.citationlistmodel import CitationListModel
from gramps.gen.lib import Citation
from gramps.gen.errors import WindowActiveError
from gramps.gui.editors import EditCitation

#-------------------------------------------------------------------------
#
# Internationalization
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# CitationTreeView
#
#-------------------------------------------------------------------------
class CitationTreeView(CitationListView):
    """
    A hierarchical view of the people based on family name.
    """
    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        CitationListView.__init__(self, pdata, dbstate, uistate)

    def get_viewtype_stock(self):
        """
        Override the default icon.  Set for hierarchical view.
        """
        return 'gramps-tree-group'

    def add(self, obj):

        store, iter_ = self.fast_selection.get_selected()
        if iter_:
            handle = store.get_value(iter_, 1)

            citation = Citation()
            citation.set_reference_handle(handle)
            try:
                EditCitation(self.dbstate, self.uistate, [], citation)
            except WindowActiveError:
                pass

    def build_fastfilter(self, hbox):

        treeview = Gtk.TreeView()

        scrollwindow = Gtk.ScrolledWindow()
        scrollwindow.set_policy(Gtk.PolicyType.NEVER,
                                 Gtk.PolicyType.AUTOMATIC)
        scrollwindow.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scrollwindow.add(treeview)

        hbox.pack_start(scrollwindow, False, True, 0)

        column = Gtk.TreeViewColumn(_('Source Title'), self.renderer)
        column.add_attribute(self.renderer, 'text', 0)
        column.set_sort_column_id(0)
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        column.set_fixed_width(300)
        treeview.append_column(column)

        self.fast_selection = treeview.get_selection()
        self.fast_selection.connect('changed', self.selection_changed)

        model = Gtk.ListStore(str, str)
        self.source_handles = {}
        for key, data in self.dbstate.db.get_source_cursor():
            handle = data[0]
            source_title = data[2]
            if handle not in self.source_handles:
                iter_ = model.append((source_title, handle))
                self.source_handles[handle] = iter_
        treeview.set_model(model)

        self.list2 = treeview
        self.model2 = model

    def selection_changed(self, selection):
        store, iter_ = selection.get_selected()
        if iter_:
            handle = store.get_value(iter_, 1)

            self.list.set_model(None)
            self.model.ff = FastSourceFilter(self.dbstate.db, handle)
            self.model.rebuild_data()
            self.list.set_model(self.model)

            self.uistate.show_filter_results(self.dbstate,
                                             self.model.displayed(),
                                             self.model.total())

    def select_fastfilter(self, handle):
        data = self.dbstate.db.get_raw_citation_data(handle)
        source_handle = data[5]
        iter_ = self.source_handles[source_handle]
        path = self.model2.get_path(iter_)
        self.fast_selection.unselect_all()
        self.fast_selection.select_path(path)
        self.list2.scroll_to_cell(path, None, 1, 0.5, 0)

class FastSourceFilter(object):

    def __init__(self, db, handle):
        self.db = db
        self.handle = handle

    def match(self, data, db):
        return data[5] == self.handle
