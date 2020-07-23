#
# This script will fetch archived (up to ~30 days) Level 3 NVW files from the UCAR
# THREDDS server, inflate them using Daryl Herzmann's ucnids.c tool, and then plot
# the associated hodographs. The hodograph plotting itself is driven completely by
# Tim Supinie's excellent vad-plotter scripts, with some modifications to allow
# plotting of NFLOW-based VWPs.
#
# UPDATES:
#       5/30/2020   -   Initial script development
#       6/6/2020    -   Added NCEI-based archived plotting capabilities
#       7/1/2020    -   Incorporated user-input options. Removed command-line args.
#       7/7/2020    -   Added quick data query & readout at start of execution
#       7/7/2020    -   Added TDWR plotting capabilities. Improved archive option.
#       7/9/2020    -   Output data now zipped to allow easier downloading.
#
# USEAGE and OUTPUT:
#       Please see the README.md for more information.
#

from datetime import datetime, timedelta

try:
    import urllib2 as urlreq
except ImportError:
    import urllib.request as urlreq

from glob import glob
import os, sys, shutil
import re
import argparse
import numpy as np
import zipfile as zf

from wsr88d import nexrads, tdwrs, nwswfos

HOME_DIR = os.environ['PWD']
ucnids = HOME_DIR + "/./ucnids"
base = "https://thredds.ucar.edu/thredds"
reg_string = "<tt>([\w]{5}[\d]{1}_[\w]{3}_[\w]{3}_[\d]{8}_[\d]{4}).nids"

def inflate_files(radar_id, files, output_path):
    """
    Pass the downloaded .nids files through the ucnids binary to inflate/
    decompress into python-readable format for passing to vad and vwp scripts
    """
    files = glob(output_path + '/*.nids')
    for f in files:
        idx = f.index('Level3')
        iname = f[idx:]
        wfo = nwswfos[radar_id]
        date = iname[-18:-5]
        oname = "K%s_SDUS34_NVW%s_%s%s" % (wfo, radar_id[1:], date[0:8], date[9:13])

        print("Inflating: %s to %s" % (f, oname))
        arg = "%s -r %s %s/%s" % (ucnids, f, output_path, oname)
        os.system(arg)

        # Remove the original .nids files
        arg = "rm %s" % (f)
        os.system(arg)

def find_files(radar_id, start_time, end_time, catalogue_base):
    """
    Query the THREDDS server catalogue listing and return the available .nids
    NVW files. If none exist, return an empty list
    """
    start = datetime.strptime(start_time, '%Y%m%d/%H')
    end = datetime.strptime(end_time, '%Y%m%d/%H')

    days_list = [start.day]
    temp_start = start
    while temp_start <= end:
        if temp_start.day != days_list[-1]: days_list.append(temp_start.day)
        temp_start += timedelta(hours=1)
    num_days = len(days_list)

    file_list = []
    for i in range(num_days+1):
        date = start + timedelta(days=int(i), minutes=0, seconds=0)
        date_str = date.strftime("%Y%m%d")
        url = ("%s/%s/%s/catalog.html") % (catalogue_base, radar_id[-3:],
                                           date_str)

        # Search the catalogue for available .nids files using regular
        # expressions. May need more robust exception handling here...
        try:
            req = urlreq.Request(url)
            result = urlreq.urlopen(req)
            txt = result.read().decode('utf-8')
            files = re.findall(reg_string, txt)
            files.sort()
            file_list.extend(files)
        except:
            pass
    return file_list

def download_files(files, start_time, end_time, download_base):
    """
    Download the requested files
    """
    start = datetime.strptime(start_time, '%Y%m%d/%H')
    end = datetime.strptime(end_time, '%Y%m%d/%H')

    curr_date = datetime.strftime(datetime.now(), "%Y%m%d-%H%M")
    output_path = HOME_DIR + "/data_" + curr_date
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    for f in files:
        ID = f[7:10]
        date_str = f[15:23]
        hhmm = f[-4:]
        dt = datetime.strptime(date_str+hhmm, '%Y%m%d%H%M')
        if (start <= dt <= end) and not (os.path.exists(output_path + '/' + f + '.nids')):
            target = ("%s/%s/%s/%s.nids") % (download_base, ID, date_str, f)
            arg = "wget -q %s -O %s" % (target, output_path + '/' + f + '.nids')
            print("Downloading: ", f, ".nids to ==>", output_path)
            os.system(arg)

    return output_path

def run_vad(output_path, radar_id, storm_motion, sfc_wind):
    """
    Automatically run the vad.py script (with all default settings). Images will be
    saved in the same directory data was downloaded into.
    """
    wfo = nwswfos[radar_id]
    fnames = glob("%s/K%s_SDUS*_NVW%s*" % (output_path, wfo, radar_id[1:]))

    for f in fnames:
        date_str = f[-12:]
        dt = datetime.strptime(date_str, '%Y%m%d%H%M')
        dt_str = datetime.strftime(dt, '%Y-%m-%d/%H%M')

        if sfc_wind is not None:
            arg = "python vad.py %s -t %s -s %s -m %s -p %s" % (radar_id,
                                                                dt_str,
                                                                sfc_wind,
                                                                storm_motion,
                                                                output_path)
        else:
            arg = "python vad.py %s -t %s -m %s -p %s" % (radar_id,
                                                          dt_str,
                                                          storm_motion,
                                                          output_path)
        os.system(arg)
        arg = "mv %s_vad.png %s/plots/%s_%s_vad.png" % (radar_id,
                                                        output_path,
                                                        radar_id,
                                                        date_str)
        os.system(arg)

def run_vwp(output_path, radar_id):
    """
    Automatically run the vwp.py script.
    """
    arg = "python vwp.py %s -p %s" % (radar_id, output_path)
    os.system(arg)

    arg = "mv %s_vwp.png %s/plots/%s_vwp.png" % (radar_id,
                                                 output_path,
                                                 radar_id)
    os.system(arg)

def main():
    # Radar site. Checks for lowercase letters and whether this is a
    # known site ID
    radar_id = input('* Enter a radar site ID [e.g. KLOT, TORD, KFWS,...]: ')
    radar_id = radar_id.upper()
    if radar_id in nexrads.keys():
        type_ = 'nexrad'
    elif radar_id in tdwrs.keys():
        type_ = 'terminal'
    else:
        print("Radar site ID not recognized. Exiting")
        sys.exit(1)
    catalogue_base = "%s/%s/level3/NVW/" % (base, type_)
    download_base = "%s/fileServer/%s/level3/NVW/" % (base, type_)

    # Search for the earliest-available online data for this radar site.
    now = datetime.now()
    start = datetime.strftime(now-timedelta(days=31), '%Y%m%d/%H')
    end = datetime.strftime(now-timedelta(days=29), '%Y%m%d/%H')
    temp_files = find_files(radar_id, start, end, catalogue_base)
    earliest = temp_files[0][-13:]
    earliest_str = datetime.strptime(earliest, '%Y%m%d_%H%M')
    earliest_str = datetime.strftime(earliest_str, '%Y%m%d/%H:%M')

    start = datetime.strftime(now-timedelta(days=1), '%Y%m%d/%H')
    end = datetime.strftime(now, '%Y%m%d/%H')
    temp_files = find_files(radar_id, start, end, catalogue_base)
    latest = temp_files[-1][-13:]
    latest_str = datetime.strptime(latest, '%Y%m%d_%H%M')
    latest_str = datetime.strftime(latest_str, '%Y%m%d/%H:%M')

    print("**************************************************************")
    print("The oldest available scan time for %s is: %s UTC" % (radar_id,
                                                                earliest_str))
    print("Any data before this will need to be downloaded from NCEI")
    print("The latest available scan time for %s is %s UTC" % (radar_id,
                                                           latest_str))
    print("**************************************************************")

    # Do we need a check for backwards-in-time entries?
    print("Inputs for starting and ending times. If providing offline or archived data, hit ENTER for the next two prompts.")
    start_time = input('* Start time [YYYYMMDD/HH]: ')
    end_time = input('* End time [YYYYMMDD/HH]: ')
    if start_time and end_time:
        try:
            start = datetime.strptime(start_time, '%Y%m%d/%H')
            end = datetime.strptime(end_time, '%Y%m%d/%H')
        except:
            print("Improperly formatted dates. Exiting")
            sys.exit(1)

    # Lowercase checks. Checks for 0 < DDD <= 360?
    print("Inputs for surface wind and storm motion. If no wind information, hit ENTER for both.")
    sfc_wind = input('* Surface wind [DDD/SS; ENTER if none]: ')
    storm_motion = input('* Storm motion [DDD/SS or BLM or BRM; ENTER if none]: ')
    if sfc_wind == "": sfc_wind = None
    if storm_motion in ["", 'BRM', 'brm']:
        storm_motion = 'right-mover'
    elif storm_motion in ['BLM', 'blm']:
        storm_motion = 'left-mover'

    if not start_time and not end_time:
        print("No start/end time. Provide filename of zipped directory containing archived NVW files")
        archive_path = input('* Folder containing archived NVW files: ')
        archive_path = HOME_DIR + '/' + archive_path
    else:
        archive_path = None

    ##########################################################
    # End of user inputs
    ##########################################################
    if archive_path == None:
        files = find_files(radar_id, start_time, end_time, catalogue_base)
        if len(files) > 0:
            output_path = download_files(files, start_time, end_time, download_base)
            inflate_files(radar_id, files, output_path)

            if not os.path.exists(output_path + '/plots'):
                os.mkdir(output_path + '/plots')

            run_vad(output_path, radar_id, storm_motion, sfc_wind)
            run_vwp(output_path, radar_id)

            # Zip the new folder up to allow download access from Jupyter
            #print("Creating zipped file %s with output" % (output_path))
            shutil.make_archive(output_path, 'zip', output_path)
        else:
            print("No archived VAD files found. Sorry...")

    # If user has specified a directory containing archived .nids NVW files
    elif archive_path != None:
        archive_path = archive_path.strip(' ')

        if not os.path.exists(archive_path + '/plots'):
            os.mkdir(archive_path + '/plots')

        # For whatever reason, some of the SDUS headers seem to change. Quick fix
        # seems to be just to rename these. Probably worth a peek inside just to make sure
        # the data's good, however.
        ncei_files = glob(archive_path + '/*SDUS*')
        for f in ncei_files:
            idx = f.index('K' + nwswfos[radar_id])
            header = int(f[idx+9:idx+11])
            if header != 34:
                new_f = f[0:idx+9] + "34" + f[idx+11:]
                print("Renaming : %s" % (f))
                shutil.move(f, new_f)

        run_vad(archive_path, radar_id, storm_motion, sfc_wind)
        run_vwp(archive_path, radar_id)

        # Zip the new folder up to allow easier download access.
        #print("Creating zipped file %s with output" % (archive_path))
        shutil.make_archive(archive_path, 'zip', archive_path)

    else:
        print("Bad user inputs.")
if __name__ == "__main__": main()
