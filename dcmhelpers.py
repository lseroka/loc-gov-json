'''
Authors: DCMS; Maco, Chos
Date Created: September 2018
Dependencies:
    Python 3.6
Description:
    Module with functions to aid other DCMS scripts, and fulfil some routine tasks
    dcmhelpers.py has only functions, and no other primary use.
Functionality:
    Put dcmhelpers.py in a folder on which your Python environment can operate
    Use 'import dcmhelpers' and call functions with dcmhelpers.FUNCTION syntax.
'''
import sys
import os
import time
import datetime
import json
from tkinter import *
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import requests

def testResult(continued='unknown', prompt='Did the first result of whatever you are automating work? Enter "Y" or "N":'):
    '''Functionality: Facilitate a loop that asks a user if the loop resulted in the desired outcome.
    Function prompts user for input. If the input is anything but 'Y', the script is quit.
    Requires a sentinal variable to exist in the main script, be passed as the "continued" parameter, and be assigned to the value the function returns.
    Example use:
        "test = 'unknown'
        for thing in things:
            do some things to the thing
            test = testResult(test)"
    Parameters:
        -continued; the sentinal string variable. must be declared in the main script before this function is called.
		-prompt; the prompt to continue that is displayed to the user. default value == 'Did the first result of whatever you are automating work? Enter "Y" or "N"'
    Returns:
        -continued; the updated value for the sentinal string variable.
    '''
    if (continued == '') or (continued == None) or (continued[0] != "Y" and continued[0] != "y"):
        continued = input(prompt + "\n").lower()
    while True:
        if continued[0] != "y" and continued[0] != "n":
            continued = input('you did not enter Y or N. Please enter "Y" or "N":\n')
        elif continued[0] == "n":
            print('~~~!!!! User selected "No" - script exiting !!!!~~~')
            sys.exit()
        elif continued[0] == "y":
            return continued

def getInputFileGUI(prompt="Select a file:"):
    '''Functionality: Open a gui prompt for an input file, get the input, close the window, and return the filepath
    Parameters:
        -prompt; a string containing the text you wish displayed in the GUI. default value == "Select a file:"
    Returns:
        -inFile; a string containing the filepath selected by the user
    '''
    root = Tk()
    ftypes = [
        ('All files', '*'),
        ('csv', '*.csv'),
        ('Text files', '*.txt'),
        ('XML files', '*.xml')
    ]
    inFile = askopenfilename(title = prompt, filetypes = ftypes)
    root.destroy()
    return inFile

def saveFileGUI(prompt="Save file as:"):
    '''Functionality: Open a gui prompt asking to save an output file, get the input from the user, close the window, and return the filepath and file name
    Parameters:
        -prompt; a string containing the text you wish displayed in the GUI. default value == "Save file as:"
    Returns:
        -outFile; a string containing the filepath input by the user
    '''
    root = Tk()
    ftypes = [
        ('All files', '*'),
        ('csv', '*.csv'),
        ('Text files', '*.txt')
    ]
    outFile = asksaveasfilename(title = prompt, filetypes = ftypes)
    root.destroy()
    return outFile

def saveInDirectory(prompt="Select a directory to save the output file in:"):
    '''Functionality: Open a gui prompt asking for a directory to save a file in,
    get the input, close the window, and return the directory path.
    If the user selects 'Cancel;, file is written to python's current working directory.
    Parameters:
        -prompt; a string containing the text you wish displayed in the GUI. default value == "Select a directory to save the output file in:"
    Returns:
        -outPath; a string containing the directory path input by the user
    '''
    root = Tk()
    outPath = askdirectory(title = prompt)
    root.destroy()
    return outPath

def getOutput(filename=None, extension=".csv", output_dir=None):
    '''Functionality: Get a filename, filetype, and path for an output file,
    and format the name according to DCMS style convention. ex: 'OUTPUT-unmanaged_list-2019-02-06-10-10-39.csv'
    If no filename parameter is passed, the user is prompted for one.
    if no output directory parameter is passed, the user is prompted for one.
    If no extension parameter is passed, the default format is CSV.
    Parameters:
        -filename; a string containing the filename for the output file. default value == None
        -extension; a string containing the desired file extension. default value == '.csv'
        -output_dir; a string containing the desired output directory. default value == None
    Returns:
        -outputpath; a string containing the desired filepath formatted in DCMS style convention
    '''
    if filename == None:
        filename = input("Input a title, with no file extension, for the output file")
    if output_dir == None:
        output_dir = saveInDirectory()
    filename = filename.replace(" ","_")
    time = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    outputname = 'OUTPUT-' + filename + ('-%s' % time) + extension
    outputpath = os.path.join(output_dir, outputname)
    return outputpath

def testRequiredInput(fieldnames, required_fieldnames):
    '''Functionality: Test if fieldnames in input list are all present in the required list.
    Intended to be used to test CSV files input by a user against elements reqiured for a script to function.
    If passed parameters are not lists, the entire script exits
    If a required_fieldname value is missing from fieldnames, it is reported to the user and the entire script exits
    Parameters:
        -fieldnames; a python list to be tested against required_fieldnames
        -required_filednames; a python list against which fieldnames is tested
    '''
    if type(fieldnames) != list or type(required_fieldnames) != list:
        print('Fieldnames are not formatted as a Python list - script exiting.')
        sys.exit()
    missing = []
    for field in required_fieldnames:
        if field not in fieldnames:
            missing.append(field)
    if missing != []:
        print('Required fieldnames missing from input file - see script for formatting')
        print('Missing fieldnames are', missing)
        print('Script exiting.')
        sys.exit()

def get_loc_gov_json(itemID, headers = {'Accept': 'application/json'}):
    '''Functionality: Get Loc.gov JSON metadata for an item.
    Requests JSON from loc.gov and returns the metadata as a dictonary.
    If errors are encountered, they are reported to the user without raising an exception.
    !!!This function is experimental and could use some evaluation and refinement!!!
    Parameters:
        -itemID; loc.gov item identifer as a string or integer
        -headers; value for python requests library parameter. Default value == {'Accept': 'application/json'}
    Returns:
        -data: a dictonary or string containing the results of the request
            =dictonary if request is successful
            ='Error' if request was unsuccessful
    '''
    print("getting json from LOC.gov for item:", itemID)
    tested_item = str(itemID).replace(' ','')
    #use the lccn to get the Loc.gov catalog json
    url = 'https://www.loc.gov/item/' + tested_item + '/?fo=json'
    try:
        data = None
        while data is None:
            try:
                response = requests.get(url, headers=headers)
                if 'seeing this error' in response.text:
                    data = "Error"
                else:
                    data = json.loads(response.text)
            except:
                print('LOC.gov response is taking longer than expected, waiting 5 seconds to retry request')
                time.sleep(5)
                pass
            try:
                if data == 'Error':
                    print('Error retrieving JSON from LOC.gov for this item:', itemID)
                    return data
                elif 'status' in data and data['status'] == 404:
                    print('404 error on LOC.gov for this item:', itemID)
                    return data
                else:
                    return data
            except:
                print('Unexpected error with data from this item:', itemID)
                data = 'Error'
                return data
    except:
        print('getLOCGOVjson function failed on this item:', itemID)
        print('Review the function for bugs and try again.')
        data = "Error"
        return data

def get_marcxml_from_loc_gov_json(loc_gov_json):
    '''Functionality: Use an item's loc.gov JSON metadata dictonary to get its MARCXML data.
    Requests MARCXML from loc.gov and returns the metadata as a string.
    If errors are encountered, they are reported to the user without raising an exception.
    !!!This function is experimental and could use some evaluation and refinement!!!
    Parameters:
        -loc_gov_json; loc.gov JSON dictonary (probably output of get_loc_gov_json())
    Returns:
        -xml: if request was successful, a string containing the results of the request
        -None: if request was unsuccessful
    '''
    try:
        formats = loc_gov_json['item']['other_formats']
        for formt in formats:
            #if a link to the marcxml exists, record that value in a variable for the log, and get the xml
            if formt['label'] == "MARCXML Record":
                MARCXMLurl = formt['link']
                try:
                    data = None
                    while data is None:
                        try:
                            print('getting marcXML from URL:', MARCXMLurl)
                            response = requests.get(str(MARCXMLurl))
                            xml = response.content
                            return xml
                        except:
                            print('XML response is taking longer than expected, waiting 5 seconds to retry request')
                            t.sleep(5)
                            pass
                except:
                    print('Unexpected error getting XML for URL', MARCXMLurl)
    except KeyError as e:
        print('Tried to get marcXML, but JSON from LOC.gov does not have the following needed data:', e)
        return None
    else:
        print('No link to XML in LOC.gov JSON')
        return None

def run_service():
    '''Functionality: Get input from a user that indicates if a script should send API service requests,
    or only run as a test without sending requests. Intended to be used with request functions in ctspost.py,
    especially as a parameter for new_service_request(), but could also be used with other APIs.
    If user inputs any value besides "y" or "t", the entire script exits.
    Returns:
        -runservice[0]: the first letter of the value input by the user
    '''
    runservice = input('''Input an option:
    "Y" if you want to run the script normally.
    "T" if you want to run the script in test mode, which doesn't make changes to CTS.
    "N" if you want to exit the script without running it.
    ''').lower()
    while True:
        if runservice[0] != "y" and runservice[0] != "n" and runservice[0] != "t":
            runservice = input('you did not enter Y, T, or N. Please enter "Y", "T", or "N":\n').lower()
        elif runservice[0] == "n":
            print('~~~!!!! User selected "N" - script exiting !!!!~~~')
            sys.exit()
        elif runservice[0] == "y" or runservice[0] == "t":
            return runservice[0]
