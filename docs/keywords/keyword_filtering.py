"""
This file filters some low quality keywords in file keywords_70k.txt
"""


import pickle

keywords_filename = "keywords_70k_2000.txt"
filtered_keywords_filename = "filtered_single_70k_2000.txt"
file_obj = open(keywords_filename,'r')
filtered_word_file_obj = open(filtered_keywords_filename,'wb')
keywords_set = pickle.load(file_obj)
keywords = list(keywords_set)

keywords_set = set()



for keyword in keywords:
    if keyword == " " :
        pass
    elif keyword =="":
        pass
    elif  "_"  in keyword:
        pass
    else:
	keywords_set.add(keyword)
#keywords_set |= set(keyword.split(' '))

pickle.dump(keywords_set, filtered_word_file_obj)

file_obj.close()
filtered_word_file_obj.close()
