#!/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import re
import pandas as pd
from datetime import datetime
import getpass
def main():
    try:
        #print(sys.argv)
        #print(len(sys.argv))

        para_list = sys.argv[1:]
        #print(para_list[0])
        #print(para_list[1])

    except Exception as e:
        print("Error parameters!!! unknown parameter")
        print(e)
        sys.exit(1)

    if(len(para_list) == 0) or para_list[0] == "-h":
        help()
        sys.exit(1)

    excel_file = pd.ExcelFile(para_list[0])

    for i in excel_file.sheet_names :
        if "memorymap" in i :
            df = pd.read_excel(para_list[0], sheet_name=i)
            note_corpus = df.values.tolist()
            note_ser = pd.Series(note_corpus)
            print("\nall data:")
            print(df)
            note_ser = pd.Series(note_corpus)
            para_list_name = [para_list[0], i]
            #gen_sysmaph(para_list_name, note_corpus, note_ser)
            #gen_sysmapsvh(para_list_name, note_corpus, note_ser)
            addrblock_yml_gen(note_corpus)


def addrblock_yml_gen(note_corpus):#{{{
    fp = open("SKY_ASIC.yml", "w") 
    cnt = 0
    corder = []
    print_line = []
    print_line.append("blocks:")
    for addrblock_info in note_corpus :
        if pd.isna(addrblock_info[1]) == True or addrblock_info[1] == "Slave" or addrblock_info[1] == "RESERVE" or addrblock_info[1] in corder :
            print("Repeat addressblock : "+str(addrblock_info[1]))
            continue
        else :
            print_line.append("  - name: "+addrblock_info[1].upper())
            print_line.append("    offset: "+addrblock_info[5].lower())
            print_line.append("    size: "+str(addrblock_info[7]))
            if pd.isna(addrblock_info[2]) == True :
                print_line.append("    path: null")
            else :
                print_line.append("    path: "+str(addrblock_info[14]))
            if pd.isna(addrblock_info[2]) == True :
                print_line.append("    protocol: null")
            else :
                print_line.append("    protocol: "+addrblock_info[2])
            corder.append(addrblock_info[1])
        cnt = cnt + 1
    
    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    #fp.write('\n')
    #fp.write('endmodule')

    fp.close()
#}}}

def gen_sysmaph(para_list, note_corpus, note_ser):#{{{ 
    
    print_line = []
    add_header(print_line, "sky_sysmap.svh")
    print_line.append("")
   
    print_line.append("#ifndef __SKY_SYSMAP_H__")
    print_line.append("#define __SKY_SYSMAP_H__")
    print_line.append("#ifndef ASIC_BASEADDR")
    print_line.append("  #define ASIC_BASEADDR 0x0UL")
    print_line.append("#endif")
    print_line.append("")

    corder = []
    for note_info in note_corpus :
        #print(note_info[1])
        if pd.isna(note_info[1]) == True or note_info[1] == "Slave" or note_info[1] == "RESERVE" or note_info[1] in corder :
            print("Repeat addressblock : "+str(note_info[1]))
            continue
        else :
            print_line.append("#ifndef ASIC_"+note_info[1].upper()+"_BASEADDR")
            print_line.append("  #define ASIC_"+note_info[1].upper()+"_BASEADDR (ASIC_BASEADDR + "+note_info[5].lower()+"UL)")
            print_line.append("#endif")
            print_line.append("")
            #print(note_info[1])
            corder.append(note_info[1])

    print_line.append("#endif //__SKY_SYSMAP_H__")

    fp = open("sky_sysmap.h", "w") 

    for line in print_line :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()

#}}}

def gen_sysmapsvh(para_list, note_corpus, note_ser):#{{{ 
    
    print_line = []
    add_header(print_line, "sky_sysmap.svh")
    print_line.append("")

    print_line.append("`ifndef __SKY_SYSMAP_SVH__")
    print_line.append("`define __SKY_SYSMAP_SVH__")
    print_line.append("`ifndef ASIC_BASEADDR")
    print_line.append("  `define ASIC_BASEADDR 'h0")
    print_line.append("`endif")
    print_line.append("")

    corder = []
    for note_info in note_corpus :
        #print(note_info[1])
        if pd.isna(note_info[1]) == True or note_info[1] == "Slave" or note_info[1] == "RESERVE" or note_info[1] in corder :
            continue
        else :
            print_line.append("`ifndef ASIC_"+note_info[1].upper()+"_BASEADDR")
            print_line.append("  `define ASIC_"+note_info[1].upper()+"_BASEADDR (ASIC_BASEADDR + 'h"+note_info[5].lower().replace("0x", "")+")")
            print_line.append("`endif")
            print_line.append("")
            corder.append(note_info[1])

    print_line.append("`endif //__SKY_SYSMAP_SVH__")

    fp = open("sky_sysmap.svh", "w") 

    for line in print_line :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()

#}}}

# add_header{{{
def add_header(print_line, filename):
    today = datetime.today()
    now = datetime.now()
    user = getpass.getuser()
    
    date1 = today.strftime("%Y/%m/%d")
    year = today.strftime("%Y")
    time = now.strftime("%H:%M")
    #print("date1 =", date1)
    #print("year =", year)
    #print("time =", time)
    #print(user)
    
    print_line.append("// +FHDR----------------------------------------------------------------------------")
    print_line.append("// Copyright (c) "+year+" Cygnusemi.")
    print_line.append("// ALL RIGHTS RESERVED Worldwide")
    print_line.append("//         ")
    print_line.append("// Author        : "+user)
    print_line.append("// Email         :  @cygnusemi.com")
    print_line.append("// Created On    : "+date1+" "+time)
    print_line.append("// Last Modified : "+date1+" "+time)
    print_line.append("// File Name     : "+filename)
    print_line.append("// Description   :")
    print_line.append("// ")
    print_line.append("// ---------------------------------------------------------------------------------")
    print_line.append("// Modification History:")
    print_line.append("// Date         By              Version                 Change Description")
    print_line.append("// ---------------------------------------------------------------------------------")
    print_line.append("// "+date1+"   "+user+"     1.0                     Original")
    print_line.append("// -FHDR----------------------------------------------------------------------------")

# }}}

def gen_note(para_list, note_corpus, note_ser):#{{{ 
    
    print_line = []
   
    print_line.append("// Component")
    print_line.append("ASIC          --  v1.0")
    print_line.append("")
    print_line.append("// Block")
    print_line.append("ASIC                        --  0x0000_0000:0xffff_ffff  --   asic top block      -- ahb")
    print_line.append("")
    print_line.append("// Sub Block")

    for note_info in note_corpus :
        if "RESERVE" in str(note_info[12]) or "DEFINE NAME" in str(note_info[12]) or "Slave"  in note_info[0] :
            continue
        else :
            print_line.append(str(note_info[12]).upper()+"      --  "+note_info[4].lower()+":"+note_info[5].lower()+"  --   "+note_info[0].lower()+" address block       -- dab")

    print_line.append("// Sub Block end")
    print_line.append("")
    print_line.append("// Block end")
    print_line.append("// Component end")

    fp = open("ASIC.note", "w") 

    for line in print_line :
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')

    fp.close()

#}}}

# help{{{
def help():
    print("############## help ####################")
    print("########################################")
    print("#######regfile excel generate xml#######")
    print("gen_asic_sysmap.py excel_path project_name ")

# }}}

if __name__ == "__main__":
    main()
