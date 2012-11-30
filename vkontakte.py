# -*- Mode: python; coding: utf-8; tab-width: 4; indent-tabs-mode: nil; -*-
#
# Copyright (C) 2012 Huhlaev Alexander  <sancheolz@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# The Rhythmbox authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and Rhythmbox. This permission is above and beyond the permissions granted
# by the GPL license by which Rhythmbox is covered. If you modify this code
# you may extend this exception to your version of the code, but you are not
# obligated to do so. If you do not wish to do so, delete this exception
# statement from your version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301  USA.

import rb
from gi.repository import GObject, Peas, Gtk, GdkPixbuf, RB, PeasGtk, Gio

from VkontakteSource import VkontakteSource

class VkontakteEntryType(RB.RhythmDBEntryType):
    def __init__(self):
        RB.RhythmDBEntryType.__init__(self, name='vkontakte')

    def do_can_sync_metadata(self, entry):
        return True

class Vkontakte(GObject.Object, Peas.Activatable):
    __gtype_name = 'Vkontakte'
    object = GObject.property(type=GObject.GObject)

    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        shell = self.object
        db = shell.props.db
        model = RB.RhythmDBQueryModel.new_empty(db)
        entry_type = VkontakteEntryType()
        db.register_entry_type(entry_type)
        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.LARGE_TOOLBAR)
        icon = GdkPixbuf.Pixbuf.new_from_file_at_size(rb.find_plugin_file(self, "icon.ico"), width, height)
        source_group = RB.DisplayPageGroup.get_by_id("library")
        self.source = GObject.new(VkontakteSource, name=_("Vkontakte"), shell=shell, query_model=model, plugin=self, pixbuf=icon, entry_type=entry_type)
        shell.append_display_page(self.source, source_group)
        shell.register_entry_type_for_source(self.source, entry_type)
        self.source.initialise()

    def do_deactivate(self):
        self.source.delete_thyself()
        self.source = None

class VkontakteConfig(GObject.GObject, PeasGtk.Configurable):
    __gtype_name__ = 'VkontakteConfig'
    object = GObject.property(type=GObject.GObject)

    def __init__(self):
        GObject.GObject.__init__(self)
        self.settings = Gio.Settings("org.gnome.rhythmbox.plugins.vkontakte")

    def do_create_configure_widget(self):
        builder = Gtk.Builder()
        builder.add_from_file(rb.find_plugin_file(self, "vkontakte-prefs.ui"))

        dialog = builder.get_object('vkontakte-vbox')
        def filemask_changed(entry, event):
            filemask = entry.get_text()
            if filemask == "":
                print "missing something"
                return
            self.settings['filemask'] = filemask
        filemask_entry = builder.get_object("filemask")
        filemask_entry.set_text(self.settings['filemask'])

        filemask_entry.connect("focus-out-event", filemask_changed)

        return dialog
