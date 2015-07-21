#! C:\python27\python
import sys


def parsemapfile(argv):
    symbol_found = 0
    symbol_list = []
    obj_dict = {}
    par = []
    mapfile = open(argv)
    line = mapfile.readline()
    black_list = [ '.bss','(.text)', '(.const)','.nvram','.nvram_crit', '.ram_boot','.ram_f4', '.shared_data', \
                   '.kw2_buffer','.nvram_versn', '***', '.pagefe' , 'initialized', '.can_buffer', '.nvram_chsum'\
                    '.pagedc','.crit_chsum', '.nvram_map','.nvram_mfg', '.mfg_map', '.CONST_FLSD','.SW_NAME',\
                   '.boot_version','.UNPAGE_CODE','.init','.pattern']
    while(line):
        if(symbol_found):
            #new symbol line should started with _K
            if not line.startswith(" "):
                smbs = line.split()
                black_found = 0
                for i in black_list:
                    if i in smbs:
                        black_found = 1
                        break
                #only analysis the addrss after 0x740000
                #a symbol record is like bellow:
                #_KtICFC_p_AXIS_GainFactorMAP                             00768006   defined in icfccald.o section .CAL_ICFC
                #                                                                     used in icfcmmod.o
                #_K*****
                if len(smbs) >= 7 and  black_found == 0 and smbs[1].startswith('007'):
                    while(True):
                        par.append(line)
                        line = mapfile.readline()
                        if not line.startswith("   "):
                            break
                    symbol_list.append(parse_new_symbl(par))
                    par = []
                else:
                    line = mapfile.readline()
            else:
                line = mapfile.readline()
        #elif line.lower().endswith(".o:\n"):
        elif ".o:" in line.lower():
              objname = line.split(":")[0]
              while(True):
                 line = mapfile.readline()
                 s1 = line.split()
                 if "start" in s1 and "(.text)" in s1:
                     pg = s1[len(s1) - 2]
                     if len(objname) < 80:
                         pgn = pg[len(pg)-2:len(pg)]
                         if('D'<=pgn[0].upper()<='F' and '0'<=pgn[1].upper()<='F'):
                             obj_dict[objname] = int(pgn,16)-208
                     else:
                         pass
                     break
                 elif line.startswith('\n'):
                     break
        else:
            if "Symbols" in line:
                symbol_found = 1
            line = mapfile.readline()
    #print (obj_dict)
    generate_report(symbol_list, obj_dict)
        #line = mapfile.readline()

def parse_new_symbl(par):
    usedlist = []
    symbol_name = ""
    addr = ""
    definedin = ""
    sections = ""
    for i in par:
        s1 = i.split()
        if i.startswith("_"):
            symbol_name = s1[0]
            addr = s1[1]
            definedin = s1[4]
            sections = s1[6]
        elif "used in" in i:
            usedlist.append(s1[2])
        elif (".o" in i):
            usedlist.append(s1[0])
    return [symbol_name,addr, definedin,sections,usedlist]

    pass

def generate_report(symbol_list, obj_dict):
    pgl = range(0x740000,0x7fffff,0x4000)
    calnoklist = []
    calnouselist = []
    #print (symbol_list)
    #print (obj_dict)
    #['_KtSPRK_phi_BaseIdleEthOfst', '0075c000', 'sprkcald.o', '.CAL_SPRK2', ['sprkfuel.o']]
    for sym in symbol_list:
        errorfound = 0
        usedlist = sym[len(sym)-1]
        caladd = sym[1]
        calsec = sym[3]
        for objs in usedlist:
            if objs in obj_dict:
                objadd = obj_dict[objs]
                try:
                    if not pgl[objadd] <= int(caladd,16) < pgl[objadd+1] and calsec != '.SHARED_CONST'\
                    and '.SHARED_CAL' != calsec and 'section' != calsec:
                        errorfound = 1
                        break
                except ValueError as e:
                    print (e,"   ", sym)
        if errorfound == 1:
            calnoklist.append(sym)
        if len(usedlist) == 0:
            calnouselist.append(sym)
    #print calnoklist
    print("----------------------------------------------------------")
    print("calibrations location error:")
    print("----------------------------------------------------------")
    for i in calnoklist:
        print (i)
    print("----------------------------------------------------------")
    print("----------------------------------------------------------")
    print("calibrations not used:")
    print("----------------------------------------------------------")
    for i in calnouselist:
        print (i)
    print("----------------------------------------------------------")
    pass

if len(sys.argv) == 1:
    print("Usage:calAnalysis filename.map")
    fn = raw_input("Input map file name:\r\n")
elif(len(sys.argv) == 2):
    fn = sys.argv[1]


parsemapfile(fn)
