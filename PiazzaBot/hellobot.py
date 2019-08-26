import os
import time
import re
from slackclient import SlackClient
# from __future__ import print_function
import datetime
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from get_piazza_data import PiazzaWrapper
import random

# instantiate Slack client
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))
calendar_id = SlackClient(os.environ.get('CALENDAR_ID'))
course_id = SlackClient(os.environ.get('COURSE_ID'))
TA_LIST = ['Einstein', 'Feynman', 'Sagan']
HAPPY_MSGS = ['Yay!','Hurray!!','Good Job!']
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

piazza = PiazzaWrapper(course_id=course_id)


def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        # print(event)
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
        elif event["type"] == "message" and "subtype" in event:
            if event["subtype"] == 'bot_message' and event['username'] == 'IFTTT':
                print(event)
                # print(event["attachments"][0]['pretext'])
                if "attachments" in event:
                    message = event["attachments"][0]['pretext']
                    user_id, _ = parse_direct_mention(event["attachments"][0]["pretext"])
                    return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    command = command.lower()
    # Default response is help text for the user
    default_response = "Not sure what you mean. Try *{}*.".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response)

    elif 'help' in command:
        response = """You can ask me the following questions\n"""
        response += """ what's the schedule?\n"""
        response += """who is the TA tomorrow?\n"""
        response += """who is the TA today?\n"""
        response += """how was piazza today?\n"""
        slack_client.api_call("chat.postMessage",channel=channel,text=response)

    elif 'schedule' in command:
        events = get_events()
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            # print(start, event['summary'])
            if(event['summary'] in TA_LIST):
                slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    text=start[:10]+'  '+event['summary'] or default_response)

    elif 'who' in command and 'tomorrow' in command:

                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text="""Tomorrow's piazza TA is """+get_TA(1) or default_response)
    # Sends the response back to the channel
    elif 'who' in command and 'today' in command:

                    slack_client.api_call(
                        "chat.postMessage",
                        channel=channel,
                        text="""Today's piazza TA is """+get_TA(0) or default_response)

    elif 'piazza' in command:
        count, count_i, count_s, count_unanswered, unanswered_posts = piazza.get_count_today()
        followup_count = piazza.get_unanswered_followup()
        response = """ Today's piazza TA was """ + get_TA(0) + """\n We had a total of """ + str(count) + " posts today"
        response += """\n Instructors answered """ + str(count_i) + " posts"
        response += """\n Students answered """ + str(count_s) + " posts (No instructor answers)\n"
        if count_unanswered != 0:
            response += str(count_unanswered) + """ posts have no answers"""
            response += """\n The following posts need our attention: \n"""
            response += ''.join('@'+str(x)+'\n' for x in unanswered_posts)
        else:
            response += """ We caught all questions today! """+ random.choice(HAPPY_MSGS)
        if followup_count>0 and count_unanswered == 0:
            response += """\n However, we still have """ +str(followup_count)+ """ unanswered followups"""
        else:
            response += """\n Also, we still have """ + str(followup_count) + """ unanswered followups"""

        slack_client.api_call("chat.postMessage",channel=channel,text=response)

    else:
        slack_client.api_call("chat.postMessage", channel=channel, text="""Sorry! I don't understand that command""")


def get_TA(days_from_now):
    events = get_events()
    response = ""
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        tomorrow = datetime.datetime.today()+ datetime.timedelta(days=days_from_now)
        tomorrow = tomorrow.strftime("%Y-%m-%d")
        date_tomorrow = tomorrow[:10]
        # print(date_tomorrow)
        # print(start, event['summary'])
        if (event['summary'] in TA_LIST):
            if start[:10] == date_tomorrow:
                if event['summary'] not in response:
                    response += event['summary'] + " "

    return response

def get_events():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('calendar', 'v3', http=creds.authorize(Http()))

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                        maxResults=10, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
    return events

if __name__ == "__main__":
    if slack_client.rtm_connect(with_team_state=False):
        print("Starter Bot connected and running!")
        # Read bot's user ID by calling Web API method `auth.test`
        starterbot_id = slack_client.api_call("auth.test")["user_id"]
        while True:
            command, channel = parse_bot_commands(slack_client.rtm_read())
            if command:
                handle_command(command, channel)
            time.sleep(RTM_READ_DELAY)
    else:
        print("Connection failed. Exception traceback printed above.")