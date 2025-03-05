#!/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
import re
import pandas as pd
from datetime import datetime
import getpass
import math
import xlrd

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
        sys.exit(0)
    
    mem_excel_path = para_list[0]
    
    harden_name = para_list[1]

    mem_reference_path = "/project/sky/user/wuming/mem/mem_reference_table.xlsx"

    
    excel_file = pd.ExcelFile(mem_excel_path)
    
    
    for sheet in excel_file.sheet_names :
        
        mem_type = []
        depth = []
        width = []
        mux = []
        bank = []
        bit_write = []
        power_gating = []
        colums = []
        rom_file = []
        #harden = ['UL','PDCSS','PDCSB','MEAS','DFF','CS_harden','TEMP']
        #harden = ['PDCSS']
       
        #if "CPU" in sheet :
        #for harden_name in harden:
        if  harden_name  in sheet :
            
                        
            # Read mem sheet
            mem_type,depth,width,mux,bank,bit_write,power_gating,rom_file,vt,device = read_excel(mem_excel_path,excel_file,sheet)
            


            for i in range(len(depth)):
                if math.isnan(depth[i]) != True and math.isnan(width[i]) != True and math.isnan(mux[i]) != True and math.isnan(bank[i]) != True :

                    mem_param_is_new = 0
                    mem_param = {str(mem_type[i])+'        depth:'+str(depth[i])+'        width:'+str(width[i])+'        bit_write:'+str(bit_write[i])+'        power_gating:'+str(power_gating[i])}
                    mem_param_is_new = check_param_in_log(sheet,mem_param)
                        
                    if int(depth[i]) != 0 :
                         
                        write_param_to_log(sheet,mem_param)
                        param = []
                        model_signal = []
                        signal_width = []
                        invert = []
                        top_signal = []
                        in_out = []
                        device_index = ''
                        vt_index = ''
                        
                        device_index = CHECK_MUX_BANK(device[i], depth[i], width[i], mux[i], bank[i])

                        mem_param = {str(mem_type[i])+'        depth:'+str(depth[i])+'        width:'+str(width[i])+'        bit_write:'+str(bit_write[i])+'        power_gating:'+str(power_gating[i])}
                        #mem_param_is_new = check_param_in_log(sheet,mem_param)
                        if vt[i] == "RVT" :
                            vt_index = "r"
                        elif vt[i] == "LVT" :
                            vt_index = "l"
                        elif vt[i] == "HVT" :
                            vt_index = "h"
                        elif vt[i] == "UHVT" :
                            vt_index = "u"
                        else :
                            print("######### mult-vt selection ERROR " + mem_param + " ############")
                            sys.exit(0)
                        
                        
                        if "spram" in mem_type[i] or 'tpram' in mem_type[i]:
                        #read mem signal reference sheet
                            param,model_signal,signal_width,top_signal,in_out = read_mem_reference(mem_type[i],mem_reference_path)
                            #initial_verilog_file(sheet,mem_type[i],depth[i],width[i],bit_write[i],power_gating[i],param,model_signal,signal_width,top_signal,in_out,mux[i],bank[i])
                            initial_verilog_file(sheet,mem_type[i],depth[i],width[i],bit_write[i],power_gating[i],param,model_signal,signal_width,top_signal,in_out,mux[i],bank[i],vt_index,device_index)
                        if "asfifo(asynchronous)" in mem_type[i] :
                            param,model_signal,signal_width,top_signal,in_out = read_mem_reference("tpram(asynchronous)",mem_reference_path)
                            initial_verilog_file(sheet,"tpram(asynchronous)",depth[i],width[i],bit_write[i],power_gating[i],param,model_signal,signal_width,top_signal,in_out,mux[i],bank[i],vt_index,device_index)
                            asfifo_wrapper(sheet,depth[i],width[i],bit_write[i],power_gating[i],vt_index,device_index)
                        if "sfifo(synchronous)" in mem_type[i] :
                            param,model_signal,signal_width,top_signal,in_out = read_mem_reference("tpram(synchronous)",mem_reference_path)
                            initial_verilog_file(sheet,"tpram(synchronous)",depth[i],width[i],bit_write[i],power_gating[i],param,model_signal,signal_width,top_signal,in_out,mux[i],bank[i],vt_index,device_index)
                            sfifo_wrapper(sheet,depth[i],width[i],bit_write[i],power_gating[i],vt_index,device_index)
                        if "rom" in mem_type[i] :
                            param,model_signal,signal_width,top_signal,in_out = read_mem_reference(mem_type[i],mem_reference_path)
                            rom_name = rom_file[i].split('/')[-1]
                            rom_name = rom_name.split('.')[0]
                            rom_wrapper(sheet, depth[i], width[i],str(rom_name) , param,model_signal,signal_width,top_signal,in_out)
               
               
        

# mem_param_excel{{{
def read_excel(mem_excel_path,excel_file,sheet):
    
    df = pd.read_excel(mem_excel_path,sheet_name=sheet)
    #print((df.iloc[0].dtype))
    power_gating = [] 
    mem_type = df['TYPE'].values
    depth = df['NumberOfWords'].values
    width = df['BitsInWord'].values
    mux = df['MUX'].values
    bank = df['BANK'].values
    bit_write = df['BitWordWrite'].values
    rom_file = df['init txt初始化文件'].values
    vt = df['multi-Vt Selection'].values
    device = df['Suggested Device'].values

    columns = df.columns.tolist()
    if "PowerGating" in columns :
        power_gating = df['PowerGating'].values
    else :
        length = len(mem_type)
        for i in range(length) :
            power_gating.append('ON')

    return mem_type,depth,width,mux,bank,bit_write,power_gating,rom_file,vt,device


def check_param_in_log(sheet,mem_param) :
    
    with open( "mem_param.log", "r") as logfile :
        lines = logfile.readlines()
        for line in lines :
            if str(mem_param) in line : 
                return 0
    return 1
    

def write_param_to_log(sheet,mem_param):
    
    fp = open( "mem_param.log", "a")
    fp.write(str(mem_param)+"\n")
    fp.close()
    print("new memeory of " + sheet + " is " + str(mem_param) + "\n")

#}}}

# mem_reference_excel {{{

def read_mem_reference(mem_type,mem_reference_path) :
    
    param = []
    model_signal = []
    width = []
    invert = []
    top_signal = []
    in_out = [] 
    
    excel_file = pd.ExcelFile(mem_reference_path)
    for sheet in excel_file.sheet_names :   
        if mem_type in sheet :
            df = pd.read_excel(mem_reference_path,sheet_name=mem_type)
            param = df['param'].values
            model_signal = df['model_signal'].values 
            width = df['width'].values
            invert = df['invert'].values
            top_signal = df['top_signal'].values
            in_out = df['in/out'].values

    return param,model_signal,width,top_signal,in_out

#}}}

#ram verilog {{{

def initial_verilog_file(sheet,mem_type,depth,width,bit_write,power_gating,param,model_signal,signal_width,top_signal,in_out,mux,bank,vt_index,device_index):
   
    width = int(width)
    depth = int(depth)
    addr_width = str(math.ceil(math.log2(int(depth))))

    if 'spram' in mem_type :
        mem_name = 'spram_'
        model_name = 'sp'
    elif 'tpram' in mem_type :
        mem_name = 'tpram_'
        model_name = 'tp'
    
    mem_name = mem_name + str(depth) + 'd' + str(width) + 'w_'
    
    if 'asynchronous' in mem_type :
        mem_name = mem_name + '2c'
        model_name = model_name + '2c'
    elif 'synchronous' in mem_type :
        mem_name = mem_name + '1c'
        model_name = model_name + '1c'
    model_name = model_name + str(depth) + 'x' + str(width) + 'm' + str(int(mux)) + 'b' + str(int(bank))
    if 'ON' in str(bit_write) :
        mem_name = mem_name + 'b'
        model_name = model_name + 'w1'
    else :
        model_name = model_name + 'w0'

    if 'ON' in str(power_gating) :
        mem_name = mem_name + 'p'
        model_name = model_name + 'p1'
    else :
        model_name = model_name + 'p0'

    if 'OFF' in str(bit_write) and 'OFF' in str(power_gating) :
        model_name = model_name +  vt_index + "_" + device_index
        mem_name = mem_name +  vt_index + "_" + device_index
    else :
        model_name = model_name +  vt_index + "_" + device_index
        mem_name = mem_name + "_" + vt_index + "_" + device_index


    wrap_name = mem_name + '_wrap'

    print('wrap_name is : ' + wrap_name + '\n')

    fp = open(wrap_name + ".v","w")
    
    print_line = []
    
    if 'spram' in mem_type :
        print_line.append('module ' + wrap_name + '  (')
        print_line.append('\tinput    [31:0]      \t' + mem_name + '_mem_ctrl  \t,')
        print_line.append('\toutput   [' + str(width-1) + ':0]      \tdout        \t,')
        print_line.append('\tinput                \tclk         \t,')
        print_line.append('\tinput                \tme          \t,')
        print_line.append('\tinput    [' + str(int(addr_width)-1) + ':0]      \taddr        \t,')
        print_line.append('\tinput    [' + str(width-1) + ':0]      \tdin          \t,')
        print_line.append('\tinput                \tlight_sleep \t,')
        if 'ON' in str(power_gating) :
            print_line.append('\toutput               \trop         \t,')
            print_line.append('\tinput                \tdeep_sleep   \t,')
            print_line.append('\tinput                \tshut_down   \t,')
        if 'ON' in str(bit_write) :
            print_line.append('\tinput    [' + str(width-1) + ':0]      \twem           \t,')
        print_line.append('\tinput                \twe        \t')
        print_line.append(');\n\n')

        print_line.append('`ifdef NO_ASIC_MEM\n')       
        print_line.append('\tspram_regfile ')
        print_line.append('\t#(')
        print_line.append('\t\t.WORD_DEPTH             ('+str(int(depth))+'         \t),')
        print_line.append('\t\t.DATA_WIDTH             ('+str(int(width))+'         \t),')
        if 'ON'in str(bit_write) :
            print_line.append('\t\t.MASK_BIT_WIDTH         (1                           \t) ')
        else :
            print_line.append('\t\t.MASK_BIT_WIDTH         ('+str(int(width))+'         \t) ')
        print_line.append('\t)')
        print_line.append('\tu_'+ mem_name+'_wrap(')
        print_line.append('\t\t.clk                    (clk                           \t), //input')
        print_line.append('\t\t.me                     (me                            \t), //input')
        print_line.append('\t\t.addr                   (addr['+str(int(addr_width)-1)+':0]                  \t), //input')
        print_line.append('\t\t.we                     (we                            \t), //input')
        print_line.append('\t\t.din                    (din['+str(int(width)-1)+':0]                    \t), //input')
        if 'ON'in str(bit_write) :
            print_line.append('\t\t.mask                   (wem['+str(int(width)-1)+':0]                    \t), //input')
        else :
            print_line.append('\t\t.mask                   (we                          \t), //input')        
        print_line.append('\t\t.dout                   (dout['+str(int(width)-1)+':0]                   \t)  //output')
        print_line.append('\t);\n\n')
        
    
    elif 'tpram' in mem_type :
        print_line.append('module ' + wrap_name + '  (')
        print_line.append('\tinput    [31:0]     \t' + mem_name + '_mem_ctrl,')
        print_line.append('\toutput   [' + str(width-1) + ':0]      \tdoutb         \t,')
        if 'asynchronous' in mem_type :
            print_line.append('\tinput               \tclka         \t,')
            print_line.append('\tinput               \tclkb         \t,')
        elif 'synchronous' in mem_type :
            print_line.append('\tinput               \tclk          \t,')
        print_line.append('\tinput               \tenb          \t,')
        print_line.append('\tinput    [' + str(int(addr_width)-1) + ':0]      \taddrb         \t,')
        print_line.append('\tinput               \tena          \t,')
        print_line.append('\tinput    [' + str(int(addr_width)-1) + ':0]      \taddra         \t,')
        print_line.append('\tinput    [' + str(width-1) + ':0]      \tdina        \t,')
        if 'ON' in str(power_gating) :
            print_line.append('\toutput              \trop            \t,')
            print_line.append('\tinput               \tdeep_sleep     \t,')
            print_line.append('\tinput               \tshut_down      \t,')
        if 'ON' in str(bit_write) :
            print_line.append('\tinput    [' + str(width-1) + ':0]         \twem      \t,')
        print_line.append('\tinput               \tlight_sleep ')
        print_line.append(');\n\n')

        
        print_line.append('`ifdef NO_ASIC_MEM\n')

        if 'ON' in str(power_gating) :
             print_line.append("\tassign             rop = 1'b1    ;\n")
        print_line.append('\twire               we          ;')
        print_line.append('\tassign             we = ena    ;\n')
        
        print_line.append('\ttpram_regfile ')
        print_line.append('\t#(')
        print_line.append('\t\t.WORD_DEPTH             ('+str(int(depth))+' \t\t),')
        print_line.append('\t\t.DATA_WIDTH             ('+str(int(width))+'    \t\t),')
        if 'ON'in str(bit_write) :
            print_line.append('\t\t.MASK_BIT_WIDTH         (1              \t\t) ')
        else :
            print_line.append('\t\t.MASK_BIT_WIDTH         ('+str(int(width))+'    \t\t) ')
        print_line.append('\t)')
        print_line.append('\tu_'+mem_name+'_reg(')
        if 'asynchronous' in mem_type :
            print_line.append('\t\t.clka                   (clka                    \t), //input')
            print_line.append('\t\t.clkb                   (clkb                    \t), //input')
        else :
            print_line.append('\t\t.clka                   (clk                     \t), //input')
            print_line.append('\t\t.clkb                   (clk                     \t), //input')
        print_line.append('\t\t.mea                    (ena                     \t), //input')
        print_line.append('\t\t.meb                    (enb                     \t), //input')
        print_line.append('\t\t.addr_a                 (addra['+str(int(addr_width)-1)+':0]             \t), //input')
        print_line.append('\t\t.addr_b                 (addrb['+str(int(addr_width)-1)+':0]             \t), //input')
        print_line.append('\t\t.wea                    (we                      \t), //input')
        print_line.append('\t\t.din                    (dina['+str(int(width)-1)+':0]               \t), //input')
        if 'ON'in str(bit_write) :
            print_line.append('\t\t.mask                   (wem['+str(int(width)-1)+':0]            \t), //input')
        else :
            print_line.append('\t\t.mask                   (we                      \t),//input')
        print_line.append('\t\t.dout                   (doutb['+str(int(width)-1)+':0]              \t) //output')
        print_line.append('\t);\n')
    
    print_line.append('`else\n')

    if 'ON' in str(power_gating) :
        print_line.append('\twire                     prdyn     ;')

    print_line.append('\twire     [31:0]          mem_ctrl  ;\n\n')

    if 'ON' in str(power_gating) :
        print_line.append('\tassign   rop   =   ~prdyn          ;')

    print_line.append('\tassign   mem_ctrl[31:0]  =   ' + mem_name + '_mem_ctrl;\n\n') 

    print_line.append("\t"+str(model_name) + ' u_' + str(model_name) + '_lib(')
    if 'spram' in mem_type :
        if "TS83CD001" in device_index :
            print_line.append("\t\t.WABLM          (mem_ctrl[11:10]    ),")
        elif "TS83CA003" in device_index :
            print_line.append("\t\t.STOV           (1'b0               ),")
            print_line.append("\t\t.WABLM          (mem_ctrl[11:10]    ),")
        else :
            print_line.append("\t\t.STOV           (1'b0               ),")
            print_line.append("\t\t.WABLM          (mem_ctrl[12:10]    ),")
       
    if "TS83CA003" in device_index and "OFF" in str(bit_write) :
            print_line.append("\t\t.GWEN           (~we                ),")

    length = len(param)
    for i in range(length) :
        if i == (length-1) :
            last = 1
        else :
            last = 0
        if 'all' in str(param[i]) :
            print_line.append(print_verilog(str(model_signal[i]),str(signal_width[i]),str(top_signal[i]),str(int(width)-1),str(int(addr_width)-1),in_out[i],0))
        if 'ON' in str(bit_write) : 
            if 'w1' in str(param[i]) :
                print_line.append(print_verilog(model_signal[i],signal_width[i],top_signal[i],str(int(width)-1),str(int(addr_width)-1),in_out[i],0))
        elif 'TS83CA003' not in device_index:
            if 'w0' in str(param[i]) :
                print_line.append(print_verilog(model_signal[i],signal_width[i],top_signal[i],str(int(width)-1),str(int(addr_width)-1),in_out[i],0))
        if 'ON' in str(power_gating) : 
            if 'p1' in str(param[i]) :
                print_line.append(print_verilog(model_signal[i],signal_width[i],top_signal[i],str(int(width)-1),str(int(addr_width)-1),in_out[i],0))
        else :
            if 'p0' in str(param[i]) :
                print_line.append(print_verilog(model_signal[i],signal_width[i],top_signal[i],str(int(width)-1),str(int(addr_width)-1),in_out[i],0))
    if "spram" in mem_type :
        print_line.append('		.RAWLM			(mem_ctrl[8:7]     	)')
    else :
        print_line.append('		.EMAB			(mem_ctrl[5:3]     	)')
    print_line.append('\t);\n')
    print_line.append('`endif\n')



        
    for line in print_line:
            #print(line)
            fp.write(line)
            fp.write('\n')

    fp.write('\n')
    fp.write('endmodule')

    fp.close()




def print_verilog(model_signal,signal_width,top_signal,width,addr_width,in_out,last) :
    
    line = ''
    if last == 0 :
        if str(top_signal) == 'none' :
            line = ('\t\t.' + str(model_signal) + '\t\t\t(                 ),')
        else :
            if 'addr_width' in str(signal_width) :
                line = ('\t\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'[' + str(addr_width) + ':0]      \t),' )
            elif 'width' in str(signal_width) :
                line =('\t\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'[' + str(width) + ':0]       \t),' )
            else : 
                line = ('\t\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'     \t),' )
            #else :
            #    line = ('\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'[' + str(signal_width) + ':0] ),\t//' + str(in_out))
    else :
        if str(top_signal) == 'none' :
            line = ('\t\t.' + str(model_signal) + '\t\t\t(                 )' )
        else :
            if 'addr_width' in str(signal_width) :
                line = ('\t\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'[' + str(addr_width) + ':0]     \t)' )
            elif 'width' in str(signal_width) :
                line =('\t\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'[' + str(width) + ':0]       \t)' )
            else : 
                line = ('\t\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'     \t)' )
            #else :
            #    line = ('\t.' + str(model_signal) + '\t\t\t(' + str(top_signal) +'[' + str(signal_width) + ':0] ),\t//' + str(in_out))

    
    return line

#}}}




#gen_sfifo_wrap{{{

def sfifo_wrapper(sheet,depth,width,bit_write,power_gating,vt_index,device_index) :

    depth = int(depth)
    width = int(width)
    
    module_name = "sfifo_" + str(depth) + "d" + str(width) + "w_";
    module_name = module_name + "1c"

    if 'ON' in str(bit_write) :
        module_name = module_name + "b"
    if 'ON' in str(power_gating) :
        module_name = module_name + "p"

    module_name = module_name + "_" + vt_index + "_" + device_index + "_wrap"

    tpram_name = "tpram_" + str(depth) + "d" + str(width) + "w_" ;
    tpram_name = tpram_name + "1c"
    if 'ON' in str(bit_write) :
        tpram_name = tpram_name + "b"
    if 'ON' in str(power_gating) :
        tpram_name = tpram_name + "p"
    
    if 'OFF' in str(bit_write) and 'OFF' in str(power_gating) :
        tpram_name = tpram_name +  vt_index + "_" + device_index
    else :
        tpram_name = tpram_name + "_" + vt_index + "_" + device_index

    fp = open(module_name+'.v', "w")
     
    print_line = []
    add_header(print_line, module_name)
    #print_line.append('// +FHDR----------------------------------------------------------------------------')
    #print_line.append('// Copyright (c) 2022 Cygnusemi.')
    #print_line.append('// ALL RIGHTS RESERVED Worldwide')
    #print_line.append('//')
    #print_line.append('// File Name     : '+ module_name +'.v')
    #print_line.append('// Description   :')
    #print_line.append('// ')
    #print_line.append('// -FHDR---------------------------------------------------------------------------')
    print_line.append('module ' + module_name +' ')
    print_line.append('#(')
    print_line.append('\tparameter DATA_WIDTH   = '+str(width)+',')
    print_line.append('\tparameter DATA_DEPTH   = '+str(depth)+',')      
    print_line.append('\tparameter DATA_PIPE_IN = 0,')
    print_line.append('\tparameter DATA_PIPE_OUT= 0,')
    print_line.append('\tparameter DATA_FWFT    = 0,')
    print_line.append('\tparameter ADDR_WIDTH   = $clog2(DATA_DEPTH),')
    print_line.append('\tparameter WORD_CNT_WID = $clog2(DATA_DEPTH+1)')
    print_line.append('\t)')
    print_line.append('\t(')
    print_line.append("\tinput      [31:0]          "+tpram_name+"_mem_ctrl,")
    print_line.append('\tinput                      light_sleep,')
    if 'ON' in str(power_gating):
        print_line.append('\tinput                      deep_sleep,')
        print_line.append('\tinput                      shut_down,')
        print_line.append('\toutput                     rop,')             
    print_line.append('\tinput                      clk,')
    print_line.append('\tinput                      rst_n ,')
    print_line.append('\tinput                      srst,')
    print_line.append('\tinput                      w_en,')
    print_line.append('\tinput                      r_en,')
    print_line.append('\tinput  [WORD_CNT_WID-1 : 0]  afull_thrd ,')
    print_line.append('\tinput  [WORD_CNT_WID-1 : 0]  aempty_thrd,')
    print_line.append('\tinput  [DATA_WIDTH-1 : 0]  wdata,')
    print_line.append('\toutput [DATA_WIDTH-1 : 0]  rdata,')
    print_line.append('\toutput                     ram_full,')
    print_line.append('\toutput                     ram_empty,')
    print_line.append('\toutput                     fifo_full,')
    print_line.append('\toutput                     fifo_afull,')
    print_line.append('\toutput                     fifo_empty,')
    print_line.append('\toutput                     fifo_aempty,')
    print_line.append('\toutput [WORD_CNT_WID-1 : 0]  word_cnt   ')
    print_line.append(');\n')

    print_line.append('\twire [ADDR_WIDTH-1:0]       addra;')
    print_line.append('\twire [ADDR_WIDTH-1:0]       addrb;')
    print_line.append('\twire [DATA_WIDTH-1:0]       dina;')
    print_line.append('\twire                        wea;')
    print_line.append('\twire                        enb;')
    print_line.append('\twire [DATA_WIDTH-1:0]       doutb;\n')

    print_line.append('sync_fifo_ctrl') 
    print_line.append("#(")
    print_line.append("    .DATA_WIDTH         (DATA_WIDTH),")
    print_line.append("    .DATA_DEPTH         (DATA_DEPTH),")
    print_line.append('    .DATA_PIPE_IN       (DATA_PIPE_IN),')
    print_line.append("    .DATA_FWFT          (DATA_FWFT),")
    print_line.append('    .DATA_PIPE_OUT      (DATA_PIPE_OUT)')
    print_line.append(')')
    print_line.append('u_sync_fifo_ctrl(')                  
    print_line.append('    .clk                    (clk                            ), //input')
    print_line.append('    .rst_n                  (rst_n                          ), //input')
    print_line.append('    .srst                   (srst                           ), //input')
    print_line.append('    .w_en                   (w_en                           ), //input')
    print_line.append('    .r_en                   (r_en                           ), //input')
    print_line.append('    .afull_thrd             (afull_thrd[WORD_CNT_WID-1:0]   ), //input')
    print_line.append('    .aempty_thrd            (aempty_thrd[WORD_CNT_WID-1:0]  ), //input')
    print_line.append('    .wdata                  (wdata[DATA_WIDTH-1:0]          ), //input')
    print_line.append('    .rdata                  (rdata[DATA_WIDTH-1:0]          ), //output')
    print_line.append('    .ram_full               (ram_full                       ), //output')
    print_line.append('    .ram_empty              (ram_empty                      ), //output')
    print_line.append('    .fifo_full              (fifo_full                      ), //output')
    print_line.append('    .fifo_afull             (fifo_afull                     ), //output')
    print_line.append('    .fifo_empty             (fifo_empty                     ), //output')
    print_line.append('    .fifo_aempty            (fifo_aempty                    ), //output')
    print_line.append('    .word_cnt               (word_cnt[WORD_CNT_WID-1:0]         ), //output')
    print_line.append('    //tpsram/regfile read/write ')
    print_line.append('    .waddr                  (addra[ADDR_WIDTH-1:0]          ), //output')
    print_line.append('    .raddr                  (addrb[ADDR_WIDTH-1:0]          ), //output')
    print_line.append('    .wdata_mem              (dina[DATA_WIDTH-1:0]           ), //output')
    print_line.append('    .wea                    (wea                            ), //output')
    print_line.append('    .reb                    (enb                            ), //output')
    print_line.append('    .rdata_mem              (doutb[DATA_WIDTH-1:0]          )  //input')                     
    print_line.append(');\n')

    print_line.append(tpram_name + '_wrap ' +' u_'+ tpram_name +'_wrap(')
    print_line.append("    ."+tpram_name+"_mem_ctrl           ("+tpram_name+"_mem_ctrl[31:0]             ), //input")
    print_line.append('    .doutb                  (doutb[DATA_WIDTH-1:0]          ), //output')
    print_line.append('    .addra                  (addra[ADDR_WIDTH-1:0]          ), //input')
    print_line.append('    .dina                   (dina[DATA_WIDTH-1:0]           ), //input')
    #print_line.append('    .wea                    (wea                            ), //input')
    print_line.append('    .ena                    (wea                            ), //input')
    print_line.append('    .addrb                  (addrb[ADDR_WIDTH-1:0]          ), //input')
    print_line.append('    .enb                    (enb                            ), //input')
    print_line.append('    .light_sleep             (light_sleep                    ), //input')
    if 'ON' in str(power_gating):
        print_line.append('    .deep_sleep              (deep_sleep                     ), //input')
        print_line.append('    .shut_down               (shut_down                      ), //input')
        print_line.append('    .rop                     (rop                            ), //output')
    if 'ON' in str(bit_write) :
        print_line.append('    .wem                     (~' + str(width) + "'b0                     ), //input")
    print_line.append('    .clk                    (clk                            )  //input')
    print_line.append(');')

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()
# }}}

#gen_asfifo_wrap{{{

def asfifo_wrapper(sheet,depth,width,bit_write,power_gating,vt_index,device_index) :

    depth = int(depth)
    width = int(width)

    
    module_name = "asfifo_" + str(depth) + "d" + str(width) + "w_";
    module_name = module_name + "2c"
    if 'ON' in str(bit_write) :
        module_name = module_name + "b"
    if 'ON' in str(power_gating) :
        module_name = module_name + "p"
    
    module_name = module_name + "_" + vt_index + "_" + device_index + "_wrap"

    tpram_name = "tpram_" + str(depth) + "d" + str(width) + "w_" ;
    tpram_name = tpram_name + "2c"
    if 'ON' in str(bit_write) :
        tpram_name = tpram_name + "b"
    if 'ON' in str(power_gating) :
        tpram_name = tpram_name + "p"
    
    if 'OFF' in str(bit_write) and 'OFF' in str(power_gating) :
        tpram_name = tpram_name +  vt_index + "_" + device_index
    else :
        tpram_name = tpram_name + "_" + vt_index + "_" + device_index

    mem_ctrl = tpram_name + "_mem_ctrl"

    fp = open(sheet + "/" + module_name+'.v', "w")
     
    print_line = []
    add_header(print_line, module_name)
    #print_line.append('// +FHDR----------------------------------------------------------------------------')
    #print_line.append('// Copyright (c) 2022 Cygnusemi.')
    #print_line.append('// ALL RIGHTS RESERVED Worldwide')
    #print_line.append('//')
    #print_line.append('// File Name     : '+ module_name +'.v')
    #print_line.append('// Description   :')
    #print_line.append('// ')
    #print_line.append('// -FHDR---------------------------------------------------------------------------')
    print_line.append('module ' + module_name + '#( ')
    print_line.append('\tparameter DATA_WIDTH   = '+str(width)+',')
    print_line.append('\tparameter DATA_DEPTH   = '+str(depth)+',')
    print_line.append('\tparameter GRAY_SYNC_S  = 2,')  
    print_line.append('\tparameter DATA_PIPE_IN = 0,')
    print_line.append('\tparameter DATA_PIPE_OUT= 1,')
    print_line.append('\tparameter DATA_FWFT    = 0,')
    print_line.append('\tparameter ASYNC_RST_CTL= 0,')
    print_line.append('\tparameter ADDR_WIDTH   = $clog2(DATA_DEPTH)')
    print_line.append('\t)')
    print_line.append('\t(')
    print_line.append('\tinput      [31:0]          '+mem_ctrl+',')
    print_line.append('\tinput                      light_sleep,')
    if 'ON' in str(power_gating):
        print_line.append('\tinput                      deep_sleep,')
        print_line.append('\tinput                      shut_down,')
        print_line.append('\toutput                     rop,')             
    print_line.append('\tinput                      r_clk      ,')
    print_line.append('\tinput                      w_clk      ,')
    print_line.append('\tinput                      r_rst_n    ,   //async reset')
    print_line.append('\tinput                      r_srst     ,   //sync clear')
    print_line.append('\tinput                      w_rst_n    ,   //async reset')
    print_line.append('\tinput                      w_srst     ,   //sync clear')
    print_line.append('\tinput                      r_en       ,')
    print_line.append('\tinput                      w_en       ,')
    print_line.append('\tinput  [ADDR_WIDTH    :0]  afull_thrd ,')
    print_line.append('\tinput  [ADDR_WIDTH    :0]  aempty_thrd,')
    print_line.append('\tinput  [DATA_WIDTH-1 : 0]  wdata      ,')
    print_line.append('\toutput [DATA_WIDTH-1 : 0]  rdata      ,')
    print_line.append('\toutput                     ram_full   ,')
    print_line.append('\toutput                     ram_empty  ,')
    print_line.append('\toutput                     fifo_full      ,')
    print_line.append('\toutput                     fifo_afull     ,')
    print_line.append('\toutput                     fifo_empty     ,')
    print_line.append('\toutput                     fifo_aempty    ,')
    print_line.append('\toutput     [ADDR_WIDTH:0]  word_cnt_w     ,')
    print_line.append('\toutput     [ADDR_WIDTH:0]  word_cnt_r     ,')
    print_line.append('\toutput                     w_reset_active ,  //async')
    print_line.append('\toutput                     r_reset_active   //async')
    print_line.append(');\n')

    print_line.append('\twire [ADDR_WIDTH-1:0]       addra;')
    print_line.append('\twire [ADDR_WIDTH-1:0]       addrb;')
    print_line.append('\twire [DATA_WIDTH-1:0]       dina;')
    print_line.append('\twire                        wea;')
    print_line.append('\twire                        enb;')
    print_line.append('\twire [DATA_WIDTH-1:0]       doutb;\n')

    print_line.append('async_fifo_ctrl')
    print_line.append('#(/*autoinstparam*/')
    print_line.append('        .DATA_WIDTH             (DATA_WIDTH                     ),')
    print_line.append('        .DATA_DEPTH             (DATA_DEPTH                     ),')
    print_line.append('        .GRAY_SYNC_S            (GRAY_SYNC_S                    ),')
    print_line.append('        .DATA_PIPE_IN           (DATA_PIPE_IN                   ),')
    print_line.append('        .DATA_PIPE_OUT          (DATA_PIPE_OUT                  ),')
    print_line.append('        .ASYNC_RST_CTL          (ASYNC_RST_CTL                  ),')
    print_line.append("        .DATA_FWFT              (DATA_FWFT                      ),")
    print_line.append('        .ADDR_WIDTH             (ADDR_WIDTH                     ) ')
    print_line.append('    )')
    print_line.append('u_async_fifo_ctrl(/*autoinst*/')
    print_line.append('        .r_clk                  (r_clk                          ), //input')
    print_line.append('        .w_clk                  (w_clk                          ), //input')
    print_line.append('        .r_rst_n                (r_rst_n                        ), //input')
    print_line.append('        .r_srst                 (r_srst                         ), //input')
    print_line.append('        .w_rst_n                (w_rst_n                        ), //input')
    print_line.append('        .w_srst                 (w_srst                         ), //input')
    print_line.append('        .r_en                   (r_en                           ), //input')
    print_line.append('        .w_en                   (w_en                           ), //input')
    print_line.append('        .afull_thrd             (afull_thrd[ADDR_WIDTH:0]       ), //input')
    print_line.append('        .aempty_thrd            (aempty_thrd[ADDR_WIDTH:0]      ), //input')
    print_line.append('        .wdata                  (wdata[DATA_WIDTH-1:0]          ), //input')
    print_line.append('        .rdata                  (rdata[DATA_WIDTH-1:0]          ), //output')
    print_line.append('        .ram_full               (ram_full                       ), //output')
    print_line.append('        .ram_empty              (ram_empty                      ), //output')
    print_line.append('        .fifo_full              (fifo_full                      ), //output')
    print_line.append('        .fifo_afull             (fifo_afull                     ), //output')
    print_line.append('        .fifo_empty             (fifo_empty                     ), //output')
    print_line.append('        .fifo_aempty            (fifo_aempty                    ), //output')
    print_line.append('        .word_cnt_w             (word_cnt_w[ADDR_WIDTH:0]       ), //output')
    print_line.append('        .word_cnt_r             (word_cnt_r[ADDR_WIDTH:0]       ), //output')
    print_line.append('        .w_reset_active         (w_reset_active                 ), //output')
    print_line.append('        .r_reset_active         (r_reset_active                 ), //output')
    print_line.append('        //tpsram/regfile read/write ')
    print_line.append('        .waddr                  (addra[ADDR_WIDTH-1:0]          ), //output')
    print_line.append('        .raddr                  (addrb[ADDR_WIDTH-1:0]          ), //output')
    print_line.append('        .wdata_mem              (dina[DATA_WIDTH-1:0]           ), //output')
    print_line.append('        .wea                    (wea                            ), //output')
    print_line.append('        .reb                    (enb                            ), //output')
    print_line.append('        .rdata_mem              (doutb[DATA_WIDTH-1:0]          )  //input')
    print_line.append(');\n')
    
    print_line.append(tpram_name + '_wrap ' +' u_'+ tpram_name +'_wrap(')
    print_line.append("    ."+mem_ctrl+"           ("+mem_ctrl+"[31:0]             ), //input")
    print_line.append('    .doutb                  (doutb[DATA_WIDTH-1:0]          ), //output')
    print_line.append('    .addra                  (addra[ADDR_WIDTH-1:0]          ), //input')
    print_line.append('    .dina                   (dina[DATA_WIDTH-1:0]           ), //input')
    #print_line.append('    .wea                    (wea                            ), //input')
    print_line.append('    .ena                    (wea                            ), //input')
    print_line.append('    .addrb                  (addrb[ADDR_WIDTH-1:0]          ), //input')
    print_line.append('    .enb                    (enb                            ), //input')
    print_line.append('    .light_sleep            (light_sleep                    ), //input')
    if 'ON' in str(power_gating):
        print_line.append('    .deep_sleep              (deep_sleep                     ), //input')
        print_line.append('    .shut_down               (shut_down                      ), //input')
        print_line.append('    .rop                     (rop                            ), //output')
    if 'ON' in str(bit_write) :
        print_line.append('    .wem                     (~' + str(width) + "'b0                     ), //input")
    print_line.append('    .clka                   (w_clk                          ),  //input')
    print_line.append('    .clkb                   (r_clk                          )  //input')
    print_line.append(');')

    for line in print_line:
        #print(line)
        fp.write(line)
        fp.write('\n')
    
    fp.write('\n')
    fp.write('endmodule')

    fp.close()
# }}}

#rom_model {{{

def rom_wrapper(sheet, depth, width, module_name, param,model_signal,signal_width,top_signal,in_out) :
    
    fp = open(module_name + "_wrap.v", "w")

    print_line = []
    add_header(print_line, "" + module_name+"_wrap.v")

    addr_width = str(math.ceil(math.log2(int(depth))))
    
    print_line.append('module ' + module_name +'_wrap (')
    print_line.append("\tinput      [31:0]\t\t\t\t"+ module_name +"_mem_ctrl,")
    print_line.append("\tinput          \t\t\t\t\tlight_sleep   \t,")
    print_line.append('\tinput          \t\t\t\t\tshut_down   \t,')
    print_line.append('\toutput     ['+str(int(width)-1)+':0]\t\t\t\tq              \t,')
    print_line.append('\tinput      ['+str(int(addr_width)-1)+':0]\t\t\t\taddr          \t,')
    print_line.append('\tinput            \t\t\t\tclk           \t,')
    print_line.append('\tinput            \t\t\t\tme')
    print_line.append(');\n\n')
    
    print_line.append('`ifdef NO_ASIC_MEM\n') 
    print_line.append('\tsrom_regfile ')
    print_line.append('\t#(')
    print_line.append('\t\t.PreloadFilename        ("/project/sky/tsmc22_lib/rom_bin_file/'+ module_name +'.bin"                ),')
    print_line.append('\t\t.DATA_DEPTH             ('+str(int(depth))+'                     \t),')
    print_line.append('\t\t.DATA_WIDTH             ('+str(int(width))+'                     \t),')
    print_line.append('\t\t.ADDR_WIDTH             ('+str(int(addr_width))+'                        \t) ')
    print_line.append('\t)')
    print_line.append('\tu_'+module_name+'_reg  (')
    print_line.append('\t\t.Q                      (q['+str(int(width-1))+':0]              \t\t), //output')
    print_line.append('\t\t.ADR                    (addr['+str(int(addr_width)-1)+':0]            \t\t), //input')
    print_line.append('\t\t.ME                     (me                   \t\t), //input')
    print_line.append('\t\t.CLK                    (clk                  \t\t)  //input')
    print_line.append('\t);')
   
    print_line.append('\n\n`else\n')       
    
    print_line.append('\twire       [' + str(int(addr_width)-1)+ ":0]       \tTA        \t;")
    print_line.append('\twire       [' + str(int(width)-1)+ ":0]        \tTQ        \t;")
    print_line.append('\twire       [31:0]          \tmem_ctrl \t;\n')

    print_line.append('\tassign     TA[' + str(int(addr_width)-1)+ ":0] \t\t= \t" + str(int(addr_width))+ "'b0 ;")
    print_line.append('\tassign     TQ[' + str(int(width)-1)     + ":0] \t\t= \t" + str(int(width))+ "'b0 ;")


    print_line.append('\tassign     mem_ctrl[31:0] \t= \t' + module_name + '_mem_ctrl;\n\n') 

    print_line.append('\t' + str(module_name) + ' u_' + str(module_name) + '_lib(')
    
    length = len(param)
    for i in range(length) :
        if i == (length-1) :
            last = 1
        else :
            last = 0
        
        print_line.append(print_verilog(str(model_signal[i]),str(signal_width[i]),str(top_signal[i]),str(int(width)-1),str(int(addr_width)-1),in_out[i],last))
    
    print_line.append('\t);\n')
    print_line.append('`endif\n')
    

    for line in print_line :
            #print(line)
            fp.write(line)
            fp.write('\n')

    fp.write('\n')
    fp.write('endmodule')

    fp.close()

# }}}

# mem model index{{{

def CHECK_MUX_BANK(mem_type, word, bits, mux, bank) :



    if mem_type == '1_1' :

        if word % 32 == 0 and 256 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 128 and mux == 8 and bank == 1 :
            mem_code = 'TS83CF000'
        elif word % 64 == 0 and 512 <= word <= 16384 and bits % 1 == 0 and 4 <= bits <= 64 and mux == 16 and bank == 1 :
            mem_code = 'TS83CF000'
        elif word % 128 == 0 and 1024 <= word <= 32768 and bits % 1 == 0 and 4 <= bits <= 32 and mux == 32 and bank == 1 :
            mem_code = 'TS83CF000'
        else :
            print('word and bit info'.center(100, '-'))
            print('word: ' + str(word) + ' | bits: ' + str(bits) + ' | mux: ' + str(mux) + ' | bank: ' + str(bank))
            raise ValueError('The entered word, bits, mux and bank do not meet the requirements')

    elif mem_type == '2_2' :

        if word % 4 == 0 and 16 <= word <= 512 and bits % 2 == 0 and 4 <= bits <= 160 and mux == 2 and bank == 1 :
            mem_code = 'TS83CD001'
        elif word % 8 == 0 and 64 <= word <= 1024 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 4 and bank == 1 :
            mem_code = 'TS83CD001'
        elif word % 16 == 0 and 128 <= word <= 2048 and bits % 1 == 0 and 4 <= bits <= 40 and mux == 8 and bank == 1 :
            mem_code = 'TS83CD001'
        else :
            print('word and bit info'.center(100, '-'))
            print('word: ' + str(word) + ' | bits: ' + str(bits) + ' | mux: ' + str(mux) + ' | bank: ' + str(bank))
            raise ValueError('The entered word, bits, mux and bank do not meet the requirements')

    elif mem_type == '3_1' :

        if word % 32 == 0 and 512 <= word <= 2048 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 4 and bank == 2 :
            mem_code = 'TS83CA001'
        elif word % 64 == 0 and 1024 <= word <= 4096 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 4 and bank == 4 :
            mem_code = 'TS83CA001'
        elif word % 128 == 0 and 2048 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 4 and bank == 8 :
            mem_code = 'TS83CA001'
        elif word % 64 == 0 and 1024 <= word <= 4096 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 8 and bank == 2 :
            mem_code = 'TS83CA001'
        elif word % 128 == 0 and 2048 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 8 and bank == 4 :
            mem_code = 'TS83CA001'
        elif word % 256 == 0 and 4096 <= word <= 16384 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 8 and bank == 8 :
            mem_code = 'TS83CA001'
        elif word % 128 == 0 and 2048 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 16 and bank == 2 :
            mem_code = 'TS83CA001'
        elif word % 256 == 0 and 4096 <= word <= 16384 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 16 and bank == 4 :
            mem_code = 'TS83CA001'
        elif word % 512 == 0 and 8192 <= word <= 32768 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 16 and bank == 8 :
            mem_code = 'TS83CA001'
        else :
            print('word and bit info'.center(100, '-'))
            print('word: ' + str(word) + ' | bits: ' + str(bits) + ' | mux: ' + str(mux) + ' | bank: ' + str(bank))
            raise ValueError('The entered word, bits, mux and bank do not meet the requirements')

    elif mem_type == '3_2' :

        if word % 32 == 0 and 512 <= word <= 2048 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 4 and bank == 2 :
            mem_code = 'TS83CA003'
        elif word % 64 == 0 and 1024 <= word <= 4096 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 4 and bank == 4 :
            mem_code = 'TS83CA003'
        elif word % 128 == 0 and 2048 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 4 and bank == 8 :
            mem_code = 'TS83CA003'
        elif word % 64 == 0 and 1024 <= word <= 4096 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 8 and bank == 2 :
            mem_code = 'TS83CA003'
        elif word % 128 == 0 and 2048 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 8 and bank == 4 :
            mem_code = 'TS83CA003'
        elif word % 256 == 0 and 4096 <= word <= 16384 and bits % 1 == 0 and 4 <= bits <= 160 and mux == 8 and bank == 8 :
            mem_code = 'TS83CA003'
        elif word % 128 == 0 and 2048 <= word <= 8192 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 16 and bank == 2 :
            mem_code = 'TS83CA003'
        elif word % 256 == 0 and 4096 <= word <= 16384 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 16 and bank == 4 :
            mem_code = 'TS83CA003'
        elif word % 512 == 0 and 8192 <= word <= 32768 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 16 and bank == 8 :
            mem_code = 'TS83CA003'
        else :
            print('word and bit info'.center(100, '-'))
            print('word: ' + str(word) + ' | bits: ' + str(bits) + ' | mux: ' + str(mux) + ' | bank: ' + str(bank))
            raise ValueError('The entered word, bits, mux and bank do not meet the requirements')

    elif mem_type == '5_2' :

        if word % 4 == 0 and 32 <= word <= 256 and bits % 1 == 0 and 6 <= bits <= 160 and mux == 2 and bank == 2 :
            mem_code = 'TS83CC000'
        elif word % 4 == 0 and 132 <= word <= 512 and bits % 1 == 0 and 6 <= bits <= 160 and mux == 2 and bank == 4 :
            mem_code = 'TS83CC000'
        elif word % 4 == 0 and 260 <= word <= 1024 and bits % 1 == 0 and 6 <= bits <= 160 and mux == 2 and bank == 8  :
            mem_code = 'TS83CC000'
        elif word % 4 == 0 and 516 <= word <= 1024 and bits % 1 == 0 and 6 <= bits <= 160 and mux == 2 and bank == 16 :
            mem_code = 'TS83CC000'
        elif word % 8 == 0 and 64 <= word <= 512 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 4 and bank == 2 :
            mem_code = 'TS83CC000'
        elif word % 8 == 0 and 264 <= word <= 1024 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 4 and bank == 4 :
            mem_code = 'TS83CC000'
        elif word % 8 == 0 and 520 <= word <= 2048 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 4 and bank == 8 :
            mem_code = 'TS83CC000'
        elif word % 8 == 0 and 1032 <= word <= 2048 and bits % 1 == 0 and 4 <= bits <= 80 and mux == 4 and bank == 16 :
            mem_code = 'TS83CC000'
        elif word % 16 == 0 and 128 <= word <= 1024 and bits % 1 == 0 and 4 <= bits <= 40 and mux == 8 and bank == 2 :
            mem_code = 'TS83CC000'
        elif word % 16 == 0 and 528 <= word <= 2048 and bits % 1 == 0 and 4 <= bits <= 40 and mux == 8 and bank == 4 :
            mem_code = 'TS83CC000'
        elif word % 16 == 0 and 1040 <= word <= 4096 and bits % 1 == 0 and 4 <= bits <= 40 and mux == 8 and bank == 8 :
            mem_code = 'TS83CC000'
        elif word % 16 == 0 and 2064 <= word <= 4096 and bits % 1 == 0 and 4 <= bits <= 40 and mux == 8 and bank == 16 :
            mem_code = 'TS83CC000'
        else :
            print('word and bit info'.center(100, '-'))
            print('word: ' + str(word) + ' | bits: ' + str(bits) + ' | mux: ' + str(mux) + ' | bank: ' + str(bank))
            raise ValueError('The entered word, bits, mux and bank do not meet the requirements')

    else :
        print('word and bit info'.center(100, '-'))
        print('word: ' + str(word) + ' | bits: ' + str(bits) + ' | mux: ' + str(mux) + ' | bank: ' + str(bank))
        raise ValueError('The suggested device column is filled with incorrect values')
        
    return mem_code

# }}}

# add_header {{{
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
    print_line.append("// Author        :  wuming,ninghechuan")
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
    print_line.append("// "+date1+"    wuming          1.0                     Original")
    print_line.append("// -FHDR----------------------------------------------------------------------------")

# }}}


def help():
    print("############## help ####################")
    print("########################################")
    print("python3 gen_mem_wrap.py excel_path sheet_name")
    print("########################################")


if __name__ == "__main__":
    main()
