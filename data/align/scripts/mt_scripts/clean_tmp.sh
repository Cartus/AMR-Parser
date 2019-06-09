#!/bin/bsh

for file in *; do if [[ "$file" == _* ]]; then rm $file; fi; done