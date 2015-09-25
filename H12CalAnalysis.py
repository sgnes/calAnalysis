__author__ = 'DZMP8F'
import sys
import os
import re

class link_file(object):
    def __init__(self, file_name):
        self.__link_file_name = file_name
    def get_bank_obj_info(self):
        link_file = open(self.__link_file_name)
        self.bank_obj_dict = {}
        self.obj_bank_dict = {}
        if link_file:
            text = link_file.read()
            all_matchs = re.findall(r"# Program flash page\s([A-Z0-9a-z]{2})\s(.*?[A-Z0-9a-z_]{2,40}.o.*?)##########################",text,re.S)
            for mat in all_matchs:
                bank_name = int(mat[0],16)-208
                objs_in_bank_list = re.findall(r"\n([A-Z0-9a-z_]{2,40}.o)",mat[1])
                if bank_name in self.bank_obj_dict:
                    self.bank_obj_dict[bank_name] = self.bank_obj_dict[bank_name] + objs_in_bank_list
                else:
                    self.bank_obj_dict[bank_name] = objs_in_bank_list
            for i in self.bank_obj_dict:
                for obj in self.bank_obj_dict[i]:
                    self.obj_bank_dict[obj] = i


shard_cal_begin_add = 0x7fc000
ppage_beginadd = 0x740000
pgl = range(0x740000,0x7fffff,0x4000)
log_begin = "-------------------------------------------------\n"

if len(sys.argv) == 3:

    link_obj = link_file(sys.argv[2])
    link_obj.get_bank_obj_info()
    bank_obj_dict = link_obj.bank_obj_dict
    objs_dict = link_obj.obj_bank_dict
    map_file = open(sys.argv[1])
    #cal_name_re = re.compile(r"_(\w*)\s*([a-z0-9A-Z]{8})\s*defined\s*in\s*\w*.o\s*section\s*")
    obj_re = re.compile(r"^(.*.[oO]):\sstart\s+[a-z0-9A-Z*]{8}")
    wheat_list = ['.bss','.SHARED_CONST']
    no_match_list = []
    useless_list = []

    corss_bank_cal_list = []
    cal_add_ok_list = []
    cal_dict = {}
    shard_cal_list = []
    cal_not_found_list = []
    used_obj_not_found_list = []
    cal_name_error_list = []
    obj_used_cal_dict = {}
    obj_size_dict = {}
    bank_used_dict = {}
    if map_file:
        map_text = map_file.read()
        map_txt_re = re.sub(r"\n\s\s\s\s\s+", "  ",map_text)
        map_txt_re = re.sub(r"\nstart\s+", " start  ",map_txt_re)
        map_file_re = open("temp.map","w")
        map_file_re.write(map_txt_re)
        map_file_re.close()
        map_file.close()
        map_file_re = open("temp.map")
        for line in map_file_re:
            if line.startswith("_K") or line.startswith("_k"):
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
                    m = re.findall(r"start\s+([a-zA-Z0-9]{8})\s+end\s+([a-zA-Z0-9]{8})\s+length\s+([a-zA-Z0-9]{1,8})\ssection\s+\.",line)
                    if m:
                        objsize = 0
                        for i in m:
                            beginadd = int(i[0],16)
                            usedsize = int(i[2])
                            if beginadd >= ppage_beginadd and beginadd < shard_cal_begin_add:
                                page_num = (beginadd -ppage_beginadd )/16384
                                if obj_name in objs_dict and objs_dict[obj_name] == page_num:
                                    objsize = objsize + usedsize
                                if page_num in bank_used_dict:
                                    bank_used_dict[page_num] = bank_used_dict[page_num] + usedsize
                                else:
                                    bank_used_dict[page_num] = usedsize
                        obj_size_dict[obj_name] = objsize
                    else:
                        obj_size_dict[obj_name] = 0
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
        for obj in objs_dict:
            list_tmp = []
            for cal in cal_dict:
                if obj in cal_dict[cal][1]:
                     list_tmp.append(cal)
            obj_used_cal_dict[obj] = list_tmp
        for bank in bank_obj_dict:
            bank_used_size = 0
            for obj in bank_obj_dict[bank]:
               bank_used_size = bank_used_size + obj_size_dict[obj]
            #bank_used_pre_dict[bank] = bank_used_size/16384.0
        for i in bank_used_dict:
            print("Total page {:x} size is  16384 bytes,   used size:  {:d} bytes, {:.2f}%".format(i+0xd0,int(bank_used_dict[i]),(bank_used_dict[i]/16384.0)*100 ))
        #print (bank_used_pre_dict)
        obj_size_dict_sorted = sorted(obj_size_dict.iteritems(), key=lambda d:d[0])
        for i in obj_size_dict_sorted:
            print("{0} : {1}".format(i[0],i[1]))
        #print (obj_size_dict)
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
        all_file.write("obj used calibrations:\n")
        all_file.write(log_begin)
        for i in obj_used_cal_dict:
            all_file.write("{0} : {1}\n".format(i, obj_used_cal_dict[i]))
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
