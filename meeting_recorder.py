from zoom_recorder import zoom_bot
from google_meet_recorder import google_bot
import sys

def start_recording(meeting_link: str, password='', client_name='default_client'):
    if 'google' in meeting_link:
        google_bot.master(meeting_link)
    elif 'zoom' in meeting_link:
        zoom_bot.master(meeting_link, password, client_name)
    else:
        print('meeting link not recognised')


if __name__ == '__main__':
    # start_recording('https://meet.google.com/oph-rmws-mic')
    start_recording(str(sys.argv[1]), str(sys.argv[2]), str(sys.argv[3]))