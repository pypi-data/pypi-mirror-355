from txt_to_pickle import helpers

def main():
    if len(sys.argv[1:]) != 2:
        raise Exception("Sorry, please input filename and a number of data length")

    filename = sys.argv[1:][0]
    data_length = sys.argv[1:][1]

    # localpath_annealing = '/Users/kawayip/Desktop/qiskit-nature-stable-0.7/docs/tutorials/annealing/'
    # localpath_submission_lih = os.path.join(localpath_annealing, 'vqa/submission/lih/')
    # filename = localpath_submission_lih + "lih_qa_min_ev_list_D1_advantage2_sample_5000.txt"
    with open(filename) as file:
        qa_list = [line.rstrip() for line in file]

    qa_list = helpers.file_to_list(ilename)
    new2_info_lists = helpers.list_to_pickle(qa_list, data_length)

if __name__ == '__main__':
    main()



