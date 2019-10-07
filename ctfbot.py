import os
import logging
import slack
import ssl as ssl_lib
import certifi
import subprocess

with open('/home/devadmin/ctfbot/vars.env') as f:
    for line in f:
        if 'export' not in line:
            continue
        if line.startswith('#'):
            continue
        # Remove leading `export `
        # then, split name / value pair
        key, value = line.replace('export ', '', 1).strip().split('=', 1)
        os.environ[key] = value

def list_challenges():
    return subprocess.getoutput("docker ps --format '{{.Names}}'").split('\n')

def validate_challenge(challenge):
    containers = list_challenges()
    if challenge in containers:
        return True
    else:
        return False

def restart_challenge(challenge):
    try:
        restart = subprocess.getoutput("docker restart " + challenge)
        print(restart)
    except:
        return False
    return True

@slack.RTMClient.run_on(event='message')
def say_hello(**payload):
    print(payload)
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    text = data.get('text', [])
    if '@UNRTFC13L' in text and 'restart' in text:
        command = text.split(' ')
        channel_id = data['channel']
        thread_ts = data['ts']
        if len(command) == 3:
            challenge = command[2]
            if validate_challenge(challenge):
                if restart_challenge(challenge):
                    web_client.chat_postMessage(
                        channel=channel_id,
                        text=f"Restarted " + challenge,
                        thread_ts=thread_ts
                    )
                else:
                    web_client.chat_postMessage(
                        channel=channel_id,
                        text=f"Restarting challenge " + challenge + " failed.",
                        thread_ts=thread_ts
                    )
            else:
                web_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Could not find challenge " + challenge,
                    thread_ts=thread_ts
                )
        else:
            web_client.chat_postMessage(
                channel=channel_id,
                text=f"Please use a valid command.",
                thread_ts=thread_ts
            )
    elif '@UNRTFC13L' in text and 'list' in text:
        command = text.split(' ')
        channel_id = data['channel']
        thread_ts = data['ts']
        if len(command) == 2:
            challenges = list_challenges()
            message = "\n".join(challenges)
            web_client.chat_postMessage(
                channel=channel_id,
                text=message,
                thread_ts=thread_ts
            )

# slack_token = 'xoxb-619777052614-773933409122-DWqV8g4rewqESAVeWhwJEocu'
# rtm_client = slack.RTMClient(token=slack_token)
# rtm_client.start()

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    slack_token = os.environ["SLACK_API_TOKEN"]
    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()