import os
import pickle


import cobra


from ..commons import log_metrics

from .tsiparser import get_db
from .tsiparser import introduce_metabolites
from .tsiparser import introduce_reactions
from .tsiparser import introduce_transporters
from .tsiparser import introduce_sinks_demands
from .tsiparser import introduce_biomass
from .tsiparser import translate_annotate_genes
from .tsiparser import set_up_groups
from .tsiparser import check_biosynthesis
from .tsiparser import check_completeness
from .tsiparser import show_contributions




def parsedb_command(args, logger):
    
    
    # adjust out folder path                      
    while args.outdir.endswith('/'):              
        args.outdir = args.outdir[:-1]
    os.makedirs(f'{args.outdir}/', exist_ok=True)
    
    
    # check and extract the required 'gsrap.maps' file
    if os.path.exists(f'{args.inmaps}') == False:
        logger.error(f"File 'gsrap.maps' not found at {args.inmaps}.")
        return 1
    try: 
        with open(f'{args.inmaps}', 'rb') as f:
            inmaps = pickle.load(f)  
    except: 
        logger.error(f"Provided file {args.inmaps} has an incorrect format.")
        return 1
    idcollection_dict = inmaps['idcollection_dict']
    summary_dict = inmaps['summary_dict']
    
    
    # check compatibility of input parameters
    if args.progress==False and args.module==True: 
        logger.error(f"You cannot ask --module without --progress (see --help).")
        return 1
    if args.progress==False and args.focus!='-':
        logger.error(f"You cannot ask --focus without --progress (see --help).")
        return 1
    if args.progress==False and args.zeroes==True:
        logger.error(f"You cannot ask --zeroes without --progress (see --help).")
        return 1
    
    
    # download database and check its structure
    db = get_db(logger)
    if type(db)==int: return 1
                                    
        
    # create the model
    model = cobra.Model('newuni')
        
    
    # introduce M / R / T
    model = introduce_metabolites(logger, db, model, idcollection_dict)
    if type(model)==int: return 1
    model = introduce_reactions(logger, db, model, idcollection_dict)
    if type(model)==int: return 1
    model = introduce_transporters(logger, db, model, idcollection_dict)
    if type(model)==int: return 1


    # introduce sinks / demands (exchanges where included during T)
    model = introduce_sinks_demands(logger, model)
    if type(model)==int: return 1


    # introducce biomass
    model = introduce_biomass(logger, db, model)
    if type(model)==int: return 1


    # translate Gs to symbols and annotate them (EC, COG, GO, ...)
    model = translate_annotate_genes(logger, model, idcollection_dict)
    if type(model)==int: return 1


    # introduce collectionas (groups of Rs as maps/modules)
    model = set_up_groups(logger, model, idcollection_dict)
    if type(model)==int: return 1
    
    
    # output the universe
    cobra.io.save_json_model(model, 'newuni.json')
    cobra.io.write_sbml_model(model, 'newuni.xml')   # groups are saved only to SBML 
    logger.info(f"'{args.outdir}/newuni.json' created!")
    logger.info(f"'{args.outdir}/newuni.xml' created!")
    log_metrics(logger, model, outmode='uni_features')

    
    response = check_biosynthesis(logger, model, args.outdir, args.growth, args.biosynth)
    if response==1: return 1
    
    
    response = check_completeness(logger, model, args.progress, args.module, args.focus, args.eggnog, args.zeroes, idcollection_dict, summary_dict)
    if response==1: return 1


    # show simple statistics of contributions
    show_contributions(logger, db)

    
      
    return 0