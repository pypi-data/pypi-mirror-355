import argparse
import sys
import yaml
import numpy as np
from pathlib import Path
from copy import deepcopy



def merge_dicts(dict1, dict2):
    """Recursively merges dict2 into dict1."""
    for key, value in dict2.items():
        if isinstance(value, dict) and key in dict1:
            merge_dicts(dict1[key], value)
        else:
            if key == 'cut' and dict2.get('use_year_selection', True):
                dict1[key] = dict1.get(key, '') + ' and ' + value
            elif key =='use_year_selection':
                pass
            else:
                dict1[key] = value

def ijazz_config_sas():
    """Entry point for the IJazZ Scale and Smearing fit configuration script.
    This script reads the provided configuration file and generates YAML files for each step.
    """
    parser = argparse.ArgumentParser(description=f'IJazZ Scale and Smearing fit')
    parser.add_argument('config', type=str, help='yaml config file')
    parser.add_argument('--cfg', type=str, default=None, help='path to the yaml config with steps')
    args = parser.parse_args(sys.argv[1:])

    with open(args.config, 'r') as fcfg:
        config = yaml.safe_load(fcfg)

    with open(args.cfg, 'r') as fcfg:
        cfg = yaml.safe_load(fcfg)
        
    config_sas(config, cfg)

def config_sas(config: dict,cfg: dict):
    """Creates YAML configuration files for SAS steps 
    based on the provided `config` and `cfg` dictionaries. This function processes 
    datasets, applies cuts, and generates YAML files for each step in the configuration.
    
    Args:
        config (dict): A dictionary containing the main configuration. 
            Expected keys include:
            - 'datasets': List of dataset dictionaries with 'file_dt' and 'file_mc' keys.
            - 'dir_yaml': Directory path to save the generated YAML files.
            - 'sas': Dictionary containing SAS-specific configurations (e.g., 'cut').
            - 'object_type': A string representing the object type.
            - 'year': A string representing the year.
            - 'dir_results': Directory path for storing results.
        cfg (dict): A dictionary containing the SAS steps configuration. 
            Expected keys include:
            - 'steps': List of step dictionaries, each containing:
                - 'name': Name of the step.
                - 'split': Boolean indicating whether to split datasets.
                - 'sas': Dictionary with SAS-specific step configurations 
                    (e.g., 'correct_data').
    Returns:
        None: The function writes YAML files to the specified directory.
        
    Example:
        config = {
            'datasets': [{'file_dt': ['data1.parquet'], 'file_mc': ['mc1.parquet']}],
            'dir_yaml': './yaml_configs',
            'sas': {'cut': 'some_cut'},
            'object_type': 'Pho',
            'year': '2023',
            'dir_results': './results'
        }
        cfg = {
            'steps': [{'name': 'Step1', 'split': False, 'sas': {'correct_data': True}}]
        }
        config_sas(config, cfg)
    """
    datasets_sas = config['datasets']

    dir_yaml = Path(config.get('dir_yaml','.'))
    dir_yaml.mkdir(parents=True, exist_ok=True)

    sas = config.get('sas', None)
    corr_name = ''

    if config and (cut := sas.get('cut', None)):
        print(f'Applying cut: {cut}')
        cfg['sas']['cut'] = cut

    for i,step in enumerate(cfg['steps']):
        print(f'Processing step: {step["name"]}')
        # print(step['sas'].get('correct_data',True))
        split = step.get('split', False)
        for dataset in datasets_sas:
            dataset['file_dt'] = [file.replace('.parquet', f'.{corr_name}.parquet' if (i and cfg['steps'][max(0,i-1)]['sas'].get('correct_data',True)) else '.parquet') for file in dataset['file_dt']]
            
        if split:
            print('Used split datasets')
            datasets = datasets_sas
            
        else:
            files_dt = []
            files_mc = []
            for dataset in datasets_sas:
                files_dt += [dataset['file_dt']] if np.isscalar(dataset['file_dt']) else dataset['file_dt']
                files_mc += [dataset['file_mc']] if np.isscalar(dataset['file_mc']) else dataset['file_mc']
            
            
            datasets = [{"subyear": '','file_dt': files_dt, 'file_mc': files_mc}]
        
        for dataset in datasets:
            file_dt = [dataset['file_dt']] if np.isscalar(dataset['file_dt']) else dataset['file_dt']
            file_mc = [dataset['file_mc']] if np.isscalar(dataset['file_mc']) else dataset['file_mc']
    
            corr_name = config['object_type'] + step['name'] + 'Corr'
            cset_name = config['object_type'] + step['name']
            dset_name = config['year'] + dataset.get('subyear','')
            
            dir_results = Path(config['dir_results']) / step['name']
            

            config_step = deepcopy(cfg)
            merge_dicts(config_step, step)
            config_step['file_dt'] = file_dt
            config_step['file_mc'] = file_mc
            config_step['dir_results'] = str(dir_results)
            config_step['dset_name'] = dset_name
            config_step['cset_name'] = cset_name
            config_step.pop('steps', None)
            # print(config_step)

            
            name_yaml = f'sas_{step["name"]}{"_" if dataset.get("subyear","") else ""}{dataset.get("subyear","")}.yaml'
            print(f'Writing yaml file: {dir_yaml / name_yaml}')
            with open(dir_yaml / name_yaml, 'w') as yaml_file:
                yaml.dump(config_step, yaml_file, default_flow_style=False, sort_keys=False)