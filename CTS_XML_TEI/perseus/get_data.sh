#!/bin/sh

find greekLit -type f | xargs grep -l 'TEI P4//DTD' | grep 'perseus-grc' >greekLit.txt
find latinLit -type f | xargs grep -l 'TEI P4//DTD' | grep 'perseus-lat' >latinLit.txt

