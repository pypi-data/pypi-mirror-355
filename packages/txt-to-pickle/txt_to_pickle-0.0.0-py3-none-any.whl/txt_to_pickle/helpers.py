import os
import sys

def file_to_list(filename):
    with open(filename) as file:
        qa_list = [line.rstrip() for line in file]
    return qa_list

def list_to_pickle(qa_list, data_length):
    d_index_str_list = [str(i) for i in range(0, data_length+1)]
    info_lists = [] 
    info_list = []
    for k in qa_list:
        if k not in d_index_str_list:
            info_list.append(k)
        else:
            info_lists.append(info_list)
            info_list = []
            
    info_lists[0][0].split("\t")

    new_info_lists = []
    for d in range(0, data_length+1):
        new_info_list = []
        for item in info_lists[d]:
            new_info_list.append(item.split("\t"))
        new_info_lists.append(new_info_list)

    new2_info_lists = []
    for d in range(0, data_length+1):
        new2_info_list = []
        for item in new_info_lists[d]:
            if len(item) == 1:
                new2_info_list.append(float(item[0]))
            else:
                for iitem in item:
                    new2_info_list.append(float(iitem))

        new2_info_lists.append(new2_info_list)

    print(new2_info_lists)
    return new2_info_lists