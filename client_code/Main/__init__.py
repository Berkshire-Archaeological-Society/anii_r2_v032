from ._anvil_designer import MainTemplate
from anvil import *
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
from anvil.js.window import document
import anvil.js

from .. import indeterminate
from ..Header import Header
from ..RowForm import RowForm
from ..TableList import TableList
from ..ImportForm import ImportForm
from ..FilterList import FilterList
from .. import Global
from .. import Function
from .. import FunctionsB
from ..Help import Help

# branch V054

class Main(MainTemplate):  
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    
    # get client variable settings from server configuration file
    globals_from_config = anvil.server.call("client_globals")
    Global.rows_per_page = globals_from_config["rows_per_page"]
    Global.version = globals_from_config["version"]
    Global.organisation = globals_from_config["organisation"]
    Global.config_version = globals_from_config["version"]
    Global.admin_domain = globals_from_config["admin_domain"]
    Global.admin_user = globals_from_config["admin_user"]
    Global.admin_user_initials = globals_from_config["admin_user_initials"]
    
    # add Header component (but make it invisible)
    Global.header = Header()
    self.add_component(Global.header, slot='header_slot')
    Global.header.visible = False
    # add Help component (but make it invisible)
    Global.help_page = Help()
    self.add_component(Global.help_page, slot='help_slot')
    Global.help_page.visible = False

    # set Main title field with name of organisation (defined in Anchurus-2.cgf file from server)
    #Global.title_label = self.title
    #self.title.text = Global.title + Global.status + Global.selected_site
    self.app_title.text = Global.system
    self.organisation.text = Global.organisation
    self.app_title.text = Global.system
    self.organisation.text = Global.organisation
    self.app_name.text = document.head.querySelector('[name=title]').content
    self.config_version.text = "cfg " + Global.config_version
    
    # add the about_us_text (taken from Anchurus-2.cfg file) to the about_us_box text field by adding a Rich Text Component
    rt = RichText(content=Global.about_us_text,format="restricted_html")
    self.about_us_box.add_component(rt)
    
    # Create empty work_area_list
    Global.work_area_list = {}

    # Get table list and create dropdown options for list and insert
    table_list = anvil.server.call("db_table_list")    
    Global.insert_action_dropdown = table_list
    Global.list_action_dropdown = table_list
    Global.import_action_dropdown = table_list
    # fill action menu options
    self.import_dropdown.items = Global.import_action_dropdown
    self.insert_dropdown.items = Global.insert_action_dropdown
    self.list_dropdown.items = Global.list_action_dropdown
    self.admin_dropdown.items = Global.sys_admin_action_dropdown
    #self.file_dropdown.items = Global.file_list
    #self.view_dropdown.items = Global.view_action_dropdown
    self.help_dropdown.items = Global.help_action_dropdown
    #
    #self.file_dropdown.items = Global.file_action_dropdown

    #self.action_list.items = Global.user_action_list
    # make all fields invisible to only show about_us_text box as welcome followed by login and registration buttons (see design of Main)
    Global.wa_header_menu_bottom = self.menu_bottom
    Global.wa_header_mb_left = self.mb_left
    Global.wa_header_mb_middle = self.mb_middle
    Global.wa_header_mb_right = self.mb_right
    #self.action_list.visible = False
    self.site_summary.visible = False
    #
    self.menu_block.visible = True
    self.title_panel.visible = True
    self.menu_top.visible = False
    self.menu_middle.visible = False
    #self.mm_left.visible = False
    #self.mm_right.visible = False
    #
    Global.wa_header_menu_bottom.visible = False
    #
    self.admin_dropdown.visible = False
    Global.main_form = self

  #
  # Functions
  # =========
  def work_area_click(self, **event_args):
    """" This function is called when the work area button is clicked. Here we make sure all the variable are set correct for the work area swap"""

    # Here the user clicked on a work_area button in the left navigation list, requested to go to a different work area.
    # first make all work_areas invisible and set button to be 'normal', i.e. not highlighted
    for name in Global.work_area:
      Global.work_area[name]["form"].visible = False
      Global.work_area[name]["button"].bold = False
      Global.work_area[name]["button"].background = Global.button_normal_background_clour
    
    # now get the name of the button (work_area_name) that was clicked and make this and the associated work_area visible
    work_area = event_args['sender']
    Global.current_work_area_name = work_area.text
    #print("Work area clicked: ",Global.current_work_area_name)
    
    # Set Global.table_name linked with work_area_type
    Global.table_name = Global.work_area[Global.current_work_area_name]["action"].split(" ")[1].lower()

    # set Global variables for site information
    Global.site_name = Global.work_area[Global.current_work_area_name]["site_name"]
    Global.site_id = Global.work_area[Global.current_work_area_name]["site_id"]
    Global.selected_site = ": " + Global.site_name
    
    # Fill header fields with work_area name and work_area Form name
    # This was for old header, can prob removed
    Global.header_work_area_name.text = Global.current_work_area_name
    Global.header_work_area_type.text = str(type(Global.work_area[Global.current_work_area_name]["form"])).split(".")[2][:-2]
    Global.header_site_name.text = Global.work_area[Global.current_work_area_name]["site_name"]

    # Show work_area and set focus on work_area_name
    Global.work_area[Global.current_work_area_name]["form"].visible = True
    Global.work_area[Global.current_work_area_name]["button"].bold = False
    Global.work_area[Global.current_work_area_name]["button"].background = Global.button_highlight_background_clour

    # make old header invisible
    Global.header.visible = False
    Global.wa_header_menu_bottom.visible = True
    
    # set menu_select_options as invisible
    Global.work_area[Global.current_work_area_name]["menu_select_options"] = self.fp_select_options
    Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = False

    Global.action_form_type = str(type(Global.work_area[Global.current_work_area_name]["form"])).split(".")[2][:-2]
    #
    #print("Work area action form type: ",Global.action_form_type)
    if Global.work_area[Global.current_work_area_name]["action"].split(" ")[0] in ["View", "Edit", "Insert", "Add", "Import"] or Global.work_area[Global.current_work_area_name]["action"] == "List Anvilusers":
      self.mb_middle.visible = False
      self.mb_left.visible = False
    elif Global.work_area[Global.current_work_area_name]["action"].split(" ")[0] in ["List"]:
      self.mb_middle.visible = True
      self.mb_left.visible = True

    self.select_all.indeterminate = False
    self.select_all.checked = False

    # update status label (page control information) if work_space is a List (but not List Anvilusers (not using the TableList form))
    if Global.work_area[Global.current_work_area_name]["action"].split(" ")[0] in ["List"] and Global.work_area[Global.current_work_area_name]["action"] != "List Anvilusers":
      #print(Global.current_work_area_name)
      FunctionsB.update_status_label(Global.work_area[Global.current_work_area_name]["self"])

    if len(Global.work_area[Global.current_work_area_name]["selected_rows"]) == 0:
      #print("work_area_click: ", Global.current_work_area_name, " 0 selected rows, disable menu")
      Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = False
      self.select_all.checked = False
      self.select_all.indeterminate = False
      #Global.work_area[Global.current_work_area_name]["self"].select_all
    else:
      #print("work_area_click: ", Global.current_work_area_name, " there are selected rows, enable menu")
      Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = True
      page_num = int(Global.work_area[Global.current_work_area_name]["table"].get_page())
      rows_per_page = int(Global.work_area[Global.current_work_area_name]["table"].rows_per_page)
      total_rows = len(Global.work_area[Global.current_work_area_name]["self"].repeating_panel_1.items)
      rest = total_rows - page_num * rows_per_page
      #print(str(len(Global.work_area[Global.current_work_area_name]["selected_rows"])),str(rest),str(Global.rows_per_page))
      if str(len(Global.work_area[Global.current_work_area_name]["selected_rows"])) == str(Global.rows_per_page) or str(len(Global.work_area[Global.current_work_area_name]["selected_rows"])) == str(rest):
        self.select_all.checked = True 
      else:
        self.select_all.indeterminate = True
    
    #self.select_all.checked = Global.work_area[Global.current_work_area_name]["self"].select_all.checked
    #self.select_all.indeterminate = Global.work_area[Global.current_work_area_name]["self"].select_all.indeterminate

    # Set selected buttons on Header for work area type
    if Global.action_form_type in Global.action_forms_with_refresh:
      # Make refresh button visible for Global.action_form_type
      Global.header_refresh_button.visible = True
      self.refresh.visible = True
    else:
      Global.header_refresh_button.visible = False
      self.refresh.visible = False
    if Global.action_form_type in Global.action_forms_with_print:
      # Make print button visible for Global.action_form_type
      Global.header_print_button.visible = True
      self.print.visible = True
    else:
      Global.header_print_button.visible = False
      self.print.visible = False
    if Global.action_form_type in Global.action_forms_with_download:
      # Make download button visible for Global.action_form_type
      Global.header_download_button.visible = True
      self.download_csv.visible = True
    else:
      Global.header_download_button.visible = False
      self.download_csv.visible = False
    if Global.action_form_type in Global.action_forms_with_filter and Global.work_area[Global.current_work_area_name]["data_list"]:
      # Make filter button visible for Global.action_form_type if data_list is not empty
      Global.header_filter_button.visible = True
      self.filter_cols.visible = True
    else:
      Global.header_filter_button.visible = False
      self.filter_cols.visible = False
  pass

  def create_new_work_area(self,action):
    """ This Function is called when a user creates a new work area"""
    #
    # First make sure the old header is invisible
    Global.header.visible = False
    Global.wa_header_menu_bottom.visible = True

    # set name of work_area to be action name
    work_area_name = action
    #print("Click work area, action: ",action)
    # For all actions not in Admin_action_list check ID field for creating unique work_area name
    if action not in Global.sys_admin_action_list and action not in Global.site_admin_action_list:
      # add first Primary Key ID field when view or edit
      table_info = anvil.server.call("describe_table",action.split(" ")[1].lower())
      primary_key_list = []
      for column in table_info:
        if column["Key"] == "PRI":
          primary_key_list.append(column["Field"])
      if action.split(" ")[0].lower() in ["view","edit"]:
        if len(primary_key_list) == 1:
          work_area_name = action.split(" ")[0] + " " + Global.table_items[primary_key_list[0]]
        else:
          work_area_name = action.split(" ")[0] + " " + Global.table_items[primary_key_list[1]]
        
    # check if work_area_name exists and keep counter
    if (Global.work_area.get(work_area_name) is None):
      if Global.action_seq_no.get(work_area_name) is None:
        # only set seq_no to 1 if the work_area_name has never been used before 
        Global.action_seq_no[work_area_name] = 1
      else:
        # this is for increasing the counter eventhough the work_area_name is not in use.
        # this code will cater if there have already been instances of work_area_name but 'earlier' ones have been deleted.
        Global.action_seq_no[work_area_name] += 1
        work_area_name = work_area_name + " (" + str(Global.action_seq_no[work_area_name]) + ")"
    else:
      # work_area_name exists, so update work_area_name to add seq_no in brackets
      Global.action_seq_no[work_area_name] += 1
      work_area_name = work_area_name + " (" + str(Global.action_seq_no[work_area_name]) + ")"

    # create new 'empty row' in nested work_area dictionary for the new work_area_name
    Global.work_area[work_area_name] = {}
    Global.work_area[work_area_name]["action"] = action
    Global.current_work_area_name = work_area_name

    # set menu_select_opti0ns as invisible
    Global.work_area[Global.current_work_area_name]["menu_select_options"] = self.fp_select_options
    Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = False

    # Set Global.table_name linked with work_area_type
    Global.table_name = Global.work_area[work_area_name]["action"].split(" ")[1].lower()

    # create the button for the work_area in the navigation panel, add it to the work_area_list Column Panel and set event handler for when clicked
    if Global.dummy_btn1 != {}:
      Global.dummy_btn1.remove_from_parent() 
      Global.dummy_btn2.remove_from_parent() 

    Global.work_area[work_area_name]["button"] = Button(text=work_area_name,align="left",tooltip="select workspace")
    self.work_area_list.add_component(Global.work_area[work_area_name]["button"])
    Global.work_area[work_area_name]["button"].add_event_handler('click', self.work_area_click)
    
    Global.dummy_btn1 = Button(text="")
    Global.dummy_btn1.enabled = False
    Global.dummy_btn1.visible = True
    self.work_area_list.add_component(Global.dummy_btn1) 
    Global.dummy_btn2 = Button(text="")
    Global.dummy_btn2.enabled = False
    Global.dummy_btn2.visible = True
    self.work_area_list.add_component(Global.dummy_btn2)
    
    # add the table_items to the work_area_name
    Global.work_area[work_area_name]["data_list"] = [Global.table_items]
    
    # create a new work_space and add this to the work_area_list and add component to main     
    #print("Main create_new_work_area: ",self)
    form_result = Function.create_work_space(action,Global.table_items)
    if form_result != "Unknown":
      #print(action, work_area_name, Global.work_area)
      Global.work_area[work_area_name]["form"] = form_result
      #print(Global.work_area[work_area_name]["form"])
      self.add_component(Global.work_area[work_area_name]["form"])
       
      # set button name to new work_area_name
      Global.work_area[work_area_name]["button"].text = work_area_name
      Global.work_area[work_area_name]["form_type"] = str(type(Global.work_area[work_area_name]["form"])).split(".")[2][:-2]
      #
      Global.work_area[work_area_name]["site_name"] = Global.site_name
      Global.header_site_name.text = Global.work_area[work_area_name]["site_name"]
      Global.work_area[work_area_name]["site_id"] = Global.site_id
    
      # set selected rows list to empty
      Global.work_area[work_area_name]["selected_rows"] = []

      # make all work spaces invisible
      for name in Global.work_area:
        Global.work_area[name]["form"].visible = False
        Global.work_area[name]["button"].bold = False
        Global.work_area[name]["button"].background = Global.button_normal_background_clour
    
      # create an empty filter and empty hidden_columns
      Global.work_area[Global.current_work_area_name]["filter"] = []
      Global.work_area[Global.current_work_area_name]["hidden_columns"] = []
    
      # Make newly created work area visible and have Focus
      Global.work_area[work_area_name]["form"].visible = True
      Global.work_area[work_area_name]["button"].bold = False
      Global.work_area[work_area_name]["button"].background = Global.button_highlight_background_clour
      #
      Global.header_work_area_name.text = work_area_name
      Global.current_work_area_name = work_area_name
      Global.header_work_area_type.text = str(type(Global.work_area[Global.current_work_area_name]["form"])).split(".")[2][:-2]
      Global.header_work_area_type.enabled = False
      #print(Global.header_work_area_type.text)
      #Global.action_form_type = Global.header_work_area_type.text.split(".")[2][:-2]
      Global.action_form_type = Global.header_work_area_type.text
      #
      # Only show page controls for List Table action
      if Global.work_area[Global.current_work_area_name]["action"].split(" ")[0] in ["View", "Edit", "Insert", "Add", "Import"] or Global.work_area[Global.current_work_area_name]["action"] == "List Anvilusers":
        self.mb_middle.visible = False
        self.mb_left.visible = False
      elif Global.work_area[Global.current_work_area_name]["action"].split(" ")[0] in ["List"]:
        self.mb_middle.visible = True
        self.mb_left.visible = True

      self.select_all.indeterminate = False
      self.select_all.checked = False

      # Set selected buttons on Header for work area type
      Global.action_form_type = Global.header_work_area_type.text
      #print(Global.action_form_type)
      if Global.action_form_type in Global.action_forms_with_refresh:
        # make Refresh button visible if action_form_type has refresh function (i.e. in list Global.action_forms_with_refresh) 
        #Global.header_refresh_button.visible = True
        self.refresh.visible = True
        #print("set refresh button")
      else:
        #Global.header_refresh_button.visible = False
        self.refresh.visible = False

      if Global.action_form_type in Global.action_forms_with_print:
        # make print button visible if action_form_type has print function (i.e. in list Global.action_forms_with_print) 
        #Global.header_print_button.visible = True
        self.print.visible = True
      else:
        #Global.header_print_button.visible = False   
        self.print.visible = False
      if Global.action_form_type in Global.action_forms_with_download:
        # Make download button visible for Global.action_form_type
        #Global.header_download_button.visible = True
        self.download_csv.visible = True
      else:
        #Global.header_download_button.visible = False
        self.download_csv.visible = False
      if Global.action_form_type in Global.action_forms_with_filter and Global.work_area[work_area_name]["data_list"]:
        # Make filter button visible for Global.action_form_type if data_list is not empty
        #Global.header_filter_button.visible = True
        self.filter_cols.visible = True
      else:
        #Global.header_filter_button.visible = False
        self.filter_cols.visible = False

      # reset action dropdown list
      #self.action_list.selected_value = None
    else:
      n = Notification("This action has not yet been implemented.")
      n.show()
    pass
  
  def login_button_click(self, **event_args):
    """" This Function is called when the users logs in """
    """This method is called when the button is clicked"""
    #print("Login button clicked")
    user = anvil.users.login_with_form(allow_cancel=True,remember_by_default=False,show_signup_option=False)
    # check if user is logged in as newly registered account needs explicit enabling by administrator 

    if user is not None:
      # make welcome block of Main form invisible
      self.welcome_page.visible = False
      
      # when user is logged in, enable Action menu, username field and logout button, and disable content panel (welcome message)
      # also set username  to user email address
      Global.username = user["email"]
      Global.name = user["firstname"] + " " + user["lastname"]
      message = Global.help_introduction.replace("<user>",Global.name)
      rt = RichText(content=message,format="restricted_html")
      Global.help_page_form.help_page_text.add_component(rt)
      
      self.username_dropdown.placeholder = Global.username
      self.username_dropdown.items = ["Logout"]

      # notify server side of login
      Global.ip_address = anvil.server.call("user_authentication")
      
      # if user has system admin role, add system admin actions list and set it visible
      user = anvil.users.get_user()
      Global.system_user_role = user["systemrole"]
      self.user_role.text = Global.system_user_role

      if Global.system_user_role in ["System Administrator"]:
        self.menu_middle.visible = True
        self.mm_right.visible = True
        self.mm_left.visible = True
        self.mm_middle.visible = False
        self.admin_dropdown.visible = True
        self.menu_block.visible = True
        #self.menu_block.visible = False
        self.admin_dropdown.items = Global.sys_admin_action_dropdown
      
      # make menu bar variable visible
      self.menu_block.visible = True
      self.menu_top.visible = True
      self.title_panel.visible = True

      Global.site_options = FunctionsB.set_select_site_dropdown_options()      
      self.select_site_dropdown.items = Global.site_options.keys()
      Global.select_site_dropdown = self.select_site_dropdown
      
      # create a introduction message and add it to the introduction_message of the introduction_message block and make it visible
      Global.help_page.visible = True
      Global.site_id = "not_selected"
    pass

  def register_button_click(self, **event_args):
    """ This Function is called when a user wants to register himself"""
    """This method is called when the button is clicked"""
    user = anvil.users.signup_with_form(allow_cancel=True)
    if user is not None:
      print(str(user["email"]))
    
      # notify user that the Project Leader will have to check and enable the user account
      alert("Thank you for registering. Your account registration request will need to be verified. You will be notified as soon as this has been completed.")
      msg = ("Hi,\n\nUser %s has requested an account for the system %s.\n"
           "Please check the new user account, complete the registration and enable the account.\n"
           % (user["email"],Global.organisation ))
      print(msg)
      anvil.server.call("send_email","New user registration",msg,"tony.bakker@berksarch.co.uk")
      # go back to login screen
      self.logout_click()
    else:
      alert("Registration cancelled")
      
    #if user is not None:
    #  # when user is logged in enable Action menu, username field and logout button, and disable content panel (welcome message)
    #  # also set username  to user email address
    #  Global.username = user["email"]
    #  self.username_dropdown.placeholder = Global.username
    #  #self.action_list.visible = True
    #  self.menu_top.visible = True
    #  self.welcome_page.visible = False
    pass

  def select_site_dropdown_change(self, **event_args):
    """ This Function is called when the users selects a site """
    """This method is called when an item is selected"""
    # print("select_site_dropdown selected")
    if self.select_site_dropdown.selected_value is not None:
      # clear help_page_text 
      #Global.help_page.help_page_text.visible = True
      #Global.help_page.help_page_text.clear()
      Global.help_page.visible = False
      
      Global.site_name = self.select_site_dropdown.selected_value
      Global.site_id = Global.site_options[self.select_site_dropdown.selected_value]
      Global.selected_site = ": " + Global.site_name
      #Global.title_label.text = Global.title + Global.status + Global.selected_site
      #Global.title_label.text = Global.title
      #Global.header_site_name.text = Global.site_name
      db_summary = anvil.server.call("db_get_summary",Global.site_id)
      self.site_summary.visible = True
      self.site_summary.items = db_summary
      
      #
      self.menu_middle.visible = True
      self.mm_left.visible = True
      self.mm_middle.visible = True
      self.mm_right.visible = True
      Global.help_page.visible = True

      #delete all work_areas and all work_area names/buttons
      temp_work_area_name_list = list(Global.work_area.keys())
      for work_area_name in temp_work_area_name_list:
        Function.delete_workspace(work_area_name)
      self.menu_bottom.visible = False
      self.site_summary.visible = False
      Global.action_seq_no = {}
      Global.work_area = {}
      # check user authorisation role for the selected site
      Global.site_user_role = anvil.server.call("user_authorisation",Global.site_options[self.select_site_dropdown.selected_value],Global.username)
      if Global.site_user_role != "unknown" or Global.system_user_role == "System Administrator":
        # user found with a role for the selected site
        Global.help_page.visible = False
        self.site_summary.visible = True

        # Update role text if system_role is not System Administrator
        if Global.system_user_role == "Site User":
          self.user_role.text = "Site " + Global.site_user_role

        if Global.site_user_role == "Manager" or Global.system_user_role == "System Administrator" :
          # add site manager admin actions to admin dropdown
          options = Global.sys_admin_action_dropdown + Global.site_admin_action_dropdown
          self.admin_dropdown.items = options
          self.admin_dropdown.visible = True
        
        Global.site_name = self.select_site_dropdown.selected_value
        Global.site_id = Global.site_options[self.select_site_dropdown.selected_value]
        Global.selected_site = ": " + Global.site_name
        #Global.title_label.text = Global.title + Global.status + Global.selected_site
        #Global.title_label.text = Global.title
        #Global.header_site_name.text = Global.site_name
        db_summary = anvil.server.call("db_get_summary",Global.site_id)
        self.site_summary.visible = True
        self.site_summary.items = db_summary
  
        #
        self.menu_middle.visible = True
        self.mm_left.visible = True
        self.mm_middle.visible = True
        self.mm_right.visible = True
        if Global.site_user_role in ["Manager"] or Global.system_user_role == "System Administrator":
          self.list_dropdown.visible = True
          self.view_row.visible = True        
          self.edit_row.visible = True
          self.insert_dropdown.visible = True     
          self.delete_row.visible = True
          self.import_dropdown.visible = True
        elif Global.site_user_role in ["Editor"]:
          self.list_dropdown.visible = True
          self.view_row.visible = True        
          self.edit_row.visible = True
          self.insert_dropdown.visible = True     
          self.delete_row.visible = False
          self.import_dropdown.visible = False
        elif Global.site_user_role in ["Viewer"]:
          self.list_dropdown.visible = True
          self.view_row.visible = True
          self.insert_dropdown.visible = False
          self.import_dropdown.visible = False
          self.edit_row.visible = False
          self.delete_row.visible = False
        else:
          # unknown role
          msg = "Unkown User Role identified: " + str(Global.site_user_role)
          n = Notification(msg)
          n.show()
          # disable able all action buttons
          self.admin_dropdown.visible = False
          self.list_dropdown.visible = False
          self.view_row.visible = False
          self.insert_dropdown.visible = False
          self.import_dropdown.visible = False
          self.edit_row.visible = False
          self.delete_row.visible = False
      else:
        msg = "Not found a role for you in site " + self.select_site_dropdown.selected_value + ". Please contact the Project Manager."
        Global.site_name = self.select_site_dropdown.selected_value
        Global.site_id = Global.site_options[self.select_site_dropdown.selected_value]
        Global.selected_site = ": " + Global.site_name
        #Global.site_name = ""
        #Global.site_id = ""
        #Global.selected_site = ""
        #self.select_site_dropdown.selected_value = None
        n = Notification(msg)
        n.show()
    pass

  # Funtions for the menu options (Menu_middle) after the user selected a site
  def admin_dropdown_change(self, **event_args):
    """ This Function is called when the users has selected an action form the Admin dropdown menu """
    """This method is called when an item from the dropdown menu is selected"""
    # Action has been selected, but only take action if action in not a separator
    # save a link to the Main form in a Global variable 
    #Global.main_form = get_open_form()
    Global.help_page.visible = False

    Global.action = self.admin_dropdown.selected_value

    if Global.action not in Global.action_list_not_implemented:
      self.create_new_work_area(Global.action)
    else:
      if Global.action != Global.separator:
        alert("Action not yet implemented.")
        
    # clear selected_value
    self.admin_dropdown.selected_value = None
    pass

  def insert_dropdown_change(self, **event_args):
    """ This Function is called when the users selects an option form the Insert dropdown"""
    """This method is called when an item is selected"""
    #Global.main_form = get_open_form()
    # make action to be "Insert ..." 
    Global.action = "Insert " + str(self.insert_dropdown.selected_value).capitalize()
    #print("Insert action - ",Global.action)
    if Global.action not in Global.action_list_not_implemented:
      # Action has been selected, create button in work area list, and make this work area in focus (highlight button)
      # for any action that has a Form defined create a new work_area
      if Global.site_id is None and Global.action not in (Global.sys_admin_action_dropdown) and Global.action not in (Global.site_admin_action_dropdown) :
        # if site is not yet selected alert user
        alert(
          content="Site has not been selected. Please select a site.",
          title="Site selection warning",
          large=True,
          buttons=[("Ok", True)],
        )
      else:
        self.create_new_work_area(Global.action)
    else:
      if Global.action != Global.separator:
        alert("Action not yet implemented.")

    # clear selected_value
    self.insert_dropdown.selected_value = None
    pass

  def list_dropdown_change(self, **event_args):
    """ This Function is called when the users selects an option form the List dropdown"""
    """This method is called when an item is selected"""
    # clear selected_value
    #Global.main_form = get_open_form()
    # make action to be "List ..."
    Global.action = "List " + str(self.list_dropdown.selected_value).capitalize()
    
    if Global.action not in Global.action_list_not_implemented:
      # Action has been selected, create button in work area list, and make this work area in focus (highlight button)
      # for any action that has a Form defined create a new work_area
      if Global.site_id is None and Global.action not in (Global.sys_admin_action_dropdown) and Global.action not in (Global.site_admin_action_dropdown) :
        # if site is not yet selected alert user
        alert(
          content="Site has not been selected. Please select a site.",
          title="Site selection warning",
          large=True,
          buttons=[("Ok", True)],
        )
      else:
        self.create_new_work_area(Global.action)
    else:
      if Global.action != Global.separator:
        alert("Action not yet implemented.")
    
    self.list_dropdown.selected_value = None
    pass

  def import_dropdown_change(self, **event_args):
    """This method is called when an item is selected"""
    """ This Function is called when the users selects an option form the Import dropdown"""
    #print("Import dropdown")
    #Global.main_form = get_open_form()
    # set action
    Global.action = "Import " + str(self.import_dropdown.selected_value).capitalize()
    #print("Import action - ",Global.action)
    if Global.action not in Global.action_list_not_implemented:
      # Action has been selected, create button in work area list, and make this work area in focus (highlight button)
      # for any action that has a Form defined create a new work_area
      if Global.site_id is None and Global.action not in (Global.sys_admin_action_dropdown) and Global.action not in (Global.site_admin_action_dropdown)  :
        # if site is not yet selected alert user
        alert(
          content="Site has not been selected. Please select a site.",
          title="Site selection warning",
          large=True,
          buttons=[("Ok", True)],
        )
      else:
        #print("Import action: ",Global.action)
        self.create_new_work_area(Global.action)
    else:
      if Global.action != Global.separator:
        alert("Action not yet implemented.")

    # clear selected_value

    self.import_dropdown.selected_value = None
    pass
    
  def help_dropdown_change(self, **event_args):
    """ This Function is called when the users selects an option form the Help dropdown"""
    """This method is called when an item is selected"""
    #Global.main_form = get_open_form()
    Global.action = self.help_dropdown.selected_value
    #print(Global.action)
    if Global.action == "Anchurus Website":
      anvil.js.window.open("https://anchurus.co.uk", '_blank')
    self.help_dropdown.selected_value = None
    pass

  def site_summary_change(self, **event_args):
    """ This Function is called when the users selects an option form the Site Summary dropdown"""
    """This method is called when an item is selected"""
    # here we do not do anything except set the selected value of th dropdown to None
    self.site_summary.selected_value = None
    pass


  # Functions on the header for the work area
  def selection_change(self, **event_args):
    #
    print("selection_change in Main")
    rows = [row for row in Global.work_area[Global.current_work_area_name]["self"].repeating_panel_1.get_components()]
    any_checked = any(row.btn_select.checked for row in rows)
    all_checked = all(row.btn_select.checked for row in rows)
    #
    #self.select_all.checked = any_checked
    #self.select_all.indeterminate = not all_checked and any_checked
    ###Global.work_area[Global.current_work_area_name]["self"].select_all.checked = any_checked
    ###Global.work_area[Global.current_work_area_name]["self"].select_all.indeterminate = not all_checked and any_checked
    Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = any_checked
    #
    pass
  
  def select_all_change(self, **event_args):
    """This method is called when this checkbox is checked or unchecked"""
    checked = self.select_all.checked
    indetermined = self.select_all.indeterminate
    #print("Select_all button clicked: ",Global.current_work_area_name, " checked: ",checked, " indeterminate: ",indetermined)
    #
    if self.select_all.indeterminate:
      # if indeterminate is True, force check to False
      checked = False
    #for row in self.repeating_panel_1.get_components(): 
    for row in Global.work_area[Global.current_work_area_name]["self"].repeating_panel_1.get_components():
      prev_status_btn_select = row.btn_select.checked
      row.btn_select.checked = checked
      #
      if checked:
        Global.work_area[Global.current_work_area_name]["selected_rows"].append(row.item)
        row.background = Global.selected_highlight_colour
      else:
        if prev_status_btn_select:
          Global.work_area[Global.current_work_area_name]["selected_rows"].remove(row.item)
          row.background = ""
    #
    if self.select_all.indeterminate:
      #print("if indeterminate was True, set indeterminate to False ")
      self.select_all.indeterminate = False
      self.select_all.checked = False
      ###Global.work_area[Global.current_work_area_name]["self"].select_all.indeterminate = False
    #
    if len(Global.work_area[Global.current_work_area_name]["selected_rows"]) == 0:
      #print("0 selected rows, clear menu")
      Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = False
      ###Global.work_area[Global.current_work_area_name]["self"].select_all.checked = False
      self.select_all.checked = False
    else:
      Global.work_area[Global.current_work_area_name]["menu_select_options"].visible = True

    ###Global.work_area[Global.current_work_area_name]["self"].select_all.checked = checked
    self.select_all.checked = checked
    pass
    
  def view_row_click(self, **event_args):
    """This method is called when the button is clicked"""
    #
    for row in Global.work_area[Global.current_work_area_name]["selected_rows"]:
      Global.table_items = row
      #print("View button for row: ",row)
      Global.action = "View " + Global.table_name.capitalize()
      if Global.main_form:  # Important to check if the form exists
        # Create new work_area "View Context" and set focus on this new work_area
        #print("From repatingPanel row calling create_new_work_area for:",Global.action)
        Global.main_form.create_new_work_area(Global.action)
      else:
        print("Main form not found!")
    pass

  def edit_row_click(self, **event_args):
    """This method is called when the button is clicked"""
    #
    for row in Global.work_area[Global.current_work_area_name]["selected_rows"]:
      Global.table_items = row
      Global.action = "Edit " + Global.table_name.capitalize()
      if Global.main_form:  # Important to check if the form exists
        # Create new work_area "View Context" and set focus on this new work_area 
        Global.main_form.create_new_work_area(Global.action)
      else:
        print("Main form not found!")
    pass

  def delete_row_click(self, **event_args):
    """This method is called when the button is clicked"""
    message = ""
    for row in Global.work_area[Global.current_work_area_name]["selected_rows"]:
      Global.table_items = row
      #print(row)
      Global.action = "Delete " + Global.table_name.capitalize()
      message = message + "\nYou have seleted to delete " + Global.table_name.capitalize() + "\n\n" + str(row)

    # ask confirmation to delete selected rows
    message = message + "\n\nDo you wish to continue?\n\nNote: This action is not yet implemented!"
    confirm(message)
    pass

  def first_page_click(self, **event_args):
    """This method is called when the button is clicked"""
    FunctionsB.clear_selection(Global.work_area[Global.current_work_area_name]["self"])
    Global.work_area[Global.current_work_area_name]["self"].table.set_page(0)
    FunctionsB.update_status_label(Global.work_area[Global.current_work_area_name]["self"])
    pass

  def prev_page_click(self, **event_args):
    """This method is called when the button is clicked"""
    FunctionsB.clear_selection(Global.work_area[Global.current_work_area_name]["self"])
    Global.work_area[Global.current_work_area_name]["self"].table.set_page(Global.work_area[Global.current_work_area_name]["self"].table.get_page() - 1)
    FunctionsB.update_status_label(Global.work_area[Global.current_work_area_name]["self"])
    pass

  def next_page_click(self, **event_args):
    """This method is called when the button is clicked"""
    FunctionsB.clear_selection(Global.work_area[Global.current_work_area_name]["self"])
    Global.work_area[Global.current_work_area_name]["self"].table.set_page(Global.work_area[Global.current_work_area_name]["self"].table.get_page() + 1)
    FunctionsB.update_status_label(Global.work_area[Global.current_work_area_name]["self"])
    pass

  def last_page_click(self, **event_args):
    """This method is called when the button is clicked"""
    FunctionsB.clear_selection(Global.work_area[Global.current_work_area_name]["self"])
    rows_per_page = int(Global.work_area[Global.current_work_area_name]["self"].table.rows_per_page)
    total_rows = len(Global.work_area[Global.current_work_area_name]["self"].repeating_panel_1.items)
    Global.work_area[Global.current_work_area_name]["self"].table.set_page(total_rows // rows_per_page)
    FunctionsB.update_status_label(Global.work_area[Global.current_work_area_name]["self"])
    pass

  def filter_cols_click(self, **event_args):
    """This method is called when the button is clicked"""
    """ Here we allow the user to filter columns to be viewed"""
    # extract table columns names
    if Global.work_area[Global.current_work_area_name]["data_list"]:
      # Get the keys (which are the column headings) from the first item
      column_headings = list(Global.work_area[Global.current_work_area_name]["data_list"][0].keys())

    # remove special columns
    column_headings.remove("select")
    column_headings.remove("SiteId")
    column_headings.remove("DBAcontrol")
    # sort column names
    column_headings.sort()
    # extract table columns names
    #print(Global.work_area[Global.current_work_area_name]["columns_show"])
    #print(Global.work_area[Global.current_work_area_name]["table"].columns)
    column_headings = []
    #print(Global.work_area[Global.current_work_area_name]["data_list"])
    if Global.work_area[Global.current_work_area_name]["data_list"]:
      # Get the keys (which are the column headings) from the first item
      column_headings = list(Global.work_area[Global.current_work_area_name]["data_list"][0].keys())
      # remove special columns
      column_headings.remove("select")
      column_headings.remove("SiteId")
      column_headings.remove("DBAcontrol")
      # sort column names
      column_headings.sort()

    # 1. Define the options you want to display
    option_id = 0
    options_data = []
    for column_name in column_headings:
      option_id = option_id + 1
      options_data.append({'text': column_name, 'id': option_id})

    # 2. Create an instance of your Dialog Form
    dialog = FilterList(options_list=options_data)

    # 3. Use alert() to show the form as a modal popup
    # The alert() function will return the 'value' passed when 'x-close-alert' is raised
    selected_list = alert(
      content=dialog, 
      title="",
      buttons=[] # Crucial: set buttons=[] to use your custom button for submission
    )
    if selected_list is not None:     # user has made a selection; if not, do nothing
      # 4. Process the result after the dialog is closed
      #
      # First unhide all columns
      # remove the columns out of the hidden columns list.
      for col in Global.work_area[Global.current_work_area_name]["hidden_columns"]:
        column = [c for c in Global.work_area[Global.current_work_area_name]["filter"] if c['title'] == col][0]
        # remove from list of hidden_columns
        Global.work_area[Global.current_work_area_name]["filter"].remove(column)
        # Add it to the Data Grid's column list
        Global.work_area[Global.current_work_area_name]["table"].columns.append(column)
      # make it 'live'
      Global.work_area[Global.current_work_area_name]["table"].columns = Global.work_area[Global.current_work_area_name]["table"].columns
      # set hidden_columns to empty list
      Global.work_area[Global.current_work_area_name]["hidden_columns"] = []

      #
      all_columns_titles = [col["title"] for col in Global.work_area[Global.current_work_area_name]["table"].columns if "title" in col]
      #remove columns with empty title
      cleaned_list = [item for item in all_columns_titles if item != ""]
      cleaned_list.sort()
      all_columns_titles = cleaned_list

      # create columns_to_hide (difference between all_columns and selected_columns)
      columns_to_hide = []
      selected_columns_titles = []
      if selected_list:
        selected_columns_titles = [col["text"] for col in selected_list if "text" in col]
        columns_to_hide = list(set(all_columns_titles).difference(selected_columns_titles))

      # add columns_to_hide to the work_area data structure as "filter"
      Global.work_area[Global.current_work_area_name]["hidden_columns"] = columns_to_hide
      for col in columns_to_hide:
        # add col to filter and remove from table
        column = [c for c in Global.work_area[Global.current_work_area_name]["table"].columns if c['title'] == col][0]
        Global.work_area[Global.current_work_area_name]["filter"].append(column)
        Global.work_area[Global.current_work_area_name]["table"].columns.remove(column)

      # make the filter 'live'
      Global.work_area[Global.current_work_area_name]["table"].columns = Global.work_area[Global.current_work_area_name]["table"].columns
    pass

  def download_csv_click(self, **event_args):
    """This method is called when the button is clicked"""
    # call server-side function create_csv to create a csv file and download this to user Download folder
    csv_file = anvil.server.call('create_csv',Global.work_area[Global.current_work_area_name]["data_list"])
    anvil.media.download(csv_file)
    pass

  def print_click(self, **event_args):
    """This method is called when the button is clicked"""
    form = str(type(Global.work_area[Global.current_work_area_name]["form"])).split(".")[2][:-2]
    #print("From new print_click, form to use and send to server function: ",form)
    # table names are all lowercase and singular, so create table name from action
    tmp_name = Global.work_area[Global.current_work_area_name]["action"].split(" ")[1]
    table_name = tmp_name.lower()

    # clear select column from data_list
    #i = 0
    #while i < len(Global.work_area[Global.current_work_area_name]["data_list"]):
    #  Global.work_area[Global.current_work_area_name]["data_list"][i].pop("select")
    #  i = i + 1

    # call the print_form at the server-side
    pdf_form = anvil.server.call('print_form',form,Global.site_id,table_name.strip(),
                                 Global.work_area[Global.current_work_area_name]["action"],
                                 Global.work_area[Global.current_work_area_name]["data_list"],
                                 Global.work_area[Global.current_work_area_name]["page_info"]
                                )
    anvil.media.download(pdf_form)
    pass

  def refresh_click(self, **event_args):
    """This method is called when the button is clicked"""
    #print("Refresh clicked: ",Global.current_work_area_name)
    #print(Global.work_area[Global.current_work_area_name])
    FunctionsB.refresh_click(Global.work_area[Global.current_work_area_name]["self"])
    pass

  def del_work_area_click(self, **event_args):
    """This method is called when the button is clicked"""
    #print("Deleting work space: ", Global.current_work_area_name)
    Function.delete_workspace(Global.current_work_area_name)
    pass

  def logout_click(self, **event_args):
    """This method is called when the button is clicked"""
    # logout user, hide action menu, username and logout button; also delete all workspaces
    anvil.server.call("user_logout_notification",Global.ip_address,Global.username)
    anvil.users.logout()

    # make help_page invisible
    Global.help_page.visible = False
    Global.help_page.help_page_text.clear()

    # Welcome_page will show the login page
    self.welcome_page.visible = True

    # make menu block and admin menu invisible
    self.menu_block.visible = True
    self.title_panel.visible = True
    self.menu_top.visible = False
    self.menu_middle.visible = False
    self.mm_left.visible = True
    self.mm_middle.visible = False
    self.mm_right.visible = False
    self.admin_dropdown.visible = False
    self.site_summary.visible = False
    self.menu_bottom.visible = False

    self.admin_dropdown.items = []

    self.username_dropdown.placeholder = Global.username
    self.username_dropdown.items = []
    Global.system_user_role = ""
    self.user_role.text = ""

    # To be done: save work areas in table for user for loading when login

    #delete all work_areas and all work_area names/buttons
    temp_work_area_name_list = list(Global.work_area.keys())
    for work_area_name in temp_work_area_name_list:
      Function.delete_workspace(work_area_name)

    # clear selected site
    self.select_site_dropdown.selected_value = None

    # clear work_area list and action_seq_no
    Global.work_area = {}
    Global.action_seq_no = {}

    #components = self.get_components()
    #print(f"{len(components)} components after deleting all workspaces")
    pass

  def username_dropdown_change(self, **event_args):
    """ This Function is called when the users has selected the logout option of the username dropdown """
    """This method is called when an item is selected"""
    # This dropdown change means that the user selected for a Logout
    # as the only selection available in the dropdown list is Logout
    # But we just check in case it is not ;)
    if self.username_dropdown.selected_value == "Logout":
      self.logout_click()

    pass
