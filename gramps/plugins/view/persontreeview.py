# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2000-2007  Donald N. Allingham
# Copyright (C) 2008       Gary Burton
# Copyright (C) 2009       Nick Hall
# Copyright (C) 2010       Benny Malengier
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
Person Tree View
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
from gramps.plugins.lib.libpersonview import BasePersonView
from gramps.gui.views.treemodels.peoplemodel import PersonListModel
from gramps.gen.lib import Name, Person, Surname
from gramps.gen.errors import WindowActiveError
from gramps.gui.editors import EditPerson
from gramps.gen.display.name import displayer as name_displayer

#-------------------------------------------------------------------------
#
# Internationalization
#
#-------------------------------------------------------------------------
from gramps.gen.const import GRAMPS_LOCALE as glocale
_ = glocale.translation.gettext

#-------------------------------------------------------------------------
#
# PersonTreeView
#
#-------------------------------------------------------------------------
class PersonTreeView(BasePersonView):
    """
    A hierarchical view of the people based on family name.
    """
    def __init__(self, pdata, dbstate, uistate, nav_group=0):
        BasePersonView.__init__(self, pdata, dbstate, uistate,
                               _('People Tree View'), PersonListModel,
                               nav_group=nav_group)

    def get_viewtype_stock(self):
        """
        Override the default icon.  Set for hierarchical view.
        """
        return 'gramps-tree-group'

    def add(self, obj):

        # attempt to get the current surname
        group_as = ''
        store, iter_ = self.fast_selection.get_selected()
        if iter_:
            group_as = store.get_value(iter_, 0)

        person = Person()
        name = Name()
        surname = Surname()
        surname.set_surname(group_as)
        name.add_surname(surname)
        name.set_primary_surname(0)
        person.set_primary_name(name)
        try:
            EditPerson(self.dbstate, self.uistate, [], person)
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

        column = Gtk.TreeViewColumn(_('Group As'), self.renderer)
        column.add_attribute(self.renderer, 'text', 0)
        column.set_sort_column_id(0)
        column.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        column.set_fixed_width(150)
        treeview.append_column(column)

        self.fast_selection = treeview.get_selection()
        self.fast_selection.connect('changed', self.selection_changed)

        model = Gtk.ListStore(str)
        ngn = name_displayer.name_grouping_data
        self.group_names = {}
        for key, data in self.dbstate.db.get_person_cursor():
            group_name = ngn(self.dbstate.db, data[3])
            if group_name not in self.group_names:
                self.group_names[group_name] = model.append((group_name,))
        treeview.set_model(model)

        self.list2 = treeview
        self.model2 = model

    def selection_changed(self, selection):
        store, iter_ = selection.get_selected()
        if iter_:
            group_as = store.get_value(iter_, 0)

            self.list.set_model(None)
            self.model.ff = FastGroupAsFilter(self.dbstate.db, group_as)
            self.model.rebuild_data()
            self.list.set_model(self.model)

            self.uistate.show_filter_results(self.dbstate,
                                             self.model.displayed(),
                                             self.model.total())

    def select_fastfilter(self, handle):
        data = self.dbstate.db.get_raw_person_data(handle)
        ngn = name_displayer.name_grouping_data
        group_name = ngn(self.dbstate.db, data[3])
        iter_ = self.group_names[group_name]
        path = self.model2.get_path(iter_)
        self.fast_selection.unselect_all()
        self.fast_selection.select_path(path)
        self.list2.scroll_to_cell(path, None, 1, 0.5, 0)

class FastGroupAsFilter(object):

    def __init__(self, db, group_as):
        self.db = db
        self.group_as = group_as

    def match(self, data, db):
        group_as = name_displayer.name_grouping_data(self.db, data[3])
        return group_as == self.group_as
