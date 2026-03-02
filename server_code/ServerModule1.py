##!/usr/local/bin/python
##
# Anvil-Uplink server
# provides callable functions for Anvil Webapp
##
# import generic stuff and special installed modules
import os
import sys
import pymysql
import csv
import logging
import os
import gzip
import shutil
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
import uuid
import pandas as pd
import numpy as np
import configparser
import bcrypt

#import anvil modules
#from anvil.users import UserExistsError
import anvil.server
import anvil.users
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
import anvil.secrets
import anvil.media
import anvil.pdf
from anvil.pdf import PDFRenderer
#from anvil.pdf import PdfRenderer
from anvil.tables import app_tables

############# Defining all the Functions #############

# ---------------------------------------
# Generic functions (not client callable)
# ---------------------------------------

def hash_password(password, salt):
  """Hash the password using bcrypt in a way that is compatible with Python 2 and 3."""
  if not isinstance(password, bytes):
    password = password.encode()
  if not isinstance(salt, bytes):
    salt = salt.encode()

  result = bcrypt.hashpw(password, salt)

  if isinstance(result, bytes):
    return result.decode('utf-8')


def table_update(type,table):
  # 
  # this function will update rows of a table a table (pandas dataframe) into the database, containing one or more rows
  # type is the table name
  # (type is used to generate the type_id (capitalize, strip last char and add Id, e.g. type = Contexts, type_id will be ContextId))
  # table is a pandas dataframe 
  #
  conn.ping(reconnect=True)
  table.replace({np.nan: None},inplace=True)
  table.replace(r'^\s+$', None, regex=True,inplace=True) 

  # creating column list for insertion: column names in table must be equal to database table column names
  cols = "`,`".join([str(i) for i in table.columns.tolist()])
  table_info = describe_table(type)
  if type == "sys_siteuserrole": #special case for sys_siteuser table
    type_id = "Email" 
  else:
    type_id = type.capitalize() + "Id"
  cur = conn.cursor()
  message = ""
  msg = ""
  # 
  # change pandas dataframe to list of records (dictionaries) for processing
  records = table.to_dict('records')

  for row in records:
    new_values = ""
    where_clause = ""
    for col in table.columns.tolist(): 
      column_info = next((column for column in table_info if column['Field'] == col), None)
      if column_info["Key"] == "PRI":
        where_clause = where_clause + col + " = '" + str(row[col]) + "' AND "
      else:
        if str(row[col]) == "None":
          new_values = new_values + col + " = NULL,"
        else:
          new_values = new_values + col + " = '" + str(row[col]) + "',"

    strip_values = new_values.rstrip(",")
    strip_where = where_clause.rstrip(" AND ")
    sql_cmd = "UPDATE " + type.lower() + " SET " + strip_values + " WHERE " + strip_where
    try:
      ret = cur.execute(sql_cmd)
      conn.commit()
      msg = "OK. " + type + " " + row[type_id] + " successfully updated."
      logmsg("INFO",msg)
    except pymysql.Error as err:
      msg = format(err)
      msg = type + " " + row[type_id] + " update to database failed: " + msg
      logmsg("ERROR", msg)
    message = message + msg + "\n"

  return message

def table_insert(type,table):
  # 
  # this function will insert a table (pandas dataframe) into the database, containing one or more rows
  # type is the table name
  # type is used to generate the type_id (capitalize, strip last char and add Id, e.g. type = Contexts, type_id will be ContextId)
  # table is a pandas dataframe 
  #
  conn.ping(reconnect=True)
  table.replace({np.nan: None},inplace=True)
  table.replace(r'^\s+$', None, regex=True,inplace=True)

  if type == "sys_siteuserrole":
    # special case for sys_siteuser table
    # set type_id to Email and make Email Column values all lowercase
    type_id = "Email"
    table['Email'] = table['Email'].str.lower()
  elif type.rfind(database_connect_info["special_finds_table_prefix"],0,2) != -1:
    # Any table starting with special_finds_table_prefix (e.g BC) has type_id as FindId
    type_id = "FindId"
  else:
    # all other tables will have the type_id set to "<type>Id"
    type_id = type.capitalize() + "Id"

  cols = "`,`".join([str(i) for i in table.columns.tolist()])

  cur = conn.cursor()
  message = ""
  msg = ""
  # 
  # change pandas dataframe to list of records (dictionaries) for processing
  records = table.to_dict('records')

  for row in records:
    if type == "sys_siteuserrole":
      # special case for sys_siteuserrole table
      # check if Email is registered in Anvil users table
      anviluser = app_tables.users.get(email = row["Email"])
      if anviluser is None:
        msg = "ERROR. sys_siteuserrole insert failed: Email " + row["Email"] + " is not registered in Anvil users table."
        logmsg("ERROR", msg)
        message = message + msg + "\n"
        continue

    sql_cmd = "INSERT INTO " + type.lower() + " (`" + cols + "`) VALUES (" + "%s,"*(len(row)-1) + "%s)"

    try:
      ret = cur.execute(sql_cmd,list(row.values()))
      conn.commit()
      msg = "OK. " + type + " " + row[type_id] + " successfully inserted."
      logmsg("INFO",msg)
    except pymysql.Error as err:
      msg = format(err)
      msg = type + " " + row[type_id] + " insert to database failed: " + msg
      logmsg("ERROR", msg)
      msg = "ERROR. " + msg
    message = message + msg + "\n"

  return message

# ------------------------
# Anvil callable functions 
# ------------------------

@anvil.server.callable
def client_globals():
  # return client global variables values back to Client
  #print(client_info)
  return client_info

@anvil.server.callable
def user_authentication():
  # check database connection, and auto-reconnect if needed
  conn.ping(reconnect=True)
  #
  user = anvil.users.get_user()
  ip_address = str(anvil.server.context.client.ip)
  msg = "Login connection from " + ip_address + ", User " + str(user['email'])

  # Check MariaDB for user authorisation (i.e. which role has the person in accessing the DB)
  # This role will the set in the Anvil user table, which can then be checked in the client and server by a simple call to 
  # anvil.users.get_user(), although to always check this form the server (more secure and accurate)

  logmsg("INFO",msg)
  return ip_address

@anvil.server.callable
def user_authorisation(site_id,email):
  global Global_site_role
  # check database connection, and auto-reconnect if needed
  conn.ping(reconnect=True)
  #
  with conn.cursor() as cur:
    query = "SELECT Role FROM sys_siteuserrole WHERE SiteId = '" + str(site_id) + "' AND Email = '" + str(email) + "' AND Enabled = 'True'"
    logmsg("INFO",query)
    cur.execute(query)
    result = cur.fetchall()
    if cur.rowcount != 0:
      Global_site_role = result[0]["Role"]
      msg = "Found user " + str(email) + " in site " + str(site_id) + " with role as " + str(Global_site_role)
    else:
      msg = "No role found for user " + str(email) + " in site " + str(site_id)
      Global_site_role = "unknown"
    logmsg("INFO",msg)
  return Global_site_role

@anvil.server.callable
def user_logout_notification(ip_address,email):
  msg = "Logout notification from " + str(ip_address) + ", User " + str(email)
  logmsg("INFO",msg)
  return

@anvil.server.callable
def create_csv(data_list):
  # 1. Create Pandas DataFrame
  df = pd.DataFrame(data_list)

  # *************************************************
  # need to add code for converting Int datatypes to Int64 to avoid problems with None values in Int columns, 
  # which will be converted to NaN in pandas (all Int values will become Floats) and then to 'nan' string when converting to string for sending to client, 
  # which is not good for client side processing (need to be empty string instead) 
  # *************************************************
  # Automatically converts to the best possible types
  #logmsg("INFO",df.dtypes)
  df = df.convert_dtypes()
  #logmsg("INFO",df.dtypes)

  # convert pandas dataframe to string (cannot send all datatypes to client so best to make all of type string)
  # pdf_result = pdf_result.mask(pdf_result.astype(str).eq('None') & df.isna(), '')
  df = df.astype('str')

  # make all None values empty string (otherwise they will be sent to client as 'None' string, which is not good for client side processing)
  df.replace(to_replace='None', value='',inplace=True)
  df.replace(to_replace='<NA>', value='',inplace=True)

  # remove the select comlun
  df_clear = df.drop("select",axis='columns')

  # 2. Get the CSV content as a string
  # Use .encode('utf-8') to convert the string to bytes, which BlobMedia requires
  csv_bytes = df_clear.to_csv(index=False).encode('utf-8')

  # 3. Create the Anvil Media Object
  # - 'text/csv' is the MIME type for a CSV file.
  # - csv_bytes is the content.
  # - name is the suggested filename for the download.
  csv_file = anvil.BlobMedia(
    'text/csv', 
    csv_bytes, 
    name='Anchurus_list_form_export.csv') 
  return csv_file

@anvil.server.callable
def print_form(form,site_id,table_name,action,data_list,page_info):
  # 1. Call PdfRenderer
  # - set name of exported csv file
  # - set page orientation and size
  # ****** Add more variables for user to select (quality, scale, margins) as well as landscape and paper size)
  # ****** need to add the column filter (set in the client) to the table before printing
  # - user render_form method for requested from and site_id
  #print("In print form")
  #print(site_id, table_name, action)
  #print(data_list)
  #pdf_form = PdfRenderer(filename='Anchurus_list_form.pdf',landscape=True,page_size='A3').render_form(form,site_id,table_name,data_list,action,page_info)
  pdf_form = PDFRenderer(filename='Anchurus_list_form.pdf',landscape=True,page_size='A3').render_form(form,site_id,table_name,data_list,action,page_info)
  return pdf_form

@anvil.server.callable
def save_work_areas(work_areas_list,site_id):
  # 
  print(site_id)
  print(work_areas_list)
  msg = "OK"
  return msg

@anvil.server.callable
def send_email(title,msg,recipient):
  #
  anvil.email.send(
    to=recipient,
    from_address="mail-server@berksarch.co.uk",
    subject=title,
    text=msg
  )

  return 

# --------------------------------------------------
# <nam>_get functions (for listing, dropdowns, etc.)
# --------------------------------------------------

@anvil.server.callable
def db_get_summary(site_id):
  # check database connection, and auto-reconnect
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    query = "SELECT table_name,table_rows FROM information_schema.tables WHERE table_schema = '" + database_connect_info["db"] + "' AND table_type = 'BASE TABLE' ORDER BY table_name"
    cur.execute(query)
    result = cur.fetchall()
    # format result in list
    list = []
    for item in result:
      #print(item)
      if item["table_name"] not in ["dbdiary","site"] and item["table_name"].find("sys_") == -1:
        table_info = describe_table(item["table_name"])
        count = 0
        for column in table_info:
          if "SiteId" in column.values():
            query = "SELECT COUNT(*) FROM " + item["table_name"] + " WHERE SiteId = '" + site_id + "'"
            cur.execute(query)
            res2 = cur.fetchall()
            count = res2[0].get("COUNT(*)")
        list.append(item["table_name"] + " - " + str(count))
    msg = "DB summary requested."
    logmsg("INFO",msg)
  return list

@anvil.server.callable
def sites_get_summary(email):
  # check database connection, and auto-reconnect
  conn.ping(reconnect=True)
  anviluser = anvil.users.get_user(email)
  with conn.cursor() as cur:
    if anviluser["systemrole"] == "System Administrator":
      query = "SELECT SiteId,SiteName FROM site ORDER BY site.SiteId" 
    else:
      query = "SELECT site.SiteId,site.SiteName FROM site,sys_siteuserrole WHERE site.SiteId = sys_siteuserrole.SiteId AND sys_siteuserrole.Email = '" + email + "' AND sys_siteuserrole.Enabled = 'True' ORDER BY site.SiteId"
    cur.execute(query)
    result = cur.fetchall()
    msg = "Found " + str(len(result)) + " sites for user " + str(anviluser["email"])
    logmsg("INFO",msg)
  return result

@anvil.server.callable
def systems_get_summary():
  # retrieve the list of systems from the Anvil DB systems table and return to client
  systems_list = []
  for row in app_tables.systems.search():
    systems_list.append(row["systemname"])
  return systems_list

@anvil.server.callable
def sites_get():
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    query = "SELECT * FROM site ORDER BY SiteId"
    cur.execute(query)
    result = cur.fetchall()
    pdf_result = pd.DataFrame(result)   
    #logmsg("DEBUG",result)
    msg = query + ". Found " + str(len(result)) + " site rows."
    logmsg("INFO",msg)
    # convert pandas dataframe to sting (cannot send all datatypes to client so best to make all of type string)
    pdf_result_str = pdf_result.astype('str')
    # now dataframe into records
    pd_list = pdf_result_str.to_dict('records')
  return pd_list

@anvil.server.callable
def areas_get_summary(site_id):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    cur.execute("SELECT AreaId FROM area WHERE SiteId = %s ORDER BY AreaId",site_id)
    result = cur.fetchall()
    msg = "Found " + str(len(result)) + " Area rows."
    logmsg("INFO",msg)
  return result

@anvil.server.callable
def areas_get(site_id):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    cur.execute("SELECT * FROM area WHERE SiteId = %s ORDER BY AreaId",site_id)
    result = cur.fetchall()
    msg = "Found " + str(len(result)) +" Area rows."
    logmsg("INFO",msg)
  return result

@anvil.server.callable
def contexts_get_summary(site_id):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    cur.execute("SELECT ContextId FROM context WHERE SiteId = %s ORDER BY ContextId",site_id)
    result = cur.fetchall()
    msg = "Found " + str(len(result)) +" Context rows."
    logmsg("INFO",msg)
  return result

@anvil.server.callable
def describe_table(table_name):
  if table_name in ["anvilusers","anviluser"]:
    # Anvil users DB table
    result = app_tables.users.list_columns()
  else:
    # MariaDB table
    query = f"DESCRIBE `{table_name}`"
    conn.ping(reconnect=True)
    with conn.cursor() as cur:
      cur.execute(query)
      result = cur.fetchall()
      #result.pop() # exclude last column, which should be DBAcontrol
      #msg = "Found " + str(len(result)) +" Area rows."
      #logmsg("INFO",msg)
  return result

@anvil.server.callable   
def table_get(site_id,table_name):
  # 
  # Description: returns all records of table
  #
  # create WHERE clause if there is a SiteId field and
  # select Primary keys for order_list (exclude SiteId)
  if table_name in ["anvilusers","anviluser"]:
    # Anvil users DB table
    pd_list = app_tables.users.search(tables.order_by("email",ascending=True))    
  else:

    table_info = describe_table(table_name)
    order_list = ""
    where_clause = ""
    for column in table_info:
      if column["Field"] == "SiteId" and table_name != "site":
        where_clause = " WHERE SiteId = '" + site_id + "'"
      elif column["Key"] == "PRI":
        if len(order_list) > 0:
          order_list = order_list + ", " + column["Field"]
        else:
          order_list = column["Field"]

    # create query
    #if table_name == "sys_siteuser":
    #  # need to create a special view for the roles of users for a site
    #  query = "SELECT Email,Role_name FROM sys_siteuser,sys_role WHERE sys_siteuser.SiteId = '" + site_id + "' AND sys_siteuser.RoleId = sys_role.RoleId ORDER BY Email"
    #else:
    query = "SELECT * FROM " + table_name + where_clause + " ORDER BY " + order_list
    #conn.ping(reconnect=True)
    with conn.cursor() as cur:
      cur.execute(query)
      result = cur.fetchall()
      # put query result in pandas dataframe

      #
      pdf_result = pd.DataFrame(result) 

      # Automatically converts to the best possible types
      pdf_result = pdf_result.convert_dtypes()


      # 1. Identify numeric columns (int and float) - replace NaN with 0
      num_cols = pdf_result.select_dtypes(include=['number']).columns
      pdf_result[num_cols] = pdf_result[num_cols].fillna(0)

      # 2. Identify object/string columns - replace NaN with empty string
      obj_cols = pdf_result.select_dtypes(exclude=['number']).columns
      pdf_result[obj_cols] = pdf_result[obj_cols].fillna('')

      msg = query + ". Found " + str(len(result)) + " " + table_name + " rows."
      logmsg("INFO",msg)

      # convert pandas dataframe to string (cannot send all datatypes to client so best to make all of type string)
      pdf_result_str = pdf_result.astype('str')

      # make all None values empty string (otherwise they will be sent to client as 'None' string, which is not good for client side processing)
      pdf_result_str.replace(to_replace='None', value='',inplace=True)
      pdf_result_str.replace(to_replace='<NA>', value='',inplace=True)
      #pdf_result_str.replace(to_replace='nan', value='',inplace=True)    

      # now dataframe into records
      pd_list = pdf_result_str.to_dict('records')

  return pd_list

@anvil.server.callable
def contexts_get(site_id):
  anviluser = anvil.users.get_user()

  logmsg("INFO","Function get contexts called for site " + site_id)
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    cur.execute("SELECT * FROM context WHERE SiteId = %s ORDER BY ContextId",site_id)
    # ContextId,AreaId,ContextName,ContextType,FieldDescription
    result = cur.fetchall()
    msg = "Found " + str(len(result)) + " Context rows."
    logmsg("INFO",msg)
  return result

@anvil.server.callable   
def finds_get(site_id):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    cur.execute("SELECT * FROM find WHERE SiteId = %s ORDER BY FindId",site_id)
    result = cur.fetchall()
    msg = "Found " + str(len(result)) +" Find rows."
    logmsg("INFO",msg)
  return result

@anvil.server.callable
def site_get_information(site_id):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    site_information = {}
    # get site information 
    #cur.execute("SELECT * FROM area WHERE SiteId = %s",(site_id))
    #count_areas = cur.rowcount
    cur.execute("SELECT * FROM context WHERE SiteId = %s",(site_id))
    count_contexts = cur.rowcount
    cur.execute("SELECT * FROM find WHERE SiteId = %s",(site_id))
    count_finds = cur.rowcount
    site_information = {"Contexts": count_contexts, "Finds": count_finds}
    msg = "Site summary for " + site_id + " #Contexts: " + str(count_contexts) + " #Finds: " + str(count_finds)
    logmsg("INFO", msg)
  return site_information

@anvil.server.callable
def context_get_details(site_id,context_id):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    # get context details
    cur.execute("SELECT * FROM context WHERE ContextId = %s AND SiteId = %s",(context_id,site_id))
    context = cur.fetchall()

  return context

@anvil.server.callable
def db_table_list():
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    cur.execute("SHOW TABLES")
    table_list = cur.fetchall()
    table_names = []
    for item in table_list:
      key = "Tables_in_" + database_connect_info["db"]
      if item[key] != "site" and item[key] != "dbdiary" and item[key].rfind("sys_") == -1: 
        # do not add 'site', 'dbdiary', 'sys_' tables
        table_names.append(item[key])
  return table_names

# ---------------------
# delete functions
# ---------------------

@anvil.server.callable
def delete_by_DBAcontrol(DBAcontrol,table_name):
  conn.ping(reconnect=True)
  with conn.cursor() as cur:
    # delete all records with this DBAcontrol
    sql_cmd = "DELETE FROM " + table_name +" WHERE DBAcontrol = '" + DBAcontrol + "'"
    try:
      ret = cur.execute(sql_cmd)
      conn.commit()
      msg = "Deleted " + str(ret) + " rows: " + sql_cmd
      logmsg("INFO", msg)
    except pymysql.Error as err:
      ret = format(err)
      msg = "Deletion of row failed: " + ret
      logmsg("ERROR", msg)
  return msg

# ---------------------
# <name>_update functions
# ---------------------
@anvil.server.callable
def row_update(table_name,items):
  # add DBAcontrol field
  description = "Update row in table " + table_name
  user = anvil.users.get_user()
  items["DBAcontrol"] = check_DBAcontrol(user["email"],"e",description)
  #logmsg("INFO",items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe, i.e. a one row table
  table = pd.DataFrame(items,index=[1])
  #print(table)
  # insert table into database; first param is table name
  #print(table_name)
  #print(table)
  message = table_update(table_name,table)
  return message

@anvil.server.callable
def site_update(site_items):
  conn.ping(reconnect=True)
  # add DBAcontrol field   
  description = "Update row in table site"
  user = anvil.users.get_user()
  site_items["DBAcontrol"] = check_DBAcontrol(user["email"],"e",descrtiption)
  #logmsg("INFO",site_items)
  message = "OK"
  id = site_items["SiteId"]
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe
  table = pd.DataFrame(site_items,index=[1])
  table = table.drop('SiteId', axis=1)
  type = "site"
  #print(table)
  table.replace({np.nan: None},inplace=True)
  cols = ""
  for i in table.columns.tolist():
    cols = cols + i + " = %s,"
  type_id = type.capitalize() + "Id"
  cur = conn.cursor()
  message = ""
  msg = ""
  # 
  for i,row in table.iterrows():
    sql_cmd = "UPDATE " + type.lower() + " SET " + cols[:-1] + " WHERE SiteId = %s "
    #logmsg("DEBUG",sql_cmd)
    values = tuple(row) + (id,)
    #logmsg("DEBUG",values)
    try:
      ret = cur.execute(sql_cmd,values)
      conn.commit()
      msg = "OK. Table " + type[:-1] + " row " + id + " successfully inserted."
      logmsg("INFO",msg)
    except pymysql.Error as err:
      msg = format(err)
      msg = type[:-1] + " " + id + " insert to database failed: " + msg
      logmsg("ERROR", msg)
    message = message + msg + "\n"
  #print(message)
  return message

@anvil.server.callable
def area_update(area_items):
  conn.ping(reconnect=True)
  # add DBAcontrol field
  description = "Update row in table area"
  user = anvil.users.get_user()
  area_items["DBAcontrol"] = check_DBAcontrol(user["email"],"e",description)
  #logmsg("INFO",site_items)
  message = "OK"
  id = area_items["AreaId"]
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe
  table = pd.DataFrame(area_items,index=[1])
  table = table.drop('AreaId', axis=1)
  table = table.drop('SiteId', axis=1)
  type = "area"
  #print(table)
  table.replace({np.nan: None},inplace=True)
  cols = ""
  for i in table.columns.tolist():
      cols = cols + i + " = %s,"
  type_id = type.capitalize() + "Id"
  cur = conn.cursor()
  message = ""
  msg = ""
  # 
  for i,row in table.iterrows():
    sql_cmd = "UPDATE " + type.lower() + " SET " + cols[:-1] + " WHERE areaId = %s "
    #logmsg("DEBUG",sql_cmd)
    values = tuple(row) + (id,)
    #logmsg("DEBUG",values)
    try:
      ret = cur.execute(sql_cmd,values)
      conn.commit()
      msg = "OK. " + type[:-1] + " " + id + " successfully inserted."
      logmsg("INFO",msg)
    except pymysql.Error as err:
      msg = format(err)
      msg = type[:-1] + " " + id + " insert to database failed: " + msg
      logmsg("ERROR", msg)
    message = message + msg + "\n"
  #print(message)
  return message

@anvil.server.callable
def context_update(context_items):
  conn.ping(reconnect=True)
  # add DBAcontrol field   
  description = "Update row in table context"
  user = anvil.users.get_user()
  context_items["DBAcontrol"] = check_DBAcontrol(user["email"],"e",description)
  #logmsg("INFO",context_items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe
  table = pd.DataFrame(context_items,index=[1])
  #print(table)
  table.replace({np.nan: None},inplace=True)
  #print(table)
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is mikiter to 65535 chars
  cols = "`,`".join([str(col) for col in list(context_items.keys())])
  values = "`,`".join([str(col) for col in list(context_items.values())])
  #logmsg("INFO",cols)
  #logmsg("INFO",values)
  sql_cmd = """UPDATE context SET Year = %s, AreaId = %s, Name = %s, ContextType = %s, RecordStatus = %s,
               FillOf = %s, Description = %s, Interpretation = %s, YearStart = %s, YearEnd = %s, DatesAssignedBy = %s,
               DBAcontrol = %s WHERE ContextId = %s AND SiteId = %s"""
  row = (context_items["Year"],context_items["AreaId"],context_items["Name"],context_items["ContextType"],context_items["RecordStatus"],
         context_items["FillOf"],context_items["Description"],context_items["Interpretation"],context_items["YearStart"],context_items["YearEnd"], context_items["DatesAssignedBy"],
         context_items["DBAcontrol"],context_items["ContextId"],context_items["SiteId"])
  #logmsg("INFO",sql_cmd)
  #logmsg("INFO",row)
  try:
    cur = conn.cursor()
    ret = cur.execute(sql_cmd,row)
    conn.commit()
    message = "OK"
    msg = "Context " + context_items["ContextId"] + " successfully updated"
    logmsg("INFO",msg)
  except pymysql.Error as err:
    message = format(err)
    msg = "Context UPDATE to database failed: " + message
    logmsg("ERROR", msg)
  return message

@anvil.server.callable
def find_update(find_items):
  conn.ping(reconnect=True)
  # add DBAcontrol field   
  description = "Update row in table find"
  user = anvil.users.get_user()
  find_items["DBAcontrol"] = check_DBAcontrol(user["email"],"e",description)
  #logmsg("INFO",find_items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put find_items dictionay into a pandas dataframe
  table = pd.DataFrame(find_items,index=[1])
  #print(table)
  table.replace({np.nan: None},inplace=True)
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is limited to 65535 chars
  cols = "`,`".join([str(col) for col in list(find_items.keys())])
  values = "`,`".join([str(col) for col in list(find_items.values())])
  #logmsg("INFO",cols)
  #logmsg("INFO",values)
  sql_cmd = """UPDATE find SET ContextId = %s, MaterialType = %s, Pieces = %s, FieldDescription = %s, DBAcontrol = %s
               WHERE FindId = %s AND SiteId = %s"""
  row = (find_items["ContextId"],find_items["MaterialType"],find_items["Pieces"],find_items["FieldDescription"],find_items["DBAcontrol"],find_items["FindId"],find_items["SiteId"])
  #logmsg("INFO",sql_cmd)
  #logmsg("INFO",row)
  try:
    cur = conn.cursor()
    ret = cur.execute(sql_cmd,row)
    conn.commit()
    message = "OK"
    msg = "Find " + find_items["FindId"] + " successfully updated"
    logmsg("INFO",msg)
  except pymysql.Error as err:
    message = format(err)
    msg = "Find UPDATE to database failed: " + message
    logmsg("ERROR", msg)
  return message

# --------------------
# <name>_add functions
# --------------------

@anvil.server.callable
def row_add(table_name,items):
  # add DBAcontrol field
  description = "Insert new row in table " + table_name
  user = anvil.users.get_user()
  items["DBAcontrol"] = check_DBAcontrol(user["email"],"i",description)
  #logmsg("INFO",items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe, i.e. a one row table
  table = pd.DataFrame(items,index=[1])
  #print(table)
  # insert table into database; first param is table name
  message = table_insert(table_name,table)
  return message

@anvil.server.callable
def site_add(site_items):
  # add DBAcontrol field   
  description = "Insert new row in table site"
  user = anvil.users.get_user()
  site_items["DBAcontrol"] = check_DBAcontrol(user["email"],"i",description)
  #logmsg("INFO",site_items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe, i.e. a one row table
  table = pd.DataFrame(site_items,index=[1])
  #print(table)
  message = table_insert("site",table)
  return message

@anvil.server.callable
def area_add(area_items):
  # add DBAcontrol field
  description = "Insert new row in table area"
  user = anvil.users.get_user()
  area_items["DBAcontrol"] = check_DBAcontrol(user["email"],"i",description)
  #logmsg("INFO",area_items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe, i.e. a one row table
  table = pd.DataFrame(area_items,index=[1])
  #print(table)
  message = table_insert("area",table)
  return message

@anvil.server.callable
def find_add(find_items):
  # add DBAcontrol field
  description = "Insert new row in table find"
  user = anvil.users.get_user()
  find_items["DBAcontrol"] = check_DBAcontrol(user["email"],"i",description)
  #logmsg("INFO",find_items)
  message = "OK"
  #print(find_items)
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe, i.e. a one row table
  table = pd.DataFrame(find_items,index=[1])
  #print(table)
  message = table_insert("find",table)
  return message

@anvil.server.callable
def context_add(context_items):
  # add DBAcontrol field
  description = "Insert new row in table context"
  user = anvil.users.get_user()
  context_items["DBAcontrol"] = check_DBAcontrol(user["email"],"i",description)
  #logmsg("INFO",context_items)
  message = "OK"
  # need to limit variables to limit of size of databae fields, e.g. FieldDescription is less than to 65535 chars
  # put context_items dictionay into a pandas dataframe, i.e. a one row table
  table = pd.DataFrame(context_items,index=[1])
  #print(table)
  # insert tabke into database; first param is table name (plural lowercase)
  message = table_insert("context",table)
  return message

# -----------------------
# Image upload functions
# ----------------------

@anvil.server.callable
def uplink_download(media_list):
  conn.ping(reconnect=True)
  # loop through list of media objects
  i = 1
  for file in media_list:
    file_extension = "." + file["File"].content_type.rsplit("/")[1]
    # get current date and time
    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    image_id = str(current_datetime) + str(i)
    # create a unique file name
    file_name = "./local/" + file["site"] + "-" + file["context"] + "-" + image_id + file_extension
    #file_name = "./local/" + file["site"] + "-" + file["context"] + "-" + uuid.uuid4().hex + file_extension
    with open(file_name,"wb") as f:
      f.write(file["File"].get_bytes())
    # Now insert media file details into DB Images Table
    sql_cmd = """INSERT INTO Images(ImageId, Caption, Copyright, ContentType, LocationURL, DBAcontrol, SiteId, ContextId, FindId)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    row = (image_id,file["caption_text"],file["copyright_text"],file["File"].content_type,file_name,"DBA1",file["site"],file["context"],file["find"])        
    msg = "Received file from client - stored at " + file_name
    try:
      cur = conn.cursor()
      cur.execute(sql_cmd,row)
      conn.commit()
      i = i + 1
      logmsg("INFO",msg)
    except pymysql.Error as err:
      message = format(err)
      msg = "Image " + file_name + " INSERT to database failed: " + message
      logmsg("ERROR", msg)
  # all done
  return

@anvil.server.callable
def images_get(site_id,context_id):
  # get images for this context
  #conn = connect()
  cur = conn.cursor()
  cur.execute("SELECT * FROM Images WHERE ContextId = %s AND SiteId = %s",(context_id,site_id))
  images = cur.fetchall()
  ret = []   # empty array for return rows
  for image in images:
    file = image["LocationURL"]
    #print(file)
    with open(file, 'rb') as f:
       ret.append({'image' : anvil.BlobMedia(image["ContentType"], f.read()),'Caption' : image["Caption"], 'Copyright' : image["Copyright"], 'ContentType' : image["ContentType"]})
    msg = "Sending file to client: " + file
    logmsg("INFO", msg)
  return ret

# --------------------
# DBAcontrol functions
# --------------------

@anvil.server.callable
def check_DBAcontrol(user,action,description):
  #
  # Description: Check DB for an existing DBAcontrol record or add a new DBAcontrol record.
  #              DBAcontrol value format is yyyymmddAIIS (where yyyy=year, mm=month, dd=day of month,A=action lowecase{b|r|e|u|i|d}, II=initials user,S=sequence letter {a|b|....|z}
  # Paramenters:
  #    user: email of User
  #    action: lowercase letter {b|r|e|u|i|d}
  # Return: an existing or a new DBAcontrol value
  #
  DBA_action_dict = {"b": "BULKLOAD", "r": "RELOAD", "e": "EDIT", "u": "UPDATE", "i": "INSERT", "d": "DELETE"}
  current_date = datetime.now().strftime("%Y%m%d")
  current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
  row = app_tables.users.get(email = user)
  user_initials = row["initials"]
  session_id = anvil.server.get_session_id()
  DBAcontrol_search = current_date + user_initials + action + "%"
  #conn = connect()
  cur = conn.cursor()
  # search for an existing DBAcontrol record using search criteria of 'today, action and initials' 
  sql_cmd = """SELECT * FROM dbdiary WHERE DBAcontrol LIKE %s ORDER BY DBAcontrol DESC LIMIT 1"""
  cur.execute(sql_cmd,DBAcontrol_search)
  records = cur.fetchall()
  # there should only be one row in the records returned !
  for row in records:
    DBAcontrol = row["DBAcontrol"]
  new_DBAcontrol = ""
  if not records:
    # no existing DBAcontrol record found so start at seq_no "a"
    new_DBAcontrol = current_date + user_initials + action + "a"
    #print("not found DBAcontrol records. Creating new DBAControl:",new_DBAcontrol )
  else:
    if session_id != row["URL"] or action == 'b':
      # DBAcontrol exists but session_id is new, OR action is Bulk Upload/Import: create new DBAcontrol
      # find latest seq_no (last position of DBAcontrol) and use next letter (may need to extend to beyond lowercase z and continue with [A..Z])
      #print(DBAcontrol)
      new_DBAcontrol = current_date + user_initials + action + chr(ord(DBAcontrol[12])+1)
      #print("Found existing DBAcontrol, but anvil session is different, so creating new DBAcontrol",new_DBAcontrol)
  if new_DBAcontrol != "":
    # there is not an existing DBAcontrol record for the current session_id in the database so a new DBAcontrol record has to be added to database
    sql_cmd = """INSERT INTO dbdiary(DBAcontrol, Activity, GazControl, URL, Description)
              VALUES (%s, %s, %s, %s, %s)"""
    email = anvil.users.get_user()['email']
    ip_address = str(anvil.server.context.client.ip)
    activity = "Web session from " + ip_address + ", User " + str(email) + ", " + current_datetime
    row = (new_DBAcontrol,activity,DBA_action_dict[action],session_id,description)        
    try:
      cur = conn.cursor()
      cur.execute(sql_cmd,row)
      conn.commit()
      msg = "Created new DBAcontrol record: " + new_DBAcontrol + " (session_id: " + session_id + ")"
      logmsg("INFO",msg)
      DBAcontrol = new_DBAcontrol
    except pymysql.Error as err:
      message = format(err)
      msg = "DBAcontrol " + new_DBAcontrol + " INSERT to database failed: " + message
      logmsg("ERROR", msg)
      DBAcontrol = ""
  else:
    # there is an existing record for this DBAcontrol, so just return this existing DBAcontrol value
    msg = "DBAcontrol: found existing DBAcontrol record: " + DBAcontrol
    logmsg("INFO",msg)
  # DBAcontrol now has the value of the exisiting or new record in the DB, so return this to caller. If the INSERT to database failed, the DBAcontrol value is empty string.
  return DBAcontrol
  
# --------------
# user functions
# --------------

@anvil.server.callable
def system_users_get():
  list = app_tables.users.search(tables.order_by("email",ascending=True))
  msg = "Returned user list to client (" + str(len(list)) + " users)"
  # = "Returned user list to client ( users)"
  logmsg("INFO",msg)
  return list

@anvil.server.callable  
def system_user_update(user,systemrole,status,initials,firstname,lastname):
  row = app_tables.users.get(email = user)
  # check that there is always one enabled System Administrator user
  if row["systemrole"] == "System Administrator" and row["enabled"] == True and (status == False or systemrole != "System Administrator"): 
    # need to check if there is another enabled System Administrator user
    admin_users = app_tables.users.search(systemrole = "System Administrator", enabled = True)
    if len(admin_users) == 1:
      msg = "ERROR: Cannot disable the only enabled System Administrator user: " + admin_users[0]["email"]
      logmsg("ERROR", msg)
      return msg
  # update relevant fields (not password!)
  row.update(systemrole = systemrole, enabled = status, initials = initials, firstname = firstname, lastname = lastname)
  print(dict(row))
  msg = "User updated: " + str(user) + ", " + str(systemrole) + ", " + str(status) + ", " + str(initials)
  logmsg("INFO", msg)
  return msg

@anvil.server.callable  
def system_user_insert(email,password,systemrole,status,initials,firstname,lastname):
  # validate fields:
  email = email.strip().lower()
  try:
    new_user = anvil.users.signup_with_email(email,password)
    #
    system_user_update(email,systemrole,status,initials,firstname,lastname)
    msg = "Created System Administrator user: " + email
    logmsg("INFO", msg)
  except Exception as e:
    msg = "An error occurred during registration of user " + email + ": " + str(e)
    logmsg("ERROR", msg)
  return msg

@anvil.server.callable
def system_user_delete(user):
  row = app_tables.users.get(email = user["email"])
  # check that there is always one enabled System Administrator user
  if row["systemrole"] == "System Administrator" and row["enabled"] == True:
     # need to check if there is another enabled System Administrator user
     admin_users = app_tables.users.search(systemrole = "System Administrator", enabled = True)
     if len(admin_users) == 1:
        msg = "ERROR: Cannot delete the only enabled System Administrator user: " + admin_users[0]["email"]
        logmsg("ERROR", msg)
        return msg
  # delete the user
  msg = "Deleted system user: " + str(user["email"]) 
  row.delete()
  logmsg("INFO", msg)
  return

@anvil.server.callable
def import_file(type,file):
  # add DBAcontrol field
  description = "Import of csv file for table " + type
  user = anvil.users.get_user()
  DBAcontrol = check_DBAcontrol(user["email"],"b",description)
  # type is database table name 
  with anvil.media.TempFile(file) as tempfilename:
    msg = "Receiving " + type + " import file from client and storing in temp file: " + tempfilename
    logmsg("INFO", msg)
    # read Import csv file as Pandas Dataframe
    registrationdate = datetime.now()
    
    try:
      table = pd.read_csv(tempfilename,dtype='str')
      table.replace({np.nan: None},inplace=True)
      if type != "anvilusers":
        # add DBAcontrol column
        table["DBAcontrol"] = DBAcontrol
        if type == "sys_siteuserrole":
          # special case for sys_siteuserrole table import: need to add RegistrationDate field
          table['RegistrationDate'] = registrationdate.strftime('%Y-%m-%d %H:%M:%S')
          # strip spaces and convert Email field to lowercase
          table["Email"] = table["Email"].str.strip().str.lower()
        #print(table)
        message = table_insert(type,table)
        #print(message)
        nr_of_rows = len(message.splitlines(False))
        nr_of_ok = message.count("OK.")
        ret_msg = "Change ID: " + DBAcontrol + "\n" + message + str(nr_of_rows) + " rows processed. " + str(nr_of_ok) + " rows successfully inserted.\n"
      else:
        # special case for Anvil users table
        # strip spaces and convert email field to lowercase
        table["email"] = table["email"].str.strip().str.lower()
        ret_msg = ""
        msg = ""
        for i,row in table.iterrows():
          #print(i,row)
          # validate systemrole field
          if row["systemrole"] in ["Site Administrator","Site User"]:
            msg = system_user_insert(row["email"],row["password"],row["systemrole"],True,row["initials"],row["firstname"],row["lastname"])
          else:
            msg = "ERROR: Invalid systemrole for user " + row["email"] + ": " + row["systemrole"]
          ret_msg = ret_msg + msg + "\n"
    except:
      ret_msg = "Error reading import file for table " + type + "\n"
    return ret_msg

# Functions to handle log file compression
def namer(name):
    return name + ".gz"

def rotator(source, dest):
    with open(source, 'rb') as f_in:
        with gzip.open(dest, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    os.remove(source)

def logmsg(level,message):
  # This function adds the Anvil session_id to the log message and logs the message to the log file with the specified log level
  if level == "INFO":
    logging.info("%s | %s",anvil.server.get_session_id(),message)
  elif level == "ERROR":
    logging.error("%s | %s",anvil.server.get_session_id(),message)
  elif level == "DEBUG":
    logging.debug("%s | %s",anvil.server.get_session_id(),message)
  elif level == "WARNING":
    logging.warning("%s | %s",anvil.server.get_session_id(),message)
  elif level == "CRITICAL":
    logging.critical("%s | %s",anvil.server.get_session_id(),message)
  return

#----------------------------------------------------------------------------------------#
# This is the start of the server code execution; the following lines are executed at
# startup of the server and before any calls from the client are processed
#----------------------------------------------------------------------------------------#

#----------------------------------------------------------------------------------------#
# The folling line has to be commented out / removed when deploying this as server code
# using the Anvil-app-server it connects direct to the Client
#----------------------------------------------------------------------------------------#

#anvil.server.connect("server_HGRHEN6VHS3TZUER3QF6XVSG-RSU3U7R2ORMFMQUN")

# setup logging 
log_path = os.getenv('ANVIL_APP_LOG_FILE', 'ANII-R2-server.log')
print("Logging to file: " + log_path)

# 1. Stop console logging (stdout/stderr)
logging.basicConfig(level=logging.DEBUG,handlers=[])
                    # handlers=[] : This prevents logging from being sent to the default stderr handler; 
                    # instead we will use a TimedRotatingFileHandler to write logs to file with rotation at midnight and keep 7 days of logs

root_logger = logging.getLogger('')
# 2. Setup TimedRotatingFileHandler with backupCount
file_handler = TimedRotatingFileHandler(
    filename=log_path, 
    when='midnight', 
    interval=1, 
)
# 3. Attach the compression functions to the handler so that when the log file is rotated at midnight, the old log file is compressed and saved with a .gz extension
file_handler.namer = namer
file_handler.rotator = rotator
# 4. Set format and add to logger
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
file_handler.setFormatter(formatter)
root_logger.addHandler(file_handler)

root_logger.addHandler(file_handler)

# log startup message

logmsg("INFO","--------------------------")
logmsg("INFO","Anchurus-II server started")
#logmsg("WARNING","This is a warning message")
#logmsg("ERROR","This is an error message")
#logmsg("DEBUG","This is a debug message")
#logmsg("CRITICAL","This is a critical message")
 
#users_table = app_tables.users

user_list = app_tables.users.search(tables.order_by("email"))

# Reading Configuration file
config = configparser.ConfigParser()
config.read('anchurus2.cfg')

database_connect_info = {}
database_connect_info["host"] =  config.get("database","host",fallback="localhost")
database_connect_info["port"] =  config.get("database","port",fallback="3306")
database_connect_info["user"] =  config.get("database","user",fallback="root")
database_connect_info["password"] =  config.get("database","password",fallback="toor")
database_connect_info["db"] =  config.get("database","db",fallback="mydb")
database_connect_info["special_finds_table_prefix"] =  config.get("database","special_finds_table_prefix")

users_info = {}
users_info["admin_domain"] = config.get("users","admin_domain")
users_info["admin_user"] = config.get("users","admin_user")
users_info["admin_pw"] = config.get("users","admin_pw")
users_info["admin_firstname"] = config.get("users","admin_firstname")
users_info["admin_lastname"] = config.get("users","admin_lastname")
users_info["admin_user_initials"] = config.get("users","admin_user_initials")

client_info = {}
client_info["rows_per_page"] = config.get("client","rows_per_page",fallback="20")
client_info["version"] = config.get("default","version")
client_info["organisation"] = config.get("client","organisation")

client_info.update(users_info)

#logmsg("INFO",client_info)

# connect to database
try:
  conn = pymysql.connect(host=database_connect_info["host"],
                               port=int(database_connect_info["port"]),
                               user=database_connect_info["user"],
                               password=database_connect_info["password"],
                               db=database_connect_info["db"],
                               cursorclass=pymysql.cursors.DictCursor)
  msg = "Successfully connected to database: " + database_connect_info["db"]
  logmsg('INFO',msg)
except pymysql.Error as err:
  logmsg("ERROR",format(err))

#
# Check if an enabled admin_user is in Anvil users table; if not then create a new user (as defined in the configuration file)
# as admin_user in the Anvil user table. 
# This is only run at startup and will ensure there is always one enabled admin user
#
# First check it users table has the extra columns (initials, firstname, lastname, systemrole) added for the
# admin user management; if not then add these columns

#cols = app_tables.users.list_columns()
#logmsg('INFO',"Columns in users table: " + str(cols))   

#if "initials" not in cols:
#  app_tables.users.add_column("initials",str)
#  app_tables.users.add_column("firstname",str)
#  app_tables.users.add_column("lastname",str)
#  app_tables.users.add_column("systemrole",str)


admin_users = app_tables.users.search(systemrole = "System Administrator", enabled = True)
if len(admin_users) > 0:
  msg = "Found System Administrator user(s): "
  for user_row in admin_users:
    msg = msg + str(user_row["email"]) + " "
else:
  # No enabled System Administrators found
  #
  # check if users_info["admin_user"] exists:
  admin_users = app_tables.users.search(email=users_info["admin_user"])
  if len(admin_users) > 0:
    # user exists but is not System Administrator or could be disabled; so force update this user to be an enabled System Administrator
    msg = system_user_update(users_info["admin_user"],
                             "System Administrator",
                             True,
                             users_info["admin_user_initials"],
                             users_info["admin_firstname"],
                             users_info["admin_lastname"]
                             )
  else:
    # create new System Administrator user
    msg = system_user_insert(users_info["admin_user"],
                             users_info["admin_pw"],
                             "System Administrator",
                             True,
                             users_info["admin_user_initials"],
                             users_info["admin_firstname"],
                             users_info["admin_lastname"]
                             )
    anvil.email.send(from_name = "My App Support", 
                 to = users_info["admin_user"],
                 subject = "Welcome",
                 text = "Hi, your email address has been configured as System Administrator in the BAS Anvil Web Application.")
logmsg('INFO',msg)

#---------------------------------------------------------------------------------------#
# The folling line has to be commented out / removed when deploying this as server code
# using the Anvil-app-server con
#---------------------------------------------------------------------------------------#
# Now wait for calls from frontend (browser)

#anvil.server.wait_forever()

