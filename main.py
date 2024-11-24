import asyncio
import secrets

import requests
import time
import pygame
from obswebsocket import obsws, requests as obs_requests
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope
TARGET_SCOPES = [AuthScope.CHANNEL_EDIT_COMMERCIAL]


class AdTime:

    def __init__(self):
        # OBS WebSocket settings
        self.obs_host = "localhost"  # OBS WebSocket host
        self.obs_port = 4455  # WebSocket port (default)
        self.obs_password = "XYWYGiiqfZl1rXlU"  # Replace with your OBS WebSocket password

        # Connect to OBS
        self.ws = obsws(self.obs_host, self.obs_port, self.obs_password)
        self.ws.connect()

    def play_sound(self, file):
        pygame.mixer.init()
        pygame.mixer.music.load(file)
        pygame.mixer.music.play()

    def change_scene(self, scene_name):
        self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=scene_name))

    def get_oauth_token(self):
        url = 'https://id.twitch.tv/oauth2/token'
        data = {
            'client_id': secrets.APP_ID,
            'client_secret': secrets.APP_SECRET,
            'grant_type': 'client_credentials'
        }

        response = requests.post(url, data=data)  # Use params, not data
        if response.status_code == 200:
            oauth_data = response.json()
            return oauth_data['access_token'], oauth_data['expires_in']
        else:
            print(f"Failed to get OAuth token: {response.status_code}, {response.text}")
            return None, None

    def play_ad(self, twitch):
        twitch.start_commercial()

    async def start_timer(self, twitch):
        original_scene = self.ws.call(obs_requests.GetCurrentProgramScene()).datain.get(
            'currentProgramSceneName')
        self.ws.call(obs_requests.SetCurrentProgramScene(sceneName='Ad Scene'))
        await asyncio.sleep(3 * 60)
        self.ws.call(obs_requests.SetCurrentProgramScene(sceneName=original_scene))

        sound_55 = "ad_warning.mp3"
        sound_57 = "ad_start_alert.mp3"
        original_scene = self.ws.call(obs_requests.GetCurrentProgramScene()).datain.get('currentProgramSceneName')
        ad_scene = "Ad Scene"  # Scene to switch to for ad break

        warning_minutes = 55
        ad_minutes = 57
        reset_minutes = 60

        while True:
            time_elapsed = 0
            while time_elapsed < reset_minutes * 60:  # 60 minutes
                if time_elapsed == warning_minutes * 60:  # 55 minutes mark
                    self.play_sound(sound_55)
                    print("55 minutes! Ad time is near.")
                elif time_elapsed == ad_minutes * 60:  # 57 minutes mark
                    self.play_sound(sound_57)
                    print("57 minutes! Ad is imminent!")
                    time.sleep(10)
                    original_scene = self.ws.call(obs_requests.GetCurrentProgramScene()).datain.get(
                        'currentProgramSceneName')
                    self.change_scene(ad_scene)  # Switch to Ad Scene
                    pygame.mixer.music.load('ad_music.mp3')  # Load the song
                    pygame.mixer.music.play(-1)
                    await twitch.start_commercial(broadcaster_id=38606166, length=180)  # Play ad for 3 minutes
                    time.sleep(3 * 60)
                    pygame.mixer.music.stop()
                    self.change_scene(original_scene)  # Switch back to original scene
                    print("Ad finished. Returning to main scene.")
                time.sleep(1)
                time_elapsed += 1
            self.change_scene(original_scene)
            print("Resetting timer.")

    async def begin(self):
        # create the api instance and get user auth either from storage or website
        twitch = await Twitch(secrets.APP_ID, secrets.APP_SECRET)
        helper = UserAuthenticationStorageHelper(twitch, TARGET_SCOPES)
        await helper.bind()
        await twitch.start_commercial(broadcaster_id=38606166, length=180)

        await self.start_timer(twitch)


if __name__ == '__main__':
    ad_time = AdTime()
    asyncio.run(ad_time.begin())
