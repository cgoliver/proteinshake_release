import os, itertools, tempfile, random, subprocess, shutil
from tqdm import tqdm
from .util import replace_avro_files, get_paths, split
from joblib import Parallel, delayed

def foldseek_create_database(ds):
    pdb_path = f'{ds.root}/raw/files/'
    out_path = f'{ds.root}/raw/foldseek/'
    db_path = f'{out_path}/foldseekDB'
    os.makedirs(out_path, exist_ok=True)
    cmd = ['foldseek', 'createdb', pdb_path, db_path]
    out = subprocess.run(cmd, capture_output=True, text=True)
    cmd = ['foldseek', 'createindex', db_path, out_path]
    out = subprocess.run(cmd, capture_output=True, text=True)

def foldseek_wrapper(ds, query, threshold, path_dict):

    assert shutil.which('cd-hit') is not None,\
    "FoldSeek installation not found. Go here https://github.com/steineggerlab/foldseek to install"

    db_path = f'{ds.root}/raw/foldseek/foldseekDB'
    out_path = f'{ds.root}/raw/foldseek/'
    out_file = f'{out_path}/output.m8'
    query_path = path_dict[query]
    n_jobs = 0 if ds.n_jobs < 0 else ds.n_jobs
    try:
        cmd = ['foldseek', 'easy-search', query_path, db_path, out_file, out_path,
            '--threads', str(min(n_jobs, 10)),
            '--max-seqs', '1000000000',
            '--lddt-threshold', str(threshold),
            '--format-output', 'target'
        ]
        out = subprocess.run(cmd, capture_output=True, text=True)
        with open(out_file, 'r') as file:
            cluster = file.read().split()
            cluster = list(set([c.split('.pdb')[0] for c in cluster])) # remove chain ID
            cluster = [ds.get_id_from_filename(c) for c in cluster]
            return cluster
    except Exception as e:
        return []

def compute_structure_split(dataset, thresholds=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9], test_ratio=0.1, val_ratio=0.1, replace_avro=True):

    print(f'Structure split {dataset.name}')
    
    proteins = list(dataset.proteins())
    pdbids, paths, path_dict = get_paths(dataset)
    foldseek_create_database(dataset)

    for threshold in thresholds:
        pool = [p for p in pdbids]
        test_size, val_size = int(len(pool)*test_ratio), int(len(pool)*val_ratio)
        pool, test = split(foldseek_wrapper, dataset, pool, test_size, threshold, path_dict, pdbids)
        train, val = split(foldseek_wrapper, dataset, pool, val_size, threshold, path_dict, pdbids)
        #train, test, val = [dataset.get_id_from_filename(p) for p in train], [dataset.get_id_from_filename(p) for p in test], [dataset.get_id_from_filename(p) for p in val]
        print(f'total: {len(proteins)} train: {len(train)} test: {len(test)} val: {len(val)}')
        for p in proteins:
            if p['protein']['ID'] in test: p['protein'][f'structure_split_{threshold}'] = 'test'
            elif p['protein']['ID'] in val: p['protein'][f'structure_split_{threshold}'] = 'val'
            elif p['protein']['ID'] in train: p['protein'][f'structure_split_{threshold}'] = 'train'
            else: p['protein'][f'structure_split_{threshold}'] = 'none'
    if replace_avro:
        replace_avro_files(dataset, proteins)

