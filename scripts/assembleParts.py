#!/usr/bin/env python
#
# Reassembles annotated chapters into one big file

import argparse
import re
import os
import sys
import logging
import traceback

import xml.dom.minidom as minidom

FORMAT = '%(asctime)-15s [%(levelname)s] %(message)s'
logging.basicConfig(format=FORMAT)
log = logging.getLogger('index')
log.setLevel(logging.INFO)

def writeXml(dom, filename):
    with open(filename, 'w') as output:
        output.write(dom.toxml("utf-8"))
#       output.write(dom.toprettyxml(encoding="utf-8"))

def getPartNumber(filename):
    m = re.match(r"(.*?)-([0-9]+)(-[^0-9]+)?\.xml",filename)
    return float(m.group(2)) if m else -1

def updateId(id, offset):
    if len(id) > 0:
        m = re.match(r"([a-zA-Z]+)([0-9]+)", id)
        d = int(m.group(2)) + offset
        mid = m.group(1) + str(d)
        return (mid,d)
    else:
        return (id,None)

def updateIds(elements, offset):
    maxId = -1
    for element in elements:
        eid = updateId(element.getAttribute('id'), offset)
        if eid[1] > maxId:
            maxId = eid[1]
        element.setAttribute('id', eid[0])
        connections = element.getAttribute('connection').split(",")
        connections = [updateId(c,offset)[0] for c in connections]
        connection = ",".join(connections)
        element.setAttribute('connection', connection)
    return maxId+1

def assemble(input, includeSectionTags, outfilename):
    # Get filelist
    files = [f for f in os.listdir(input) if f.endswith('.xml')]
    # Sort files by order
    files.sort(key=lambda val: (getPartNumber(val), val))
    # Iterate through chapters
    chapters = []
    characters = []
    charactersByName = {}
    maxSpanId = 0
    for file in files:
        chdom = minidom.parse(input + '/' + file)
        characterElems = chdom.getElementsByTagName('character')
        for characterElem in characterElems:
            name = characterElem.getAttribute('name')
            if not charactersByName.get(name):
                charactersByName[name] = {'xml': characterElem}
                characterElem.setAttribute('id', str(len(characters)))
                characters.append(charactersByName[name])
        textElems = chdom.getElementsByTagName('text')
        for textElem in textElems:
            # TODO: fix up span ids for quote, mention, connection
            spanOffset = maxSpanId
            m1 = updateIds(chdom.getElementsByTagName('quote'), spanOffset)
            m2 = updateIds(chdom.getElementsByTagName('mention'), spanOffset)
            maxSpanId = m1 if m1 > maxSpanId else maxSpanId
            maxSpanId = m2 if m2 > maxSpanId else maxSpanId
            chapters.append({'xml': textElem})
    # Final output
    impl = minidom.getDOMImplementation()
    dom = impl.createDocument(None, "doc", None)
    docElem = dom.documentElement
    charactersElem = dom.createElement('characters')
    for character in characters:
        charactersElem.appendChild(character['xml'].cloneNode(True))
    docElem.appendChild(charactersElem)
    docElem.appendChild(dom.createTextNode('\n'))
    textElem = dom.createElement('text')
    for chapter in chapters:
        t = chapter['xml']
        if includeSectionTags:
            chapterElem = dom.createElement('chapter')
            textElem.appendChild(dom.createTextNode('\n'))
            textElem.appendChild(chapterElem)
        else:
            chapterElem = textElem
        for c in t.childNodes:
            chapterElem.appendChild(c.cloneNode(True))
    docElem.appendChild(textElem)
    writeXml(dom, outfilename)

def main():
    # Argument processing
    parser = argparse.ArgumentParser(description='Assembles annotated parts together')
    parser.add_argument('infile')
    parser.add_argument('-p', dest='includeSectionTags', help='paragraphs and headings', action='store_true')
    parser.add_argument('outfile', nargs='?')
    args = parser.parse_args()
    outname = args.outfile or args.infile + '.xml'
    assemble(args.infile, args.includeSectionTags, outname)

if __name__ == "__main__": main()