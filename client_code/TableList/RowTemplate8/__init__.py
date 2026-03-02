from ._anvil_designer import RowTemplate8Template
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from .. import Global

class RowTemplate8(RowTemplate8Template):
  
  def btn_delete_click(self, **event_args):
    """This handler is called by the dynamically created button."""
    #print(self.item)
    #print(Global.table_name)
    Global.table_items = self.item
    Global.action = "Delete " + Global.table_name.capitalize()
    message = "You have seleted to delete " + Global.table_name.capitalize() + "\n\n" + str(self.item) + "\n\nDo you wish to continue?"
    confirm(message)
  pass
  
  def btn_select_click(self, **event_args):
    """This handler is called by the dynamically created button."""
    #
    Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = True
    self.parent.raise_event('x-selection-change')
    #     
    if event_args["sender"].checked:
      # add row to selected list but first remove select column
      row = self.item
      Global.work_area[Global.current_work_area_name]["selected_rows"].append(row)
      self.background = Global.selected_highlight_colour
    else:
      #remove row from selected list
      Global.work_area[Global.current_work_area_name]["selected_rows"].remove(self.item)
      self.background = ""
    #
    # remove menu_select_options if there are no more selected_rows
    if len(Global.work_area[Global.current_work_area_name]["selected_rows"]) == 0:
      Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = False

    Global.table_items = self.item
    Global.action = "Select " + Global.table_name.capitalize()
  pass

  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
    # create the view and edit button for the row and set button click event handlers
    self.btn_select = CheckBox(text='',align='left',tooltip="select row")
    self.btn_select.set_event_handler('change',self.btn_select_click)
    self.item['select'] = self.btn_select
    self.spacing_above = 'none'
    self.spacing_below = 'none'

    self.add_component(self.item['select'], column='1')

