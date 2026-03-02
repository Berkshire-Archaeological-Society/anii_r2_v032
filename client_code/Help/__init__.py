from ._anvil_designer import HelpTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

from .. import Global

class Help(HelpTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    
    # Any code you write here will run before the form opens.
    Global.help_page_form = self
    #rt = RichText(content=Global.help_introduction,format="restricted_html")
    #self.help_page_text.add_component(rt)
    self.help_page_text.visible = True
