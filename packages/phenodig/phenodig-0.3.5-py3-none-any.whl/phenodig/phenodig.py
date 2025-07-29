import os
import glob
import io
import requests
import logging
import warnings
import statistics
import math
from pathlib import Path
from importlib import resources
import concurrent.futures as confu 

import numpy as np
import pandas as pnd
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator



from .preproc import *
from .wellfits import *
from .plotplates import *

        
        
def phenodig(args, logger): 
    
    
    # adjust out folder path
    while args.output.endswith('/'):
        args.output = args.output[:-1]
        
    # adjust cores:
    if args.cores == 0:
        args.cores = os.cpu_count()
        if args.cores == None: args.cores = 1
    
        
    strain_to_df = collect_raw_data(logger, args.cores, args.input, args.plates, args.replicates, args.discarding)
    if type(strain_to_df) == int: return 1


    strain_to_df = data_preprocessing(logger, args.cores, strain_to_df, args.output)
    if type(strain_to_df) == int: return 1


    strain_to_bestfit = curve_fitting(logger, args.cores, args.output, strain_to_df, args.thrauc, args.thrymax, args.thrr2, args.plotfits)
    if type(strain_to_bestfit) == int: return 1


    response = plot_plates_strain(logger, args.cores, args.output, strain_to_df, strain_to_bestfit, args.noynorm)
    if response==1: return 1
    
    
    response = plot_plates_compare(logger, args.cores, args.output, strain_to_df, strain_to_bestfit, args.noynorm)
    if response==1: return 1
        
    return 0