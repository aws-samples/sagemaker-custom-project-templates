import argparse
import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def read_parameters(param_file):
    '''  '''
    print("Reading param_file : ", param_file)
    with open(param_file) as f:
        params = json.load(f)

    parameters = params['Parameters']
    tags = params['Tags']

    paramlist = []
    for key in parameters:
        p = {
            'ParameterKey' : key,
            'ParameterValue' : parameters[key],
            'UsePreviousValue' : False
        }
        paramlist.append(p)

    taglist = []
    for key in tags.keys():
        t = {
                'Key' : key,
                'Value' : tags[key]
            }
        taglist.append(t)

    return paramlist, taglist

def main():
    ''' '''
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack-name")
    parser.add_argument("--region")
    parser.add_argument("--param-file")
    parser.add_argument("--project-id")
    args, _ = parser.parse_known_args()

    cfn_client = boto3.client('cloudformation', region_name = args.region)
    parameters, tags = read_parameters(args.param_file)

    cfn_client.create_stack(
        StackName = args.stack_name + '-' + args.project_id,
        TemplateBody = open('endpoint-config-template.yml').read(),
        Parameters = parameters,
        Tags = tags 
    )

if __name__ == '__main__':
    main()
