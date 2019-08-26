# PiazzaBot
Piazza + Slack + Google Calendar integration


# Installation
1. Install the packages listed in requirements.txt
2. Generate a token for the Slack Bot (see https://www.fullstackpython.com/blog/build-first-slack-bot-python.html on how to create a slack bot) and set
``` export SLACK_BOT_TOKEN = <generated token> ```
3. Create a google calendar with TA names as events, get the calendar ID(See https://developers.google.com/calendar/quickstart/python) and do the following:
``` CALENDAR_ID = <calendar token> ```
4. Get the piazza course ID (you can get it feom the class page URL https://piazza.com/class/<courseID>) and set
  ``` COURSE_ID = <course ID>```
  
# IFTTT Integration
You can also integrate IFTTT to trigger a Piazza summary post to be displayed on Slack from your phone. Create an applet that posts "piazza" on the channel of interest. Piazza Bot reads this event and posts a summary in response. You can use this to post summary of events at a specific time/Push of a button widget from your phone.
 
 
