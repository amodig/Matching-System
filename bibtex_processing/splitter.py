#! /usr/bin/env python
import string
stopwords = open('stopwords.txt', 'r').read().split()
files = open('all_processed.txt','r').read().splitlines()
names = ['file'+ str("%06d"%num) for num in range(len(files))]
for num,file in enumerate(files):
    fileLower = file.lower()
    fileShortened = fileLower.translate(string.maketrans("",""), string.punctuation)
    fileArray = fileShortened.split()
    filteredtext = [t for t in fileArray if t not in stopwords]
    finalText = " ".join(filteredtext)
    outputfile = open(names[num],'w')
    outputfile.write(finalText)
    outputfile.close()

