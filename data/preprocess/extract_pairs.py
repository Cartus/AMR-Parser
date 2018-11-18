import sys

input = sys.argv[1]
sent = sys.argv[2]
graph = sys.argv[3]

with open(input) as f:
    lines = f.readlines()

with open(sent, 'w') as sent_file, open(graph, 'w') as node_file:
    for line in lines:
        line = line.strip()
        if line.startswith('# ::tok'):
            if cache:
                if '_______________' in cache:
                    loc = line.find('_')
                    line = line[:loc] + '_______________ "'
                    sent_file.write(line[8:]+'\n')
                    continue
                elif 'd)Finaly' in cache:
                    sent_file.write(line[12:] + '\n')
                    continue

                list_one = cache[8:].split('>')
                list_two = list_one[0].split('"')
                list_three = list_one[1].split('</a')
                list_four = list_two[0].split(' ')
                string = ''
                for ele in list_four:
                    if ele == '<a':
                        string += '< a '
                    elif ele == 'href=':
                        string += 'href = " '
                    elif ele == '':
                        continue
                    else:
                        string += ele + ' '

                if '~' in list_two[1]:
                    loc = list_two[1].find('~')
                    string += list_two[1][:loc] + list_two[1][(loc+1):] + ' " > '
                else:
                    string += list_two[1] + ' " > '

                if '~' in list_three[0]:
                    loc = list_three[0].find('~')
                    string += list_three[0][:loc] + list_three[0][(loc + 1):] + ' < / a > '
                else:
                    string += list_three[0] + ' < / a > '
                sent_file.write(string + '\n')
            else:
                if ':)' in line:
                    loc = line.find(':)')
                    line = line[:loc]
                sent_file.write(line[8:] + '\n')
        elif line.startswith('# ::id'):
            continue
        elif line.startswith('# ::snt'):
            cache = ''
            if line.count('eibnet') == 2 or line.count('wattsupwiththat') == 3 or line.count('fyye8') == 2 or line.count('//www.gwu.edu/') == 2 or 'http://www.counterpunch.org/2011/12/02/' in line\
                    or 'http://webcache.googleusercontent' in line or 'http://ftp.resource.org/courts.gov' in line\
                    or 'http://chicago.cbslocal.com/2012/' in line or 'watch?v=L-62sO2ZuV0' in line \
                    or 'watch?v=dpHjukQowZ0' in line or 'watch?v=oqtDG-7ZUpQ' in line \
                    or 'watch?v=-zH0Dr5WS_8&quot' in line or 'watch?v=iBT4ZWy6Lm4' in line\
                    or 'watch?v=hZEvA8BCoBw' in line or '84401122.LQSJZ3oY.jpg' in line or 'watch?v=-vCF389CTOU' in line\
                    or 'abs-investigators.html' in line or 'watch?v=1bVu_z0M0ts' in line or 'p=6972434&postcount=190' in line\
                    or 'p=6972455&postcount=192' in line or 'p=6972478&postcount=194"' in line or 'ENGNEWS01_1300189582P.pdf' in line\
                    or 'ENGNEWS01_1300191989P.pdf' in line or '?set=a.10100229278541028.2548594' in line \
                    or '?fbid=10100229283725638&set' in line or 'showthread.html?t=335250&highlight=russia' in line\
                    or 'national1238EST0613.DTL' in line or 'www.nytimes.com/2000/01/13/' in line\
                    or '_______________' in line\
                    or 'd)Finaly' in line:
                cache = line
            continue
        elif line.startswith('# ::save-date'):
            continue
        elif line.startswith('# ::alignments'):
            continue
        elif line.startswith('# ::node'):
            continue
        elif line.startswith('# ::root'):
            continue
        elif line.startswith('# ::edge'):
            continue
        elif line.startswith('id:'):
            continue
        elif not line:
            node_file.write('\n')
        else:
            if '~' in line:
                loc = line.find('~')
                node_file.write(line[:loc] + line[(loc + 1):])
            elif ':op1 "LSD" :op2 41 :op3 "Whidbey" :op4 "Island"' in line:
                line = ':name (n / name :op1 "LSD" :op2 "41" :op3 "Whidbey" :op4 "Island"))'
                node_file.write(line.lower() + ' ')
            else:
                node_file.write(line.lower()+' ')