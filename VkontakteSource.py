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

from gi.repository import GObject, Gio, GLib, Peas, Gtk, Gdk
from gi.repository import RB

from VkontakteSearch import VkontakteSearch
import shutil, os, tempfile
import vk_auth
import VkontakteAccount

APP_ID = 1850196

class VkontakteSource(RB.Source):
    def __init__(self, **kwargs):
        super(VkontakteSource, self).__init__(kwargs)
        self.initialised = False
        self.downloading = False
        self.download_queue = []
        self.__load_current_size = 0
        self.__load_total_size = 0
        self.error_msg = ''
        self.searches = {}
        self.token = ''
        self.account = VkontakteAccount.instance()
        self.settings = Gio.Settings("org.gnome.rhythmbox.plugins.vkontakte")

    def initialise(self):
        login, password = self.account.get()
        self.token, self.user_id = vk_auth.auth(login, password, APP_ID, "audio,friends")
        if len(self.token) == 0:
            self.show_login_ctrls()
        else:
            self.show_search_ctrls()

    def show_search_ctrls(self):
        shell = self.props.shell
        # list of tracks
        entry_view = RB.EntryView.new(db=shell.props.db, shell_player=shell.props.shell_player, is_drag_source=True, is_drag_dest=False)
        entry_view.append_column(RB.EntryViewColumn.TITLE, True)
        entry_view.append_column(RB.EntryViewColumn.ARTIST, True)
        entry_view.append_column(RB.EntryViewColumn.DURATION, True)
        entry_view.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        entry_view.connect("entry_activated", self.entry_activated_cb)
        self.entry_view = entry_view

        search_entry = Gtk.Entry()
        search_entry.set_activates_default(True)

        self.search_entry = search_entry
        search_button = Gtk.Button(_("Search"))
        search_button.connect("clicked", self.on_search_button_clicked)

        hbox = Gtk.HBox()
        hbox.pack_start(search_entry, True, True, 0)
        hbox.pack_start(search_button, False, False, 5)

        vbox = Gtk.VBox()
        vbox.pack_start(hbox, False, False, 0)
        vbox.pack_start(entry_view, True, True, 5)

        self.pack_start(vbox, True, True, 0)
        self.show_all()

        entry_view.connect("show_popup", self.show_popup_cb)

        action_copyurl = Gtk.Action ('CopyURL', 'Copy URL', 'Copy URL to Clipboard', "")
        action_copyurl.connect ('activate', self.copy_url, shell)
        action_download = Gtk.Action ('Download', 'Download', 'Download', "")
        action_download.connect ('activate', self.download, shell)
        action_group = Gtk.ActionGroup ('VkontakteSourceViewPopup')
        action_group.add_action (action_copyurl)
        action_group.add_action (action_download)
        shell.props.ui_manager.insert_action_group (action_group)

        popup_ui = """
<ui>
  <popup name="VkontakteSourceViewPopup">
    <menuitem name="CopyURL" action="CopyURL"/>
    <menuitem name="Download" action="Download"/>
    <separator name="Sep"/>
  </popup>
</ui>
"""

        self.ui_id = shell.props.ui_manager.add_ui_from_string(popup_ui)
        shell.props.ui_manager.ensure_update()

        self.initialised = True
  
    def show_login_ctrls(self):
        login_label = Gtk.Label(_("Login or e-mail:"))

        self.login_entry = Gtk.Entry()
        self.login_entry.set_activates_default(True)

        password_label = Gtk.Label(_("Password:"))

        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)

        alignleft_for_login = Gtk.Alignment.new(0, 0, 0, 0)
        alignleft_for_login.add(login_label)

        alignleft_for_password = Gtk.Alignment.new(0, 0, 0, 0)
        alignleft_for_password.add(password_label)

        login_button = Gtk.Button(_("Login"))
        login_button.connect("clicked", self.on_login_button_clicked)

        table = Gtk.Table(3, 5, False)
        table.attach(Gtk.Label(), 0, 1, 0, 5, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)

        table.attach(alignleft_for_login, 1, 2, 0, 1, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)
        table.attach(self.login_entry, 1, 2, 1, 2, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)
        table.attach(alignleft_for_password, 1, 2, 2, 3, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)
        table.attach(self.password_entry, 1, 2, 3, 4, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)
        table.attach(login_button, 1, 2, 4, 5, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)

        table.attach(Gtk.Label(), 2, 3, 0, 5, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, Gtk.AttachOptions.EXPAND | Gtk.AttachOptions.FILL, 5, 5)

        vbox = Gtk.VBox()
        vbox.pack_start(table, False, False, 5)

        self.pack_start(vbox, True, True, 0)

        self.show_all()

        self.initialised = True

    def do_impl_get_entry_view(self):
        return self.entry_view

    # rhyhtmbox api break up (0.13.2 - 0.13.3)
    def do_impl_activate(self):
        self.do_selected()

    # play entry by enter or doubleclick
    def entry_activated_cb(self, entry_view, selected_entry):
        self.props.shell.props.shell_player.play_entry(selected_entry, self)

    def do_selected(self):
        print "do_selected"
        if not self.initialised:
            self.initialise()

    # rhyhtmbox api break up (0.13.2 - 0.13.3)
    def do_impl_get_status(self):
        return self.do_get_status()

    def do_get_status(self, status, progress_text, progress):
        if self.downloading:
            print "self.downloading = %s" % self.downloading
            if self.__load_total_size > 0:
                # Got data
                progress = min (float(self.__load_current_size) / self.__load_total_size, 1.0)
            else:
                # Download started, no data yet received
                progress = -1.0
            status = "Downloading %s" % self.filename[:70]
            if self.download_queue:
                status += " (%s files more in queue)" % len(self.download_queue)
            return (status, "", progress)

        if hasattr(self, 'current_search') and self.current_search:
            print "self.current_search = '%s'" % self.current_search
            if self.searches[self.current_search].is_complete():
                self.error_msg = self.searches[self.current_search].error_msg
                if not self.error_msg:
                    return (self.props.query_model.compute_status_normal("Found %d result", "Found %d results"), "", 1)
            else:
                return ("Searching for \"{0}\"".format(self.current_search), "", -1)

        if self.error_msg:
            print "self.error_msg = '%s'" % self.error_msg
            #error_msg = self.error_msg
            #self.error_msg = ''
            return (self.error_msg, "", 1)

        return ("", "", 1)

    def do_impl_delete_thyself(self):
        if self.initialised:
            self.props.shell.props.db.entry_delete_by_type(self.props.entry_type)
        RB.Source.do_impl_delete_thyself(self)

    def do_impl_can_add_to_queue(self):
        return True

    def do_impl_can_pause(self):
        return True

    def on_login_button_clicked(self, button):
        login, password = self.login_entry.get_text(), self.password_entry.get_text()
        self.token, self.user_id = vk_auth.auth(login, password, APP_ID, "audio,friends")
        if len(self.token) > 0:
            self.account.update(login, password)
        for child in self.get_children():
            child.destroy()
        self.show_search_ctrls()

    def on_search_button_clicked(self, button):
        print "clicked search"
        entry = self.search_entry
        self.current_search = entry.get_text()
        if len(self.current_search) > 0:
            self.entry_view.set_sorting_order("Title", Gtk.SortType.ASCENDING)
        print "searching for '%s'" % self.current_search

        search = VkontakteSearch(self.token, self.user_id, self.current_search, \
                               self.props.shell.props.db, self.props.entry_type)
        # Start the search asynchronously
        GLib.idle_add(search.start, priority=GLib.PRIORITY_HIGH_IDLE)
        self.props.query_model = search.query_model

        self.searches[self.current_search] = search
        self.entry_view.set_model(self.props.query_model)

    def show_popup_cb(self, entry_view, over_entry):
        # rhythmbox api break up (0.13.2 - 0.13.3)
        if over_entry:
            menu = self.props.shell.props.ui_manager.get_widget('/VkontakteSourceViewPopup')
            menu.popup(None, None, None, None, 3, 0)

    def copy_url(self, action, shell):
        # rhythmbox api break up (0.13.2 - 0.13.3)
        try:
            selected_source = shell.get_property("selected-source")
        except:
            selected_source = shell.get_property("selected-page")
        download_url = self.entry_view.get_selected_entries()[0].get_playback_uri();
        atom = Gdk.atom_intern('CLIPBOARD', True)
        clipboard = Gtk.Clipboard.get(atom)
        clipboard.set_text(download_url, -1)
        clipboard.store()

    def download(self, action, shell):
        # rhythmbox api break up (0.13.2 - 0.13.3)
        try:
            selected_source = shell.get_property("selected-source")
        except:
            selected_source = shell.get_property("selected-page")
        for entry in self.entry_view.get_selected_entries():
            self.download_queue.append(entry)
        if not self.downloading:
            entry = self.download_queue.pop(0)
            self._start_download(entry)

    def _start_download(self, entry):
        shell = self.props.shell
        self.download_url = entry.get_playback_uri()

        filemask = self.settings['filemask']
        artist = ''
        title = ''
        shell.props.db.entry_get(entry, RB.RhythmDBPropType.ARTIST, artist)
        artist = artist[:50].replace('/', '')
        shell.props.db.entry_get(entry, RB.RhythmDBPropType.TITLE, title)
        title = title[:50].replace('/', '')
        filemask = filemask.replace('%A', artist)
        filemask = filemask.replace('%T', title)

        self.filename = u"%s - %s" % (artist, title)
        self.save_location = os.path.expanduser(filemask)
        dir, file = os.path.split(self.save_location)
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except:
                self.error_msg = "Can't create or access directory. Check settings (Edit => Plugins => Configure)"
                self.notify_status_changed()
                return

        # Download file to the temporary folder
        self.output_file = tempfile.NamedTemporaryFile(delete=False)
        self.downloading = True
        self.notify_status_changed()

        self.downloader = RB.ChunkLoader()
        self.downloader.set_callback(self.download_callback, self.output_file)
        self.downloader.start(self.download_url, 64 * 1024)

    def download_callback (self, loader, data, total, out):
        if not data:
            # Download finished
            error = loader.get_error()
            if error:
                # report error somehow?
                print "Error during downloading process happened: %s" % error
                pass
            out.file.close()
            self.__load_current_size = 0
            self.downloading = False
            # Move temporary file to the save location
            try:
                shutil.move(out.name, self.save_location)
            except:
                self.error_msg = "Can't write to directory. Check settings (Edit => Plugins => Configure)"
                self.notify_status_changed()
                return
            if self.download_queue:
                entry = self.download_queue.pop(0)
                return self._start_download(entry)
            else:
                self.downloading = False

        if self.downloading:
            # Write to the file, update downloaded size
            self.__load_current_size += len(data.str)
            self.__load_total_size = total
            out.file.write(data.str)

        self.notify_status_changed()

GObject.type_register(VkontakteSource)
