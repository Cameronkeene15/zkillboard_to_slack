# Eve-Online-Slack-Bot
This is a script which will go through all recent kills happening in EVE and post any killmails that are losses or kills to slack in a formated message.


Once downloaded, the config.ini file needs to be configured with the corporation ID (which can be found in the url of the corporations zkillboard page), a queue_id is optional. The slack webhook is needed which can be setup from the slack website and pasted into the config file.


To run the script crontab can be used. The example below runs the script every five minutes and uses flock to make sure that it will not run the script twice if it is already running to prevent errors.

*/5 * * * * flock -nx /home/cameron/zkillboard_to_slack/.processlock -c /home/cameron/zkillboard_to_slack/zkillboard_to_slack.py >> /home/cameron/zkillboard_to_slack/log.txt 2>&1
