# covidnh
A simple Python script to automatically send daily text notifications about the number of new COVID cases in New Haven.

## Architecture
An AWS CloudWatch chron job kicks off this AWS Lambda script each weekday morning at 10am. The script pulls the latest data from <a href="https://covid19.newhavenct.gov/datasets/a085f0a76f6b44efbdd185bf40243688_1/data?page=9&showData=true">the New Haven government's website</a>, performs some arithmetic to generate the text message content, and uses Twilio to send it.

The government publishes only the cumulative number of cases, sometimes updating this number multiple times a day, sometimes not for several days (especially on weekends). This script takes this data and converts it into a message like
>There have been 30 new COVID cases in New Haven over the last 24 hours. On average over the last two weeks, there have been 28 new cases each day, and the cumulative total is now 2450. (As of: May 29 9am).

## Dependencies & Configuration
* Python 3.7
* AWS Lambda <a href="https://docs.aws.amazon.com/lambda/latest/dg/python-package.html">requires</a> you to include any Python libraries that you use in the zip file you upload. You'll see those in the folder structure of this repository. Note that using Pandas with Lambda requires some <a href="https://hackersandslackers.com/pandas-with-aws-lambda/">hoop-jumping</a> and felt too heavyweight, so I instead implemented my logic in core Python.
* A Twilio account. You'll need to add your credentials as environment variables and the sending and receiving phone numbers to a JSON file. 
