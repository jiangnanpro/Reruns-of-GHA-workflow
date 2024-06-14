import pandas as pd
import matplotlib.pyplot as plt


def build_flakiness_data(data_records, rerun_type):

    flakiness_data = []

    for index,record in enumerate(data_records):
        
        for set_n in range(len(record['reruns ids'])):
            
            # verify if there's only 'success' and 'failure' in current rerun set. If not, skip the set.
            set_conclusion = list(set(record['rerun conclusion'][set_n]))
            verified = False
            
            if len(set_conclusion) == 2 and 'success' in set_conclusion and 'failure' in set_conclusion:
                verified = True
            
            if len(set_conclusion) == 1 and ('success' in set_conclusion or 'failure' in set_conclusion): 
                verified = True

                
            if verified == True:
                
                new_set = []
                temp_set = []
                
                for run_n in range(len(record['rerun conclusion'][set_n])):
                    
                    dict_record = {}

                    if rerun_type == 'wf':
                        dict_record['reruns ids'] = record['reruns ids'][set_n][run_n]
                        dict_record['event'] = record['event'][set_n][run_n]
                    if rerun_type == 'job':
                        dict_record['reruns ids'] = record['reruns ids'][set_n]
                        dict_record['event'] = record['event'][set_n]

                    dict_record['repo'] = record['repo path']
                    dict_record['branch'] = record['branch']
                    dict_record['default'] = record['default']
                    
                    if record['rerun conclusion'][set_n][run_n] == 'failure':
                        temp_set.append(dict_record)
                        
                    if record['rerun conclusion'][set_n][run_n] == 'success' and len(temp_set) > 0:
                        temp_set.append(dict_record)
                        new_set.append(temp_set)
                        temp_set = []
                        
                if len(new_set) > 0:
                    flakiness_data.append(new_set)
                        
                    
    print(f'Successfully loaded {len(flakiness_data)} flakiness sets.')
    
    return flakiness_data


    
def flakiness_df_generator(flakiness_data):
    
    list_flakiness = []
    
    for repo_n,flaky in enumerate(flakiness_data):
        for set_n,flaky_set in enumerate(flaky):
            dict_flakiness = {}

            dict_flakiness['#_failures_before_succeed'] = len(flaky_set)-1
            dict_flakiness['repo_url'] = 'https://github.com/' + flaky_set[0]['repo']+ '/actions/runs/' 
            dict_flakiness['branch'] = flaky_set[0]['branch']
            dict_flakiness['default'] = flaky_set[0]['default']
            dict_flakiness['event'] = flaky_set[0]['event']
            dict_flakiness['ids'] = [flaky_set[i]['reruns ids'] for i in range(len(flaky_set))]

            list_flakiness.append(dict_flakiness)

    df_flakiness = pd.DataFrame(list_flakiness) 
    
    return df_flakiness



def flakiness_sets_printer(df_flakiness, rerun_type, gross_number=5):
    
    most_frequent = df_flakiness.sort_values(by='#_failures_before_succeed', ascending=False).values.tolist()[:]
    dict_repo = {}
    count = 0
    
    for r_set in most_frequent[:gross_number]:
        if r_set[1] not in dict_repo:
            
            count += 1
            dict_repo[r_set[1]] = 1
            f_failure = r_set[1] + str(r_set[5][0])
            
            if rerun_type == 'wf':
                f_success = r_set[1] + str(r_set[5][-1])

            print(f'current number: {count}')
            print(f'# reruns: {r_set[0]}')
            print(f'event: {r_set[4]}')
            print(f'branch: {r_set[2]}')
            print(f_failure)
            if rerun_type == 'wf':
                print(f_success)
            
            print()
            
    return



def show_frequency(flakiness_data):
    
    len_hash = {2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0,10:0}

    for repo_n,flaky in enumerate(flakiness_data):
        for set_n,flaky_set in enumerate(flaky):
            len_flaky = len(flaky_set)
            for k in len_hash:
                if len_flaky >= k:

                    len_hash[k] += 1

    keys = list(len_hash.keys())
    values = list(len_hash.values())

    labels = [f'$\\geq {key}$' for key in keys]

    plt.figure(figsize=(7, 5))
    plt.grid(True, linestyle='--', alpha=0.7, zorder=0)
    plt.bar(keys, values, color=(55/255, 103/255, 149/255), zorder=10)

    plt.title('Frequency of failures before success in flakiness sets')
    plt.xlabel('# failed runs')
    plt.ylabel('# flakiness sets')
    plt.xticks(keys, labels)

    for i, value in enumerate(values):
        plt.text(keys[i], value, str(value), ha='center', va='bottom')

    plt.show()
    
    return