import os
import time
# from . import util
from .arguments import Arguments
from .exceptions import InvalidVideoIdException, NoContents, PatternUnmatchError, UnknownConnectionError
from .extractor import Extractor
from .html_archiver import HTMLArchiver
# from .util import extract_video_id
from .progressbar import ProgressBar
from .videoinfo2 import VideoInfo
from .youtube import channel
from .youtube import playlist
from json.decoder import JSONDecodeError
from pathlib import Path

from . import myutil as util

from youtube_transcript_api import (
    YouTubeTranscriptApi as Api,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
    VideoUnavailable,
    NotTranslatable,
    TranslationLanguageNotAvailable,
    CookiePathInvalid,
)


import sys
import traceback
import re

SECTION_GROUP = ['streams', 'videos', 'shorts']

class Downloader:

    def __init__(self, dir_videos: set):
        self._dir_videos = dir_videos

    def video(self, video, splitter_string):
        is_complete = False
        try:
            video_id = util.extract_video_id(video.get('id'))
        except Exception as e:
            video_id = video.get("id")
            print(type(e), str(e))
        try:
            if not os.path.exists(Arguments().output):
                raise FileNotFoundError
            separated_path = str(Path(Arguments().output)) + os.path.sep
            path = util.checkpath(separated_path + video_id + '.html')
            # check if the video_id is already exists the output folder
            if video_id in self._dir_videos:
                # raise Exception(f"Video [{video_id}] is already exists in {os.path.dirname(path)}. Skip process.")
                print(
                    f"\nSkip the process...\n  The file for the video [{video_id}] already exists in {os.path.dirname(path)}.")
                sys.argv = []
                return False
            
            skipmessage = None
            if video.get("duration") is None:
                video['duration'] = VideoInfo(video.get("id")).get_duration()
                if video.get("duration") is None:
                    skipmessage = "Unable to retrieve transcript: Cannot retrieve the duration."
            
            elif video.get("duration") == 'LIVE':
                skipmessage = "Unable to retrieve transcript: This stream is live."
                
            elif video.get("duration") == 'UPCOMING':
                skipmessage = "Unable to retrieve transcript: This stream is upcoming."
                

            print(splitter_string)
            print(f"\n"
                  f"[title]    {video.get('title')}\n"
                  f"[id]       {video_id}    [published] {video.get('time_published')}\n"
                  f"[channel]  {video.get('author')}"
                  )
            print(f"[path]     {path}  [duration] {video.get('duration')}")
            if skipmessage:
                print(f"{skipmessage}\n")
                return
            
            duration = util.time_to_seconds(video["duration"])
            if duration == 0:
                return                        
            if video.get("error"):
                # error getting video info in parse()
                print(f"The video [{video_id}] may be private or deleted.")
                return False
            try:
                duration = util.time_to_seconds(video["duration"])
            except KeyError:
                return False
            pbar = ProgressBar(total=(duration * 1000), status="Extracting")

            ex = Extractor(video_id,
                           callback=pbar._disp)
            # signal.signal(signal.SIGINT, (lambda a, b: self.cancel(ex, pbar)))
            transcripts = ex.extract()
            # print(transcripts)
            # if transcripts.get("error"):
            #     if transcripts["error"] == 4:  # cancel
            #         exit(0)
            #     return False
            pbar.reset("#", "=", total=len(transcripts), status="Rendering  ")
            processor = HTMLArchiver(
                Arguments().output + video_id + '.html', callback=pbar._disp)
            processor.process(transcripts)
            processor.finalize()
            pbar.close()
            print("\nCompleted")
            is_complete = True
            print()
            if pbar.is_cancelled():
                print("\nThe extraction process has been discontinued.\n")
                return False
            return True

        except InvalidVideoIdException:
            print("Invalid Video ID or URL:", video_id)
        except NoContents as e:
            print('---' + str(e) + '---')
        except FileNotFoundError:
            print("The specified directory does not exist.:{}".format(
                Arguments().output))
            exit(0)
        except JSONDecodeError as e:
            print(e.msg)
            print("Cannot parse video information.:{}".format(video_id))
            if Arguments().save_error_data:
                util.save(e.doc, "ERR_JSON_DECODE", ".dat")
        except PatternUnmatchError as e:
            print("Cannot parse video information.:{}".format(video_id))
            if Arguments().save_error_data:
                util.save(str(e), "ERR_PATTERN_UNMATCH", ".dat")
        except KeyboardInterrupt:
            is_complete = "KeyboardInterrupt"
        except AttributeError as e:
            pass
        except Exception as e:
            print("[OUTER EXCEPTION]" + str(type(e)), str(e))
            tb = traceback.extract_tb(sys.exc_info()[2])
            trace = traceback.format_list(tb)
            print('---- traceback ----')
            for line in trace:
                if '~^~' in line:
                    print(line.rstrip())
                else:
                    text = re.sub(r'\n\s*', ' ', line.rstrip())
                    print(text)
            print('-------------------')
        finally:
            clear_tasks()
            return is_complete

    def videos(self, video_ids):
        for i, video_id in enumerate(video_ids):
            if '[' in video_id or ']' in video_id:
                video_id = video_id.replace('[', '').replace(']', '')
            try:
                video = self.get_info(video_id)
                if video.get("error"):
                    print("The video id is invalid :", video_id)
                    continue
                splitter_string = f"\n{'-'*10} video:{i+1} of {min(len(video_ids),Arguments().first)} {'-'*10}"
                ret = self.video(video,splitter_string)
                if ret == "KeyboardInterrupt":
                    self.cancel()
                    return
            except InvalidVideoIdException:
                print(f"Invalid video id: {video_id}")
            except UnknownConnectionError:
                print(f"Network Error has occured during processing:[{video_id}]")  # -!-
            except Exception as e:
                print("[OUTER EXCEPTION]" + str(type(e)), str(e))

    def channels(self, channels, tabs):
        if tabs is None:
            tabs = SECTION_GROUP
        else:
            tabs = [tabs]

        for tab in tabs:
            for i, ch in enumerate(channels):
                counter = 0
                for video in channel.get_videos(channel.get_channel_id(ch),tab=tab):
                    if counter > Arguments().first - 1:
                        break
                    splitter_string = f"\n{'-'*10} channel: {i+1} of {len(channels)} / video: {counter+1} of {Arguments().first} {'-'*10}"
                    ret = self.video(video,splitter_string)
                    if ret == "KeyboardInterrupt":
                        self.cancel()
                        return
                    if ret:
                        counter += 1

    def playlist_ids(self, playlist_ids):
        stop=False
        for i, playlist_id in enumerate(playlist_ids):
            counter = 0
            page = 1
            video_list, num_pages, metadata = playlist.get_playlist_page(playlist_id,page=str(page))

            while True:
                for video in video_list:
                    if counter > Arguments().first - 1:
                        stop=True
                        break
                    splitter_string = f"\n{'-'*10} playlist: {i+1} of {len(playlist_ids)} / video: {counter+1} of {Arguments().first} {'-'*10}"
                    ret = self.video(video, splitter_string)
                    if ret == "KeyboardInterrupt":
                        self.cancel()
                        return
                    if ret:
                        counter += 1
                page += 1
                if stop or page > num_pages:
                    break
                video_list, num_pages, metadata = playlist.get_playlist_page(playlist_id,page=str(page))

    def cancel(self, ex=None, pbar=None):
        '''Called when keyboard interrupted has occurred.
        '''
        print("\nKeyboard interrupted.\n")
        if ex:
            ex.cancel()
        if pbar:
            pbar.cancel()
        exit(0)

    def get_info(self, video_id):
        video = dict()
        for i in range(3):
            try:
                info = VideoInfo(video_id)
                break
            except PatternUnmatchError:
                time.sleep(2)
                continue
            except Exception as e:
                print("[OUTER EXCEPTION]" + str(type(e)), str(e))
                return {"error": True}    
        else:
            print(f"PatternUnmatchError:{video_id}")
            video['id'] = ""
            video['author'] = ""
            video['time_published'] = ""
            video['title'] = ""
            video['duration'] = ""
            video['error'] = True
            return video

        video['id'] = video_id
        video['author'] = str(info.get_channel_name())
        video['time_published'] = "Unknown"
        video['title'] = str(info.get_title())
        video['duration'] = str(info.get_duration())
        return video
    
def clear_tasks():
    pass
