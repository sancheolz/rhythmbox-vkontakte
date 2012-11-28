from gi.repository import GObject, Gio, GLib, Peas, Gtk
from gi.repository import RB

from VkontakteSearch import VkontakteSearch
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
        entry_view.set_sorting_order("Title", Gtk.SortType.ASCENDING)
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
    if entry.get_text():
      self.current_search = entry.get_text()
      print "searching for '%s'" % self.current_search
 
      search = VkontakteSearch(self.token, self.user_id, self.current_search, \
                               self.props.shell.props.db, self.props.entry_type)
      # Start the search asynchronously
      GLib.idle_add(search.start, priority=GLib.PRIORITY_HIGH_IDLE)
      self.props.query_model = search.query_model

      self.searches[self.current_search] = search
      self.entry_view.set_model(self.props.query_model)

GObject.type_register(VkontakteSource)
