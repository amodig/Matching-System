def processLine(splitline, thefile):    
    lines = []
    openparentheses = splitline[1].count('{') - splitline[1].count('}')
    splitline[1] = splitline[1].lstrip()
    lines.append(splitline[1])
    while openparentheses > 0:
        currentline = thefile.readline()
        openparentheses = openparentheses + currentline.count('{') - currentline.count('}')
        lines.append(currentline.lstrip())
    line = " ".join(lines)
    line = line.translate(None, "{}")
    line = line[:-2]
    line = line.replace('\n', "")
    return line

print "Extracting abstracts from bibtex"
filename = 'all.txt'
thefile = open(filename, 'r')
outputfilename = 'all_processed.txt'
outputfile = open(outputfilename, 'w')
alllines = []
nextline = thefile.readline()
while nextline:
    if "@proceedings" in nextline or "@book" in nextline:
        proceedings = True
    elif nextline.find("@") == 0:
        proceedings = False
    splitline = nextline.split('=')
    if (splitline[0] == '  title     ' and proceedings == False):
        line = processLine(splitline, thefile)
        outputfile.write(line + '\n')
        alllines.append(line)
    nextline = thefile.readline()
print "Wrote " + str(len(alllines)) + " titles"
thefile.close()
outputfile.close()
