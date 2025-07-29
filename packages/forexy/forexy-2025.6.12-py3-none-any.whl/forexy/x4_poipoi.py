#!/usr/bin/python3
ver="2025.04.07"
############################################################
# POIPOI Ver.2025.04.07
# (Utility to remove pointer from EXFOR in JSON)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
from datetime import timezone
import datetime
import json
import os
import re
import argparse
import copy

def main(file_inp,file_dict,data_id,file_out,key_keep,force0,delpoin0,keep0010):
  global x4_json, dict_json
  global force, delpoin, keep001

  force=force0
  delpoin=delpoin0
  keep001=keep0010

  x4_json_full=read_x4json(file_inp)
  dict_json=read_dict(file_dict)

  found=True
  if data_id=="all":
    dir_out=file_out
  else:
    found=False
    if len(data_id)==11:
      pointer=data_id[10:11]
    elif len(data_id)==9:
      pointer=""

  for nentry, entry in enumerate(x4_json_full["entries"]):
    x4_json=dict()
    x4_json=x4_json_full["entries"][nentry]
    for nsubent, subentry in enumerate(x4_json["subentries"]):
      if nsubent==0:
        continue

      if "SUBENT" in subentry:
        ansan=subentry["SUBENT"]["N1"]
        for reaction in x4_json["subentries"][nsubent]["REACTION"]:
          if data_id=="all":
            pointer=reaction["pointer"]
            if pointer=="":
              file_out=dir_out+"/"+ansan[0:5].lower()+"."+ansan[5:8]+".json"
              print("** Processing "+ansan[0:5]+"."+ansan[5:8])
            else:
              file_out=dir_out+"/"+ansan[0:5].lower()+"."+ansan[5:8]+"."+pointer+".json"
              print("** Processing "+ansan[0:5]+"."+ansan[5:8]+"."+reaction["pointer"])
            poipoi(nsubent,pointer,file_out,key_keep)

          elif ansan[0:5]==data_id[0:5] and ansan[5:8]==data_id[6:9] and reaction["pointer"]==pointer:
            found=True
            print("** Processing "+data_id)
            poipoi(nsubent,pointer,file_out,key_keep)

      else:
        ansan=subentry["NOSUBENT"]["N1"]
        if data_id=="all":
          file_out=dir_out+"/"+ansan[0:5].lower()+"."+ansan[5:8]+".json"
          print("** Processing "+ansan[0:5]+"."+ansan[5:8])
          poipoi(nsubent,"",file_out,key_keep)
        elif ansan[0:5]==data_id[0:5] and ansan[5:8]==data_id[6:9]:
          found=True
          print("** Processing "+data_id)
          poipoi(nsubent,"",file_out,key_keep)

  if found==False:
    msg="The dataset "+data_id+" does not exist in "+file_inp+"."
    print_error_fatal(msg,"")

  print("POIPOI: Processing terminated normally.")


def poipoi(nsubent,pointer,file_out,key_keep):

  if keep001==True:
    title="J4 - EXFOR in JSON without pointer with common subentry"
  else:
    title="J4 - EXFOR in JSON without pointer without common subentry"

  time=datetime.datetime.now(timezone.utc)
  time_out=time.strftime("%Y-%m-%dT%H:%M:%S%z")

  x4_json_poi=[]

# BIB section of condensed JSON file when preservation of 001 choosen
  if keep001==True:
    nsubents=[0]

    x4_json_poi.append(None)
    x4_json_poi[0]=dict()
    x4_json_poi[0]["SUBENT"]={
      "N1": x4_json["subentries"][0]["SUBENT"]["N1"],
      "N2": x4_json["subentries"][0]["SUBENT"]["N2"],
      "alteration_flag": x4_json["subentries"][0]["SUBENT"]["alteration_flag"],
      "transmission_identification": x4_json["subentries"][0]["SUBENT"]["transmission_identification"]
    }
    bib_condensed=dict() 
    bib_condensed=condense_bib(nsubents,pointer,key_keep)
    if len(bib_condensed)==0:
      x4_json_poi[0]["NOBIB"]={
        "N1": 0,
        "N2": 0
      }
    else:
      x4_json_poi[0]["BIB"]={
        "N1": len(bib_condensed),
        "N2": 0
      }
     
      x4_json_poi[0].update(bib_condensed)
     
      x4_json_poi[0]["ENDBIB"]={
        "N1": 0,
        "N2": 0
      }

# COMMON section (001) of condensed JSON file when preservation of 001 choosen
    common_condensed=dict()
    common_condensed=condense_common(nsubents,pointer)
    if len(common_condensed["pointer"])==0:
      x4_json_poi[0]["NOCOMMON"]={
        "N1": 0,
        "N2": 0
      }
    else:
      x4_json_poi[0]["COMMON"]={
        "N1": len(common_condensed["pointer"]),
        "N2": 0
      }

      x4_json_poi[0]["COMMON"].update(common_condensed)

      x4_json_poi[0]["ENDCOMMON"]={
        "N1": 0,
        "N2": 0
      }
    x4_json_poi[0]["ENDSUBENT"]={
      "N1": 0,
      "N2": 0
    }

# END of output for 001 (common subentry)

  if keep001==True:
    nsubents=[nsubent]
    ind=1
  else:
    nsubents=[0,nsubent]
    ind=0

  x4_json_poi.append(None)

  x4_json_poi[ind]=dict()

  if "SUBENT" not in x4_json["subentries"][nsubent]:
    if keep001==True:
      x4_json_poi[ind]["NOSUBENT"]={
        "N1": x4_json["subentries"][nsubent]["NOSUBENT"]["N1"],
        "N2": x4_json["subentries"][nsubent]["NOSUBENT"]["N2"]
      }

      x4_json_poi_out=dict()
      x4_json_poi_out={
       "title"              : title,
       "time_stamp"         : time_out,
       "entries":[
         {
           "ENTRY":{
             "N1": x4_json["ENTRY"]["N1"],
             "N2": x4_json["ENTRY"]["N2"],
             "alteration_flag": x4_json["ENTRY"]["alteration_flag"],
             "transmission_identification": x4_json["ENTRY"]["transmission_identification"]
           },
           "subentries":[
           ]
         }
       ]
      }
      x4_json_poi_out["entries"][0]["subentries"]=x4_json_poi

      x4_json_poi_out["entries"][0]["ENDENTRY"]={
        "N1": 2,
        "N2": 0
      }
      json_out=json.dumps(x4_json_poi_out,indent=2)
      f=open(file_out,"w")
      f.write(json_out)
      f.close()

      return

    else:
      if delpoin==False:
        x4_json_poi[ind]["SUBENT"]={
          "N1": x4_json["subentries"][0]["SUBENT"]["N1"],
          "N2": x4_json["subentries"][0]["SUBENT"]["N2"],
          "alteration_flag": x4_json["subentries"][0]["SUBENT"]["alteration_flag"],
          "transmission_identification": x4_json["subentries"][0]["SUBENT"]["transmission_identification"]
        }
      else:
        ansan_out=x4_json["subentries"][0]["SUBENT"]["N1"][0:5]+"???"
        x4_json_poi[ind]["SUBENT"]={
          "N1": ansan_out,
          "N2": x4_json["subentries"][0]["SUBENT"]["N2"],
          "alteration_flag": x4_json["subentries"][0]["SUBENT"]["alteration_flag"],
          "transmission_identification": x4_json["subentries"][0]["SUBENT"]["transmission_identification"]
        }
  else:
    if delpoin==False:
      x4_json_poi[ind]["SUBENT"]={
        "N1": x4_json["subentries"][nsubent]["SUBENT"]["N1"],
        "N2": x4_json["subentries"][nsubent]["SUBENT"]["N2"],
        "alteration_flag": x4_json["subentries"][nsubent]["SUBENT"]["alteration_flag"],
        "transmission_identification": x4_json["subentries"][nsubent]["SUBENT"]["transmission_identification"]
      }
    else:
      ansan_out=x4_json["subentries"][0]["SUBENT"]["N1"][0:5]+"???"
      x4_json_poi[ind]["SUBENT"]={
        "N1": ansan_out,
        "N2": x4_json["subentries"][0]["SUBENT"]["N2"],
        "alteration_flag": x4_json["subentries"][0]["SUBENT"]["alteration_flag"],
        "transmission_identification": x4_json["subentries"][0]["SUBENT"]["transmission_identification"]
      }

# BIB section of condensed JSON file
  bib_condensed=dict()
  bib_condensed=condense_bib(nsubents,pointer,key_keep)
  if len(bib_condensed)==0:
    x4_json_poi[ind]["NOBIB"]={
      "N1": 0,
      "N2": 0
    }
  else:
    x4_json_poi[ind]["BIB"]={
      "N1": len(bib_condensed),
      "N2": 0
    }
   
    x4_json_poi[ind].update(bib_condensed)
   
    x4_json_poi[ind]["ENDBIB"]={
      "N1": 0,
      "N2": 0
    }

# COMMON section of condensed JSON file
  common_condensed=dict()
  common_condensed=condense_common(nsubents,pointer)
  if len(common_condensed["pointer"])==0:
    x4_json_poi[ind]["NOCOMMON"]={
      "N1": 0,
      "N2": 0
    }
  else:
    x4_json_poi[ind]["COMMON"]={
      "N1": len(common_condensed["pointer"]),
      "N2": 0
    }

    x4_json_poi[ind]["COMMON"].update(common_condensed)

    x4_json_poi[ind]["ENDCOMMON"]={
      "N1": 0,
      "N2": 0
    }

# DATA section of condensed JSON file
  data_condensed=dict()
  data_condensed=condense_data(nsubent,pointer)
  if len(data_condensed["pointer"])==0:
    x4_json_poi[ind]["NODATA"]={
      "N1": 0,
      "N2": 0
    }
  else:
    x4_json_poi[ind]["DATA"]={
      "N1": len(data_condensed["pointer"]),
      "N2": len(data_condensed["value"])
    }

    x4_json_poi[ind]["DATA"].update(data_condensed)

    x4_json_poi[ind]["ENDDATA"]={
      "N1": 0,
      "N2": 0
    }

  x4_json_poi[ind]["ENDSUBENT"]={
    "N1": 0,
    "N2": 0
  }

  x4_json_poi_out=dict()
  x4_json_poi_out={
   "title"              : title,
   "time_stamp"         : time_out,
   "entries":[
     {
       "ENTRY":{
         "N1": x4_json["ENTRY"]["N1"],
         "N2": x4_json["ENTRY"]["N2"],
         "alteration_flag": x4_json["ENTRY"]["alteration_flag"],
         "transmission_identification": x4_json["ENTRY"]["transmission_identification"]
       },
       "subentries":[
       ]
     }
   ]
  }
  x4_json_poi_out["entries"][0]["subentries"]=x4_json_poi

  if keep001==True:

    x4_json_poi_out["entries"][0]["ENDENTRY"]={
      "N1": 2,
      "N2": 0
    }
  else:
    x4_json_poi_out["entries"][0]["ENDENTRY"]={
      "N1": 1,
      "N2": 0
    }

  json_out=json.dumps(x4_json_poi_out,indent=2)
  f=open(file_out,"w")
  f.write(json_out)
  f.close()

  return


def condense_bib(nsubents,pointer,key_keep):

# pointers=["",pointer]
# pointers=list(dict.fromkeys(pointers)) # ["",""] -> [""]

  new=dict()
  identifiers=[] # list of all identifiers
  for nsubent in nsubents:
    identifiers.extend(list(x4_json["subentries"][nsubent].keys()))
  identifiers=list(dict.fromkeys(identifiers))

  keywords=[] # list of all keywords (i.e., w/o system identifier)
  for keyword in identifiers:
    if keyword in [x["keyword"] for x in dict_json["002"]]:
      keywords.append(keyword) 

  for keyword in keywords:
    if key_keep!=["all"]:
      if keyword not in key_keep and keyword!="REACTION":
        continue
    new[keyword]=[]
    for nsubent in nsubents:
      if keyword in x4_json["subentries"][nsubent]:

        x4_copy=copy.deepcopy(x4_json["subentries"][nsubent][keyword])
        records=[x for x in x4_copy if x["pointer"]=="" or x["pointer"]==pointer]

        for record in records:
          if delpoin==False:
            record["pointer"]=pointer
          else:
            record["pointer"]=""
        new[keyword]+=records

  for keyword in list(new):
    if len(new[keyword])==0:
      new.pop(keyword) # remove keyword with empty array

  return new


def condense_common(nsubents,pointer):

  new=dict()
  new["pointer"]=[]
  new["heading"]=[]
  new["unit"]=[]
  new["value"]=[]

  for nsubent in nsubents:
    if "COMMON" in x4_json["subentries"][nsubent]:
      pointers=x4_json["subentries"][nsubent]["COMMON"]["pointer"]
      for i, poi in enumerate(pointers):
        if poi=="" or poi=="pointer":
          if delpoin==False:
            new["pointer"].append(pointer)
          else:
            new["pointer"].append("")
          new["heading"].append(x4_json["subentries"][nsubent]["COMMON"]["heading"][i])
          new["unit"].append(x4_json["subentries"][nsubent]["COMMON"]["unit"][i])
          new["value"].append(x4_json["subentries"][nsubent]["COMMON"]["value"][i])

  return new


def condense_data(nsubent,pointer):
  new=dict()

  new["pointer"]=[]
  new["heading"]=[]
  new["unit"]=[]
  new["value"]=[]
  if "flag" in x4_json["subentries"][nsubent]["DATA"]:
    new["flag"]=[]

  if "DATA" in x4_json["subentries"][nsubent]:
    pointers=x4_json["subentries"][nsubent]["DATA"]["pointer"]
    cols=[]
    for i, poi in enumerate(pointers):
      if poi=="" or poi==pointer:
        if delpoin==False:
          new["pointer"].append(pointer)
        else:
          new["pointer"].append("")
        new["heading"].append(x4_json["subentries"][nsubent]["DATA"]["heading"][i])
        new["unit"].append(x4_json["subentries"][nsubent]["DATA"]["unit"][i])
        cols.append(i)

    if "flag" in x4_json["subentries"][nsubent]["DATA"]:
      for i, (vals,flgs) in enumerate((zip(x4_json["subentries"][nsubent]["DATA"]["value"],\
                                           x4_json["subentries"][nsubent]["DATA"]["flag"]))):
        new["value"].append([])
        for j in cols:
          new["value"][i].append(vals[j])
        new["flag"].append(flgs)

    else:
      for i, vals in enumerate(x4_json["subentries"][nsubent]["DATA"]["value"]):
        new["value"].append([])
        for j in cols:
          new["value"][i].append(vals[j])

  return new


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Remove pointer structure in J4",\
   epilog="example: x4_poipoi.py -i exfor.json -d dict_9131.json -e 22742.004.1 -o exfor_poi.json -k all")
  parser.add_argument("-v", "--version",\
         action="version", version=ver)
  parser.add_argument("-i", "--file_inp",\
   help="input J4 file")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary")
  parser.add_argument("-e", "--data_id",\
   help="EXFOR Dataset ID ('all' to process all datasets)")
  parser.add_argument("-o", "--file_out",\
   help="output J4 file")
  parser.add_argument("-k", "--key_keep",\
   help="keywords to be kept (optional, 'all' to process all keywords)", default=["all"], nargs="+")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-p", "--delpoin",\
   help="delete pointer", action="store_true")
  parser.add_argument("-c", "--keep001",\
   help="keep common subentry 001", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("POIPOI (Ver."+ver+") run on "+date)
  print("----------------------------------------")

  force0=args.force
  delpoin0=args.delpoin
  keep0010=args.keep001

  file_inp=args.file_inp
  if file_inp is None:
    file_inp=input("input J4 file [exfor.json] -------------> ")
    if file_inp=="":
      file_inp="exfor.json"
  if not os.path.exists(file_inp):
    print(" ** File "+file_inp+" does not exist.")
  while not os.path.exists(file_inp):
    file_inp=input("Input J4 file [exfor.json] -------------> ")
    if file_inp=="":
      file_inp="exfor.json"
    if not os.path.exists(file_inp):
      print(" ** File "+file_inp+" does not exist.")

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("input JSON Dictionary [dict_9131.json] -> ")
    if file_dict=="":
      file_dict="dict_9131.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("input JSON DIctionary [dict_9131.json] --> ")
    if file_dict=="":
      file_dict="dict_9131.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  data_id=args.data_id
  if data_id is None:
    data_id=input("EXFOR Dataset ID [22742.004.1] ---------> ")
    if data_id=="":
      data_id="22742.004.1"
  data_id=data_id.upper()
  if not re.compile(r"^[1-9A-Z]\d{4}\.\d{3}(\.[1-9A-Z])?$").search(data_id) and data_id!="all":
    print(" ** EXFOR Dataset ID "+data_id+" is illegal.")
  while not re.compile(r"^[1-9A-Z]\d{4}\.\d{3}(\.[1-9A-Z])?$").search(data_id) and data_id!="all":
    data_id=input("EXFOR Dataset ID [22742.004.1] ---------> ")
    if data_id=="":
      data_id="22742.004.1"
    data_id=data_id.upper()
    if not re.compile(r"^[1-9A-Z]\d{4}\.\d{3}(\.[1-9A-Z])?$").search(data_id) and data_id!="all":
      print(" ** EXFOR Dataset ID "+data_id+" is illegal.")

  file_out=args.file_out
  if data_id=="all":
    if file_out is None:
      file_out=input("Directory of output J4 files [json] -> ")
    if file_out=="":
      file_out="json"
   
    if os.path.isdir(file_out):
      msg="Directory '"+file_out+"' exists and must be overwritten."
      print_error(msg,"",force0)
    else:
      msg="Directionry '"+file_out+"' does not exist and must be created."
      print_error(msg,"",force0)
      os.mkdir(file_out)

  else:
    if file_out is None:
      file_out=input("Output J4 file [exfor_poi.json] --------> ")
    if file_out=="":
      file_out="exfor_poi.json"
    if os.path.isfile(file_out):
      msg="File '"+file_out+"' exists and must be overwritten."
      print_error(msg,"",force0)

  key_keep=args.key_keep
# if key_keep is None:
#   key_keep=input("input keywords to keep [all] -----------> ")
#   if key_keep=="":
#     key_keep="all"
  print("input keywords to keep -----------------> ", end="")
  for char in key_keep:
    print(char+" ", end="")
  print("\n")

  return file_inp,file_dict,data_id,file_out,key_keep,force0,delpoin0,keep0010
  

def read_x4json(file_inp):
  f=open(file_inp)
  try:
    x4_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_inp+" is not in JSON format."
    print_error_fatal(msg,"")

  if x4_json["title"]!="J4 - EXFOR in JSON" and\
     x4_json["title"]!="J4 - EXFOR in JSON (number as string)" :
    msg=file_inp+" is not an EXFOR in JSON."
    print_error_fatal(msg,"")

  f.close()
  return x4_json


def read_dict(file_dict):
  f=open(file_dict)
  try:
    dict_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_dict+" is not in JSON format."
    print_error_fatal(msg,"")

  if dict_json["title"]!="EXFOR/CINDA Dictionary in JSON":
    msg=file_dict+" is not an EXFOR/CINDA Dictionary in JSON."
    print_error_fatal(msg,"")

  return dict_json


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


def print_error_fatal(msg,line):
  print("**  "+msg)
  print(line)
  exit()


if __name__ == "__main__":
  args=get_args(ver)
  (file_inp,file_dict,data_id,file_out,key_keep,force0,delpoin0,keep0010)=get_input(args)
  main(file_inp,file_dict,data_id,file_out,key_keep,force0,delpoin0,keep0010)
  exit()
