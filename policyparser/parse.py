"""
Created on Mar 20, 2014

@author: Mohammad Rafay Aleem
"""
from match_outbound_inbound import match
from policy_generator import generate

import json
from os import listdir, path
from os.path import isfile, join


def main(as_names, outbound_files, inbound_files):
    """Entry point for the policy parser
    :params outbound_files: is a list
    :params inbound_files: is a dictionary
    """

    cached_inbound_files = {key: json.loads(open(value).read()) for key, value in inbound_files.iteritems()}

    for i, f in enumerate(outbound_files):
        json_data = open(f).read()
        outbound_data = json.loads(json_data)
        if match(as_names[i], outbound_data, cached_inbound_files) is True:
            generate(as_names[i], outbound_data)
        else:
            continue

if __name__ == '__main__':
    in_policy_dir = 'jsonpolicies/inbound'
    out_policy_dir = 'jsonpolicies/outbound'

    only_files = [join(out_policy_dir, f) for f in listdir(out_policy_dir) if isfile(join(out_policy_dir, f))]
    outbound_files = [f for f in only_files if f.endswith('.json')]
    as_names = [path.split(f)[1].split('.')[0].upper() for f in outbound_files]

    only_files = [join(in_policy_dir, f) for f in listdir(in_policy_dir) if isfile(join(in_policy_dir, f))]
    inbound_files = [f for f in only_files if f.endswith('.json')]
    in_as_names = [path.split(f)[1].split('.')[0].upper() for f in inbound_files]

    for name in in_as_names:
        assert(name in as_names)

    inbound_files = {key: value for (key, value) in zip(in_as_names, inbound_files)}

    main(as_names, outbound_files, inbound_files)
