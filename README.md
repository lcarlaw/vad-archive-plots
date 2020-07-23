# vad-archive-plots [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lcarlaw/vad-archive-plots/master?urlpath=lab) [![Run on Repl.it](https://repl.it/badge/github/lcarlaw/vad-archive-plots)](https://repl.it/github/lcarlaw/vad-archive-plots)
Download archived VAD wind data and plot associated hodographs and VWPs. Useful for post-event recaps.

The actual VAD-based hodograph plotting is completed by Tim Supinie's excellent vad-plotter, but several additions have been made here to facilitate the retrieval and plotting of archived VAD data. The online-accessible archived data seems to be available for about 30 days, after which downloading from NCEI becomes necessary. This capability has been added, but the user must follow some additional steps which are outlined below. Additionally, some scripts were modified to produce VWP profiles based on a graphic shared by [@WxLiz (Elizabeth Leitman at SPC) at this link](https://twitter.com/WxLiz/status/1152433001227268096), which emulates some nice NFLOW VWP graphics.

![](https://github.com/lcarlaw/vad-archive-plots/blob/master/example_images/KGRB_vwp.png?raw=true)
<p align="center">
  <em>Example VWP output showing a descending rear inflow jet. Example from the KGRB radar on July 19, 2019.</em>
</p>

## Required Libraries
Outside of NumPy and Matplotlib, no additional libraries are required. If you're running this on a local machine, the `ucnids.c` script will need to be compiled. This C compilation is taken care of automatically when you load the repl.it webpage or open the Binder Notebook (see Usage section below).

```
cc ucnids.c -o ucnids -lz
```

## Usage
At this time, there are two options to run this online, using **[Binder (more information at the link)](https://mybinder.org/)** and **[Repl.it](repl.it)**

Either way you choose to run it, three user inputs are required (`*`), and two are optional:

* `*RADAR_ID` is a 4-character radar identifier (e.g. KLOT, KTLX, KFWS, TORD, TDAL, etc. This can be lower case.)
* `*START_TIME` is for the initial download request time. It's in the form YYYYMMDD/HH
* `*END_TIME` is for the last download request time. It's in the form YYYYMMDD/HH
* `STORM_MOTION` is the storm motion vector. It can take one of two forms. The first is either `BRM` for the Bunkers right-mover vector or `BLM` for the Bunkers left-mover vector. The second form is `DDD/SS`, where `DDD` is the direction the storm is coming from in degrees, and `SS` is the storm speed in knots. An example might be 240/35 (from the WSW at 35 kts).  If the argument is not specified, the default is to use the Bunkers right-mover vector.
* `SFC_WIND` is the surface wind vector. Its form is the same as the `DDD/SS` form of the storm motion vector. A dashed red line will be drawn on the hodograph from the lowest point in the VWP to the surface wind to indicate the approximate wind profile in that layer.

While the `STORM_MOTION` and `SFC_WIND` flags are optional, they're strongly encouraged. If they are left off, the script will assume a Bunkers Right Supercell storm motion and use the lowest VAD wind retrieval as the surface wind, both of which can have significant impacts on the various derived parameters.

### Binder [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/lcarlaw/vad-archive-plots/master?urlpath=lab)

* Click on the Binder badge to access the online Binder Notebook. You'll be taken to a landing screen as the environment loads. This should only take a few seconds.

* Towards the bottom left of the interactive pane that loads, click the **Terminal ($_)** icon. A shell terminal tab should open up after a second or two.

![](https://raw.githubusercontent.com/lcarlaw/vad-archive-plots/master/example_images/binder_landing.png)

* Type `python main.py` and hit `Enter`. You'll see the user prompts appear.

* Once things finish running, a `.zip` file (the format will be something like `data_YYYYMMDD-HHmm.zip`) should appear in the left hand navigation bar. Right click it and select "Download" to save the images off locally.

### Repl.it ![Run on Repl.it](https://repl.it/badge/github/lcarlaw/vad-archive-plots)

* Click on the Run of Repl.it badge to access the online repl.it Python IDE where you will run this program. This will create a clone of the original GitHub Repo allowing you to interact with the code without making changes to the original scripts. On the webpage that appears (give it a minute or two), you'll be given an @anonymous username with three random words:

<p align="center">
  <img width="750" height="60" src="https://github.com/lcarlaw/vad-archive-plots/blob/master/example_images/username.png?raw=true">
</p>

* On the landing screen, hit the ***run*** button. You'll see the user prompts appear on the right hand side of the page.

### NCEI-based archive downloads
If past the 30-day online archive window, you can manually download Level 3 NVW files from NCEI for plotting. If the don't specify a start and end time, a final prompt will appear asking for a directory containing user-downloaded files.

The download process might look something like this:

* Proceed to https://www.ncdc.noaa.gov/nexradinv/map.jsp and select a radar site
* Select a year, month, and day from the dropdown and find the "NVW" files using the Product Filter. Click `Create Graph`:

![](https://raw.githubusercontent.com/lcarlaw/vad-archive-plots/master/example_images/NCEI_step_1.png)

* Select a start and end time from the dropdowns. Type in an email address for data delivery. Click `Order Data`.

![](https://raw.githubusercontent.com/lcarlaw/vad-archive-plots/master/example_images/NCEI_step_2.png)

* Once the data arrives, download using whatever means you're comfortable with (individual wget commands, ftp, sftp, etc). The https://www.ncdc.noaa.gov/has/has.orderguide may be useful. Just make sure the data files make their way into an **individual directory**.

* Drag and drop this folder into the "Files" column on the left hand side of the repl.it screen. In this case, we've added a folder called `October_Dallas_TORs`:

![](https://github.com/lcarlaw/vad-archive-plots/blob/master/example_images/file_upload.png)

* Click the ***run*** button again. This time you won't enter a start or end time (just hit "Enter" or the return key) and will be prompted at the end to specify the name of the directory you just uploaded:

* `*ARCHIVE_PATH` is a zip file containing archived NVW files. This optional input is accessed by not entering start and end times when initially running the script.  You'll then be prompted for a directory containing NCEI-downloaded NVW files. The script will attempt to create hodographs and a VWP from the files contained within the `ARCHIVE_PATH` directory.

## Output
A directory in the form `data_YYYYMMDD-HHmm` will be created into which the necessary inflated NVW .nids files will be stored. Associated plots of each individual hodograph, as well as a VWP spanning the entire download time, will be store in the `./plots/` subdirectory.

Currently, repl.it only allows you to download all of the repo files at once in a zip file. Click on the three dots in the "Files" column and select "Download as zip". This will download a zipped file that you can then unzip on your local system!

![](https://github.com/lcarlaw/vad-archive-plots/blob/master/example_images/download_example.png)
