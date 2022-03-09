from zoom_recorder import zoom_bot
from google_meet_recorder import google_bot


def start_recording(meeting_link: str, password=''):
    if 'google' in meeting_link:
        google_bot.master(meeting_link)
    elif 'zoom' in meeting_link:
        zoom_bot.master(meeting_link, password)
    else:
        print('meeting link not recognised')


if __name__ == '__main__':
    start_recording('https://us04web.zoom.us/j/74537331996?pwd=JFc6MXZk5J4u2xeS39wvYf2wYg1XLn.1', 't2GMws')