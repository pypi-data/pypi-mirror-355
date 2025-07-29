import io
import requests

import pandas as pnd

import gempipe

__OPTTHR__ = 0.001   # optimization threshold



def force_id_on_sbml(file_path, model_id):
    
    with open(file_path, 'r') as file:
        content = file.read()
    content = content.replace(
        f'<model metaid="meta_{model_id}" fbc:strict="true">', 
        f'<model metaid="meta_{model_id}" id="{model_id}" fbc:strict="true">'
    )
    with open(file_path, 'w') as file:
        file.write(content)
        

def get_expcon(logger):
    
    
    logger.info("Downloading the experimental constraints file...")
    sheet_id = "1qGbIIipHJgYQjk3M0xDWKvnTkeInPoTeH9unDQkZPwg"
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    response = requests.get(url)  # download the requested file
    if response.status_code == 200:
        excel_data = io.BytesIO(response.content)   # load into memory
        exceldb = pnd.ExcelFile(excel_data)
    else:
        logger.error(f"Error during download. Please contact the developer.")
        return 1
    
    
    # check table presence
    sheet_names = exceldb.sheet_names
    for i in ['media', 'PM1', 'PM2A', 'PM3B', 'PM4A', 'authors']: 
        if i not in sheet_names:
            logger.error(f"Sheet '{i}' is missing!")
            return 1
        
        
    # load the tables
    expcon = {}
    expcon['media'] = exceldb.parse('media')
    expcon['PM1'] = exceldb.parse('PM1')
    expcon['PM2A'] = exceldb.parse('PM2A')
    expcon['PM3B'] = exceldb.parse('PM3B')
    expcon['PM4A'] = exceldb.parse('PM4A')
    expcon['authors'] = exceldb.parse('authors')
    
    
    # assign substrates as index
    expcon['media'].index = expcon['media'].iloc[:, 1]
    # remove first 2 useless column (empty & substrates)
    expcon['media'] = expcon['media'].iloc[:, 2:]
    
    
    for sheet in ['PM1', 'PM2A', 'PM3B', 'PM4A']:
        # assign wells as index
        expcon[sheet].index = expcon[sheet].iloc[:, 2]
        # remove first 3 useless columns
        expcon[sheet] = expcon[sheet].iloc[:, 3:]
    

    return expcon



def apply_medium_given_column(logger, model, medium, column, is_reference=False):
        
        
    # retrieve metadata
    description = column.iloc[0]
    doi = column.iloc[1]
    author = column.iloc[2]
    units = column.iloc[3]

    
    # convert substrates to dict
    column = column.iloc[4:]
    column = column.to_dict()

    
    # add trace elements:
    column['fe2'] = 'NL'
    column['mobd'] = 'NL'
    column['cobalt2'] = 'NL'


    # reset exchanges
    gempipe.reset_growth_env(model)    
    modeled_rids = [r.id for r in model.reactions]


    for substrate, value in column.items():

        if type(value)==float:
            continue   # empty cell, exchange will remain close

            
        # check if exchange is modeled
        if is_reference == False: 
            if f'EX_{substrate}_e' not in modeled_rids:
                logger.error(f"No exchange reaction found for substrate '{substrate}' in medium '{medium}'.")
                return 1
        else:  # external reference models might follow different standards.
            # The exr might not be present. 
            if f'EX_{substrate}_e' not in modeled_rids:
                logger.info(f"Reference has no exchange reaction for '{substrate}' in medium '{medium}': this substrate will be ignored.")
                continue


        # case "not limiting"
        value = value.strip().rstrip()
        if value == 'NL':   # non-limiting case
            model.reactions.get_by_id(f'EX_{substrate}_e').lower_bound = -1000


        # case "single value"
        elif '+-' not in value and '±' not in value:  # single number case
            value = value.replace(' ', '')  # eg "- 0.03" --> "-0.03"
            try: value = float(value)
            except: 
                logger.error(f"Invalid value found in medium '{medium}': '{substrate}' {value}.")
                return 1
            model.reactions.get_by_id(f'EX_{substrate}_e').lower_bound = value


        # case "with experimental error"
        else:  # value +- error
            if '±' in value: 
                value, error = value.split('±', 1)
            else: value, error = value.split('+-', 1)
            value = value.rstrip()
            error = error.strip()
            value = value.replace(' ', '')  # eg "- 0.03" --> "-0.03"
            try: value = float(value)
            except: 
                logger.error(f"Invalid value found in medium '{medium}': '{substrate}' {value} +- {error}.")
                return 1
            try: error = float(error)
            except: 
                logger.error(f"Invalid value found in medium '{medium}': '{substrate}' {value} +- {error}.")
                return 1
            model.reactions.get_by_id(f'EX_{substrate}_e').lower_bound = value -error
            model.reactions.get_by_id(f'EX_{substrate}_e').upper_bound = value +error

    return 0



def verify_growth(model, boolean=True):
        
    global __OPTTHR__
    res = model.optimize()
    obj_value = res.objective_value
    status = res.status
    if boolean:
        if obj_value < __OPTTHR__ or status=='infeasible':
            return False
        else: return True
    else:
        if status =='infeasible':
            return 'infeasible'
        elif obj_value < __OPTTHR__:
            return 0
        else:
            return round(obj_value, 3)
        
        
def log_metrics(logger, model, outmode='starting_uni'):
    
    
    G = len([g.id for g in model.genes])
    R = len([r.id for r in model.reactions if len(set([m.id.rsplit('_',1)[-1] for m in r.metabolites]))==1])
    T = len([r.id for r in model.reactions if len(set([m.id.rsplit('_',1)[-1] for m in r.metabolites]))!=1])
    M = len([m.id for m in model.metabolites])
    uM = len(set([m.id.rsplit('_',1)[0] for m in model.metabolites]))
    gr = len([gr.id for gr in model.groups])
    bP = len([m.id for m in model.reactions.get_by_id('Biomass').reactants])

    
    if   outmode == 'starting_uni':
        logger.info(f"Starting universe: [oG: {G}, R: {R}, T: {T}, uM: {uM}, bP: {bP}]")
    elif outmode == 'uni_features':
        biomass = round(model.slim_optimize(), 3)
        logger.info(f"Universe features: [oG: {G}, R: {R}, T: {T}, uM: {uM}, bP: {bP}, Biomass: {biomass}]")
    elif outmode == 'recon_model':
        logger.info(f"Resulting model: [G: {G}, R: {R}, T: {T}, uM: {uM}, bP: {bP}]")
    elif outmode == 'loaded_model':
        logger.info(f"Loaded model: [G: {G}, R: {R}, T: {T}, uM: {uM}, bP: {bP}]")
