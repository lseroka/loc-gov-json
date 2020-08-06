#!/usr/bin/env python3
# encoding: utf-8

import requests
import json
import time
import os
import sys

# Get the JSON for any loc.gov URL
# Will retry until it has valid JSON
# Returns the JSON, or 404 if status == 404
def get_locgov_json(url):
    print(url)
    r = None
    loc_json = None
    while loc_json == None:
        try:
            r = requests.get(url)
        except:
            print('Time out, waiting 5 seconds')
            time.sleep(5)
            pass
        if r is not None:
            try:
                loc_json = json.loads(r.text)
            except:
                #print(r)
                #print(r.content)
                print('Time out, waiting 5 seconds')
                time.sleep(5)
                pass
    if 'status' in loc_json and loc_json['status'] == 404:
        return 404
    return loc_json

# Return JSON for a defined and pre-constructed search URL
def locgov_search(search_url):
    print(search_url)
    search = None
    while search == None:
        response = requests.get(search_url)
        try:
            search = json.loads(response.text)
        except:
            print('Time out, waiting 5 seconds')
            time.sleep(5)
            pass
    return search

# Return the Item JSON for a loc.gov /item
def locgov_item(item, locgov_server):
    url_start = 'https://%s.loc.gov/item/' % locgov_server
    url = url_start + item + '/?fo=json&at=item'
    item_json = get_locgov_json(url)
    if item_json == 404:
        return 404
    return item_json['item']

# Returns the Resources given an Item URL
# This should have file data for all files in all of the item's resources
def locgov_item_resources(item, locgov_server):
    url_start = 'https://%s.loc.gov/item/' % locgov_server
    url = url_start + item + '/?fo=json&at=resources'
    resources_json = get_locgov_json(url)
    if resources_json == 404:
        return 404
    return resources_json['resources']

# Get the Item for a given Resource
def locgov_resource_item_section(aggregate, resource_id, locgov_server):
    url_start = 'https://%s.loc.gov/resource/' % locgov_server
    url = url_start + aggregate + '.' + resource_id + '/?fo=json&at=item'
    item_json = get_locgov_json(url)
    if item_json == 404:
        return 404
    return item_json['item']
