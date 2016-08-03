"""
Darcy: DART Bus Assistant
By Justin Tamayo and Jorge Troncoso

This code is meant to be uploaded to AWS Lambda, in conjunction with Amazon 
Alexa. 

Information for creating an AWS Lambda function for an Alexa skill can be found at
http://amzn.to/1LzFrj6

The Alexa Skills Kit Getting Started guide can be found at
http://amzn.to/1LGWsLG

Adapted from alexa-skills-kit-color-expert-python.py
"""

from __future__ import print_function

import csv
import requests
from bs4 import BeautifulSoup
import re

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "MyStopIsIntent":
        return set_stop_in_session(intent, session)
    elif intent_name == "MyRouteIsIntent":
        return set_route_in_session(intent, session)
    elif intent_name == "MyLineIsIntent":
        return set_route_in_session(intent, session)
    elif intent_name == "WheresMyBusIntent":
        return get_next_arrival(intent, session)
    elif intent_name == "WheresMyBusGivenBusRouteIntent":
        return get_next_arrival_given_route(intent, session)
    elif intent_name == "WheresMyBusGivenTrainLineIntent":
        return get_next_arrival_given_route(intent, session)  
    elif intent_name == "DoesMyRouteGoToStopIntent":
        return check_saved_route_to_stop(intent, session)
    elif intent_name == "GetFareIntent":
        return get_fare(intent, session)
    elif intent_name == "GetReducedFareIntent":
        return get_reduced_fare(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}


    speech_output = "Hello, my name is Darcy, your DART bus and train locator. "

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.

    reprompt_text = "Please tell me your bus or train stop ID by saying, " \
                    "my stop i.d. is 1 8 1 2 1. If you don't know your stop ID, " \
                    "open Google Maps and tap on your stop to get its ID number. " \
                    "Or ask me about fare information."

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"

    speech_output = "Thank you for trying me. Have a nice day! "

    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def set_stop_in_session(intent, session):
    """ Sets the stop in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    # Check if user-provided stop ID is valid, and save it in session attributes
    if intent['slots']['StopID'].get('value', ''):
        StopID = intent['slots']['StopID']['value']
        stopName = ''   # Stores DART-given name of stop, e.g. 'Forest @ Landa - W - NS'

        # Parse stops.txt for the given stop ID, and get the stop's name
        with open('dart_gtfs_data/stops.txt', 'rb') as f:
            reader = csv.reader(f)
            try:
                for row in reader:
                    if row[0] == StopID:
                        stopName = row[2]
                        break
            except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

        if stopName:
            session_attributes['StopID'] = StopID
            stopName = stopName.split(' -')[0]  # Strip the capital letters after the stop name
            speech_output = "Okay, I've set your stop ID to " + stopName.split(' -')[0] + "."
            reprompt_text = "Please tell me your route by saying, " \
                            "my bus route is 582 going northbound. " \
                            "Or, my train line is red going southbound."
        else:
            speech_output = "Sorry, that stop ID isn't valid. Please try again."
            reprompt_text = "That stop ID is not valid. " \
                            "You can tell me your stop ID by saying, " \
                            "my stop i.d. is 1 8 1 2 1. If you don't know your bus stop ID, " \
                            "open Google Maps and tap on your stop to get its ID number."
    else:
        speech_output = "I'm not sure what your bus or train stop ID is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your bus or train stop ID is. " \
                        "You can tell me your stop ID by saying, " \
                        "my stop i.d. is 1 8 1 2 1. If you don't know your bus stop ID, " \
                        "open Google Maps and tap on your stop to get its ID number."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def set_route_in_session(intent, session):
    """ Sets the route in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    routeNum = ''   # User-provided route number or train line, e.g. '582' or 'red'
    RouteNumID = '' # DART's five-digit ID for a bus or train route
    RouteDirID = '' # Either 0 or 1 to indicate direction, e.g. northbound/southbound

    # Set routeNum to user-provided route number or train line color
    if 'RouteNum' in intent['slots'] and intent['slots']['RouteNum'].get('value', ''):
        routeNum = intent['slots']['RouteNum']['value']
    elif 'TrainLine' in intent['slots'] and intent['slots']['TrainLine'].get('value', ''):
        # Train lines in routes.txt are in all caps
        routeNum = intent['slots']['TrainLine']['value'].upper()
        if routeNum == "M LINE":    # String fix if user specifies the M-Line streetcar
            routeNum == "M-LINE"

    # Check if user-provided route is valid, and get route's ID
    if routeNum:
        with open('dart_gtfs_data/routes.txt', 'rb') as f:
            reader = csv.reader(f)
            try:
                for row in reader:
                    if row[2] == routeNum:
                        RouteNumID = row[0]
                        break
            except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

    # Check if user-provided direction is valid, and get route's direction ID
    if 'RouteDir' in intent['slots'] and intent['slots']['RouteDir'].get('value', ''):
        # Directions in route_directions.txt are in all caps
        routeDir = intent['slots']['RouteDir']['value'].upper()
        with open('dart_gtfs_data/route_direction.txt', 'rb') as f:
            reader = csv.reader(f)
            try:
                for row in reader:
                    if (row[0] == routeNum) and (row[2] == routeDir):
                        RouteDirID = row[1]
                        break
            except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

    # If route and direction are valid, store in session attributes
    if RouteNumID and RouteDirID:
        # RouteNumDirID is needed when sending a URL request to m.dart.org
        # e.g. '123450', where RouteNumID = '12345' and RouteNumDirID = '0'
        RouteNumDirID = RouteNumID + RouteNumDirID
        session_attributes['RouteNumID'] = RouteNumID
        session_attributes['RouteNumDirID'] = RouteNumDirID
        
        if routeNum.isdigit():  # if RouteNumID represents a bus route
            speech_output = "Alright, I've set your bus route and direction to " + \
                            routeNum + ' going ' + routeDir + "."
            reprompt_text = "Please ask me when the next bus arrives by asking, " \
                            "where is my bus?"
        else:                   # RouteNumID represents a train
            speech_output = "Alright, I've set your train line and direction to " + \
                            routeNum + ' going ' + routeDir + "."
            reprompt_text = "Please ask me when the next train arrives by asking, " \
                            "where is my train?"
    else:
        speech_output = "I'm not sure what your route and direction is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your route and direction is. " \
                        "You can tell me your route and direction by saying, " \
                        "my bus route is 582 going northbound. " \
                        "Or, my train line is red going southbound."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_next_arrival(intent, session):
    """ Returns the next scheduled bus or train of the saved route and direction.
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    # Check if stop, route, and direction are already saved in session attributes, then get the next arrival!
    if ('StopID' in session['attributes']) and ('RouteNumID' in session['attributes']) and ('RouteNumDirID' in session['attributes']):
        StopID = session['attributes']['StopID']
        RouteNumID = session['attributes']['RouteNumID']
        RouteNumDirID = session['attributes']['RouteNumDirID']

        speech_output, reprompt_text = get_next_arrival_helper(StopID, RouteNumID, RouteNumDirID)
    else:
        speech_output = "You did not provide both a stop and route. " \
                        "Please enter stop and route information and try again."
        reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_next_arrival_helper(StopID, RouteNumID, RouteNumDirID):
    reprompt_text = None

    url = "http://m.dart.org/next_bustrain.asp?sSwitch=returnSchedule&sSignID=109" + \
              "&sBusLineID=" + RouteNumID + \
              "&sBusStopID=" + StopID + \
              "&sLineDirID=" + RouteNumDirID

    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    # Check if the HTTP response returned is valid
    try: 
        nextBusText = soup.body.find('div', attrs={'id':'maincontent'}).find('div', attrs={'id':'container'})
    except AttributeError as e:
        speech_output = "Sorry, the information you provided is not valid. " \
                        "Please re-enter the stop and route information and try again."
    else:
        # Check if the route is currently running by navigating down the HTML document.
        # If the route is not running, then relevant information is already in nextBusText.contents[0]
        try:
            nextBusText = nextBusText.find('div', attrs={'id':'row'}).find('div', attrs={'id':'span'}).find('br').contents[0]
        except AttributeError as e:
            speech_output = nextBusText.contents[0]
        else:
            # Check if the HTTP response includes an arrival time in terms of minutes to wait.
            # Else, return whatever is actually there.
            try:
                speech_output = "The next arrival is in " + re.split(r'(\d+)', nextBusText.split(' minute')[0])[-2] + " minutes."
            except IndexError:
                speech_output = nextBusText.contents[0]
    return speech_output, reprompt_text

def get_next_arrival_given_route(intent, session):
    """ Returns the next scheduled bus or train that the user asks for in the utterance.
        This function is similar to get_next_arrival().
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    routeNum = ''
    RouteNumID = ''
    RouteDirID = ''

    if 'RouteNum' in intent['slots'] and intent['slots']['RouteNum'].get('value', ''):
        routeNum = intent['slots']['RouteNum']['value']
    elif 'TrainLine' in intent['slots'] and intent['slots']['TrainLine'].get('value', ''):
        routeNum = intent['slots']['TrainLine']['value'].upper()
        if routeNum == "M LINE":
            routeNum == "M-LINE"

    if routeNum:
        with open('dart_gtfs_data/routes.txt', 'rb') as f:
            reader = csv.reader(f)
            try:
                for row in reader:
                    if row[2] == routeNum:
                        RouteNumID = row[0]
                        break
            except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

    if intent['slots']['RouteDir'].get('value', ''):
        routeDir = intent['slots']['RouteDir']['value'].upper()
        with open('dart_gtfs_data/route_direction.txt', 'rb') as f:
            reader = csv.reader(f)
            try:
                for row in reader:
                    if (row[0] == routeNum) and (row[2] == routeDir):
                        RouteDirID = row[1]
                        break
            except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))

    if RouteNumID and RouteDirID:
        RouteNumDirID = RouteNumID + RouteDirID
        if 'StopID' in session['attributes']:
            StopID = session['attributes']['StopID']

            speech_output, reprompt_text = get_next_arrival_helper(StopID, RouteNumID, RouteNumDirID)
        else:
            speech_output = "You did not provide a stop." \
                            "Please enter stop information and try again."
            reprompt_text = None
    else:
        speech_output = "I'm not sure what that route and direction is. " \
                        "Please try again."
        reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def check_saved_route_to_stop(intent, session):
    """ Checks if the saved route stops by a user-specified stop.
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    # Check if route and direction are already saved
    if ('RouteNumID' in session['attributes']) and ('RouteNumDirID' in session['attributes']):
        RouteNumID = session['attributes']['RouteNumID']
        RouteNumDirID = session['attributes']['RouteNumDirID']

        # Check if user-specified stop is valid, and check if route goes to stop
        if 'StopID' in intent['slots'] and intent['slots']['StopID'].get('value', ''):
            StopID = intent['slots']['StopID']['value']
            readableStopID = ' '.join(StopID)

            with open('dart_gtfs_data/stops.txt', 'rb') as f:
                reader = csv.reader(f)
                try:
                    for row in reader:
                        if row[0] == StopID:
                            stopName = row[2]
                            url = "http://m.dart.org/next_bustrain.asp?sSwitch=returnSchedule&sSignID=109" + \
                                "&sBusLineID=" + RouteNumID + \
                                "&sBusStopID=" + StopID + \
                                "&sLineDirID=" + RouteNumDirID
                            page = requests.get(url)
                            soup = BeautifulSoup(page.content, "html.parser")

                            # If try statement does not throw exception, then the saved route currently goes to the stop.
                            try:
                                nextBusText = soup.body.find('div', attrs={'id':'maincontent'}).find('div', attrs={'id':'container'}).find('div', attrs={'id':'row'}).find('div', attrs={'id':'span'}).find('br').contents[0]
                                speech_output = "Yes, your saved route goes to " + stopName.split(' -')[0] + "."
                                reprompt_text = None
                            except AttributeError:
                                speech_output = "No, your saved route does not go to " + stopName.split(' -')[0] + "."
                                reprompt_text = None
                            break
                    else:
                        speech_output = "The stop ID " + readableStopID + \
                            " is not valid. Please try again."
                        reprompt_text = None
                except csv.Error as e:
                    sys.exit('file %s, line %d: %s' % (filename, reader.line_num, e))
        else:
            speech_output = "You did not provide a stop i.d. " \
                        "Please provide a stop i.d. and try again."
            reprompt_text = None
    else:
        speech_output = "You did not provide a route. " \
                        "Please enter route information and try again."
        reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_fare(intent, session):
    """ Return general fare information.
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    speech_output = "For local service within Dallas, a dart ticket costs $2.50, and is valid for two hours. An all-day ticket costs $5.00. Midday passes, which are valid on weekdays from 9:30 am to 2:30 pm, cost $1.75."
    reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

def get_reduced_fare(intent, session):
    """ Return reduced fare information.
    """

    card_title = intent['name']
    if 'attributes' in session:
        session_attributes = session['attributes']
    else:
        session_attributes = {}
    should_end_session = False

    speech_output = "Seniors ages sixty five and older, persons with disabilities, and college students can pay half of the local fare with valid dart photo i.d."
    reprompt_text = None
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }