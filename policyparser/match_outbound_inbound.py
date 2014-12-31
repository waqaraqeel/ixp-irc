"""
Created on Mat 21, 2014

@author: Mohammad Rafay Aleem
"""


def match(participant, outbound_data, inbound_data):

    # print outbound_data['outbound']

    log_list = []
    conflict_dict = {}

    for key, value in inbound_data.iteritems():
        if key != participant:
            conflict_dict[key] = False

    for ipprefix, protocol_rules in outbound_data['outbound'].iteritems():
        for rule in protocol_rules:
            for route in rule['routes']:
                # if route in inbound_data:  # This should always be true based on initial assertion tests.
                item_list = []
                for item in inbound_data[route]:
                    if ipprefix in item.values():
                        item_list.append(item)
                    else:
                        continue
                if len(item_list) > 0:
                    for filtered_item in item_list:
                        if participant in filtered_item['blacklist']:
                            conflict_dict[route] = True
                            break
                        if filtered_item['whitelist'] != '*':
                            if participant in filtered_item['whitelist']:
                                continue
                            else:
                                conflict_dict[route] = True
                                break
                else:
                    conflict_dict[route] = True
                    break


    print participant, conflict_dict

    for key, value in conflict_dict.iteritems():
        if value is True:
            return False
    return True
