'''
/*
 * Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License").
 * You may not use this file except in compliance with the License.
 * A copy of the License is located at
 *
 *  http://aws.amazon.com/apache2.0
 *
 * or in the "license" file accompanying this file. This file is distributed
 * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
 * express or implied. See the License for the specific language governing
 * permissions and limitations under the License.
 */
'''

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import sys
import logging
import time
import json
import argparse


host = 'YOURHOST'
rootCAPath = 'YOURCA'
certificatePath = 'YOURCERT'
privateKeyPath = 'YOURKEY'
useWebsocket = False
clientId = 'YOURCLIENTID'
thingName = 'YOURTHINGNAMG'

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTShadowClient
myAWSIoTMQTTShadowClient = None
if useWebsocket:
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId, useWebsocket=True)
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 443)
    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath)
else:
    myAWSIoTMQTTShadowClient = AWSIoTMQTTShadowClient(clientId)
    myAWSIoTMQTTShadowClient.configureEndpoint(host, 8883)
    myAWSIoTMQTTShadowClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTShadowClient configuration
myAWSIoTMQTTShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTShadowClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTShadowClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect to AWS IoT
myAWSIoTMQTTShadowClient.connect()
bulbColor = "green"

# Confiugre last will message
JSONPayload = '{"state":{"reported":{"connected": "no"}}}'
myAWSIoTMQTTShadowClient.configureLastWill('bulb/lastwill', JSONPayload, 1)


# Create a deviceShadow with persistent subscription
deviceShadowHandler = myAWSIoTMQTTShadowClient.createShadowHandlerWithName(thingName, True)

# Shadow JSON schema:
#
# Name: Bot
# {
#	"state": {
#		"desired":{
#			"color": "green"
#		}
#	}
#}

# Custom Shadow callback
def customShadowCallback_Update(payload, responseStatus, token):
# payload is a JSON string ready to be parsed using json.loads(...)
# in both Py2.x and Py3.x
    if responseStatus == "timeout":
        print("Update request " + token + " time out!")
    if responseStatus == "accepted":
        payloadDict = json.loads(payload)
	print("~~~~~~~~~~~~~~~~~~~~~~~")
	print("Update request with token: " + token + " accepted!")
	print(payloadDict)
	print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
	print("Update request " + token + " rejected!")

def customShadowCallback_Delete(payload, responseStatus, token):
    if responseStatus == "timeout":
        print("Delete request " + token + " time out!")
    if responseStatus == "accepted":
        print("~~~~~~~~~~~~~~~~~~~~~~~")
        print("Delete request with token: " + token + " accepted!")
        print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")
    if responseStatus == "rejected":
        print("Delete request " + token + " rejected!")


# Custom Shadow callback
def customShadowCallback_Delta(payload, responseStatus, token):
    
    # debug message
    print(responseStatus)
    payloadDict = json.loads(payload)
    print("++++++++DELTA++++++++++")
    print(payloadDict)
    print("+++++++++++++++++++++++\n\n")
    
    # apply color change to device
    deltaColor = payloadDict["state"]["color"]
    bulbColor = deltaColor

    # publish current device color
    JSONPayload = '{"state":{"reported":{"color":"' + deltaColor + '"}}}'
    deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)


# Listen on deltas
deviceShadowHandler.shadowRegisterDeltaCallback(customShadowCallback_Delta)


def customShadowCallback_Get(payload, responseStatus, token):
    
    # debug message
    print(responseStatus)
    print("++++++++GET+++++++++")
    payloadDict = json.loads(payload)
    print(payloadDict)

    # apply color change to device
    if "reported" in  payloadDict["state"]:
        bulbColor = payloadDict["state"]["reported"]["color"]
    if "delta" in  payloadDict["state"]:
        bulbColor = payloadDict["state"]["delta"]["color"]
    if "desired" in  payloadDict["state"]:
        bulbColor = payloadDict["state"]["desired"]["color"]


deviceShadowHandler.shadowGet(customShadowCallback_Get, 5)

# Reinitialize shadow JSON doc
# deviceShadowHandler.shadowDelete(customShadowCallback_Delete, 5)
# JSONPayload = '{"state":{"reported":{"color":"green", "connected": "yes"}}}'
# deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)
JSONPayload = '{"state":{"reported":{"color":"green", "connected": "yes"}}}'
deviceShadowHandler.shadowUpdate(JSONPayload, customShadowCallback_Update, 5)

# Loop forever
while True:
    time.sleep(1)
