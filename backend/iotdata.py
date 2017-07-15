import sys
import boto3
import simplejson as json
from datetime import import datetime

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "python iodata.py <bulb_color>"
        sys.exit(-1)
    desired_color = sys.argv[1]
    client = boto3.client('iot-data')
    thing_name = 'THINGNAME'
    
    # get shadow
    response = client.get_thing_shadow(thingName=thing_name)
    shadow = json.loads(response['payload'].read())
    print shadow

    # shadow checking
    if "desired" not in shadow["state"]:
        shadow["state"]["desired"] = dict()
        if "delta" in shadow["state"]:
            del shadow["state"]["delta"]
            if "color" in shadow["state"]["desired"]:
                reported_color = shadow["state"]["desired"]["color"]
                if reported_color == desired_color:
                    print "desired color is already same as reported color"
                    sys.exit(-1)

    # update shadow
    shadow["state"]["desired"]["color"] = desired_color
    payload = json.dumps(shadow)
    r = client.update_thing_shadow(
        thingName=thing_name,
        payload=payload
    )
    print(r)
