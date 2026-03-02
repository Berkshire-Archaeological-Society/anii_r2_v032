import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users
# This is a module.
# You can define variables and functions here, and use them from any form. For example, in a top-level form:
#
#    from .. import Module1
#
#    Module1.say_hello()
#
# Global Variables
#
main_form = ""
separator = "------------------"
sys_admin_action_list = ["List Anvilusers","Edit AnvilUser","Insert Anviluser","Import Anvilusers",separator,"List Site","Edit Site","Add Site"]
site_admin_action_list = [separator,"List SiteUser","Edit SiteUsers","Add SiteUser","Import SiteUsers"]
admin_action_list_not_implemented = [separator]
user_action_list = ["Select Site",separator,
                    "List Contexts","Add Context","Bulk Upload Contexts",separator,
                    "List Finds", "Add Find","Bulk Upload Finds",separator,
                    "List Anomalies","Add Anomaly",separator,
                    "List Interpretations","Add Interpretation"
                   ]
# action_list_not_implemented should always contain the separator
action_list_not_implemented = [separator,"Bulk Upload Finds","Draw","List Areas","Add Area","Add Anomaly"]
# the list_action_list is a list of the tables in DB (not yet sites)
list_action_dropdown = ["Contexts","Finds","Anomolies","Interpretations"]
insert_action_dropdown = ["Context","Find","Anomoly","Interpretation"]
file_action_dropdown = ["Import",separator,"Save"]
view_action_dropdown = []
help_action_dropdown = ["Anchurus Website"]
sys_admin_action_dropdown = [("List Users","List Anvilusers"),("Insert User","Insert Anviluser"),("Import Users","Import Anvilusers"),separator,("List Sites","List Site"),("Insert Site","Add Site")]
site_admin_action_dropdown = [(separator,separator),("List Site Users","List sys_siteuserrole"),("Insert Site User","Add sys_siteuserrole"),("Import Site Users","Import sys_siteuserrole")]
#
import_action_dropdown = ["context","find"]
#
#
action_forms_with_refresh = ["TableList","RowForm","ListAnvilUsers","ListSites","ListContexts","ListFinds","ListAreas","BulkUpload","Add Area","List Areas"]
#action_forms_with_print = ["ListUsers","ListSites","ListContexts","ListFinds","ListAreas","List Areas","View Context","View Find","View Area"]
#action_forms_with_print = ["ListContexts","ListFinds","TableList","RowForm"]
action_forms_with_print = []
action_forms_with_download = ["ListContexts","ListFinds","TableList"]
action_forms_with_filter = ["ListContexts","ListFinds","TableList"]
#
action_seq_no = {}
csv_file = None
current_work_area = {}
current_work_area_name = ""
current_work_area_type = ""
# variables for work area header
header = {}
header_work_area_name = {}
header_refresh_button = {}
header_print_button = {}
header_download_button = {}
header_filter_button = {}
header_work_area_type= {}
header_site_name = {}
header_site_summary_information = {}
# variables for Global Header dropdown lists
gh_file_list = {}
gh_view_list = {}
gh_help_list = {}
gh_list_list = {}
gh_insert_list = {}
gh_admin_list = {}
#
work_area = {}
# variable for work area header menu options 
wa_header_menu_bottom = {}
wa_header_mb_left = {}
wa_header_mb_middle = {}
wa_header_mb_right = {}
#
selected_row = []
selected_highlight_colour = "#66FFFF"
#
menu_select_options = ""
Quill_toolbarOptions = [
['bold', 'italic', 'underline', 'strike'],        # toggled buttons
['link'],
[{ 'header': 1 }, { 'header': 2 }],               # custom button values
[{ 'list': 'ordered'}, { 'list': 'bullet' }, { 'list': 'check' }],
[{ 'script': 'sub'}, { 'script': 'super' }],      # superscript/subscript
[{ 'indent': '-1'}, { 'indent': '+1' }],          # outdent/indent
[{ 'direction': 'rtl' }],                         # text direction
[{ 'size': ['small', 'normal', 'large', 'huge'] }],  # custom dropdown
[{ 'header': [1, 2, 3, 4, 5, 6] }],
[{ 'color': [] }, { 'background': [] }],          # dropdown with defaults from theme
[{ 'font': [] }],
[{ 'align': [] }],
['clean']                                         # remove formatting button
]
#
button_normal_background_clour = "#DCE5DD"
button_highlight_background_clour = "#CBEAD6"
#
action = ""
action_form_type = ""
admin_action = ""
admin_domain = ""
admin_user = ""
admin_user_initials = ""
area_items = {}
area_id = None
area_options = {}
dummy_btn1 = {}
dummy_btn2 = {}
context_id = None
context_items = {}
context_options = {}
context_types = ["Deposit","Cut","Structure"]
copyright = ""
DBAcontrol = ""
field_description_changed = False
file = []
find_id = None
file_list = []
find_items = {}
find_options = {}
find_types = {"Bulk Find","Small Find","Sample","FindGroup"}
google_link = ""
context_help_information = """
Deposit description:
1. Colour 2. Consistency 3. Texture 4. lnclusions (<50%) 5. Thickness and extent, 5. Other comments. 7. Method and conditions
Cut description:
1. Shape in plan (sketch overleaf) 2. Corners 3. Dimensions/depth 4. Break of slope -top 5. Sides, 6. Break of slope -
base 7. Base 8. Orientation 9. Shape of profile (sketch overleaf) 10. Fill Nos 11. Other comments
Masonry description:
1. Materials 2. Size of materials (brick; BLT in mm) 3. Finish of stones,4. Coursing/bond 5. Form 6. Direction of
face(s) 7. Bonding material (brick height of 4 courses and 4 bed joints in mm 8 . Dimensions of masonry as found 9. Other comments 
"""
image_type = ""
ip_address = ""
print_action = False
selected_material_types = {}
material_types = ["CBM Tile","CBM Brick","CBM Drain Pipe","CBM Mortar",
                  "Stone","Roofing Slate","Flint","Worked Flint","Pottery",
                  "Clay Pipe","Metalwork","Nails","Iron Slag","Glass","Animal Bone",
                  "Oyster Shells","Wood","Charcoal"]
login_options = {"Sign in", "Sign out"}
#
organisation = ""
query_view = False
view_queries = ["sys_siteuserrole"]
#
# The following variable rows_per_page has to be set to 0, to make sure the print function prints the whole table
# During startup of the client (i.e. browser URL click of website) this value can be overwritten by a value for this
# defined in the server side configuration file
# Note that the 'page' is this context is a webpage and not a physical printing page
rows_per_page = 0 
#
selected_site = ""
sign_in_out_button_text = "Sign in"
site_id = None
site_name = ""
site_options = {}
site_items = {}
select_site_dropdown = {}
header_site_summary_information = {}
system_name = ""
SurveyMethod_options = {"BNG","Aligned to BNG north","Not aligned to BNG north"}
system = "Anchurus-II R2"
status = ""
#
table_name = ""
table_items = {}
table_colwidth_60 = ["FillOf","Year","Count","Weight"]
table_colwidth_70 = []
table_colwidth_80 = ["ContextId","AreaId","YearStart","YearEnd","Workflow","BoxId","FromSample","FindType","Enabled"]
table_colwidth_90 = ["FindId"]
table_colwidth_100 = ["FindGroupId","ContextYear","ContextType","PackageType","SmallFindId","FromSample","RecordStatus","SiteId","Role"]
table_colwidth_120 = ["SiteId"]
table_colwidth_140 = ["RegistrationDate"]
table_colwidth_200 = ["Address"]
table_colwidth_250 = []
table_colwidth_300 = ["email","Email","Description1","Description2"]
table_colwidth_default = 110
#
title = system + "\n\n" + organisation
sign_in_out_button_text = "Sign in"
username = ""
password = ""
name = ""
user_firstname = ""
user_lastname = ""
user_initials = ""
system_user_role = ""
site_user_role = ""
user_status = ""
site_user_role_options = {"Viewer","Editor","Manager","Administrator"}
system_user_role_options = {"Site User","System Administrator"}
user_status_options = {"True", "False"}
user_items = {}
config_version = ""
#
about_us_text = """
<h3>Welcome to the Anchurus-II R2 Web Application</h3>

<p>
This system allows for the digital recording of archaeological excavations.
The software has been developed by Archaeology IT Solutions, an independent 'not-for-profit' or 'nonprofit' organisation developing software solutions for the archaeological community.
It is developed using the <a href="https://anvil.works/" target="_blank>Anvil Framework</a> and is using the open source Anvil App Server which allows to run the application on your
own dedicated server. It uses its own MariaDB database to store the excavation details.  
This software is released under Creative Commons license: 
<a href="https://creativecommons.org/licenses/by-nc-sa/4.0/" target=_blank>Attributions-NonCommercial-ShareAlike 4.0 International (CC BY-NC-AS 4.0) license</a>.
</p>

<p>
For more information please contact ...</p>
"""
help_page_form = ""
help_page = {}
help_introduction = """
<h3>Introduction</h3>
<p>
Welcome <user>.
</p>
<p>You have successfully logged into the Anchurus-II Web service Application.
</p>
<p>
Please select a site. If a site you require access to, is not in the 'Select Site' list, please contact the Project Manager for that site to provide you with access.
<br>Once selected you can use the menu items to select your actions.</p>
<p>
<b>Note:</b> When changing/selecting a new site, all current workspaces wil be deleted.</p>
<h3> </h3>
<p>
For more information on recording Archaeological excavations please go to the
<a href="https://anchurus.co.uk/" target=_blank>Anchurus Website</a></p>
"""
