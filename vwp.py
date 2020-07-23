from __future__ import print_function

import numpy as np

import sys
#import ast

from vad_reader import download_vwp, VADFile
from params import compute_parameters
from plot import plot_vwp
from wsr88d import nwswfos

import re
import argparse
from datetime import datetime, timedelta
import json

from glob import glob

"""
vwp.py
Author:     Lee Carlaw (alterations to Tim Supinie's initial vad.py module
Completed:  September 2019
Modified:   
"""
def is_vector(vec_str):
    return bool(re.match(r"[\d]{3}/[\d]{2}", vec_str))


def parse_vector(vec_str):
    return tuple(int(v) for v in vec_str.strip().split("/"))


def parse_time(time_str):
    no_my = False
    now = datetime.utcnow()
    if '-' not in time_str:
        no_my = True

        year = now.year
        month = now.month
        time_str = "%d-%d-%s" % (year, month, time_str)

    plot_time = datetime.strptime(time_str, '%Y-%m-%d/%H%M')

    if plot_time > now:
        if no_my:
            if month == 1:
                month = 12
                year -= 1
            else:
                month -= 1
            time_str = "%d-%d-%s" % (year, month, time_str)
            plot_time = datetime.strptime(time_str, '%Y-%m-%d/%H%M')
        else:
            raise ValueError("Time '%s' is in the future." % time_str)

    return plot_time

def vwp_plotter(radar_id, time=None, fname=None, local_path=None, web=False, fixed=False, add_hodo=False, comp_rap=False):
    #add_hodo = ast.literal_eval(add_hodo)
    #comp_rap = ast.literal_eval(comp_rap)

    plot_time = None
    if time:
        plot_time = parse_time(time)
    #elif local_path is not None:
    #    raise ValueError("'-t' ('--time') argument is required when loading from the local disk.")

    if not web:
        print("Plotting VWP for %s ..." % radar_id)

    if local_path is None:
        vwp, times = download_vwp(radar_id, time=plot_time)
    else:
        data = []
        times = []
        inames = "%s/K%s_SDUS34_NVW*" % (local_path, nwswfos[radar_id])
        inames = sorted(glob(inames))[::-1]

        for iname in inames:
            try:
                vad = VADFile(open(iname, 'rb'))
                data.append(vad)
                ts = datetime.strptime(iname[-12:], "%Y%m%d%H%M")
                times.append(ts)
            except:
                raise ValueError("Could not add '%s'" % iname)
                data.append([])
        
        vwp = data
        #vwp = VADFile(open(iname, 'rb'))
    vwp[0].rid = radar_id
    
    """
    f = open(('%s_output.txt') % (radar_id), 'w')
    n_vals = len(vwp[0]['wind_dir'])
    for val in range(n_vals):
            alt, dir_, spd = vwp[0]['altitude'][val], vwp[0]['wind_dir'][val],\
                             vwp[0]['wind_spd'][val]
            f.write(("%s, %s, %s\n") % (str(alt), str(dir_), str(spd)))
    f.close()
    """
    
    if not web:
        print("Valid time:", vwp[0]['time'].strftime("%d %B %Y %H%M UTC"))
    
    if add_hodo:
        params = compute_parameters(vwp[0], 'right-mover')
    else:
        params = []

    #if comp_rap:
    #    rap_data = download_rap(site_id, time=
    #else:
    plot_vwp(vwp, times, params, add_hodo=add_hodo, fname=fname, web=web, fixed=fixed, archive=(local_path is not None))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('radar_id', help="The 4-character identifier for the radar (e.g. KTLX, KFWS, etc.)")
    ap.add_argument('-a', '--add-hodo', dest='add_hodo', action='store_true', help="[True|False] Plot the hodograph as an inset on the VWP. Defaults to False.")
    ap.add_argument('-r', '--comp-rap', dest='comp_rap', action='store_true', help="[True|False] If True, downloads Op40 sounding data from the nearest available airport for overlay on VWP. Defaults to False.")
    ap.add_argument('-t', '--time', dest='time', help="Latest time to plot in the VWP retrievals. Takes the form DD/HHMM, where DD is the day, HH is the hour, and MM is the minute.")
    ap.add_argument('-f', '--img-name', dest='img_name', help="Name of the file produced.")
    ap.add_argument('-p', '--local-path', dest='local_path', help="Path to local data. If not given, download from the Internet.")
    ap.add_argument('-w', '--web-mode', dest='web', action='store_true')
    ap.add_argument('-x', '--fixed-frame', dest='fixed', action='store_true')
    args = ap.parse_args()

    np.seterr(all='ignore')

    try:
        vwp_plotter(args.radar_id,
            time=args.time,
            fname=args.img_name,
            local_path=args.local_path,
            web=args.web,
            add_hodo=args.add_hodo,
            comp_rap=args.comp_rap,
            fixed=args.fixed
        )
    except:
        if args.web:
            print(json.dumps({'error':'error'}))
        else:
            raise

if __name__ == "__main__":
    main()