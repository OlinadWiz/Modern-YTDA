from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown
from kivy.clock import Clock
from kivy.core.window import Window
from yt_dlp import YoutubeDL

import os
import re
import threading
import webbrowser
import subprocess
import time

Window.clearcolor = (0.1, 0.1, 0.1, 1)

class YouTubeDownloaderApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        header = Label(
            text='YouTube Audio Downloader',
            font_size='24sp',
            bold=True,
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height='40dp'
        )

        self.url_input = TextInput(
            multiline=False,
            hint_text='Inserisci URL del video YouTube',
            size_hint_y=None,
            height='40dp',
            background_color=(0.2, 0.2, 0.2, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 1)
        )

        self.format_button = Button(
            text='Formato: MP3',
            size_hint_y=None,
            height='48dp',
            background_color=(0.3, 0.5, 0.8, 1)
        )
        self.dropdown = DropDown()
        for format in ['MP3', 'FLAC']:
            btn = Button(text=format, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.select_format(btn.text))
            self.dropdown.add_widget(btn)
        self.format_button.bind(on_release=self.dropdown.open)
        self.selected_format = 'mp3'

        self.bitrate_button = Button(
            text='Qualità: Media (256k)',
            size_hint_y=None,
            height='48dp',
            background_color=(0.3, 0.5, 0.8, 1)
        )
        self.bitrate_dropdown = DropDown()
        bitrates = [
            ('Bassa (128k)', '128k'),
            ('Media (256k)', '256k'),
            ('Alta (320k)', '320k')
        ]
        for name, value in bitrates:
            btn = Button(text=name, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn, v=value: self.select_bitrate(btn.text, v))
            self.bitrate_dropdown.add_widget(btn)
        self.bitrate_button.bind(on_release=self.bitrate_dropdown.open)
        self.selected_bitrate = '256k'

        download_button = Button(
            text='Scarica Audio',
            size_hint_y=None,
            height='48dp',
            background_color=(0.1, 0.6, 0.2, 1)
        )
        download_button.bind(on_press=self.download_audio)

        open_folder_button = Button(
            text='Apri Cartella Download',
            size_hint_y=None,
            height='48dp',
            background_color=(0.2, 0.4, 0.6, 1)
        )
        open_folder_button.bind(on_press=self.open_download_folder)

        self.status_label = Label(
            text='Pronto per il download',
            color=(0, 1, 0, 1),
            size_hint_y=None,
            height='30dp'
        )

        self.spinner = Spinner(
            text='Caricamento...',
            size_hint=(None, None),
            size=(100, 50)
        )
        self.spinner.opacity = 0

        layout.add_widget(header)
        layout.add_widget(self.url_input)
        layout.add_widget(self.format_button)
        layout.add_widget(self.bitrate_button)
        layout.add_widget(download_button)
        layout.add_widget(open_folder_button)
        layout.add_widget(self.spinner)
        layout.add_widget(self.status_label)

        return layout

    def select_format(self, format_name):
        self.format_button.text = f'Formato: {format_name}'
        self.selected_format = format_name.lower()
        self.dropdown.dismiss()

    def select_bitrate(self, name, value):
        self.bitrate_button.text = f'Qualità: {name}'
        self.selected_bitrate = value
        self.bitrate_dropdown.dismiss()

    def extract_video_id(self, url):
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
            r'(?:embed\/)([0-9A-Za-z_-]{11})'
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return f"https://youtube.com/watch?v={match.group(1)}"
        return url

    def download_audio(self, instance):
        self.spinner.opacity = 1
        threading.Thread(target=self._download_audio_thread).start()

    def open_download_folder(self, instance):
        download_path = os.path.abspath('downloads')
        if os.path.exists(download_path):
            webbrowser.open(download_path)
        else:
            self.status_label.text = 'Cartella downloads non trovata'
            self.status_label.color = (1, 0, 0, 1)

    def _download_audio_thread(self):
        def update_ui(dt):
            self.spinner.opacity = 0

        def update_status(text, color):
            def update(dt):
                self.status_label.text = text
                self.status_label.color = color
            Clock.schedule_once(update)

        def my_hook(d):
            if d['status'] == 'downloading':
                perc = d.get('_percent_str', '...')
                update_status(f'Download: {perc}', (1, 1, 0, 1))

        try:
            url = self.extract_video_id(self.url_input.text)
            update_status('Inizio download...', (1, 1, 0, 1))

            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)

            ydl_opts = {
                'format': 'bestaudio/best',
                'progress_hooks': [my_hook],
                'outtmpl': os.path.join(downloads_dir, '%(title)s.%(ext)s'),
                'noplaylist': True
            }

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                downloaded_file = ydl.prepare_filename(info)

            title = info.get('title', '')
            artist = info.get('uploader', '')
            year = info.get('upload_date', '')[:4]
            album = info.get('album', '') or info.get('playlist_title', '') or 'YouTube Audio'

            thumbnail_url = info.get('thumbnail', '')
            thumb_path = os.path.join(downloads_dir, 'thumb.jpg')
            subprocess.run(['curl', '-L', thumbnail_url, '-o', thumb_path], check=False)
            temp_thumb = os.path.join(downloads_dir, 'thumb_scaled.jpg')
            subprocess.run(['ffmpeg', '-i', thumb_path, '-vf', 'scale=800:800', '-y', temp_thumb], check=False)

            output_file = os.path.splitext(downloaded_file)[0] + '.' + self.selected_format

            command = [
                'ffmpeg',
                '-i', downloaded_file,
                '-i', temp_thumb,
                '-map', '0:a',
                '-map', '1:v',
                '-c:a', 'libmp3lame' if self.selected_format == 'mp3' else 'flac',
                '-c:v', 'mjpeg',
                '-id3v2_version', '3',
                '-metadata', f'title={title}',
                '-metadata', f'artist={artist}',
                '-metadata', f'album={album}',
                '-metadata', f'date={year}',
                '-metadata:s:v', 'title=Album cover',
                '-metadata:s:v', 'comment=Cover (front)',
                '-disposition:v:0', 'attached_pic',
                '-b:a', self.selected_bitrate,
                '-ar', '44100',
                '-y',
                output_file
            ]

            subprocess.run(command, check=False)

            if os.path.exists(downloaded_file):
                os.remove(downloaded_file)
            for f in [thumb_path, temp_thumb]:
                if os.path.exists(f):
                    os.remove(f)

            update_status('Conversione completata!', (0, 1, 0, 1))

        except Exception as e:
            update_status(f'Errore: {str(e)}', (1, 0, 0, 1))
        finally:
            Clock.schedule_once(update_ui)

if __name__ == '__main__':
    YouTubeDownloaderApp().run()
