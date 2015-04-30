import xml.etree.ElementTree as ET
import os
from copy import deepcopy

baseDir = "CTS_XML_TEI/perseus" # For Test purpose, leave it blank
cts5NS = b"http://chs.harvard.edu/xmlns/cts"
cts3NS = b"http://chs.harvard.edu/xmlns/cts3/ti"

missingFiles = []

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
    xml = bytes(xml).replace(b"ns0", b"ti").replace(cts3NS, cts5NS)
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

        for text in work2.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}edition") + work.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}translation"):
            v = text.get("projid").split(":")[1]
            versionUrn = workUrn + "." + v
            filename = str(versionUrn + ".xml").split(":")[-1]

            path = "/".join([baseDir, ns, tg, w, filename] )
            try:
                f = open(path)
                xml = ET.parse(f)
            except Exception as E:
                missingFiles.append(type(E).__name__ + "\t" + path)
                xml = None
            
            if xml:
                teiHeaders = [xml.find(".//teiHeader")] + [xml.find(".//{http://www.tei-c.org/ns/1.0}teiHeader")]
                teiHeaders = [teiHeader for teiHeader in teiHeaders if teiHeader is not None]
                teiHeader = teiHeaders[0]

                teiNS = teiHeader.tag.replace(b"teiHeader", b"")
                encodingDesc = teiHeader.find("./{0}encodingDesc".format(teiNS))
                if encodingDesc is None:
                    encodingDesc = ET.Element("{0}encodingDesc".format(teiNS))
                    teiHeader.append(encodingDesc)

                refsDecl = encodingDesc.find("./{0}refsDecl[@id='CTS']".format(teiNS))
                if refsDecl is None:
                    refsDecl = ET.Element("{0}refsDecl".format(teiNS))
                    refsDecl.set("id", "CTS")
                    encodingDesc.append(refsDecl)

                print(refsDecl)
                """
                refsDecl = [xml.find(".//refsDecl")] + [xml.find(".//{http://www.tei-c.org/ns/1.0}teiHeader")]
                refsDecl = [teiHeader for refsDecl in refsDecl if refsDecl is not None]
                refsDecl = refsDecl[0]
                """
                f.close()
        # for edition in work.findall("./{http://chs.harvard.edu/xmlns/cts3/ti}edition"):
        #    print(ET.tostring(edition))
        # And now the modifications should take place in the file
        # 
with open("error.txt", "wb") as f:
    f.write("\n".join(missingFiles))
    f.close()