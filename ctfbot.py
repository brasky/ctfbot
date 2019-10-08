import os
import logging
import slack
import ssl as ssl_lib
import certifi
import subprocess

with open('/home/challenge/ctfbot/vars.env') as f:
    for line in f:
        if 'export' not in line:
            continue
        if line.startswith('#'):
            continue
        # Remove leading `export `
        # then, split name / value pair
        key, value = line.replace('export ', '', 1).strip().split('=', 1)
        os.environ[key] = value

def get_challenge_ports(challenge):
    challenges = subprocess.getoutput("docker ps --format '{{.Names}}|{{.Ports}}'").split('\n')
    if challenge in challenges:
        for running_challenge in challenges:
            if challenge in running_challenge:
                ports = running_challenge.split('|')[1]
                ports = ports.replace('->', ':')
                ports = ports.split(',')

                return ports
                # ports = ports.replace(':', '')
                # ports = ports.replace('0.0.0.0', '')
                # ports = ports.replace('/tcp', '')
                # ports = ports.split('->')
    return []

def kill_challenge(challenge):
    try:
        subprocess.getoutput("docker kill " + challenge)
    except:
        return False

# def remove_image(image_name):
#     try:
#         subprocess.getoutput("docker rm")

# def build_image(image_name):
#     pass

def run_challenge(challenge, image_name, ports):
    try:
        ports_arg = ''
        for port in ports:
            ports_arg += '-p ' + port + ' '
        subprocess.getoutput("docker run --name "  + challenge + " -d " + ports_arg + image_name)
    except:
        return False

def remove_challenge(challenge):
    try:
        subprocess.getoutput("docker rm " + challenge)
    except:
        return False

def reset_challenge(challenge):
    if validate_challenge(challenge):
        try:
            ports = get_challenge_ports(challenge)
            image_name = challenge + '-image'
            kill_challenge(challenge)
            remove_challenge(challenge)
            # remove_image(image_name)
            # build_image(image_name)
            run_challenge(challenge, image_name, ports)
            return True
        except:
            return False
    return False

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
        # print(restart)
    except:
        return False
    return True

def invalid_command(web_client, channel_id, thread_ts):
    web_client.chat_postMessage(
        channel=channel_id,
        text=f"Please use a valid command. Try using @ctfbot help for assistance!",
        thread_ts=thread_ts
    )

@slack.RTMClient.run_on(event='message')
def say_hello(**payload):
    print(payload)
    data = payload['data']
    web_client = payload['web_client']
    text = data.get('text', [])
    try:
        user = data['user']
    except:
        return

    if '@UP742UDL6' in text and 'restart' in text:
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
            invalid_command(web_client, channel_id, thread_ts)

    elif '@UP742UDL6' in text and 'list' in text:
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
        else:
            invalid_command(web_client, channel_id, thread_ts)

    elif '@UP742UDL6' in text and 'help' in text:
        command = text.split(' ')
        channel_id = data['channel']
        thread_ts = data['ts']
        if len(command) == 2:
            message = "@ctfbot list: Shows all running challenges\n\n@ctfbot restart [challenge]: restarts the specified challenge. May not fix all issues.\n\n@ctfbot reset [challenge]: Destroys and rebuilds challenge. Takes longer but fixes most things."
            web_client.chat_postMessage(
                channel=channel_id,
                text=message,
                thread_ts=thread_ts
            )
        else:
            invalid_command(web_client, channel_id, thread_ts)

    elif '@UP742UDL6' in text and 'reset' in text:
        command = text.split(' ')
        channel_id = data['channel']
        thread_ts = data['ts']
        if len(command) == 3:
            challenge = command[2]
            if reset_challenge(challenge):
                web_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Reset " + challenge,
                    thread_ts=thread_ts
                )
            else:
                web_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Resetting challenge " + challenge + " failed.",
                    thread_ts=thread_ts
                )
        else:
            invalid_command(web_client, channel_id, thread_ts)

    elif '@UP742UDL6' in text:
        channel_id = data['channel']
        thread_ts = data['ts']
        invalid_command(web_client, channel_id, thread_ts)

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler())
    ssl_context = ssl_lib.create_default_context(cafile=certifi.where())
    slack_token = os.environ["SLACK_API_TOKEN"]
    rtm_client = slack.RTMClient(token=slack_token, ssl=ssl_context)
    rtm_client.start()