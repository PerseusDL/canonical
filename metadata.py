import xml.etree.ElementTree as ET
import os
from copy import deepcopy
import sys
baseDir = "CTS_XML_TEI/perseus" # For Test purpose, leave it blank
cts5NS = "http://chs.harvard.edu/xmlns/cts"
cts3NS = "http://chs.harvard.edu/xmlns/cts3/ti"
ET.register_namespace("", "http://www.tei-c.org/ns/1.0")

missingFiles = []


def remove_namespace(doc, namespace="http://www.tei-c.org/ns/1.0"):
    """Remove namespace in the passed document in place."""
    ns = '{%s}' % namespace
    nsl = len(ns)
    for elem in doc.getiterator():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]

def copy_tree( tree_root ):
    return deepcopy( tree_root );

def cdir(path):
    try:
        os.makedirs("/".join([baseDir] + path))
    except Exception as E:
        return True 
        print(E)

def createMetadata(path, node, exclude=[]):
    cdir(path)
    root = copy_tree(node)
    nodes = root.findall("./*")
    remove = [node for node in nodes if node.tag in ["{http://chs.harvard.edu/xmlns/cts3/ti}" + ex for ex in exclude]]
    for n in remove:
        root.remove(n)
    xml = ET.tostring(root)
    xml = bytes(xml).replace("ns0", "ti").replace(cts3NS, cts5NS)
    with open("/".join([baseDir] + path + ["__cts__.xml"]), "wb") as f:
        f.write(xml)
        f.close()
    return True


inventory = ET.parse("sample.xml")
textgroups = inventory.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}textgroup")
for textgroup in textgroups:
    tg = textgroup.get("projid").split(":")[1]
    ns = textgroup.get("projid").split(":")[0]
    groupUrn = "urn:cts:" + textgroup.get("projid")
    textgroup.set("urn", groupUrn)

    createMetadata([ns, tg], textgroup, ["work"])
    for work in textgroup.findall("./{http://chs.harvard.edu/xmlns/cts3/ti}work"):
        w = work.get("projid").split(":")[1]
        workUrn = groupUrn + "." + w
        work.set("groupUrn", groupUrn)
        work.set("urn", workUrn)

        # Remove online in deep copy
        work2 = deepcopy(work)
        for text in work2.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}edition") + work2.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}translation"):
            text.remove(text.find("./{http://chs.harvard.edu/xmlns/cts3/ti}online"))
        createMetadata([ns, tg, w], work2, [])

        for text in work.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}edition") + work.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}translation"):
            v = text.get("projid").split(":")[1]
            versionUrn = workUrn + "." + v
            filename = str(versionUrn + ".xml").split(":")[-1]

            path = "/".join([baseDir, ns, tg, w, filename] )

            citations = text.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}citation")
            refs = {}
            for citation in citations:
                scope = citation.get("scope")
                xpath = citation.get("xpath")
                label = citation.get("label")
                refs[scope.count("?") + 1] = {
                    "xpath": scope + xpath,
                    "label": label
                }

            try:
                f = open(path)
                xml = ET.parse(f)
            except Exception as E:
                missingFiles.append(type(E).__name__ + "\t" + path)
                xml = None
            
            if xml:
                # <-
                # We update the refs
                for refId in refs:
                    ref = refs[refId]
                    i = ref["xpath"].find("?")
                    ii = 1
                    while i >= 0:
                        ref["xpath"] = ref["xpath"][:i] + "$" + str(ii) +ref["xpath"][i+1:]
                        i = ref["xpath"].find("?")
                        ii += 1

                    # We need to add tei: namespace when required
                    xpath = ref["xpath"]
                    xpath = xpath.split("/")
                    for xIndex in range(0, len(xpath)):
                        xp = xpath[xIndex]
                        if "tei:" not in xp and len(xp) > 0:
                            xpath[xIndex] = "tei:" + xp


                    ref["xpath"] = "#xpath("+"/".join(xpath)+")"

                    ref["p"] = "This pointer pattern extracts {0}".format(" and ".join([refs[labelId]["label"] for labelId in range(1, refId+1)]))
                    ref["regexp"] = ".".join(["(\w+)" for z in range(1, refId+1)])
                # 
                # ->
                teiHeaders = [xml.find(".//teiHeader")] + [xml.find(".//{http://www.tei-c.org/ns/1.0}teiHeader")]
                teiHeaders = [teiHeader for teiHeader in teiHeaders if teiHeader is not None]
                teiHeader = teiHeaders[0]

                teiNS = teiHeader.tag.replace("teiHeader", "")
                encodingDesc = teiHeader.find("./{0}encodingDesc".format(teiNS))
                if encodingDesc is None:
                    encodingDesc = ET.Element("{0}encodingDesc".format(teiNS))
                    teiHeader.append(encodingDesc)

                refsDecl = encodingDesc.find("./{0}refsDecl[@id='CTS']".format(teiNS))
                if refsDecl is None:
                    refsDecl = ET.Element("{0}refsDecl".format(teiNS))
                    refsDecl.set("id", "CTS")
                    encodingDesc.append(refsDecl)
                else:
                    for toRemove in refsDecl.findall("*"):
                        refsDecl.remove(toRemove)
                # We create the <cRefPattern>
                # We need to go in reverse order
                for refId in range(1, len(refs) + 1)[::-1]:
                    ref = refs[refId]
                    cRefPattern = ET.Element("{0}cRefPattern".format(teiNS), attrib = {
                        "matchPattern": ref["regexp"],
                        "replacementPattern": ref["xpath"]
                    })
                    p = ET.Element("{0}p".format(teiNS))
                    p.text = ref["p"]
                    cRefPattern.append(p)
                    refsDecl.append(cRefPattern)
                
                f.close()

                teiNSClean = teiNS.replace("{", "").replace("}", "")
                if len(teiNSClean) > 0:
                    remove_namespace(xml)
                roottag = xml.getroot().tag
                with open(path, "wb") as f:
                    xml.write(f, encoding="utf-8", xml_declaration=True)
                    f.close()

                txt = open(path).read()
                roottag = "<"+roottag
                place = txt.find(roottag)
                with open(path, "w") as f:
                    f.write(txt[:place + len(roottag)] + " xmlns=\"http://www.tei-c.org/ns/1.0\" " + txt[place + len(roottag):])
                    f.close()


                # And no we add back the tag
                
        # for edition in work.findall("./{http://chs.harvard.edu/xmlns/cts3/ti}edition"):
        #    print(ET.tostring(edition))
        # And now the modifications should take place in the file
        # 
with open("error.txt", "w") as f:
    f.write("\n".join(missingFiles))
    f.close()