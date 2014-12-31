"""
Created on Mar 21, 2014

@author: Mohammad Rafay Aleem
"""
from string import ascii_lowercase
import os

import jinja2


policy_string = '%s = UpdatePolicy("%s", (%s), %s, %s, %s, "%s", "%s", "%s", "%s", "%s")'
rules_alpha = list(ascii_lowercase)

cwd = os.getcwd()


class Match(object):
    srcip, dstip, protocol, dstport, srcport, time = range(6)


class Rule(object):
    def __init__(self, ipprefix, rule):
        self.ipprefix = ipprefix
        self.srcip = str(rule['from'])
        self.dstport = str(rule['dstport'])
        self.srcport = str(rule['srcport'])
        self.time = str(rule['time'])
        self.latency = str(rule['latency'])
        self.loss = str(rule['loss'])
        self.cost = str(rule['cost'])
        self.routes = rule['routes']
        self.default = rule['default']
        self.update_interval = str(rule['update_interval'])
        self.policy_type = str(rule['policy_type'])
        self.check_interval = str(rule['check_interval'])


def generate(as_name, outbound_data):
    data = outbound_data
    rule_strings_list = []
    i = 0

    for ipprefix, protocol_rules in data['outbound'].iteritems():
        for rule in protocol_rules:
            rule_strings_list.append(get_rule(ipprefix, rule, i))
            i += 1

    rule_strings_list.append(rules_alpha[len(rule_strings_list)] + ' = drop')
    rule_strings_list.reverse()

    template_loader = jinja2.FileSystemLoader(searchpath="/")
    template_env = jinja2.Environment(loader=template_loader)

    template_file = cwd + '/policy_template.jinja'
    template = template_env.get_template(template_file)

    template_vars = {"as_name": as_name,
                     "rule_strings_list": rule_strings_list,
                     "rules_alpha": rules_alpha[0]}

    output_text = template.render(template_vars)

    f = open(os.path.abspath(os.path.join(cwd, os.pardir)) + '/policies/' + as_name + '.py', 'w')
    f.write(output_text)
    f.close()


def get_rule(ipprefix, rule, i):
    r = Rule(ipprefix, rule)
    pred = ''
    match_list = []

    if r.srcip != '*':
        match_list.append(generate_match_case(Match.srcip, r.srcip))
    if r.ipprefix != '*':
        match_list.append(generate_match_case(Match.dstip, r.ipprefix))
    if r.time != '*':
        match_list.append(generate_match_case(Match.time, r.time))
    if r.dstport != '*':
        match_list.append(generate_match_case(Match.dstport, r.dstport))
    if r.srcport != '*':
        match_list.append(generate_match_case(Match.srcport, r.srcport))

    match_list = [' & ' + match if j > 0 else match for j, match in enumerate(match_list)]

    pred = ''.join(match_list)

    routes = str(r.routes)
    default = str(r.default)

    r_str = policy_string % (rules_alpha[i], r.ipprefix, pred, rules_alpha[i+1], routes, default, r.latency, r.loss,
                             r.update_interval, r.check_interval, r.policy_type)

    return r_str


def generate_match_case(case, value):
    if case == Match.srcip:
        return 'match(srcip=IPPrefix("%s"))' % value
    elif case == Match.dstip:
        return 'match(dstip=IPPrefix("%s"))' % value
    elif case == Match.dstport:
        return 'match(dstport=%s)' % value
    elif case == Match.srcport:
        return 'match(srcport=%s)' % value
    elif case == Match.time:
        return 'match(time=HRange(%s))' % value
    else:
        raise NotImplementedError("Case not implemented in generate_match_case function!")





