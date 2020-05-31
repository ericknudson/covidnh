import urllib.request, json 
from datetime import datetime, timedelta
import pytz
from twilio.rest import Client
import os

est = pytz.timezone("America/New_York")

#helper function to convert a raw GMT time into a timezone-aware EST time
def convert_timestamp(input_string):
    input_string = str(input_string) + '00'
    aware_timestamp = datetime.strptime(input_string, '%Y/%m/%d %H:%M:%S%z')
    localized_timestamp = aware_timestamp.astimezone(est)
    return(localized_timestamp)

def lambda_handler(event, context):
    #download latest data
    with urllib.request.urlopen("https://opendata.arcgis.com/datasets/a085f0a76f6b44efbdd185bf40243688_1.geojson") as url:
        data = json.loads(url.read().decode())

    #see if there's been an update in the last 24 hours
    latest_features = data['features'][-1]
    latest_properties = dict(latest_features['properties'])
    last_update_date = convert_timestamp(latest_properties['reportdt'])
    current_time = datetime.now().astimezone(est)
    twentyfourhrsago = current_time - timedelta(days=1)

    #if there's been an update in the last 24 hours, compose a message.
    if last_update_date > twentyfourhrsago: #if last_update_date.day == current_time.day:
        
        #first, calculate the number of newly-reported cases in the last 24 hours
        latest_cumulative_total = latest_properties['confirmed']
        i = -2
        yesterdays_total = None
        while yesterdays_total is None:
            previous_features = data['features'][i]
            previous_properties = dict(previous_features['properties'])
            previous_update_date = convert_timestamp(previous_properties['reportdt'])
            if previous_update_date < twentyfourhrsago:
                yesterdays_total = previous_properties['confirmed']
            i = i - 1
        new_cases = latest_cumulative_total - yesterdays_total
        
        #calculate average change over the last two weeks
        twoweeksago = current_time - timedelta(days=14)
        j = [i['properties'] for i in data['features']]
        x = [[k['reportdt'],k['confirmed']] for k in j]
        my_dict = {}
        for obs in x:
            obs[0] = convert_timestamp(obs[0])
            if obs[0] > twoweeksago:
                date = obs[0].strftime("%m/%d/%Y")
                if date not in my_dict:
                    my_dict[date] = []
                my_dict[date].append(obs[1])
        cumulative_values = []
        for key, value in my_dict.items():
            cumulative_values.append(max(value))
        first_diff = [cumulative_values[i+1] - cumulative_values[i] for i in range(len(cumulative_values)-1)] 
        avg_change = round(sum(first_diff)/len(first_diff))
        
        #generate a result for testing
        result = "its now: " + str(datetime.now()) + ", data last updated: " + str(last_update_date) + ", latest: " + str(latest_cumulative_total) + ", yesterday: " + str(yesterdays_total) + "as of " + str(previous_update_date)

        #generate date language
        month = datetime.strftime(last_update_date, "%B") + ' '
        if last_update_date.day == 1:
            day = str(last_update_date.day) + 'st '
        elif last_update_date.day == 2:
            day = str(last_update_date.day) + 'nd '
        elif last_update_date.day == 3:
            day = str(last_update_date.day) + 'rd '
        else:
            day = str(last_update_date.day) + 'th '
        if last_update_date.hour < 12:
            hour = str(last_update_date.hour) + 'AM'
        else:
            hour = str(last_update_date.hour - 12) + 'PM'
        
        #compose the message
        string = "There have been " + str(new_cases) + " new COVID cases in New Haven over the last 24 hours. On average over the last two weeks, there have been " + str(avg_change) + " new cases each day, and the cumulative total is now " + str(latest_cumulative_total) + ". (As of: " + month + day + hour +")"

    #Otherwise, if there's no new data, notify the user of that.
    else:
        string = "There is no new COVID data. We'll check for updates again tomorrow."
        
        #generate a result for testing
        result = "it's now: " + str(current_time) + "/ data last updated: " + str(last_update_date)

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)
    
    with open('phone_numbers.json') as f:
        phone_numbers = json.load(f)
    
    numbers_to_message = phone_numbers['recipients']
    for number in numbers_to_message:
        client.messages.create(
            body = string,
            from_ = phone_numbers['sender'],
            to = number
        )

    return(result)