from ._anvil_designer import ImportFormTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.media
from .. import Global

class ImportForm(ImportFormTemplate):
  def Import_refresh(self, **event_args):
    # this function does the filling of the table contents
    print("Import refresh button pressed. Current work_area ",Global.current_work_area_name )
    self.message_log.text = ""
    self.upload_file.clear()
  pass
  
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    self.Import_title.text = "Here you can import csv files for importing to the Database. You can download a template csv file if needed."
    Global.table_name = Global.action.split(" ")[1].lower()
    self.selected_table.text = Global.table_name
    Global.main_form.mb_left.visible = False
    Global.main_form.mb_middle.visible = False


  def upload_file_change(self, file, **event_args):
    """This method is called when a new file is loaded into this FileLoader"""
    #print(Global.current_work_area_name)
    self.selected_file_name.text = ""
    self.message_log.text = ""
    Global.DBAcontrol = ""
    self.selected_file_name.text = "You have selected file: " + file.name
    msg = "You have selected file: " + file.name + "\nDo you wish to continue?"
    if confirm(content=msg):
      msg = anvil.server.call("import_file", Global.table_name, file)
      self.message_log.text = msg
      change_id = msg.splitlines(False)[0]
      #print(change_id)
      Global.DBAcontrol = change_id.split(" ")[2]
      #print(Global.DBAcontrol)
    else:
      self.upload_file.clear()
      self.selected_file_name.text = ""
      self.message_log.text = ""
    pass

  def cancel_inserts_click(self, **event_args):
    """This method is called when the button is clicked"""
    message = anvil.server.call("delete_by_DBAcontrol",Global.DBAcontrol,Global.table_name)
    self.message_log.text = self.message_log.text + message
    byte_string = bytes(self.message_log.text, "utf-8")
    text_file = anvil.BlobMedia('text/plain', byte_string, name='Import_message.log')
    anvil.media.download(text_file)
    note = "The successful inserts to table " + Global.table_name + " have been cancelled and deleted from the table. The message log has been downloaded."
    n = Notification(note)
    n.show()
    #
    self.upload_file.clear()
    self.selected_file_name.text = ""
    self.message_log.text = ""
    pass

  def commit_inserts_click(self, **event_args):
    """This method is called when the button is clicked"""
    byte_string = bytes(self.message_log.text, "utf-8")
    text_file = anvil.BlobMedia('text/plain', byte_string, name='Import_message.log')
    anvil.media.download(text_file)
    n = Notification("The successful Inserts have been comitted to the table. The message log has been downloaded.")
    n.show()
    #
    self.upload_file.clear()
    self.selected_file_name.text = ""
    self.message_log.text = ""
    pass
