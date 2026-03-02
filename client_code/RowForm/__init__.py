from ._anvil_designer import RowFormTemplate
from anvil import *
import anvil.server
import re
import datetime
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil_extras.Quill import Quill

from ..Validation import Validator
from .. import FunctionsB
from .. import Global

class RowForm(RowFormTemplate):
  def input_change(self, **event_args):
    """This method is called when the text in this text box is edited"""
    column = event_args["sender"].placeholder
    #print(str(type(event_args["sender"])))
    if str(type(event_args["sender"])) == "<class 'anvil_extras.Quill.Quill'>":
      self.form_fields[column]["header"].text = column + " (" + str(len(self.form_fields[column]["field"].get_html())) + "/" + str(self.form_fields[column]["length"]) + "):"
    else:
      if str(type(event_args["sender"])) != "<class 'anvil.DatePicker'>":
        self.form_fields[column]["header"].text = column + " (" + str(len(self.form_fields[column]["field"].text)) + "/" + str(self.form_fields[column]["length"]) + "):"
  pass
  
  def __init__(self, site_id, table_name, data_list, action, page_info, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    self.site_id = site_id
    # Global.site_id is only None when form called from server side (e.g. printing form)
    if Global.site_id is None:
      # initialise some Globals variables for when the function is called from the server side
      Global.site_id = site_id
      Global.action = "View " + table_name.capitalize()
      Global.current_work_area_name = Global.action
      Global.table_name = table_name
      Global.work_area = {}
      Global.work_area[Global.current_work_area_name] = {}
      #print(data_list)
      Global.work_area[Global.current_work_area_name]["data_list"] = data_list
    else:
      # set table_name to one of "context", "find", from the action Global variable
      #print(Global.table_name)
      #print(Global.work_area[Global.current_work_area_name]["action"])
      Global.table_name = Global.work_area[Global.current_work_area_name]["action"].split(" ")[1].lower()
      # Global.action.split(" ")[1].rstrip("s").lower()
      
    action = Global.action.split(" ")[0].lower()
    self.validator = Validator()
    # we need to find out which table we are dealing with
    self.title.text = "This form is to " + Global.action
    # get table information
    #print("In RowForm: ",Global.table_name)
    table_info = anvil.server.call("describe_table",Global.table_name)
    # And then we need to create all the fields based on table information 
    # loop over table columns
    self.field_details = {}
    self.form_fields = {}
    for item in table_info:
      column_name = item["Field"]
      column_type = item["Type"]
      # types can be varchar(length),int(length),text,float,double,date
      # type text can be 65535 char so need to be a TextArea, other can be a TextBox
      # create the label and the input field
      if column_type == "text":
        #create TextArea input field for text type
        #input = TextArea(tag=column_name)
        input = Quill(placeholder=column_name,toolbar=Global.Quill_toolbarOptions)
        max_length = 65535
        input.add_event_handler('text_change',self.input_change)
      elif column_type == "date":
        # by default create TextBox fields
        input = DatePicker(placeholder=column_name,format="%Y-%m-%d")
        #input = TextBox(placeholder=column_name)
        # date type is 10 long
        max_length = 10
        # add event handler for when input field is changed to update the character count
        input.add_event_handler('change',self.input_change)
      else:
        # by default create TextBox fields
        input = TextBox(placeholder=column_name)
        # extract length from type
        match = re.search(r'\d+',column_type)
        max_length = int(match.group())
        if column_type.find("decimal") != -1 or column_type.find("float") != -1 or column_type.find("double") != -1:
          # for these data types add 1 to max _length as length does not take into account the decimal point
          # (nor negative symbol but that is not applicable for us)
          max_length = max_length + 1
          
        # add event handler for when input field is changed to update the character counth
        input.add_event_handler('change',self.input_change)
        
      # set specific validators for the various fields
      # if column is Primary Key or a known special column then make it un-editable
      if (action == "view") or (action in ["edit"] and item["Key"] == "PRI") or column_name in ["SiteId","DBAcontrol","RegistrationDate"]:
        input.enabled = False
        input.foreground = "#ffffff"
        input.background = "#000000"
      #
      if column_name in ["YearEnd","YearStart"]:
        self.validator.regex(component=input,
                           events=['lost_focus', 'change'],
                           pattern="^-?\d{1,4}(?:BC|AD)?$",
                           required=False,
                           message="Please enter a valid year YYYY BC|AD (or -YYYY for BC year)")
      elif column_name in ["Year"]:   
        self.validator.regex(component=input,
                                       events=['lost_focus', 'change'],
                                       pattern="^\d{4}$",
                                       required=True,
                                       message="Please enter a valid year in YYYY format")
      elif column_name in ["Email"]:
        self.validator.regex(component=input,
                             events=['lost_focus', 'change'],
                             pattern="^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                             required=True,
                             message="Please enter a correct email address")
      elif column_type.find("int") != -1:
        self.validator.integer(component=input,
                               events=['lost_focus', 'change'])
        #self.validator.regex(component=input,
        #                     events=['lost_focus', 'change'],
        #                     pattern="^\d*$",
        #                    required=True,
        #                     message="Please enter a valid whole number")
      elif column_type.find("decimal") != -1 or column_type.find("float") != -1 or column_type.find("double") != -1:
        dec_type = re.findall(r'\d+',column_type)
        # regex ^\d{0,x}\.?\d{1,y}
        pattern_string = "^\d{0," + str(int(dec_type[0])-int(dec_type[1])) + "}\.?\d{1," + str(int(dec_type[1])) + "}$"
        print(dec_type[0],dec_type[1])
        msg = "Please enter a valid number in the form " + "x" * (int(dec_type[0]) - int(dec_type[1])) + "." + "x" * int(dec_type[1])
        self.validator.regex(component=input,
                             events=['lost_focus', 'change'],
                             pattern=pattern_string,
                             required=True,
                             message=msg)
      # add more validations for fields if required
      elif  column_name in ["RecordStatus"]:
        self.validator.regex(component=input,
                             events=['lost_focus', 'change'],
                             pattern="(?i)^(registered|planned|dated|grouped|report)$",
                             required=True,
                             message="This defines the state of this context record. Pick one of Registered, Planned, Dated, Grouped, Report.")      
      elif  column_name in ["ContextType"]:
        self.validator.regex(component=input,
                             events=['lost_focus', 'change'],
                             pattern="(?i)^(deposit|fill|cut|structure|feature)$",
                             required=True,
                             message="Pick one of Deposit, Fill, Cut, Strucure or Feature.")      

      # end of validation 
      
      # spedial case when Field is RegistrationDate: Pre-fill is for Insert and also block edit contents
      cur_len = 0
      #print(column_name)
      if action in ["insert","add"] and column_name == "RegistrationDate":
        # force RegistrationDate
        input.text = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        input.enabled = False
        input.foreground = "#ffffff"
        input.background = "#000000"

      # if action is View or Edit then fill all fields
      if action in ["edit","update","view"]:
        if str(type(input)) == "<class 'anvil_extras.Quill.Quill'>":
          html_text = Global.work_area[Global.current_work_area_name]["data_list"][0][column_name]
          #if html_text == "None":
          #  html_text = ""
          delta = input.clipboard.convert(html_text)
          #print(delta)
          input.setContents(delta, 'silent')
          cur_len = 0
          if html_text is not None:
            cur_len = len(html_text)
          if action == "view":
            input.enable(False)
            input.background = "#052014CC"
        elif str(type(input)) == "<class 'anvil.DatePicker'>":
          input.date = Global.work_area[Global.current_work_area_name]["data_list"][0][column_name]
        else:
          input.text = Global.work_area[Global.current_work_area_name]["data_list"][0][column_name]
          if input.text == "None":
            input.text = ""
            cur_len = 0
          if input.text is not None:
            cur_len = len(input.text)
      if column_name == "SiteId" and action in ["edit","insert","add"]: # pre-set SiteId when
        #print(column_name,action)
        Global.work_area[Global.current_work_area_name]["data_list"][0][column_name] = Global.site_id
        input.text = Global.work_area[Global.current_work_area_name]["data_list"][0][column_name]
        if input.text == "None":
          input.text = ""
          cur_len = 0
        if input.text is not None:
          cur_len = len(input.text)
        #print(Global.work_area[Global.current_work_area_name]["data_list"][0][column_name])

      # set default label text
      col = column_name + " (" + str(cur_len) + "/" + str(max_length) + ")" 
      lab = Label(text=col,font_size=14,tag=column_name)
      # add columns details to nested dictionary
      field_details = {"header": lab, "field": input, "length": max_length}
      self.form_fields[column_name] = field_details
      # add label and input field to column_panel
      if column_name != "DBAcontrol": # do not add an input field for DBAcontrol column
        self.column_panel_1.add_component(lab)
        self.column_panel_1.add_component(input)
    
    # Add a Submit button if Edit or Add action
    if action in ["edit","add","insert"]:     #"Edit Context","Edit Find","Add Context","Add Find"]:
      submit_btn = Button(text="Submit",role="outlined-button")
      submit_btn.add_event_handler("click",self.submit_btn_click)
      self.column_panel_1.add_component(submit_btn)

    # For this work_area form the page_info details are all set to 0; this is for when the server print function calls this form
    Global.work_area[Global.current_work_area_name]["page_info"] = {"page_num": 0, "rows_per_page": 0, "total_rows": 0}

  def submit_btn_click(self, **event_args):
    """This method is called when the button is clicked"""
    #print("Submit button clicked: ",Global.action)
    action = Global.action.split(" ")[0].lower()
    table_name = Global.action.split(" ")[1].lower()
    if self.validator.are_all_valid():
      row_list = {}
      for col in self.form_fields.items():
        if str(type(col[1]["field"])) == "<class 'anvil_extras.Quill.Quill'>":
          row_list[col[0]] = col[1]["field"].getText()
          #delta = col[1]["field"].getContents()
          #print("Quill Value is: ",row_list[col[0]])
          #row_list[col[0]] = col[1]["field"].clipboard.convert(html_text)
          #Global.work_area[Global.current_work_area_name]["data_list"][0][column_name]
          #delta = col[1]["field"].clipboard.convert(html_text)
          #col[1]["field"].setContents(delta, 'silent')
          #cur_len = 0
          #if html_text is not None:
            #cur_len = len(html_text)
        elif str(type(col[1]["field"])) == "<class 'anvil.DatePicker'>":
          row_list[col[0]] = col[1]["field"].date
        else:
          row_list[col[0]] = col[1]["field"].text
        # set empty fields to None
        if row_list[col[0]] in ["","\n"]:
          row_list[col[0]] = None
      #
      if action in ["add","insert"]:
        ret = anvil.server.call("row_add",table_name,row_list)
        # if success then goto list contexts
        if ret[:2] == "OK":
          msg = "Row has been successfully inserted to the database."
          # if a site has been added, update the site selection dropdown
          if table_name == "site":
            Global.site_options = FunctionsB.set_select_site_dropdown_options() 
            Global.select_site_dropdown.items = Global.site_options.keys()
        else:
          msg = "Row has not been inserted to the database, because of " + ret
      elif action in ["edit","update"]:
        ret = anvil.server.call("row_update",table_name,row_list)
        # if success then goto list contexts
        if ret[:2] == "OK":
          msg = "Row has been successfully updated in the database."
        else:
          msg = "Row has not been updated in the database, because of " + ret
      else:
        msg = "Unknown action: " + action
      alert(content=msg)
    else:
      alert("Please correct the field(s) with errors before submitting.")
    pass

  # a previous version of the submit function; to be check and moved relevant bits to current submit_btn_click function
  def submit_button_click(self, **evemt_args):
    if self.validator.are_all_valid():
      # All fields are filled in correct (I hope ;))
      # collect form details and then call anvil.server add_context
      Global.context_items["ContextId"] = self.ContextId.text
      Global.context_items["SiteId"] = self.SiteId.text
      Global.context_items["Name"] = self.Name.text
      Global.context_items["Year"] = self.Year.text
      #Global.context_items["AreaId"] = self.AreaId.selected_value
      Global.context_items["AreaId"] = self.AreaId.text
      Global.context_items["RecordStatus"] = self.RecordStatus.text
      Global.context_items["FillOf"] = self.FillOfFindId.text
      Global.context_items["ContextType"] = self.ContextType.selected_value
      Global.context_items["Description"] = self.Description.text
      Global.context_items["Interpretation"] = self.Interpretation.text
      Global.context_items["DatesAssignedBy"] = self.DatesAssignedBy.text
      Global.context_items["YearStart"] = self.YearStart.text
      Global.context_items["YearEnd"] = self.YearEnd.text
      #
      if (self.ContextType.selected_value) is not None:
        # call server for database update
        # set all empty fields to None (will be Null in DB)
        for x in Global.context_items:
          if Global.context_items[x] == "":
            Global.context_items[x] = None
        msg = "This message text should not be seen. Global.action = " + Global.action
        #print(Global.action)
        if Global.work_area[Global.current_work_area_name]["action"] == "Add Context":
          ret = anvil.server.call("context_add",Global.context_items)
          # if success then goto list contexts
          if ret[:2] == "OK":
            msg = "The context has been successfully inserted to the database."
          else:
            msg = "The context has not been inserted to the database, because of " + ret
        elif Global.work_area[Global.current_work_area_name]["action"] == "Edit Context":
          ret = anvil.server.call("context_update",Global.context_items)
          # if success then goto list contexts
          if ret[:2] == "OK":
            msg = "The context has been successfully updated in the database."
          else:
            msg = "The context has not been updated in the database, because of " + ret
        alert(content=msg)
      else:
        alert("Please select a value for Contect Type and/or Area ID.")
    else:
      alert("Please correct the field(s) with errors before submitting.")
    pass