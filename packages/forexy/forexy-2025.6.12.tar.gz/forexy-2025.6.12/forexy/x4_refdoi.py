#!/usr/bin/python3
ver="2025.04.07"
############################################################
# REFDOI Ver.2025.04.07
# (Utility to obtain DOIs for references in EXFOR file)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import datetime
import json
import os
import re
import argparse

if os.path.isfile("x4_x4toj4.py"):
  import x4_x4toj4
else:
  from forexy import x4_x4toj4

if os.path.isfile("x4_refbib.py"):
  import x4_refbib
else:
  from forexy import x4_refbib

def main(file_x4,file_dict,file_doi,key_anal,email,force0):

# Input parameters for X4TOJ4 and REFDOI
  force=force0

# Input parameters for X4TOJ4
  time=datetime.datetime.now()
  file_tmp= time.strftime('%Y%m%d%H%M%S%f')
  chkrid   = False  # record identificaiton not checked in X4TOJ4
  key_keep = "REFERENCE REL-REF MONIT-REF STATUS" # keep reference keywords only
  keepflg  = False  # ignore flags at col.80 in X4TOJ4
  add19    = True   # Add 19 to two digits year
  outstr   = True   # print real numbers as strings in X4TOJ4
  delpoin  = True   # delete pointer in the output in POIPOI
  keep001  = True   # keep common subentry in POIPOI

# Input parameters for REFDOI
  format="doi"
  strip=False
  fauthor=""

# Conversion to J4 format by X4TOJ4
  x4_x4toj4.main(file_x4,file_dict,file_tmp,key_keep,force,chkrid,add19,keepflg,outstr)
  x4_json_full=read_x4json(file_tmp)
  os.remove(file_tmp)

# Extract reference codes
  ansans=[]
  keywords=[]
  codes=[]

  for nentry, entry in enumerate(x4_json_full["entries"]):
    x4_json=dict()
    x4_json=x4_json_full["entries"][nentry]

    for nsubent, subentry in enumerate(x4_json["subentries"]):

      if "SUBENT" in subentry:
        ansan=subentry["SUBENT"]["N1"]
        ansan=ansan[0:5]+"."+ansan[5:8]

        if "REFERENCE" in key_anal and "REFERENCE" in subentry:
          for reference in subentry["REFERENCE"]:
            if "coded_information" in reference:
              for code_unit in reference["coded_information"]["code_unit"]:
                ansans.append(ansan)
                keywords.append("REFERENCE") 
                codes.append(code_unit["unit"])

        if "REL-REF" in key_anal and "REL-REF" in subentry:
           for relref in subentry["REL-REF"]:
            if "coded_information" in relref:
              ansans.append(ansan)
              keywords.append("REL-REF") 
              codes.append(relref["coded_information"]["reference"]["code"]) 

        if "MONIT-REF" in key_anal and "MONIT-REF" in subentry:
          for monitref in subentry["MONIT-REF"]:
            if "coded_information" in monitref:
              ansans.append(ansan)
              keywords.append("MONIT-REF") 
              codes.append(monitref["coded_information"]["reference"]["code"])
 
        if "STATUS" in key_anal and "STATUS" in subentry:
           for status in subentry["STATUS"]:
            if status["coded_information"] is not None:
              if status["coded_information"]["reference"] is not None:
                ansans.append(ansan)
                keywords.append("STATUS") 
                codes.append(status["coded_information"]["reference"]["code"]) 

# Check with REFDOI
  f=open(file_doi, "w")
  errors=[]
  for ansan, keyword, code in zip(ansans,keywords,codes):
    x4_refbib.main(code,fauthor,file_dict,file_tmp,format,email,force,strip)
    g=open(file_tmp, "r")
    lines=g.readlines()
    g.close()
    os.remove(file_tmp)

    keyword="%-10s" % keyword
    code="%-30s" % code

    if lines[0][0:2]=="**":
      if re.compile("DOI").search(lines[0]):
        char="** Suspicious reference code"
        errors.append(ansan+" "+keyword+" "+code)
      else:
        char="** DOI presence not checked"

    else:
      char=lines[0]
      
    f.write(ansan+" "+keyword+" "+code+" "+char+"\n")

  print()
  print("-----------------------------------------")
  if len(errors)==0:
    print ("Suspicious reference not code detected")
  else:
    print (str(len(errors))+" suspicious reference code(s) detected")
    print()
    for error in errors:
      print(error)
  print("-----------------------------------------")

  print("REFDOI: Processing terminated normally.")


def read_x4json(file_j4):
  f=open(file_j4)
  try:
    x4_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_j4+" is not in JSON format."
    print_error_fatal(msg,"")

  if x4_json["title"][0:18]!="J4 - EXFOR in JSON":
    msg=file_j4+" is not an EXFOR in JSON."
    print_error_fatal(msg,"")

  f.close()
  return x4_json


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Check presence of references in EXFOR file",\
   epilog="example: x4_refdoi.py -i exfor.txt -d dict_9131.json -o x4_refdoi_out.txt -e email@address.com")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_x4",\
   help="input EXFOR file")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary")
  parser.add_argument("-o", "--file_doi",\
   help="output DOI file")
  parser.add_argument("-k", "--key_anal",\
   help="keywords to analyse (optional)", default="REFERENCE", nargs="+")
  parser.add_argument("-e", "--email",\
   help="your email address")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("REFDOI (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force

  file_x4=args.file_x4
  if file_x4 is None:
    file_x4=input("input EXFOR file [exfor.txt] --------> ")
    if file_x4=="":
      file_x4="exfor.txt"
  if not os.path.exists(file_x4):
    print(" ** File "+file_x4+" does not exist.")
  while not os.path.exists(file_x4):
    file_x4=input("input EXFOR file [exfor.txt] -----------> ")
    if file_x4=="":
      file_x4="exfor.txt"
    if not os.path.exists(file_x4):
      print(" ** File "+file_x4+" does not exist.")

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("JSON Dictionary [dict_9131.json] ----> ")
    if file_dict=="":
      file_dict="dict_9131.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("JSON Dictionary [dict_9131.json] -> ")
    if file_dict=="":
      file_dict="dict_9131.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_doi=args.file_doi
  if file_doi is None:
    file_doi=input("Output DOI file [x4_refdoi_out.txt] -> ")
  if file_doi=="":
    file_doi="x4_refdoi_out.txt"
  if os.path.isfile(file_doi):
    msg="File '"+file_doi+"' exists and must be overwritten."
    print_error(msg,"",force0)

  key_anal=args.key_anal
# if key_anal is None:
#   key_anal=input("input keywords to analyze [REFERENCE] --> ")
#   if key_anal=="":
#     key_anal="REFERENCE"
  print("input keywords to analyse -----------> ", end="")
  for char in key_anal:
    print(char+" ", end="")
  print("\n")

  email=args.email
  if email is None:
    email=input("your email address ------------------> ")
  if not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
    print(" ** Input a correct email address.")
  while not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
    email=input("your email address ------------------> ")
    if not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
      print(" ** Input a correct email address.")

  return file_x4,file_dict,file_doi,key_anal,email,force0


def print_error(msg,line,force):
  print("** "+msg)
  print(line)

  if force:
    answer="Y"
  else:
    answer=""

  while answer!="Y" and answer!="N":
    answer=input("Continue? [Y] --> ")
    if answer=="":
        answer="Y"
    if answer!="Y" and answer!="N":
      print(" ** Answer must be Y (Yes) or N (No).")
  if answer=="N":
    print("program terminated")
    exit()


if __name__ == "__main__":
  args=get_args(ver)
  (file_x4,file_dict,file_doi,key_anal,email,force0)=get_input(args)
  main(file_x4,file_dict,file_doi,key_anal,email,force0)
  exit()
