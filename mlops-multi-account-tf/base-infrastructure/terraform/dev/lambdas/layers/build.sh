#!/bin/bash
export PYTHON_VERSION="3.11"
 
#Init Packages Directory
mkdir -p packages/
 
# For each folder in lambda-layers
for layer in layers/*/ ; do
    echo "Processing: ${layer}"
    echo
 
    # Install requriements in a directory layer-name/pacakge/python/*
    docker run --rm -v "${PWD}":/var/task "public.ecr.aws/sam/build-python${PYTHON_VERSION}" \
    /bin/sh -c "pip install -r ${layer}requirements.txt -t ${layer}package/python/lib/python${PYTHON_VERSION}/site-packages/; exit"
 
    # Zip
    cd ${layer}package/
    ZIP_NAME=$(echo "${layer}" | awk -F "/" '{print $2}') # folder name
    zip -qr ../../../packages/${ZIP_NAME}.zip .
    cd ../../..     # clean up
done
