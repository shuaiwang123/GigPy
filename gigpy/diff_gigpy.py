#! /usr/bin/env python
#################################################################
###  This program is part of GigPy  v1.0                      ### 
###  Copy Right (c): 2019, Yunmeng Cao                        ###  
###  Author: Yunmeng Cao                                      ###                                                          
###  Email : ymcmrs@gmail.com                                 ###
###  Univ. : King Abdullah University of Science & Technology ###   
#################################################################

import sys
import os
import re
import subprocess
import argparse
import numpy as np
import h5py



def read_hdf5(fname, datasetName=None, box=None):
    # read hdf5
    with h5py.File(fname, 'r') as f:
        data = f[datasetName][:]
        atr = dict(f.attrs)
        
    return data, atr

def read_attr(fname):
    # read hdf5
    with h5py.File(fname, 'r') as f:
        atr = dict(f.attrs)
        
    return atr


def write_h5(datasetDict, out_file, metadata=None, ref_file=None, compression=None):
    
    if os.path.isfile(out_file):
        print('delete exsited file: {}'.format(out_file))
        os.remove(out_file)

    print('create HDF5 file: {} with w mode'.format(out_file))
    with h5py.File(out_file, 'w') as f:
        for dsName in datasetDict.keys():
            data = datasetDict[dsName]
            ds = f.create_dataset(dsName,
                              data=data,
                              compression=compression)
        
        for key, value in metadata.items():
            f.attrs[key] = str(value)
            #print(key + ': ' +  value)
    print('finished writing to {}'.format(out_file))
        
    return out_file

def get_dataNames(FILE):
    with h5py.File(FILE, 'r') as f:
        dataNames = []
        for k0 in f.keys():
            dataNames.append(k0)
    return dataNames
    
def cmdLineParse():
    parser = argparse.ArgumentParser(description='Calculate differences between two data sets',formatter_class=argparse.RawTextHelpFormatter,epilog=INTRODUCTION+'\n'+EXAMPLE)
    parser.add_argument('data1', help='the first data')
    parser.add_argument('data2',help='the second data')
    parser.add_argument('--type', dest='type', choices = {'turb','aps','hgt','trend','sigma'}, default = 'aps',help = 'type of the high-resolution tropospheric map.[default: aps]')
    parser.add_argument('--absolute', dest='absolute', action='store_true',help='Absolute (not relative) value in the space-time domain.')
    parser.add_argument('--add', dest='add', action='store_true',help='Add the two datasets')
    parser.add_argument('-o','--out', dest='out',help = 'Name of the output file.')
      
    inps = parser.parse_args()

    return inps


INTRODUCTION = '''
##################################################################################
   Copy Right(c): 2019, Yunmeng Cao   @GigPy v1.0
   
   Calculate differences/accumulation between two gigpy-based datasets.
'''

EXAMPLE = """Example:
  
  diff_gigpy.py 20190101_aps.h5 20190120_aps.h5 --data aps_sar 
  diff_gigpy.py timeseries_gps_aps.h5 timeseries_gps_turb.h5 -o difference_0101_0120_aps.h5
  diff_gigpy.py timeseries_gps_aps.h5 timeseries_gps_turb.h5 --absolute
  diff_gigpy.py 20190101_aps.h5 20190120_aps.h5 --data turb_sar 
  diff_gigpy.py timeseries.h5 timeseries_gps_aps.h5 -o timeseries_gpsCor.h5 --add
  
###################################################################################
"""

###############################################################

def main(argv):
    
    inps = cmdLineParse()
    file1 = inps.data1
    file2 = inps.data2
    meta = read_attr(file1)
    datasetNames = get_dataNames(file1)
    datasetDict = dict()
    
    if meta['FILE_TYPE'] == 'timeseries':
        data_type = 'timeseries'
        data1 = read_hdf5(file1, datasetName = 'timeseries')[0]
        data2 = read_hdf5(file2, datasetName = 'timeseries')[0]
        
        if not inps.absolute:
                    
            REF_X = int(meta['REF_X'])
            REF_Y = int(meta['REF_Y'])
            for i in range(data1.shape[0]):
                data1[i, :, :] -= data1[i, REF_Y,REF_X]
                data2[i, :, :] -= data2[i, REF_Y,REF_X]
            #data1 -= data1[:,REF_Y,REF_X]
            #data2 -= data2[:,REF_Y,REF_X]
            data1 -= data1[0,:,:]
            data2 -= data2[0,:,:]
            
            if inps.add: data = data1 + data2
            else: data = data1 - data2
        
        else:      
            
            if inps.add: data = data1 + data2
            else: data = data1 - data2
            
        for datasetName in datasetNames:
            datasetDict[datasetName] = read_hdf5(file1, datasetName = datasetName)[0]
        
        datasetDict['timeseries'] = data
            
    else:
        
        data_type = inps.data
        data1 = read_hdf5(file1, datasetName = inps.data)[0]
        data2 = read_hdf5(file2, datasetName = inps.data)[0]
        
        if not inps.absolute:
            REF_X = int(meta['REF_X'])
            REF_Y = int(meta['REF_Y'])
            
            data1 -= data1[REF_Y,REF_X]
            data2 -= data2[REF_Y,REF_X]
            if inps.add: data = data1 + data2
            else: data = data1 - data2
        else:
            if inps.add: data = data1 + data2
            else: data = data1 - data2
         
        datasetDict[data_type] = data
        
    if inps.out: OUT = inps.out
    else: OUT = 'diff_' + (os.path.basename(file1)).split('.')[0] + '_' + (os.path.basename(file1)).split('.')[0] + '.h5'
    write_h5(datasetDict, OUT, metadata=meta, ref_file=None, compression=None)
    print('Done.')   

    sys.exit(1)
    
###############################################################

if __name__ == '__main__':
    main(sys.argv[:])