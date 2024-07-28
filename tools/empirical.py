import time
import requests


def api_request(url, headers):
    
    '''
    return the json file resulting from parsing the GHA api
    '''
    
    response = requests.get(url, headers=headers)
    response_json = response.json()
    
    return response_json


def check_access_token(headers):
    
    '''
    check the # of accesses left with a certain GHA token, 
    the program enters sleep mode if the # left is less than 5
    '''
    
    # check if is approaching the token's access limit.
    access_limit = requests.get('https://api.github.com/rate_limit', headers=headers)
    access_limit = access_limit.json()['resources']['core']
    
    
    if access_limit['remaining'] < 5: 

        current_time = int(time.time())
        sleep_time = access_limit['reset'] - current_time + 2
        print('The program entered a sleep state due to access limit.')
        
        while sleep_time > 0:

            print(f"Remaining sleep time: {sleep_time} seconds", end='\r')
            time.sleep(1)
            sleep_time -= 1
            
            if sleep_time == 0:
                print('Access limit is reset, restart the program.')

    return



def analyze_wasted_time(wasted_time):
    
    '''
    analyze the time wasted, print the evaluation results
    '''
    
    wasted_time_list = []
    max_wasted_time_list = []
    min_wasted_time_list = []
    rerun_set_count = 0
    
    for wasted_time_repo in wasted_time:
        
        sum_wasted_time_repo = sum(wasted_time_repo)
        max_wasted_time_repo = max(wasted_time_repo) if len(wasted_time_repo) != 0 else 0
        min_wasted_time_repo = min(wasted_time_repo) if len(wasted_time_repo) != 0 else 0
        wasted_time_list.append(sum_wasted_time_repo)
        max_wasted_time_list.append(max_wasted_time_repo)
        min_wasted_time_list.append(min_wasted_time_repo)
        
        rerun_set_count += len(wasted_time_repo)
    
    sum_wasted_time = sum(wasted_time_list)
    avg_wasted_time = round(sum_wasted_time/rerun_set_count,2) if rerun_set_count > 0 else 0
    max_wasted_time = max(max_wasted_time_list)
    min_wasted_time = min(min_wasted_time_list)
    
    #index_max = max(range(len(max_wasted_time_list)), key=max_wasted_time_list.__getitem__)
    
    #print(f'There are {rerun_set_count} rerun sets in total.')
    print('--------------------------------------------------------')
    print(f'In total {sum_wasted_time} secs ({round(sum_wasted_time/(60*60*24), 2)} days) have been wasted.')
    #print(f'Which equals {round(sum_wasted_time/(60*60*24), 2)} days.')
    print(f'On average {avg_wasted_time} secs ({round(avg_wasted_time/(60*60), 2)} hours) have been wasted per rerun set.')
    #print(f'Which equals {round(avg_wasted_time/(60*60), 2)} hours.')
    print(f'Maximum wasted time per rerun set: {max_wasted_time} secs ({round(max_wasted_time/(60*60), 2)} hours).')
    #print(f'Which equals {round(max_wasted_time/(60*60), 2)} hours.')
    print('--------------------------------------------------------')
    

    
##### Functions for Step 1 #####

def find_next_run(index, workflow_list, rerun_list, hash_dict):
    
    '''
    recursive function. -> identify if the next workflow run is still with in the rerun set, if not, return the current rerun set as a list of re-run workflows 'rerun_list'
    '''
    
    rerun_list.append(workflow_list[index])
    if index != len(workflow_list) - 1 :
        
        current_sha = workflow_list[index]['head_sha']
        current_id = workflow_list[index]['id']
        next_sha = workflow_list[index+1]['head_sha']
        next_id = workflow_list[index+1]['id']
        
        
        if (current_sha == next_sha or hash_dict[next_sha] == 0) and current_id != next_id: # -> make sure that he current id is different from the next id, why there're identical ids is still unclear.
            
            # 1. when two workflow runs have identical hashcodes. -> means workflow triggered by something else than commit (e.g. manually, issues) \
            # 2. when two workflow runs have different hashcodes but actually nothing has been changed. -> Means empty commit(the most suspicious case) 

            return find_next_run(index+1, workflow_list, rerun_list, hash_dict)
        
        else:
            
            return rerun_list, index
        
    else:
        return rerun_list, index
    

        

def find_reruns(workflow_run_dict, hash_dict):
    '''
    returns all the rerun sets for both workflow and job reruns for a specific working branch within a repo
    '''
    
    rerun_workflow = []
    rerun_job = []

    for key in workflow_run_dict:

        workflow_list = copy.deepcopy(workflow_run_dict[key])
        workflow_list.reverse()

        rerun_workflow_all = []
        rerun_job_all = []
        
        end_index = 0
        last_start = 0
        
        for index,workflow in enumerate(workflow_list):
            

            rerun_workflow_list = []
            
            if workflow['run_attempt'] > 1:
                rerun_job_all.append(workflow)
                
            if workflow['conclusion'] == 'failure':

                if index > end_index: # the end_index here is used to prevent overlap, a rerun set will only be found once.
                    
                    try:
                        results, end_index = find_next_run(index, workflow_list, rerun_workflow_list, hash_dict)
                        
                    except KeyError as ke:
                        results = []
                        pass

                    if (len(results) > 1) and results[0]['id'] != last_start: # make sure one rerun set will only be found once.
                        
                        rerun_workflow_all.append(results)
                        last_start = results[0]['id']

        rerun_workflow.append(rerun_workflow_all)
        rerun_job.append(rerun_job_all)
        
        
    return rerun_workflow, rerun_job




def build_rerun_df(repos, rerun_index, rerun_type, all_rerun):
    
    '''
    build the dataframe for both workflow and job reruns
    '''

    print(f'{len(rerun_index)} workflow files have {rerun_type} reruns.')

    all_r_list = []
    all_r_id_list = []
    r_path_list = []
    w_path_list = []
    branch_list = []
    default_list = []
    all_event_list = []
    all_content_list = []
    num_rerun_avg_list = []
    num_rerun_max_list = []
    num_rerun_min_list = []
    num_rerun_set_list = []
    rerun_conclusion_list = []
    last_rerun_conclusion_list = []
    num_success_list = []
    num_failure_list = []


    for index in rerun_index:

        r_i,b_i,w_i = index
    
        if rerun_type == 'workflow':
            
            r_path = all_rerun[r_i][b_i][1][w_i][0][0]['repository']['full_name']
            w_path = all_rerun[r_i][b_i][1][w_i][0][0]['path']
            branch = all_rerun[r_i][b_i][0]
            
            if branch == repos[r_i][1]:
                default = True
            else:
                default = False
                
        
            r_list = []
            r_id_list = []
            event_lists = []
            content_lists = []
            rerun_conclusions = []
            last_rerun_conclusion = []
            
            
            for rerun in all_rerun[r_i][b_i][1][w_i]:
                r_list.append(len(rerun)-1)
                
                last_rerun_conclusion.append(rerun[-1]['conclusion'])
                
                id_list = []
                event_list = []
                content_list = []
                run_conclusion = []
                
                for one_run in rerun:
                    
                    head_sha = one_run['head_sha']
                    
                    id_list.append(one_run['id'])
                    event_list.append(one_run['event'])
                    content_list.append(one_run['repository']['contents_url'].removesuffix('{+path}')+w_path+'?ref='+head_sha)
                    run_conclusion.append(one_run['conclusion'])
                
                
                r_id_list.append(id_list)
                event_lists.append(event_list)
                content_lists.append(content_list)
                rerun_conclusions.append(run_conclusion)
            
            all_content_list.append(content_lists)
            rerun_conclusion_list.append(rerun_conclusions)
        
        elif rerun_type == 'job':
            
            r_path = all_rerun[r_i][b_i][1][w_i][0]['repository']['full_name']
            w_path = all_rerun[r_i][b_i][1][w_i][0]['path']
            branch = all_rerun[r_i][b_i][0]
            
            if branch == repos[r_i][1]:
                default = True
            else:
                default = False
            
            r_list = []
            r_id_list = []
            event_lists = []
            last_rerun_conclusion = []
            
            for rerun in all_rerun[r_i][b_i][1][w_i]:
                r_list.append(rerun['run_attempt']-1)
                r_id_list.append(rerun['id'])
                event_lists.append(rerun['event'])
                last_rerun_conclusion.append(rerun['conclusion'])
                
                

        all_r_list.append(r_list)
        all_r_id_list.append(r_id_list)
        r_path_list.append(r_path)
        w_path_list.append(w_path)
        branch_list.append(branch)
        default_list.append(default)
        all_event_list.append(event_lists)
        num_rerun_avg_list.append(sum(r_list)/len(r_list))
        num_rerun_max_list.append(max(r_list))
        num_rerun_min_list.append(min(r_list))
        num_rerun_set_list.append(len(r_list))
        last_rerun_conclusion_list.append(last_rerun_conclusion)
        num_success_list.append(last_rerun_conclusion.count('success'))
        num_failure_list.append(last_rerun_conclusion.count('failure'))
    
    
    df_rerun = pd.DataFrame()

    df_rerun['File index'] = rerun_index
    df_rerun['repo path'] = r_path_list
    df_rerun['workflow file path'] = w_path_list
    df_rerun['branch'] = branch_list
    df_rerun['default'] = default_list
    df_rerun['event'] = all_event_list
    df_rerun['reruns'] = all_r_list
    df_rerun['reruns ids'] = all_r_id_list
    df_rerun['# avg rerun'] = num_rerun_avg_list
    df_rerun['# max rerun'] = num_rerun_max_list
    df_rerun['# min rerun'] = num_rerun_min_list
    df_rerun['# rerun sets'] = num_rerun_set_list
    df_rerun["last rerun's conclusion"] = last_rerun_conclusion_list
    df_rerun['# success'] = num_success_list
    df_rerun['# failure'] = num_failure_list
    
    if rerun_type == 'workflow':
        
        df_rerun['content'] = all_content_list
        df_rerun['rerun conclusion'] = rerun_conclusion_list
    
    
    default_percentage = round(sum(default_list)/len(default_list)*100,1)
    
    print(f'{sum(default_list)}/{len(default_list)}({default_percentage}%) reruns occurred in default branches.')
    
    return df_rerun




##### Functions for Step 2 #####

def extract_runtime_wf(jobs_details):
    
    '''
    extract the computational time for workflow reruns
    '''
    
    runtime = []

    for repo_job in jobs_details:

        repo_runtime = []

        for set_job in repo_job:

            set_runtime = []

            for run_job in set_job:

                run_runtime = 0

                if run_job is not None:
                    
                    for job in run_job:

                        try:
                            start_timestamp = datetime.strptime(job['started_at'], '%Y-%m-%dT%H:%M:%SZ')
                            end_timestamp = datetime.strptime(job['completed_at'], '%Y-%m-%dT%H:%M:%SZ')

                            job_runtime = end_timestamp - start_timestamp

                            run_runtime += job_runtime.total_seconds()

                        except Exception as e :

                            print(job)
                            print(e)

                            run_runtime += 0
                            pass

                set_runtime.append(run_runtime)

            repo_runtime.append(set_runtime)

        runtime.append(repo_runtime)
        
    return runtime



def extract_runtime_jobs(jobs_details):
    
    '''
    extract the computational time for job reruns
    '''
    
    runtime = []

    for repo_job in jobs_details:

        repo_runtime = []

        for set_job in repo_job:

            set_runtime = []
            
            for i in range(len(set_job)):
                
                run_runtime = 0
                
                if i < len(set_job) - 1: # not the first attempt
                    
                    former_attempt_timestamps = []
                    
                    for j in range(len(set_job[i+1])): # collect the 'created_at' timestamps for the former attempt.
                        
                        former_attempt_timestamps.append(set_job[i+1][j]['started_at'])
                    
                    for j in range(len(set_job[i])): # match the latter attempt's timestamps to the former ones.
                        
                        job_latter = set_job[i][j]
                        
                        if job_latter['started_at'] not in former_attempt_timestamps:

                            try:
                                start_timestamp = datetime.strptime(job_latter['started_at'], '%Y-%m-%dT%H:%M:%SZ')
                                end_timestamp = datetime.strptime(job_latter['completed_at'], '%Y-%m-%dT%H:%M:%SZ')

                                job_runtime = end_timestamp - start_timestamp

                                run_runtime += job_runtime.total_seconds()

                            except Exception as e :

                                print(job_latter)
                                print(e)

                                run_runtime += 0
                                pass
                        
                
                if i == len(set_job) -1: # the first attempt
                    
                    for job in set_job[i]:
                    
                        try:
                            start_timestamp = datetime.strptime(job['started_at'], '%Y-%m-%dT%H:%M:%SZ')
                            end_timestamp = datetime.strptime(job['completed_at'], '%Y-%m-%dT%H:%M:%SZ')

                            job_runtime = end_timestamp - start_timestamp

                            run_runtime += job_runtime.total_seconds()

                        except Exception as e :

                            print(job)
                            print(e)

                            run_runtime += 0
                            pass
                    
                
                set_runtime.append(run_runtime)

            repo_runtime.append(set_runtime)

        runtime.append(repo_runtime)
        
        
    return runtime