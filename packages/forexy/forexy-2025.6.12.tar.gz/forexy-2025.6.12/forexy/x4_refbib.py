#!/usr/bin/python3
ver="2025.04.21"
############################################################
# REFBIB Ver.2025.04.21
# (Utility for getting and processing CrossRef metadata)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
#  on behalf of the International Network of
#  Nuclear Reaction Data Centres (NRDC)
############################################################
import datetime
import os
import re
import argparse
import json
import requests
import unicodedata
import time
from pylatexenc.latexencode import unicode_to_latex
from spellchecker import SpellChecker
spell = SpellChecker()

def main(ref_inp,fauthor,file_dict,file_bib,format,email,force0,strip0):

  global force, strip

  force=force0
  strip=strip0

  msg=""

  if fauthor=="any":
    fauthor=""

  if re.compile("^[A-Z],").search(ref_inp):
    x4_ref=ref_inp.strip()
    x4_doi=None
  else:
    x4_ref=None
    x4_doi=ref_inp.strip()

  (issn12,issn21,code,range_type,range_min,range_max)=read_dict_044()

  if x4_doi is None: # input is an EXFOR reference code
    reference=x4_ref.split(",")
    (ref_type,ref_code,volume,issue,page,year,msg)=anal_reference(reference)

    if msg=="":
      if re.compile(r".\(.+\)$").search(page):
        msg="Parenthesized paper number not supported"
     
      else:
        if re.compile(r"\d+\-\d+").search(volume):
          volume0=re.sub(r"(\d)\-\d+", "\\1", volume) # e.g., 700-701 -> 700
        elif re.compile(r"^\d+$").search(volume):
          volume0=volume
        else:
          msg="Non-integer volume number not supported"

    if msg=="": 
      issn=""
      for issn0 in issn12: # find primary ISSN for the given code and vol. range
        for code0, range_min0, range_max0 in zip(code[issn0],range_min[issn0],range_max[issn0]):
          if range_type[issn0]=="V":
            if ref_code==code0 and int(volume0)>=range_min0 and int(volume0)<=range_max0:
              issn=issn0
              break
     
      if issn=="":
        msg="ISSN not found in Dict.044."

  else: # input is a DOI
    issn=""
    fauthor=""
    volume=""
    issue=""
    page=""
    year=""

# Check presence of DOI and registration agency (RA)
    url="https://doi.org/doiRA/"+x4_doi 
    xref_out=requests.get(url, params="")
    data=xref_out.json()
    char=json.dumps(data,indent=2,ensure_ascii=False)

    if "RA" not in data[0]:
      msg="DOI unresolvable"

    elif data[0]["RA"]!="Crossref":
      msg="DOI registered not by CrossRef but by "+data[0]["RA"]+"."


# Get metadata from CrossRef in piped format
# Example of piped output
# 00903752|Nuclear Data Sheets|Otuka|120||272|2014|full_text||10.1016/j.nds.2014.07.065

  if msg=="":
    (url,params)=get_url(email,"piped",x4_doi,issn,fauthor,volume,issue,page,year)
    xref_out=requests.get(url, params=params)
    arr=xref_out.text.rstrip(os.linesep).split("|")
    doi=arr[-1]

    if x4_doi=="":
      if doi=="": # DOI not found. Try with the secondary ISSN
        issn=issn12[issn]
        if issn!="        ":
          (url,params)=get_url(email,"piped",x4_doi,issn,fauthor,volume,issue,page,year)
          xref_out=requests.get(url, params=params)
          arr=xref_out.text.rstrip(os.linesep).split("|")
          doi=arr[-1]

    else:
      if len(arr)!=10:
        msg="DOI not for a joural article"
   
  if msg=="":
    issn=arr[0]
    if issn=="":
      msg="Metadata not in CrossRef"

    elif doi=="":
      for i in range(5):
        time.sleep(1)
        (url,params)=get_url(email,"piped",x4_doi,issn,fauthor,volume,issue,page,year)
        xref_out=requests.get(url, params=params)
        arr=xref_out.text.rstrip(os.linesep).split("|")
        doi=arr[-1]
        if doi!="":
          break
      if doi=="": 
        msg="DOI not found in CrossRef"

  if msg=="":
    issn=arr[0]
    jour=arr[1]
    fauthor=arr[2]
    volume=arr[3]
    page=arr[5]
    year=arr[6]
    type=arr[8]
   

# Print output

  if msg=="":
    print("")
    print("DOI:   "+doi)
    print("")
    print_file(file_bib,format,email,doi,issn,jour,fauthor,volume,issue,page,year,strip)

  else:
    print("")
    print("** "+msg)
    print("")
    f=open(file_bib,"w")
    f.write("** "+msg)
    f.close()

  print("REFBIB: Processing terminated normally.")


def print_file(file_bib,format,email,doi,issn,jour,fauthor,volume,issue,page,year,strip):

  if format=="doi":
    f=open(file_bib,"w")
    f.write(doi)
    f.close()

  else:
    if format=="exfor" or format=="bibtex":
      format_xref="json"
      url="https://api.crossref.org/works/"+doi
      xref_out=requests.get(url)

    elif format=="piped" or format=="json" or format=="xml":
      format_xref=format

      (url,params)=get_url(email,format_xref,doi,issn,fauthor,volume,issue,page,year)
      xref_out=requests.get(url, params=params)
    
#   print(xref_out.url)         # print URL for submission to CrossRef
#   print(xref_out.status_code) # 200 -> successful
#   print(xref_out.encoding)    # encoding type (json, text, ...)

    if format=="piped" or format=="xml":
      char=xref_out.text
      if strip:
        char=strip_accents(char)
      f=open(file_bib,"w", encoding="utf-8")
      f.write(char)
      f.close()
    
    elif format=="json":
      data=xref_out.json()
      char=json.dumps(data,indent=2,ensure_ascii=False)
      if strip:
        char=strip_accents(char)
      f=open(file_bib,"w", encoding="utf-8")
      f.write(char)
      f.close()

    elif format=="exfor":
      data=xref_out.json()
      print_exfor(file_bib,data,volume,year)

    elif format=="bibtex":
      data=xref_out.json()
      print_bibtex(file_bib,data,doi,jour,volume,year)

  return


def print_exfor(file_bib,data,volume,year):

  f=open(file_bib,"w")

# Not clear what can be in ["title"][1] (2025-01-31)
  title=data["message"]["title"][0]
  title=re.sub(r"<\/?.+?>", "", title)
  title=title_lower(title,format)
  titles=title.split()
  line_out="TITLE     "
  iout=0;
  for title in titles:
    chars=list(title)

    title=""
    for char in chars:
      if re.compile("^[α-ωΑ-Ω]$").search(char):
        char=greek_to_name(char)
      title=title+char

    title=strip_accents(title)
    if iout==0:
      len_max=66;
    else:
      len_max=55;
    if len(line_out+" "+title)>len_max:
      f.write(line_out+"\n")
      line_out="            "+title
      iout+=1
    else:
      line_out=line_out+" "+title
  if len(line_out)!=0:
    f.write(line_out+"\n")
  
  authors=[]
  for author in data["message"]["author"]:
    if "family" in author:
      if "given" in author:
        if re.compile(r"\.$").search(author["given"]):
          author=author["given"]+author["family"]
        else:
          author=author["given"]+" "+author["family"]
      else:
        author=author["family"]
      authors.append(author)
  line_out="AUTHOR     ("
  iout=0;
  for author in authors:
    author=strip_accents(author)
    author=author.replace(". ",".")
    if iout==0:
      len_max=66;
    else:
      len_max=55;
    if len(line_out+", "+author+",")>len_max:
      f.write(line_out+",\n")
      line_out="            "+author
    else:
      if line_out=="AUTHOR     (":
        line_out=line_out+author
      else:
        line_out=line_out+", "+author
  if len(line_out)!=0:
    f.write(line_out+")\n")


  line_out="REFERENCE  (J,"

  (issn12,issn21,code,range_type,range_min,range_max)=read_dict_044()
  issn=data["message"]["ISSN"][0]
  issn=issn.replace("-","")
  if issn not in code:
    issn=issn21[issn]

  if "page" in data["message"]:
    page=re.sub(r"(\d+)\-(\d+)", "\\1", data["message"]["page"])
  elif "article-number" in data["message"]:
    page=data["message"]["article-number"]
  else:
    page="???"

  if len(code[issn])==1:
    line_out=line_out+code[issn][0]+","+volume+","+page+","+year
  else:
    for i in range(len(code[issn])+1):
      if i==len(code[issn]):
        line_out=line_out+code[issn][0]+"?,"+volume+","+page+","+year
      elif int(volume)>=range_min[issn][i] and int(volume)<=range_max[issn][i]:
        line_out=line_out+code[issn][i]+","+volume+","+page+","+year
        break

  f.write(line_out+")\n")

  f.close()
  return


def print_bibtex(file_bib,data,doi,jour,volume,year):

  f=open(file_bib,"w")

  f.write("@article{,\n")
  line_out="  author  ={"
  for author in data["message"]["author"]:
    family=unicode_to_latex(author["family"])
    family=re.sub(r"\.(\w)", ". \\1", family)
    if "given" in author:
      given=unicode_to_latex(author["given"])
      given=re.sub(r"\.(\w)", ". \\1", given)
      if line_out=="  author  ={":
        line_out=line_out+family+", "+given
      else:
        line_out=line_out+" and "+family+", "+given
    else:
      if line_out=="  author  ={":
        line_out=line_out+family
      else:
        line_out=line_out+" and "+family
  line_out=line_out+"},"
  f.write(line_out+"\n")

# Not clear what can be in ["title"][1] (2025-01-31)
  title=data["message"]["title"][0]
  title=re.sub(r"<\/?.+?>", "", title)
  title=unicode_to_latex(title)
  title=title_lower(title,format)
  f.write("  title   ={"+title+"},\n")

  jour=unicode_to_latex(jour)
  f.write("  journal ={"+jour+"},\n")

  f.write("  year    ={"+year+"},\n")
  f.write("  volume  ={"+volume+"},\n")

  if "page" in data["message"]:
    page=re.sub(r"(\d)\-(\d)", "\\1--\\2", data["message"]["page"])
  elif "article-number" in data["message"]:
    page=data["message"]["article-number"]
  else:
    page="???"

  f.write("  pages   ={"+page+"},\n")

  f.write("  doi     ={"+doi+"}\n")

  f.write("}\n")

  f.close()
  return


def read_dict_044():

  code=dict()
  issn12=dict()
  issn21=dict()
  range_type=dict()
  range_min=dict()
  range_max=dict()

  file_dict="dict_arc_new.044"
  lines=get_file_lines(file_dict)
  for line in lines:
    if line[12:20]=="        ":
      continue
    line=line.rstrip(os.linesep)
    code0=[]
    range_min0=[]
    range_max0=[]
    issn=line[12:20]                 # ISSN primary, usually for print verison
    issn12[issn]=line[48:56]         # ISSN secondary for the ISSN primary
    issn21[line[48:56]]=issn         # ISSN primary for the ISSN secondary

    range_type[issn]=line[46:47]     # V -> volume, Y -> year

    for i in range(3):
      col_cod=58+i*16
      col_min=col_cod+6
      col_max=col_min+5

      char_cod=line[col_cod-1:col_cod+5].rstrip()
      char_min=line[col_min-1:col_min+4].lstrip()
      char_max=line[col_max-1:col_max+4].lstrip()

      if re.compile(r"[A-Z]").search(char_cod):
        code0.append(char_cod)
        if (char_min=="" and char_max==""):
          range_min0.append(0)
          range_max0.append(9999999)
        elif (char_max==""):
          range_min0.append(int(char_min))
          range_max0.append(9999999)
        elif (char_min==""):
          range_min0.append(0)
          range_max0.append(int(char_max))
        else:
          range_min0.append(int(char_min))
          range_max0.append(int(char_max))

    code[issn]=code0
    range_min[issn]=range_min0
    range_max[issn]=range_max0

  return issn12,issn21,code,range_type,range_min,range_max


def anal_reference(reference):

  ref_type=reference[0]
  ref_code=reference[1]

  date=reference[-1]

  if date[0:2]!="19" and date[0:2]!="20":
    date="19"+date
  year=date[0:4]

  volume=""
  issue=""
  page=""

  if ref_type!="J":
    msg="Reference type "+ref_type+" not supported."

  elif len(reference)!=5 and len(reference)!=6:
    msg="Too few or many comma separators: "+x4_ref

  else:
    msg=""

    volume=reference[2]
   
    if len(reference)==5:
      issue=""
      page=reference[3]
   
    elif len(reference)==6:
      issue=reference[3]
      issue=re.sub(r"^\(|\)$", "", issue)
      page=reference[4]

  return ref_type,ref_code,volume,issue,page,year,msg


def get_url(email,format,x4_doi,issn,fauthor,volume,issue,page,year):

  doi=""

  url="https://doi.crossref.org/servlet/query"

# Example of Cross Ref API for J,NDS,120,272,2014 in piped format (to be abolished?)
#      https://doi.crossref.org/servlet/query?usr=email@address.com&format=json&qdata=00903752|||120||272|2014|||
# Example of Cross Ref API for 10.1016/j.nds.2014.07.065 in piped format (to be abolished?)
#      https://doi.crossref.org/servlet/query?usr=email@address.com&format=json&qdata=|||||||||10.1016/j.nds.2014.07.065

# qdata=issn+"||"+fauthor+"|"+volume+"|"+issue+"|"+page+"|"+year+"|||"+doi

# Example of Cross Ref API for N.Otuka+,J,NDS,120,272,2014 in XML format
#      https://doi.crossref.org/servlet/query?usr=email@address.com&format=json&qdata=<?xml version = "1.0" encoding="UTF-8"?><query_batch xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0" xmlns="http://www.crossref.org/qschema/2.0"  xsi:schemaLocation="http://www.crossref.org/qschema/2.0 http://www.crossref.org/qschema/crossref_query_input2.0.xsd"><head><doi_batch_id>0000</doi_batch_id> </head><body><query><issn>00903752</issn><author match="fuzzy" search-all-authors="false">Otuka</author><volume>120</volume><issue></issue><first_page>272</first_page><year>2014</year></query></body></query_batch>

# Example of Cross Ref API for 10.1016/j.nds.2014.07.065 in XML format
#      https://doi.crossref.org/servlet/query?usr=email@address.com&format=json&qdata=<?xml version = "1.0" encoding="UTF-8"?><query_batch xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.0" xmlns="http://www.crossref.org/qschema/2.0"  xsi:schemaLocation="http://www.crossref.org/qschema/2.0 http://www.crossref.org/qschema/crossref_query_input2.0.xsd"><head><doi_batch_id>0000</doi_batch_id> </head><body><query><doi>10.1016/j.nds.2014.07.065</doi></query></body></query_batch>

# An alternative solution for 10.1016/j.nds.2014.07.065
#      https://api.crossref.org/works/10.1016/j.nds.2014.07.065

  qdata="<?xml version=\"1.0\" encoding=\"UTF-8\"?><query_batch xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" version=\"2.0\" xmlns=\"http://www.crossref.org/qschema/2.0\"  xsi:schemaLocation=\"http://www.crossref.org/qschema/2.0 http://www.crossref.org/qschema/crossref_query_input2.0.xsd\"><head><doi_batch_id>0000</doi_batch_id> </head><body><query>"

  if x4_doi is None:
    qdata=qdata+"<issn>"+issn+"</issn><author match=\"fuzzy\" search-all-authors=\"false\">"+fauthor+"</author><volume>"+volume+"</volume><issue>"+issue+"</issue><first_page>"+page+"</first_page><year>"+year+"</year></query></body></query_batch>"

  else:
    qdata=qdata+"<doi>"+x4_doi+"</doi></query></body></query_batch>"
  
  params = {
             "usr": email,
             "format": format,
             "qdata": qdata
           } 

  return url,params


def strip_accents(char):

  try:
    char=unicode(char,'utf-8')
  except NameError: # unicode is a default on python 3 
    pass

  char=unicodedata.normalize('NFD',char).encode('ascii','ignore').decode("utf-8")
  char=str(char)
  return char


def greek_to_name(symbol):

  (greek,size,letter,what,*with_tonos)=unicodedata.name(symbol).split()
  assert greek, letter==("GREEK", "LETTER")
  if size=="SMALL":
    return what.lower()
  else:
    return what.title()

 
def title_lower(title,format):
  words=title.split()
  typos=spell.unknown(words)
  title=""
  for i,word in enumerate(words):
    if word.lower() in typos:
      if format=="bibtex":
        title=title+" {"+word+"}"
      else:
        title=title+" "+word
    else:
      title=title+" "+word.lower() 
      if i==0:
        title=title[1:].capitalize()

  return title


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Get CrossRef Metadata for an EXFOR reference code or DOI",\
   epilog="example: x4_refbib.py -i J,NDS,120,272,2014 -a any -d dict_9131.json -o x4_refbib_out.txt -r doi -e email@address.com")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--ref_inp",\
   help="EXFOR reference code or DOI")
  parser.add_argument("-a", "--fauthor",\
   help="family name of the first author (optional, 'any' for any firat authors)", default="any")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary")
  parser.add_argument("-o", "--file_bib",\
   help="output bibliography file")
  parser.add_argument("-r", "--format",\
   help="output format (doi, piped, exfor, bibtex, json or xml)")
  parser.add_argument("-e", "--email",\
   help="your email address")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-s", "--strip",\
   help="strip accent", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("REFBIB (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  strip0=args.strip

  ref_inp=args.ref_inp
  if ref_inp is None:
    ref_inp=input("EXFOR reference code or DOI [J,NDS,120,272,2014] -> ")
    if ref_inp=="":
      ref_inp="J,NDS,120,272,2014"
  if not re.compile(r"^([A-Z],|10\.)").search(ref_inp):
    print(" ** Input a correct EXFOR reference code or DOI.")
  while not re.compile(r"^([A-Z],|10\.)").search(ref_inp):
    ref_inp=input("EXFOR reference code or DOI [J,NDS,120,272,2014] -> ")
    if ref_inp=="":
      ref_inp="J,NDS,120,272,2014"
    if not re.compile(r"^([A-Z],|10\.)").search(ref_inp):
      print(" ** Input a correct EXFOR reference code or DOI.")

  fauthor=args.fauthor
# if fauthor is None:
#   fauthor=input("Family name of the first author [any] ------------> ")
#   if fauthor=="":
#     fauthor="any"
  print("Family name of the first author ------------------> "+fauthor)

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("JSON Dictionary [dict_9131.json] -----------------> ")
    if file_dict=="":
      file_dict="dict_9131.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("JSON DIctionary [dict_9131.json] -----------------> ")
    if file_dict=="":
      file_dict="dict_9131.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_bib=args.file_bib
  if file_bib is None:
    file_bib=input("output bibliography file [x4_refbib_out.txt] -----> ")
  if file_bib=="":
    file_bib="x4_refbib_out.txt"
  if os.path.isfile(file_bib):
    msg="File '"+file_bib+"' exists and must be overwritten."
    print_error(msg,"",force0)
    os.remove(file_bib)

  format=args.format
  if format is None:
    format=input("output format [doi] ------------------------------> ")
    if format=="":
      format="doi"
  if format!="doi" and format!="piped" and format!="json" and\
     format!="xml" and format!="exfor" and format!="bibtex":
    print(" ** Format must be piped, json, xml, exfor or bibtex.")
  while format!="doi" and format!="piped" and format!="json" and\
        format!="xml" and format!="exfor" and format!="bibtex":
    format=input("output format [doi] ------------------------------> ")
    if format=="":
      format="doi"
    if format!="doi" and format!="piped" and format!="json" and\
       format!="xml" and format!="exfor" and format!="bibtex":
      print(" ** Format must be doi, piped, json, xml, exfor or bibtex.")

  email=args.email
  if email is None:
    email=input("your email address -------------------------------> ")
  if not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
    print(" ** Input a correct email address.")
  while not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
    email=input("your email address -------------------------------> ")
    if not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
      print(" ** Input a correct email address.")

  return ref_inp,fauthor,file_dict,file_bib,format,email,force0,strip0


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, "r")
    lines=f.readlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    print_error_fatal(msg)
  return lines


def print_error_fatal(msg,line):
  print("** "+msg)
  print(line)
  exit()


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


def print_error_1(msg,line):
  print("**  "+msg)
  print(line)

  return


if __name__ == "__main__":
  args=get_args(ver)
  (ref_inp,fauthor,file_dict,file_bib,format,email,force0,strip0)=get_input(args)
  main(ref_inp,fauthor,file_dict,file_bib,format,email,force0,strip0)
  exit()
