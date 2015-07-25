__author__ = 'DZMP8F'
import sys
import os
import re

shard_cal_begin_add = 0x7fc000
pgl = range(0x740000,0x7fffff,0x4000)
log_begin = "-------------------------------------------------\n"

if len(sys.argv) == 2:

    map_file = open(sys.argv[1])
    #cal_name_re = re.compile(r"_(\w*)\s*([a-z0-9A-Z]{8})\s*defined\s*in\s*\w*.o\s*section\s*")
    obj_re = re.compile(r"(^\w+.[oO]):.*.page([a-zA-Z0-9]{2})")
    wheat_list = ['.bss','.SHARED_CONST']
    no_match_list = []
    useless_list = []
    objs_dict = {}
    corss_bank_cal_list = []
    cal_add_ok_list = []
    cal_dict = {}
    shard_cal_list = []
    cal_not_found_list = []
    used_obj_not_found_list = []
    cal_name_error_list = []
    if map_file:
        map_text = map_file.read()
        map_txt_re = re.sub(r"\n\s\s\s\s\s+", "  ",map_text)
        map_txt_re = re.sub(r"\nstart", " start ",map_txt_re)
        map_file_re = open("temp.map","w")
        map_file_re.write(map_txt_re)
        map_file_re.close()
        map_file.close()
        map_file_re = open("temp.map")
        for line in map_file_re:
            if line.startswith("_K"):
                s1 = line.split("used in")
                if len(s1) == 2:
                    s2 = s1[0].split()
                    cal_name = s2[0]
                    cal_add = s2[1]
                    cal_section = ""
                    if "section" in line:
                        cal_section = s2[s2.index("section")+1]
                        #print("section:{}  calname:{}  ".format(cal_section, line))
                    used_obj_list = s1[1].split()
                    #print("calname:", cal_name, "   add:" , cal_add, " usedobj:", used_obj_list)
                    cal_dict[cal_name[1:]] = ((cal_add, cal_section), used_obj_list)
            elif ".o:" in line.lower():
                m = obj_re.match(line)
                if m:
                    #print m.groups()
                    obj_name = m.groups()[0]
                    pgn = m.groups()[1]
                    if('D'<=pgn[0].upper()<='F' and '0'<=pgn[1].upper()<='F'):
                        objs_dict[obj_name] = int(pgn,16)-208

                else:
                    ## re not match
                    #print("re not match:", line)
                    no_match_list.append(line)
            else:
                #print("useless:", line)
                useless_list.append(line)
        map_file_re.close()
        for cal in cal_dict:
            #if cal in objs_dict:
            if 1:
                cal_add = int(cal_dict[cal][0][0],16)
                cal_section = cal_dict[cal][0][1]
                if not cal_section.startswith(".CAL") and not cal_section.startswith('.SHARED_CAL'):
                    cal_name_error_list.append((cal,cal_dict[cal]))
                if cal_add >= shard_cal_begin_add:
                    #shard cal loacate in page ff
                    #can be accessed in all page mode
                    shard_cal_list.append((cal,cal_dict[cal]))
                elif cal_section in wheat_list:
                    pass
                else:
                    cal_used_list = cal_dict[cal][1]
                    error_found = 0
                    for obj in cal_used_list:
                        if obj in objs_dict:
                            obj_pg = objs_dict[obj]
                            if not pgl[obj_pg] <= cal_add < pgl[obj_pg+1]:
                                error_found = 1
                        else:
                            if obj not in used_obj_not_found_list:
                                used_obj_not_found_list.append(obj)
                    if error_found:
                        corss_bank_cal_list.append((cal,cal_dict[cal]))
                    else:
                        cal_add_ok_list.append((cal,cal_dict[cal]))

            else:
                cal_not_found_list.append(cal)

        error_file = open("error_information_map.log","w")
        error_file.write(log_begin)
        error_file.write("calibrations cross banks:\n")
        error_file.write(log_begin)
        for i in corss_bank_cal_list:
            error_file.write("{}\n".format(i))
        error_file.write(log_begin)
        error_file.write("calibrations with bad section names:\n")
        for i in cal_name_error_list:
            error_file.write("{}\n".format(i))
        error_file.write(log_begin)
        all_file = open("all_information_map.log","w")
        all_file.write(log_begin)
        all_file.write("calibrations location without problem:\n")
        all_file.write(log_begin)
        for i in cal_add_ok_list:
            all_file.write("{}\n".format(i))
        all_file.write(log_begin)
        all_file.write("all founded calibrations:\n")
        all_file.write(log_begin)
        for i in cal_dict:
            all_file.write("{0}{1}\n".format(i, cal_dict[i]))
        all_file.write(log_begin)
        all_file.write("all founded objs:\n")
        all_file.write(log_begin)
        for i in objs_dict:
            all_file.write("{}:{}\n".format(i,objs_dict[i]))
        all_file.write(log_begin)
        all_file.write("useless text:\n")
        all_file.write(log_begin)
        for i in useless_list:
                all_file.write("{}\n".format(i))
        error_file.write(log_begin)
        error_file.write("Those objs are used cals but not found their location:\n")
        error_file.write(log_begin)
        for i in used_obj_not_found_list:
            error_file.write("{}\n".format(i))
        error_file.write(log_begin)
        error_file.write("re not match:\n")
        error_file.write(log_begin)
        for i in no_match_list:
            error_file.write("{}\n".format(i))
        error_file.write(log_begin)
        error_file.close()
        all_file.close()
else:
    print("Usage:")
    print("      H12CalAnalysis *.map")