#!/usr/bin/python2.7
'''
*-----------------------------------*
| Module name:  mpilgrim.opt_ics    |
| Last Update:  2019/01/21 (Y/M/D)  |
| Main Author:  David Ferro-Costas  |
*-----------------------------------*
'''

#--------------------------------------------------#
import time
import os
import sys
#--------------------------------------------------#
import names    as     PN
import rdwr     as     RW
#--------------------------------------------------#
from   common.files    import read_gtsfile
#--------------------------------------------------#
from   common.fncs     import print_string
from   common.fncs     import same_freqs
#--------------------------------------------------#
from   common.internal import count_ics
from   common.internal import ics_depure
from   common.internal import ics_from_gts
from   common.internal import nonredundant_gtsfiles
#--------------------------------------------------#
from   common.Molecule import Molecule
#--------------------------------------------------#
from   common.physcons import AMU
#--------------------------------------------------#
from   diverse         import ffchecking
from   diverse         import get_input_data
from   diverse         import status_check
#--------------------------------------------------#


#---------------------------------------------------------------#
def check_ics_gtsfile(gtsfile,ics):
    # number of internal coordinates
    nics = count_ics(ics)
    # read gts and prepare Molecule
    molecule = Molecule()
    molecule.set_from_gts(gtsfile)
    molecule.setup()
    # number of vibrational degrees of freedom
    nvdof = len(molecule._ccfreqs)
    # enough internal coordinates
    if nics < nvdof: return False, nvdof
    # calc ic-freqs
    molecule.icfreqs(ics)
    # comparison
    valid = same_freqs(molecule._ccfreqs,molecule._icfreqs)
    return valid, nvdof
#---------------------------------------------------------------#
def string_nics(nics,nvdof,valid):
    string = "number(ics,vib.DOF) = (%i,%i)"%(nics,nvdof)
    if valid: string += "; VALID"
    else    : string += "; NOT VALID"
    return string
#---------------------------------------------------------------#
def check_ics(ics,gtsfiles):
    # counting
    nics = count_ics(ics)
    # checking
    valid = True
    for gts in gtsfiles:
        valid, nvdof = check_ics_gtsfile(gts,ics)
        if not valid: break
    # return
    return valid, nvdof, nics
#---------------------------------------------------------------#
def mode1(gtsfiles):
    '''
    generate massive set of internal coordinates
    '''
    if len(gtsfiles) == 0: return [], 0
    for gts in gtsfiles:
        ics = ics_from_gts(gts)
        valid,nvdof,nics = check_ics(ics,gtsfiles)
        if valid: return ics,nvdof
    return [], nvdof
#---------------------------------------------------------------#
def mode2(gtsfiles,ics=[]):
    # mode 1
    if len(ics)==0:
       ics, nvdof = mode1(gtsfiles)
       if len(ics)==0: return [],nvdof
    else:
       valid,nvdof,nics = check_ics(ics,gtsfiles)
       if not valid: return ics,nvdof
    # mode 2
    ics2 = ics_depure(ics)
    # check them
    valid,nvdof2,nics2 = check_ics(ics2,gtsfiles)
    if valid: return ics2,nvdof2
    else    : return ics ,nvdof
#---------------------------------------------------------------#
def mode3(gtsfiles,ics=[]):
    # mode 2
    ics, nvdof  = mode2(gtsfiles,ics)
    nics        = count_ics(ics)
    # mode 3
    if nics > nvdof:
       ics2, valid = nonredundant_gtsfiles(gtsfiles,ics)
       if valid: return ics2,nvdof
    return ics,nvdof
#---------------------------------------------------------------#


#===============================================================#
def main(idata,status,mode=2,target="*"):

    stat2check = [1]
    mustexist  = []
    tocreate   = []

    #-------------------------------------------------------#
    # Read Pilgrim input files and check file/folder status #
    #-------------------------------------------------------#
    # expand data
    (dctc,dimasses), ltemp, dpath, dtes, dchem, tkmc, ddlevel = idata
    # status ok?
    fstatus = status_check(status,stat2check)
    if fstatus == -1: exit()
    # existency of folders
    fstatus = ffchecking(mustexist,tocreate)
    if fstatus == -1: exit()
    #-------------------------------------------------------#

    #----------------#
    # deal with mode #
    #----------------#
    msg = {}
    msg["-1"] = "ics will be removed"
    msg["-2"] = "ics will be checked"
    msg[ "1"] = "ics will be generated according to connectivity"
    msg[ "2"] = "ics will be generated according to connectivity\n"+\
                "and reduced"
    msg[ "3"] = "ics will be generated according to connectivity\n"+\
                "and reduced to a non-redundant set"
    print "   Selected mode is '%s'"%mode
    if mode not in ["-2","-1","1","2","3"]:
       print "    - Unknown mode!"
       print
       return
    for idx,line in enumerate(msg[mode].split("\n")):
        if idx == 0: print "    - "+line
        else       : print "      "+line
    print

    #------------------#
    # deal with target #
    #------------------#
    print "   Selected target is '%s'"%target
    systems = []
    if target == "*": targets = [key for key in dctc.keys() if dctc[key]._type==1]
    else            : targets = [target]
    for target in sorted(targets):
        systems_i = []
        if "." in target: ctc,itc = target.split(".")
        else            : ctc,itc = target, None
        if ctc not in dctc.keys():
           print "    - %s is NOT defined in '%s'\n"%(ctc,PN.IFILE1)
           return
        # itcs in dctc
        dctc_itcs = [itc_i for itc_i,weight_i in dctc[ctc]._itcs]
        # the itcs
        if   itc is      None: itcs = dctc_itcs
        elif itc in dctc_itcs: itcs = [itc]
        else:
            print "    - %s is NOT defined in '%s'\n"%(itc,PN.IFILE1)
            return
        # specific itcs
        if "." in target:
           systems_i.append( ([itc],itc) )
        else:
           dics  = dctc[ctc]._dics
           itcsB = [itc for itc in dics.keys() if itc != "*"]
           itcsA = [itc for itc in itcs        if itc not in itcsB]
           # add data
           if itcsA != []: systems_i.append( (itcsA,"*") )
           for itc in sorted(itcsB): systems_i.append( ([itc],itc) )
        # add data to total
        systems.append( (ctc,systems_i) )
    print

    # print name of file to modify
    print "   File to be updated: '%s'"%PN.IFILE1
    print

    #--------------#
    # Generate ics #
    #--------------#
    NEPL = 10
    NOTVALID = [] # updated via global variable
    for ctc,systems_i in systems:
        # Print
        print "   -------------------"
        print "   System: %s"%ctc
        print "   -------------------"
        print
        for itcs,key in systems_i:
            # print conformers
            string = ""
            for idx in range(0,len(itcs),NEPL):
                str_i = ",".join(itcs[idx:idx+NEPL])
                if idx == 0: string +=       "     conformer(s): "+str_i
                else       : string += ",\n"+"                   "+str_i
            print string
            print
            # gts files
            gtsfiles = [dctc[ctc].gtsfile(itc) for itc in itcs]
            # set of ics
            ics  = dctc[ctc]._dics.get(key,[])
            # negative modes
            if mode == "-2":
               nics = count_ics(ics)
               print "         * %i ics will be removed"%nics
               print
               dctc[ctc]._dics[key] = []
               continue
            if mode == "-1":
               valid,nvdof,nics = check_ics(ics,gtsfiles)
               print "         * "+string_nics(nics,nvdof,valid)
               print
               continue
            # ics already in file?
            if len(ics) != 0:
               valid,nvdof,nics = check_ics(ics,gtsfiles)
               print "         * ics found!"
               print "           "+string_nics(nics,nvdof,valid)
               if not valid:
                  question = "           remove set and generate new one (y/N)? "
                  answer = raw_input(question).strip().lower()
                  if answer in ["y","yes"]: ics = []
                  else                    : print; continue
               print 
            else:
               nvdof = None
            # is algorithm needed?
            nics = count_ics(ics)
            if nics != nvdof:
               # positive modes
               print "         * applying algorithm..."
               if mode == "1" and len(ics) == 0:
                  ics,nvdof = mode1(gtsfiles)
               if mode == "2":
                  ics,nvdof = mode2(gtsfiles,ics)
               if mode == "3":
                  ics,nvdof = mode3(gtsfiles,ics)
               # check final set after positive modes
               if len(ics) == 0:
                  print "           algorithm failed!"
                  print
                  NOTVALID.append( (ctc,itcs) )
                  continue
               valid,nvdof,nics = check_ics(ics,gtsfiles)
               print "           "+string_nics(nics,nvdof,valid)
               print
               # update dictionary and rewrite
               dctc[ctc]._dics[key] = ics
               RW.write_ctc(dctc,dimasses)
            else:
               print "         * number(ics) = (vib.DOF); skypping..."
               print
        print "   -------------------"
        print
        print

    # any fail?
    if len(NOTVALID) != 0:
        print "   The algorithm failed for:"
        for ctc,itcs in NOTVALID:
            # print conformers
            string = ""
            for idx in range(0,len(itcs),NEPL):
                str_i = ",".join(itcs[idx:idx+NEPL])
                if idx == 0: string +=       "       * %s: "%ctc           +str_i
                else       : string += ",\n"+"         %s  "%(" "*len(ctc))+str_i
            print string
        print

    # rewrite again (for mode = -2)
    RW.write_ctc(dctc,dimasses)
#===============================================================#

