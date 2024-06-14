import os
import sys
import pandas as pd
import time
import pickle
from datetime import datetime
#from github import Github
import requests
from tqdm import tqdm
from tools import *

import logging

logging.basicConfig(filename='error.log',level=logging.DEBUG,format='[%(levelname)s]: [%(asctime)s] [%(message)s]', datefmt='%m/%d/%Y %I:%M:%S %p')

# GitHub API endpoint for getting workflow runs

workflow_runs_url = "https://api.github.com/repos/{owner}/{repo}/actions/runs"
commits_url = "https://api.github.com/repos/{owner}/{repo}/commits"
token1 = "personal_token"
token2 = "personal_token"

# load the repositories from .csv file.

repositories = (
    pd.read_csv('./dataset/repositories_with_workflows_3324.csv.gz')
    [['name', 'defaultBranch']]
    .sort_values('name')
    .values
    .tolist()
)


# get all the branches from a repository

def get_branchs(repository_owner, repository_name, headers):
    
    check_access_token(headers)
    
    branch_url = f"https://api.github.com/repos/{repository_owner}/{repository_name}/branches"
    branches_json = requests.get(branch_url, headers=headers).json()
    
    #print(branches_json)
    branch_names = []
    
    for branch in branches_json:
        branch_names.append(branch['name'])

    return branch_names


# download the workflow runs of a repository from GitHub.

def get_workflow_runs(repository_owner, repository_name, headers, params, start_yy, start_mm, start_dd):
    
    check_access_token(headers)
    
    params = params
    params["created"] = f">{start_yy}-{start_mm}-{start_dd}"
    
    res = requests.get(workflow_runs_url.format(owner=repository_owner, repo=repository_name), headers=headers, params=params)
    
    workflow_runs_json = res.json()
    
    while 'next' in res.links.keys():
        
        check_access_token(headers)
        res = requests.get(res.links['next']['url'], headers=headers)
        workflow_runs_json['workflow_runs'].extend(res.json()['workflow_runs'])
    
    return workflow_runs_json

# seperate the runs of different workflow files according to their path, 
# restore the results into a dictionary with key : value = file path : run

def create_workflow_run_dict(workflow_runs):
    
    workflow_run_dict = {}

    for run in workflow_runs['workflow_runs']:
        if run['path'] not in workflow_run_dict:
            workflow_run_dict[run['path']] = []
            workflow_run_dict[run['path']].append(run)
        else:
            workflow_run_dict[run['path']].append(run)
        
    return workflow_run_dict

# down load the commits of a repository from GitHub.
# create a hashmap with key : value == hashcode(sha) : changes of files.

def create_hash_dict(repository_owner, repository_name, headers, params, start_yy, start_mm, start_dd):
    
    check_access_token(headers)
    
    start_date = datetime(start_yy, start_mm, start_dd)
    
    params = params
    params["since"] = start_date
    
    res = requests.get(commits_url.format(owner=repository_owner, repo=repository_name), headers=headers, params=params)
    
    commits_json = res.json()
    
    while 'next' in res.links.keys():
        
        check_access_token(headers)
        res=requests.get(res.links['next']['url'], headers=headers)

        commits_json.extend(res.json())
       
    hash_dict = {}
    
    for commit in commits_json:
        
        check_access_token(headers)
        commit_detail = requests.get(commit["url"], headers=headers).json()
        
        hash_dict[commit_detail["sha"]] = len(commit_detail["files"])
    
    return hash_dict

# this function collects the two dictionaries.

def collect_dicts(repository_owner, repository_name, headers1, headers2, params, start_yy, start_mm, start_dd):
    
    workflow_runs = get_workflow_runs(repository_owner, repository_name, headers1, params, start_yy, start_mm, start_dd)
    
    if workflow_runs['total_count'] != 0:
        
        workflow_run_dict = create_workflow_run_dict(workflow_runs)

        # check if workflow_runs.total_count == 0, if yes then no need to create hash map for sha.
        commit_hash_dict = create_hash_dict(repository_owner, repository_name, headers2, params, int(start_yy), int(start_mm), int(start_dd))
        
        return workflow_run_dict, commit_hash_dict
    
    else:
 
        return {},{}




if __name__ == "__main__":
    
    
    start_yy = '2023'
    start_mm = '01'
    start_dd = '01'

    headers1 = {
        "Authorization": f"Bearer {token1}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    headers2 = {
        "Authorization": f"Bearer {token2}",
        "Accept": "application/vnd.github.v3+json"
    }

    # now we start collecting data.
    
    with open(f'./dataset/all_branch_workflow_runs2023.pkl', 'rb') as f:
        all_workflow_runs = pickle.load(f)
        
    with open(f'./dataset/all_branch_commit_hashs2023.pkl', 'rb') as f:
        all_commit_hashs = pickle.load(f)
    
    
    '''
    all_workflow_runs = []
    all_commit_hashs = []
    
    
    repo_index = 3
    n_collect = 1
    
    '''
    
    repo_index = int(sys.argv[1])
    
    if len(sys.argv) > 2:
        n_collect = int(sys.argv[2])
    else:
        n_collect = 100
    
    end_index = repo_index+n_collect

    for repository in tqdm(repositories[repo_index:end_index]):

        branch_workflow_runs = []
        branch_commit_hashs = []

        repo_path, default_branch = repository
        repository_owner, repository_name = repo_path.split('/')


        branch_names = get_branchs(repository_owner, repository_name, headers1)

        
        for branch_name in branch_names:

            params = {"branch":branch_name, "page":1, "per_page":100}

            try:
                workflow_run_dict, commit_hash_dict = collect_dicts(repository_owner, repository_name, headers1, headers2, params, start_yy, start_mm, start_dd)

                branch_workflow_run = [branch_name, workflow_run_dict]
                branch_commit_hash= [branch_name, commit_hash_dict]

                branch_workflow_runs.append(branch_workflow_run)
                branch_commit_hashs.append(branch_commit_hash)

            except Exception as e:
                logging.error(str(e))
                pass
        

        all_workflow_runs.append(branch_workflow_runs)
        all_commit_hashs.append(branch_commit_hashs)

        repo_index +=1
        
        # store the collected dicts into pkl files after collecting data for every 10 repos.
      
        if repo_index%1 == 0:
            
            #print(f'{repo_index + 1} repo(s) saved.', end='\r')
            workflow_runs_path = f"./dataset/all_branch_workflow_runs2023.pkl"
            commit_hashs_path = f"./dataset/all_branch_commit_hashs2023.pkl"
            
            with open(workflow_runs_path, 'wb') as f:
                pickle.dump(all_workflow_runs, f)
            with open(commit_hashs_path, 'wb') as f:
                pickle.dump(all_commit_hashs, f)
