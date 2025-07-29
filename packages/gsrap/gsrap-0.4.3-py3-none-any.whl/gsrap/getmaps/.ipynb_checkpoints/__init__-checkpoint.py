import shutil
import os


from .kdown import download_raw_txtfiles
from .kdown import create_dict_ko
from .kdown import create_dict_c
from .kdown import create_dict_r
from .kdown import create_dict_map
from .kdown import create_dict_md
from .kdown import create_idcollection_dict
from .kdown import create_summary_dict



def getmaps_command(args, logger):
    
    
    # adjust out folder path                      
    while args.outdir.endswith('/'):              
        args.outdir = args.outdir[:-1]
    os.makedirs(f'{args.outdir}/', exist_ok=True)
    

        
    logger.info(f"Respectfully retrieving metabolic information from KEGG. Raw data are being saved into '{args.outdir}/kdown/'. Be patient, could take a couple of days...")
    os.makedirs(f'{args.outdir}/kdown/', exist_ok=True)
    
    
    response = download_raw_txtfiles(logger, args.outdir , args.usecache)
    if response == 1: return 1

    response = create_dict_ko(logger, args.outdir )
    if type(response) == int: return 1
    else: dict_ko = response
    
    response = create_dict_c(logger, args.outdir )
    if type(response) == int: return 1
    else: dict_c = response
    
    response = create_dict_r(logger, args.outdir )
    if type(response) == int: return 1
    else: dict_r = response
    
    response = create_dict_map(logger, args.outdir )
    if type(response) == int: return 1
    else: dict_map = response
    
    response = create_dict_md(logger, args.outdir )
    if type(response) == int: return 1
    else: dict_md = response
    
    
    # create 'gsrap.maps':
    idcollection_dict = create_idcollection_dict(dict_ko, dict_c, dict_r)
    summary_dict = create_summary_dict(dict_c, dict_r, dict_map, dict_md)
    with open(f'{args.outdir}/gsrap.maps', 'wb') as wb_handler:
        pickle.dump({'idcollection_dict': idcollection_dict, 'summary_dict': summary_dict}, wb_handler)
    logger.info(f"'{args.outdir}/gsrap.maps' created!")
    
        
    # clean temporary files:
    if not args.keeptmp:
        shutil.rmtree(f'{args.outdir}/kdown', ignore_errors=True)
        logger.info(f"Temporary raw files deleted!")

    
    return 0