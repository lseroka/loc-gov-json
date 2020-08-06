#!/usr/bin/env python3
# encoding: utf-8

# Pull Item and Resource CSVs from loc.gov JSON
# Follow prompts in script for data inputs
# See: https://staff.loc.gov/wikis/display/DCMSection/Pull+loc.gov+JSON+data+for+Items+and+Resources

import sys
import csv
import os
import json
import requests
from dcmhelpers import *
from locgov import *
import timeit

# TO ADD:
# output p1_item_id


# Search loc.gov based on a starting seed URL
def paged_search(seed, item_writer, resource_writer, catalog_option, locgov_server, segments_option_choice):
    # search_counter = '10'
    # current_page = 1
    # # If basic search or if a collection, weed out unnecessary JSON parts
    # if 'loc.gov/collections/' in seed:
    #     exclude = '&at!=expert_resources,topics,featured_items,facet_views,views,pages,next,content,next_sibling,previous_sibling,facets'
    # if 'loc.gov/search' in seed:
    #     exclude = '&at!=views,facet_views,facets'
    # # Build up the URL based on the excludes, results per page, and current page
    # url_args = '&fo=json&all=true&c=' + search_counter + exclude
    # url_page = '&sp=' + str(current_page)
    # search_url = seed + url_args
    # starter_url = search_url + url_page

    search_counter = '10'
    current_page = 1
    url_args = '&fo=json&all=true&c=' + search_counter
    url_page = '&sp=' + str(current_page)
    search_url = seed + url_args
    starter_url = search_url + '&at=pagination,search'

    # Get the first page of results, to get info on total results and total pages
    starter_search = locgov_search(starter_url)
    totals = starter_search['search']
    pages = starter_search['pagination']
    total_pages = pages['total']

    print('Search query: ', totals['in'])
    print('Total hits: ', totals['hits'])
    print('Total pages: ', total_pages)

    if totals['hits'] == 0:
        resultrow = {
            'p1_item': seed,
            'p1_resource' : 'NO RESULT FOR SEARCH'
        }
        item_writer.writerow(resultrow)
        resource_writer.writerow(resultrow)
        print(resultrow)
    else:
        # Proceed with search for each page of results
        while current_page <= total_pages:
            #this_url = search_url + url_page + exclude
            this_url = search_url + url_page + '&at=results'
            search = locgov_search(this_url)
            results = search['results']
            for result in results:
                write_resource_rows(result, item_writer, resource_writer, catalog_option, locgov_server, segments_option_choice)
            current_page += 1
            url_page = '&sp=' + str(current_page)

# Write the rows to the files for each search result
def write_resource_rows(result, item_writer, resource_writer, catalog_option, locgov_server, segments_option_choice):
    p1_item = result['id']
    p1_item_id = p1_item.split('/')[-2]
    # If not an item (such as a Framework page), skip
    if 'item' not in p1_item and 'lccn.loc.gov' not in p1_item:
        print('Not an item: ', p1_item)
        return
    # If its a catalog record, skip based on decision
    if 'lccn.loc.gov' in p1_item and catalog_option == '2':
        print('Skipping catalog item: ', p1_item)
        return

    # Pull all data out of the result JSON
    p1_resources = []
    digitized = ''
    number_lccn = ''
    number_fileID = ''
    number_uuid = ''
    online_format = []
    mime_type = []
    partof = []
    group = []
    if 'digitized' in result:
        digitized = result['digitized']
    if 'number_lccn' in result:
        number_lccn = result['number_lccn']
    if 'number_fileID' in result:
        number_fileID = result['number_fileID']
    if 'number_uuid' in result:
        number_uuid = result['number_uuid']
    if 'online_format' in result:
        online_format = result['online_format']
    if 'mime_type' in result:
        mime_type = result['mime_type']
    if 'partof' in result:
        partof = result['partof']
    if 'group' in result:
        group = result['group']
    if 'resources' in result and result['resources'] is not None:
        for resource in result['resources']:
            p1_resources.append(resource)
    # print('p1 item: ', p1_item)
    # print('p1 resources: ', p1_resources)
    resultrow = {
        'p1_item_id': p1_item_id,
        'p1_item': p1_item,
        'digitized': digitized,
        'number_lccn': number_lccn,
        'number_fileID': number_fileID,
        'number_uuid': number_uuid,
        'online_format': online_format,
        'mime_type': mime_type,
        'partof': partof,
        'group': group,
    }
    if len(p1_resources) == 0:
        resultrow.update({
            'p1_resource': 'NONE',
            'p1_resource_count': 0,
        })
        item_writer.writerow(resultrow)
        #resource_writer.writerow(resultrow)
        print(resultrow)
        return

    # For each of the resources, get data and write its own row
    short_resources = []
    for resource in p1_resources:
        resourcerow = resultrow.copy()
        p1_resource = ''
        etl_aggregate = ''
        p1_resource_id = ''
        p1_resource_caption = ''
        p1_resource_segment_count = 0
        has_fulltext = False
        if 'caption' in resource:
            p1_resource_caption = resource['caption']
        if 'segments' in resource:
            p1_resource_segment_count = resource['segments']
        elif 'files' in resource:
            p1_resource_segment_count = resource['files']
        if 'url' in resource:
            p1_resource = resource['url']
            p1_resource_section = p1_resource.split('/')[-2]
            if '.' in p1_resource_section:
                etl_aggregate, p1_resource_id = p1_resource_section.split('.', 1)
        if 'fulltext_file' in resource and resource['fulltext_file'] != '':
            has_fulltext = True

        short_resources.append({
            'p1_resource': p1_resource,
            'p1_resource_caption': p1_resource_caption,
            'p1_resource_segment_count': p1_resource_segment_count,
        })

        resourcerow.update({
            'p1_resource': p1_resource,
            'etl_aggregate': etl_aggregate,
            'p1_resource_id': p1_resource_id,
            'p1_resource_caption': p1_resource_caption,
            'p1_resource_segment_count': p1_resource_segment_count,
            'has_fulltext': has_fulltext
        })
        if 'representative_index' in resource:
            resourcerow.update({
                'representative_index': resource['representative_index']
            })

        if segments_option_choice == '2':
            # Add more resource and segment data here
            this_resource = None
            p1_resource_segment_with_text = 0
            if p1_resource != '':
                full_resources = locgov_item_resources(p1_item_id, locgov_server)
                for full_resource in full_resources:
                    if 'url' in full_resource and full_resource['url'] == p1_resource:
                        this_resource = full_resource
            if this_resource != None:
                for f in this_resource['files']:
                    for s in f:
                        if 'use' in s and s['use'] == 'text':
                            p1_resource_segment_with_text += 1
            resourcerow.update({
                'p1_resource_segment_with_text': p1_resource_segment_with_text,
            })


        resource_writer.writerow(resourcerow)
        print(resourcerow)
    resultrow.update({
        'p1_resource_count': len(short_resources),
        'p1_resource': short_resources
    })
    item_writer.writerow(resultrow)
    print(resultrow)


valid_methods = ['1', '2', '3', '4', '5']
search_inputs = ['1', '2', '3']
file_inputs = ['4', '5']
print('This script will return lists of loc.gov Items and Resources based on your criteria')
method_prompt = """
Enter number for methods to get Items/Resources:
    1. Enter loc.gov COLLECTION
    2. Enter loc.gov PART OF
    3. Enter loc.gov SEARCH QUERY
    4. Select list of loc.gov ITEMS
    5. Select list of loc.gov SEARCH QUERIES"""
print(method_prompt)
method_input = input()
if method_input not in valid_methods:
    print('Wrong input! : ', method_input)

if method_input == '1':
    collection_prompt = """
    Enter loc.gov COLLECTION
        Input exactly as shown in loc.gov/collecton URL, including -'s
        Ex: https://www.loc.gov/collections/rare-book-selections/
        Enter: rare-book-selections"""
    print(collection_prompt)
    p1_collection = input()

if method_input == '2':
    partof_prompt = """
    Enter loc.gov PART OF
        Input exactly as shown in loc.gov search URL, including +'s
        Ex: https://www.loc.gov/search/?fa=partof:world+digital+library
        Enter: world+digital+library"""
    print(partof_prompt)
    p1_partof = input()

if method_input == '3':
    search_prompt = """
    Enter loc.gov SEARCH QUERY
        Input exactly as shown in loc.gov search URL, including +'s
        Include quotes if required or if searching for exact identifier
        This will also search full text of items so you may get unexpected results for broad searches!
        Ex: https://www.loc.gov/search/?in=&q="france+in+america"
        Enter: "france+in+america" """
    print(search_prompt)
    p1_search = input()

if method_input == '4':
    print('Select CSV file with item_id list')
    print('Should match expected data to follow loc.gov/item/....')
    item_file = getInputFileGUI(prompt="Select CSV file with item list: ")
    required_input_fieldnames = ['item_id']
    item_list = []
    with open(item_file, 'r', encoding='utf-8-sig') as item_file:
        reader = csv.DictReader(item_file)
        testRequiredInput(reader.fieldnames, required_input_fieldnames)
        for row in reader:
            item_list.append(row['item_id'])

if method_input == '5':
    print('Select CSV file with query list')
    print('Likely use case is a list of identifiers that do not match to item or resource urls')
    query_file = getInputFileGUI(prompt="Select CSV file with query list: ")
    required_input_fieldnames = ['query']
    query_list = []
    with open(query_file, 'r', encoding='utf-8-sig') as query_file:
        reader = csv.DictReader(query_file)
        testRequiredInput(reader.fieldnames, required_input_fieldnames)
        for row in reader:
            query_list.append(row['query'])

segments_option_valid = ['1', '2']
segments_option_prompt = """
Enter the number for whether to get full resource segment list.
This will be much slower, but give more data. Use this for full text / transcription information.
    1. Do NOT pull segments data (FASTER)
    2. Pull segments data (SLOWER)"""
print(segments_option_prompt)
segments_option_choice = input()
if segments_option_choice not in segments_option_valid:
    print('Wrong input! : ', segments_option_choice)
    exit()

locgov_server_valid = ['1', '2', '3']
locgov_server_prompt = """
Enter number for methods to get Items/Resources:
    1. PRODUCTION (www.loc.gov)
    2. TEST (test.loc.gov)
    3. DEV (dev.loc.gov)"""
print(locgov_server_prompt)
locgov_server_choice = input()
if locgov_server_choice not in locgov_server_valid:
    print('Wrong input! : ', locgov_server_choice)
    exit()

if locgov_server_choice == '1':
    locgov_server = 'www'
if locgov_server_choice == '2':
    locgov_server = 'test'
if locgov_server_choice == '3':
    locgov_server = 'dev'

catalog_valid = ['1', '2']
catalog_option_prompt = """
Enter number for whether to include lccn.loc.gov item
    You may want to include this to find un-ETLed items that redirect to the Catalog
    Probably don't include if you know you have a lot of expected un-ETLed items
    Include lccn.loc.gov items?
    1. YES
    2. NO"""
print(catalog_option_prompt)
catalog_option = input()
if catalog_option not in catalog_valid:
    print('Wrong input! : ', catalog_option)


print('Select output location for ITEMS list')
item_output = getOutput(filename='loc_gov_items')
item_output_fieldnames = ['p1_item_id', 'p1_item', 'p1_resource_count', 'p1_resource', 'digitized',
    'number_lccn', 'number_fileID', 'number_uuid',
    'online_format', 'mime_type', 'partof', 'group',
]

print('Select output location for RESOURCES list')
resource_output = getOutput(filename='loc_gov_resources')
resource_output_fieldnames = ['p1_item_id', 'p1_item', 'p1_resource', 'etl_aggregate', 'p1_resource_id',
    'p1_resource_caption', 'p1_resource_segment_count', 'digitized',
    'number_lccn', 'number_fileID', 'number_uuid',
    'online_format', 'mime_type', 'partof', 'group',
    'has_fulltext', 'representative_index',
]

if segments_option_choice == '2':
    resource_output_fieldnames.append(
        'p1_resource_segment_with_text'
    )

with open (item_output, 'w', encoding='utf-8-sig') as item_output:
    item_writer = csv.DictWriter(item_output, fieldnames=item_output_fieldnames, lineterminator='\n')
    item_writer.writeheader()

    with open (resource_output, 'w', encoding='utf-8-sig') as resource_output:
        resource_writer = csv.DictWriter(resource_output, fieldnames=resource_output_fieldnames, lineterminator='\n')
        resource_writer.writeheader()

        # Build the search seed URL based on input
        if method_input in search_inputs:
            if method_input == '1':
                url_start = 'https://%s.loc.gov/collections/' % locgov_server
                search_url = url_start + p1_collection + '/?'
            if method_input == '2':
                url_start = 'https://%s.loc.gov/search/?fa=partof:' % locgov_server
                search_url = url_start + p1_partof
            if method_input == '3':
                url_start = 'https://%s.loc.gov/search/?q=' % locgov_server
                search_url = url_start + p1_search

            paged_search(search_url, item_writer, resource_writer, catalog_option, locgov_server, segments_option_choice)

        # Get each item individually for item CSV
        if method_input == '4':
            for i in item_list:
                item = locgov_item(i, locgov_server)
                if item == 404:
                    resultrow = {
                        'p1_item': i,
                        'p1_resource': 'INVALID'
                    }
                    item_writer.writerow(resultrow)
                    resource_writer.writerow(resultrow)
                    print(resultrow)
                else:
                    write_resource_rows(item, item_writer, resource_writer, catalog_option, locgov_server, segments_option_choice)

        # Perform each search individually for search CSV
        if method_input == '5':
            for i in query_list:
                url_start = 'https://%s.loc.gov/search/?q=' % locgov_server
                i = i.replace(' ', '+')
                search_url = url_start + '"' + i + '"'
                paged_search(search_url, item_writer, resource_writer, catalog_option, locgov_server, segments_option_choice)
