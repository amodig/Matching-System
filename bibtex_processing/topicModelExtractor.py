def file_len(fname):
    with open(fname) as f:
        for i, l in enumerate(f):
            pass
    return i + 1

import pickle
from collections import OrderedDict

MAX_ABSTRACTS = 2500

topic_keys_filename = 'arxiv_topic_keys.txt'
doc_topics_filename = 'bibtex_doc_topics.txt'
word_weights_filename = 'arxiv_word_weights.txt'

output_topic_keys_filename = '../docs/keywords/mallet_abstract.txt'
output_doc_topics_filename = '../docs/keywords/mallet_corpus_abstract.txt'
output_topic_keywords_filename = '../docs/keywords/mallet_topic_keywords.txt'
output_topic_keywordweights_filename = '../docs/keywords/mallet_topic_keywordweights.txt'
output_topic_articleweights_filename = '../docs/keywords/mallet_topic_articleweights.txt'

file = open(topic_keys_filename, 'r')
topics = dict()
topicnumbercounts = dict()
topicvectors = dict()
topickeywords = dict()
number_of_topics = file_len(topic_keys_filename)
print "Counted " + str(number_of_topics) + " topics"
nextline = file.readline()
processed = 0
topicnumberset = set()
while (nextline != ''):
    topic_key = nextline.split('\t')
    keyword = topic_key[2]
    keyword_with_newline_removed = keyword[:-2]
    topickeywords[topic_key[0]] = keyword_with_newline_removed
    topics[topic_key[0]] = topic_key[0]
    topicvector = [0] * number_of_topics
    topicvectors[topic_key[0]] = topicvector
    topicnumbercounts[processed] = 0
    processed += 1
    if ((processed % 50) == 0):
        print "Processed " + str(processed) + " topics"
    nextline = file.readline()
file.close()

print "Processing abstracts"

file = open(doc_topics_filename, 'rb')
nextline = file.readline()
nextline = file.readline()
number_of_abstracts = file_len(doc_topics_filename) - 1
print "Counted " + str(number_of_abstracts) + " abstracts"

corpora_representation_dict = OrderedDict()
corpora_weight_dict = OrderedDict()

abstract_number = 0
zero_topic = []

while (nextline != ''):
    linelist = nextline.split()
    filename = linelist[1]
    topic_list = []
    topic_weight_dict = {}
    topic_number_reference = 2
    topic_probability_reference = 3
    while((len(linelist) > topic_probability_reference)):
        if abstract_number < MAX_ABSTRACTS:
            topic_number = linelist[topic_number_reference]
            topic_name = topics[topic_number]
        
            topic_value = topicnumbercounts.get(int(topic_number), 0)
            topic_value += 1
            topicnumbercounts[int(topic_number)] = topic_value

            topic_weight_dict[topic_name] = linelist[topic_probability_reference]
            topic_list.append(topic_name)
        topic_number_reference += 2
        topic_probability_reference += 2

    string_containing_file_name = linelist[1]
    # CHANGE THIS IF THE FILENAMES CHANGE
    file_name = string_containing_file_name[-16:-11]
    corpora_representation_dict[file_name] = ",".join(topic_list)
    corpora_weight_dict[file_name] = topic_weight_dict
    abstract_number += 1
    nextline = file.readline()
    if ((abstract_number % 1000) == 0):
        print "Processed " +str(abstract_number) + " abstracts out of " + str(number_of_abstracts)
file.close()
print "Abstracts processed"

corpora_representation_dict = OrderedDict(sorted(corpora_representation_dict.items(), key=lambda t: t[0]))
print "Dictionary size: " + str(len(corpora_representation_dict.keys()))
corpora_representation_list = corpora_representation_dict.values()

print str(len(corpora_representation_list)) + " abstracts used"

file_abstract_list = open(output_doc_topics_filename, 'w')
pickle.dump(corpora_representation_list, file_abstract_list)
file_abstract_list.close()

corpora_weight_dict = OrderedDict(sorted(corpora_weight_dict.items(), key=lambda t: t[0]))
corpora_weight_list = corpora_weight_dict.values()

file_weight_list = open(output_topic_articleweights_filename, 'w')
pickle.dump(corpora_weight_list, file_weight_list)
file_weight_list.close()

topicset = set()
empty = 0
for key in topicnumbercounts.keys():
    if topicnumbercounts[key] > 0:
        topicset.add(topics[str(key)])
    else:
        empty += 1

file_topic_list = open(output_topic_keys_filename, 'wb')
pickle.dump(topicset, file_topic_list)
file_topic_list.close()

file_keyword_list = open(output_topic_keywords_filename, 'wb')
pickle.dump(topickeywords, file_keyword_list)
file_keyword_list.close()

print "Topics processed"
print "Ignored " + str(empty) + " empty topics"

print "Processing topic keywords"
file = open(word_weights_filename, 'r')

currenttopic = 1000
currentwords = []
topickeywordweights = [None] * 300
topicsum = 0

for line in file:
    splitline = line.split('\t')
    if int(splitline[0]) != currenttopic:
        if (currenttopic != 1000):
            topicdict = topickeywordweights[currenttopic]
            for item in topicdict.items():
                weight = item[1]
                weight = float(weight) / topicsum
                topicdict[item[0]] = weight
        topicsum = 0
        currenttopic = int(splitline[0])
        currentwords = (topickeywords[splitline[0]]).split()
        topickeywordweights[currenttopic] = dict()
        if currenttopic % 50 == 0:
            print "Processing topic number " + str(currenttopic)

    wordweight = splitline[2]
    wordweight = wordweight[:-2]
    wordweight = float(wordweight)
    if splitline[1] in currentwords:
        topicsum = topicsum + wordweight
        topicdict = topickeywordweights[currenttopic]
        topicdict[splitline[1]] = wordweight

file.close()

file_weight_list = open(output_topic_keywordweights_filename, 'wb')
pickle.dump(topickeywordweights, file_weight_list)
file_weight_list.close()



