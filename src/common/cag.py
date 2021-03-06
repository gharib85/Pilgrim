#!/usr/bin/python2.7
'''
---------------------------
 Licensing and Distribution
---------------------------

Program name: Pilgrim
Version     : 1.0
License     : MIT/x11

Copyright (c) 2019, David Ferro Costas (david.ferro@usc.es) and
Antonio Fernandez Ramos (qf.ramos@usc.es)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
---------------------------

*----------------------------------*
| Package    :  common             |
| Module     :  cag                |
| Last Update:  2019/04/03 (Y/M/D) |
| Main Author:  David Ferro-Costas |
*----------------------------------*

This module contains the function
for the calculation of the CAG
correction factor
''' 

#===================================#
from physcons import KB
import numpy as np
#===================================#


#===================================#
def calc_cag(ltemp,VadiSpl,lscvt=None):
    # calculate dE
    sAG, VAG =  VadiSpl.get_max()
    if lscvt is None: Ediff = [VAG-VadiSpl(0.0) for T   in ltemp]
    else            : Ediff = [VAG-VadiSpl(s_i) for s_i in lscvt]
    # get cag
    cag = [np.exp(-dE/KB/T) for T,dE in zip(ltemp,Ediff)]
    return Ediff , cag
#===================================#


