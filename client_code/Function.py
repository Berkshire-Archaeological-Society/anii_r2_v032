from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

#from .ListUsers import ListUsers

# This is a module.
# You can define variables and functions here, and use them from any form. For example, in a top-level form:
#
#    from .. import Function
#
#    Function.say_hello()
#
# Global Functions
from . import Global

from ListContexts import ListContexts
from ListFinds import ListFinds
from ListSites import ListSites
from ListAreas import ListAreas
from ListAnvilUsers import ListAnvilUsers
from TableList import TableList
from ContextForm import ContextForm
from FindForm import FindForm
from AreaForm import AreaForm
from RowForm import RowForm
from SiteForm import SiteForm
from AnvilUserForm import AnvilUserForm
from ImportForm import ImportForm
from Help import Help

from Draw import Draw
#from Workarea import Workarea

def create_work_space(type,data_list):
  #print("Work space to create is: ",type)
  page_info = {}
  table_name = type.split(" ")[1].lower()
  action = type.split(" ")[0].lower()
  Global.query_view = False
  if table_name in Global.view_queries:
    Global.query_view = True

  #print(type, action, table_name)
  # First param of RowForm and TableList is site_id, but is blanked out. Only used by server print function
  # Make sure any List actions that are not using the TableList Form should be listed first
  if type == "List Anvilusers":
    work_space = ListAnvilUsers()
  elif type == "Edit AnvilUser" or type == "Insert Anviluser":
    work_space = AnvilUserForm()
  #elif type == "List Site":
  #  work_space = ListSites()
  #
  elif action == "list":
    work_space = TableList("",table_name,data_list,type,page_info)
  #
  elif action == "import":
    work_space = ImportForm()
  #
  elif action in ["add","insert"]:
    work_space = RowForm("",table_name,data_list,type,page_info)
  #
  elif action == "edit":
    work_space = RowForm("",table_name,data_list,type,page_info)
  #
  elif action == "view":
    #print(action, table_name)
    work_space = RowForm("",table_name,data_list,type,page_info)

  #elif type == "Draw":
  #  work_space = Draw()
  #
  elif type == "Help":
    work_space = Help()
  else:
    #print("Unknown Type - no known workspace")
    work_space = "Unknown"
  return work_space

def delete_workspace(work_area_name):
  # remove work_area_name form and work_area_name button
  Global.work_area[work_area_name]["button"].remove_from_parent()
  Global.work_area[work_area_name]["form"].remove_from_parent()
  # now remove (pop) the work_area_name from lists
  Global.work_area.pop(work_area_name)
  # clear header and make it invisible
  Global.header_work_area_name.text = ""
  Global.header_work_area_type.text = ""
  Global.header.visible = False
  Global.main_form.menu_bottom.visible = False
  return

def delete_all_workspace(work_area_list):
  return

def save_work_areas():
  # need to create a media object of the work_area list 
  
  success = anvil.server.call("save_work_areas", Global.work_area,Global.site_id) 
  return

