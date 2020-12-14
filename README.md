# SoziVideoCreator
SoziVideoCreator enables the export of Sozi HTML presentations (including embedded videos) into a video. Sozi (https://sozi.baierouge.fr) is a zooming presentation editor and player. Unlike in most presentation applications, a Sozi document is not organized as a slideshow, but rather as a poster where the content of your presentation can be freely laid out. Posters must be in Scalable Vector Graphics (SVG) format, so the ideal tool for the creation is Inkscape (https://inkscape.org). Using Inkscape enables to embed videos into the presentation via Sozi extensions for Inkscape.

# Description
This Sozi video export is based on Selenium (https://www.selenium.dev) in combination with the Firefox web browser (https://www.mozilla.org/firefox). For each video frame the converter takes a screenshot of the running presentation at the desired frame rate. Afterwards these individual frames are composed into a video via ffmpeg (https://ffmpeg.org). The conversion process even works with videos embedded into the presentation. This works by adjusting the timings in the Sozi presentation and the playback rate of the embedded videos.

# Requirements
 * Python 3 installation
 * Additional Python modules
    * Web browser automation: `python.exe -m pip install selenium`
    * Video composing: `python.exe -m pip install ffmpeg-python`
    * Image manipulation: `python.exe -m pip install Pillow`
 * Put the Firefox Gecko driver from https://github.com/mozilla/geckodriver/releases into the third-party directory (or use any other directory because full path has to be specified anyway via --driver_exe command line option)
 * Put the ffmpeg executable (if not already installed) from https://ffmpeg.org/download.html into the third-party directory (or use any other directory because full path has to be specified anyway via --ffmpeg_exe command line option). ffmpeg must be built with x264 codec support.

# Usage
`C:\Python38\python.exe SoziVideoCreator.py --input_file <Sozi HTML presentation> --output_dir <output directory> --driver_exe <full path to web driver> --ffmpeg_exe <full path to ffmpeg executable> --width <width in pixels> --height <height in pixels> --fps <frame rate> --seconds <recording duration in seconds>`

# Examples
 * See `examples` directory
 * Example video: https://www.youtube.com/watch?v=JhO9_Mx0-7o
 
# Remarks
This code has been tested on Windows 10, but should also work on Linux.
