#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Requirements:
#  * Python 3 installation
#  * Additional Python modules
#     * python.exe -m pip install selenium
#     * python.exe -m pip install ffmpeg-python
#     * python.exe -m pip install Pillow
# * Put the Firefox Gecko driver from https://github.com/mozilla/geckodriver/releases into the third-party directory
#   (or use any other directory because full path has to be specified anyway via --driver_exe command line option)
# * Put the ffmpeg executable (if not already installed) from https://ffmpeg.org/download.html into the third-party directory
#   (or use any other directory because full path has to be specified anyway via --ffmpeg_exe command line option).
#   ffmpeg must be built with x264 codec support.
#

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import os
import sys
import time
import re
import argparse
import ffmpeg
from PIL import Image

class SoziVideoCreator:
    
    def __init__(self, input_file, output_directory, driver_exe, ffmpeg_exe, width, height, fps, seconds):
        self._fps = fps
        self._recording_secs = seconds
        self._width = width
        self._height = height
        self._inset_width = 0
        self._inset_height = 0
        self._input_filename = input_file
        self._output_directory = output_directory
        self._tmp_filename = self._input_filename + ".tmp.html"
        self._driver_exe = driver_exe
        self._ffmpeg_exe = ffmpeg_exe
    
    def _initialize_driver(self):
        os.environ['MOZ_HEADLESS_WIDTH'] = str(self._width + self._inset_width)
        os.environ['MOZ_HEADLESS_HEIGHT'] = str(self._height + self._inset_height)
        self._options = FirefoxOptions()
        self._options.add_argument("--headless")
        self._driver = webdriver.Firefox(options = self._options, executable_path = self._driver_exe)
        self._driver.maximize_window()
    
    def _deinitialize_driver(self):
        self._driver.quit()
    
    def _print_progress(self, iteration, total):
        prefix = 'Progress'
        suffix = ''
        decimals = 1
        length = 50
        fill = '*'
        print_end = '\r'
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = print_end)
        if iteration == total: 
            print()
    
    def _determine_image_inset(self):
        print("Determining image inset.")
        self._driver.get("file:///" + self._input_filename)
        time.sleep(2.0)
        tmp_file = self._output_directory + "/tmp.png"
        self._driver.get_screenshot_as_file(tmp_file)
        image = Image.open(tmp_file)
        width, height = image.size
        self._inset_width = self._width - width
        self._inset_height = self._height - height
        print("Inset width: " + str(self._inset_width) + " inset height: " + str(self._inset_height))
    
    def _determine_max_frame_time(self):
        print("Determining maximum export time of individual frames.")
        self._driver.get("file:///" + self._input_filename)
        time.sleep(2.0)
        self._max_frame_time = 0.0
        overall_start = time.time()
        while time.time() - overall_start < self._recording_secs:
            start = time.time()
            self._driver.get_screenshot_as_file(self._output_directory + "/tmp.png")
            frame_time = time.time() - start
            if frame_time > self._max_frame_time:
                self._max_frame_time = frame_time
            self._print_progress(int(time.time() - overall_start), self._recording_secs)
        print("Maximum export time [seconds]: " + str(self._max_frame_time))
    
    def _replace_times(self, content, pattern, time_scaling):
        replace_list = []
        for match in re.finditer(pattern + '([0-9]+)', content):
            start = match.start()
            end = match.end()
            orig_duration = int(match.group(1))
            new_duration = int(orig_duration / time_scaling)
            replace_list.append([start, end, new_duration])
        
        for i in range(len(replace_list) - 1, -1, -1):
            start = replace_list[i][0]
            end = replace_list[i][1]
            duration = replace_list[i][2]
            content = content[:start] + pattern + str(duration) + content[end:]
        return content
    
    def _create_time_scaled_file(self):
        file = open(self._input_filename, "r", encoding="utf8")
        content = file.read()
        file.close()
        content = self._replace_times(content, '"transitionDurationMs":', self._time_scaling)
        content = self._replace_times(content, '"timeoutMs":', self._time_scaling)
        file = open(self._tmp_filename, "w", encoding="utf8")
        file.write(content)
        file.close()
    
    def _adjust_playback_rate(self):
        javascript = """
            var videoElements = document.getElementsByTagName('video');
            var videoElement;
            for (videoElement = 0; videoElement < videoElements.length; videoElement++) {
                videoElements[videoElement].playbackRate = """ + str(self._time_scaling) + """;
            }
            """
        self._driver.execute_script(javascript)
    
    def convert(self):
        self._initialize_driver()
        self._determine_image_inset()
        self._deinitialize_driver()
        self._initialize_driver()
        self._determine_max_frame_time()
        self._recordable_fps = int(1.0 / self._max_frame_time)
        self._time_scaling = self._recordable_fps / self._fps
        self._create_time_scaled_file()
        
        print("Exporting individual frames.")
        
        self._driver.get("file:///" + self._tmp_filename)
        time.sleep(2.0)
        self._adjust_playback_rate()
        time.sleep(2.0)
        
        nr_frames = int(self._recording_secs * self._fps)

        frame_record_time = 1.0 / self._recordable_fps
        for i_frame in range(0, nr_frames):
            start = time.time()
            self._driver.get_screenshot_as_file(self._output_directory + "/capture_{:05d}.png".format(i_frame))
            diff = time.time() - start
            self._print_progress(i_frame + 1, nr_frames)
            if diff < frame_record_time:
                time.sleep(frame_record_time - diff)
        print("Exported all frames.")
        print("Converting individual frames into video.")
        ffmpeg \
                .input(self._output_directory + "/capture_%05d.png", framerate = self._fps) \
                .output(self._output_directory + "/video.mp4", crf = 25, pix_fmt='yuv420p', vcodec = 'libx264') \
                .run(cmd = self._ffmpeg_exe)
        print("Finished video creation.")
        self._deinitialize_driver()

def parse_command_line():
    parser = argparse.ArgumentParser(description = 'Creates a video from a Sozi presentation')
    parser.add_argument('--input_file', action = 'store', type = str, required = True, help = 'input file name')
    parser.add_argument('--output_dir', action = 'store', type = str, required = True, help = 'output directory')
    parser.add_argument('--driver_exe', action = 'store', type = str, required = True, help = 'web driver executable')
    parser.add_argument('--ffmpeg_exe', action = 'store', type = str, required = True, help = 'ffmpeg executable')
    parser.add_argument('--width', action = 'store', type = int, required = True, help = 'width of video')
    parser.add_argument('--height', action = 'store', type = int, required = True, help = 'height of video')
    parser.add_argument('--fps', action = 'store', type = int, required = True, help = 'frames per second')
    parser.add_argument('--seconds', action ='store', type = int, required = True, help = 'recording seconds')
    args = parser.parse_args()
    if not os.path.isfile(args.input_file):
        print('The specified input file does not exist')
        sys.exit()
    if not os.path.isdir(args.output_dir):
        print('The specified output directory does not exist')
        sys.exit()
    if not os.path.isfile(args.driver_exe):
        print('The specified web driver executable does not exist')
        sys.exit()
    if not os.path.isfile(args.ffmpeg_exe):
        print('The specified ffmpeg executable does not exist.')
        sys.exit()
    return args

if __name__ == "__main__":
    args = parse_command_line()
    videoCreator = SoziVideoCreator(args.input_file, args.output_dir, args.driver_exe, args.ffmpeg_exe, args.width, args.height, args.fps, args.seconds)
    videoCreator.convert()
