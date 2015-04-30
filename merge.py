"""
    This file merge existing inventories into only one
"""

import xml.etree.ElementTree as ElementTree
from glob import glob
import re


spaces = re.compile(r'\s+', flags=re.UNICODE)

invPath = "CTS_XML_TextInventory/*.xml"
inventories = glob(invPath)

def getByFor(tag, attr, node, attrName="projid", ns="http://chs.harvard.edu/xmlns/cts3/ti"):
    return node.findall(
        ".//ti:{tag}[@{attrName}='{attr}']".format(
            tag=tag,
            attr=attr,
            attrName=attrName
        ), 
        {"ti" : ns}
    )


master = ElementTree.Element("TextInventory")
for inv in inventories:
    inventory = ElementTree.parse(inv)
    tgs = inventory.findall(".//ti:textgroup", {"ti" : "http://chs.harvard.edu/xmlns/cts3/ti"})
    tgs = [tg for tg in tgs if len(tg.findall(".//{http://chs.harvard.edu/xmlns/cts3/ti}online")) > 0]
    for tg in tgs:
        projid = tg.get("projid")

        # We check if we already have this textgroup in our new master
        existing = getByFor("textgroup", projid, master)
        if len(existing) >= 1:
            tgNodes = tg.findall("./*")
            for tgNode in tgNodes:
                tag = tgNode.tag
                if "work" not in tag:
                    tgNodeSTR = re.sub(spaces, '', ElementTree.tostring(tgNode).decode())
                    existingSTR = existing[0].findall(tag)
                    existingSTR = re.sub(spaces, '', "".join([ElementTree.tostring(node).decode() for node in existingSTR]))
                    if tgNodeSTR not in existingSTR:
                        existing[0].append(tgNode)
                else:
                    work = tgNode
                    projid = work.get("projid")
                    existingWork = getByFor("work", projid, existing[0])
                    if len(existingWork) == 0:
                        existing[0].append(work)
                    else:
                        wNodes = work.findall("./*")
                        for wNode in wNodes:
                            tag = wNode.tag
                            if "edition" not in tag and "translation" not in tag:
                                wNodeSTR = re.sub(spaces, '', ElementTree.tostring(wNode).decode())
                                existingWorkSTR = existingWork[0].findall(tag)
                                existingWorkSTR = re.sub(spaces, '', "".join([ElementTree.tostring(node).decode() for node in existingWorkSTR]))
                                if wNodeSTR not in existingWorkSTR:
                                    existingWork[0].append(wNode)
                            else:
                                text = wNode
                                projid = text.get("projid")
                                texts = existingWork[0].findall("./{tag}[@projid='{projid}']".format(tag=tag, projid=projid))
                                if len(texts) == 0:
                                    existingWork[0].append(text)

        else:
            master.append(tg)

        # if master.findall()
    

with open("sample.xml", "wb") as f:
    f.write(ElementTree.tostring(master))
    f.close()