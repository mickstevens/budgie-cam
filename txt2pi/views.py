from django.shortcuts import render
from django.views.generic.base import TemplateView

import subprocess
import time

from twilio.rest import TwilioRestClient 

from budgie_settings import BUDGIE_PASSPHRASE, BUDGIE_FILE_PATH, BUDGIE_WEB_PATH, RASPI_IP
from twilio_credentials import ACCOUNT_SID, AUTH_TOKEN

class BudgieCamView(TemplateView):

    def get(self, request, **kwargs):

        """ Response Code 418: I'm a teapot
        """

        template = 'response.html'
        context = {
            'response': '418'
        }
        return render(request, template, context)

    def post(self, request, **kwargs):

        """ Twilio is configured to POST to this URL when a text message is received.
            1. Receive text message
            2. Verify text message and continue if verified
            3. Snap photo (use subprocess module)
            4. Photo needs to be accessible via a URL
            5. Use Twilio API to attach photo to SMS
        """

        text_message = request.POST.get('Body')
        requesting_phone_number = request.POST.get('From')
        budgiecam_phone_number = request.POST.get('To')

        context = {}

        if text_message:
            if BUDGIE_PASSPHRASE in text_message.lower():
                if 'video' in text_message.lower():
                    try:
                        budgie_filename = '{0}.h264'.format(''.join(['{0:02d}'.format(x) for x in time.localtime()[:6]]))
                        # raspivid -o video.h264 -t 10000
                        subprocess.call(['raspivid', '--nopreview', '-t', '30000','-o', '{0}{1}'.format(BUDGIE_FILE_PATH, budgie_filename)])

                        # This would convert the h264 video to mp4 but unfortunately it doesn't run quickly enough on the Raspberry Pi
                        # Maybe later versions of the Pi would be able to handle it, but this one can't.
                        # try:
                        #     print "\t Converting {0} to mp4".format(budgie_filename)
                        #     subprocess.call([
                        #         'ffmpeg',
                        #         '-i',
                        #         '{0}{1}'.format(BUDGIE_FILE_PATH, budgie_filename),
                        #         "{0}{1}.mp4".format(BUDGIE_FILE_PATH, budgie_filename[:-5])
                        #     ])

                        # except Exception:
                        #     print "[ERROR] Failed to convert {0} to mp4".format(budgie_filename)
                        # else:
                        #     subprocess.call([
                        #         'rm',
                        #         '{0}{1}'.format(BUDGIE_FILE_PATH, budgie_filename)
                        #     ])
                        #     budgie_filename = "{0}.mp4".format(budgie_filename[:-5])
                    except Exception, e:
                        print "[ERROR] Call to raspivid failed; could not take video ({0}: {1}{2})".format(e, BUDGIE_FILE_PATH, budgie_filename)
                    else:
                        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
                        client.messages.create(
                            to=requesting_phone_number,
                            from_=budgiecam_phone_number,
                            body="Video ready here: {0}{1}{2}".format(RASPI_IP, BUDGIE_WEB_PATH, budgie_filename)
                        )
                        context['response'] = '200'
                else:
                    try:
                        budgie_filename = '{0}.jpg'.format(''.join(['{0:02d}'.format(x) for x in time.localtime()[:6]]))
                        subprocess.call(['raspistill', '--nopreview', '-t', '5000', '-o', "{0}{1}".format(BUDGIE_FILE_PATH, budgie_filename)])
                    except Exception, e:
                        print "[ERROR] Call to raspistill failed; could not take photo ({0}: {1}{2})".format(e, BUDGIE_FILE_PATH, budgie_filename)
                        context['response'] = '500'
                    else:
                        client = TwilioRestClient(ACCOUNT_SID, AUTH_TOKEN)
                        client.messages.create(
                            to=requesting_phone_number,
                            from_=budgiecam_phone_number,
                            body="{0}".format(budgie_filename),
                            media_url="{0}{1}{2}".format(RASPI_IP, BUDGIE_WEB_PATH, budgie_filename),
                        )
                        context['response'] = '200'
            else:
                context['response'] = '401'
        else:
            context['response'] = '400'

        template = 'response.html'
        return render(request, template, context)
