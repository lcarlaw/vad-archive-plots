from __future__ import print_function

import numpy as np

import matplotlib as mpl
mpl.use('agg')
import pylab
from matplotlib.patches import Circle, Rectangle
from matplotlib.lines import Line2D
from matplotlib.colors import ListedColormap
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

import json
from datetime import datetime, timedelta

from params import vec2comp

_seg_hghts = [0, 3, 6, 9, 12, 18] 
_seg_colors = ['r', '#00ff00', '#008800', '#993399', 'c']
_vwp_colors = ['#737373','#a2cdde','#1987cc','#1ac015','#014b00','#ff7a09',
               '#fe2101','#e205e0','000000']
_vwp_levs = np.arange(0, 100, 10)
_vwp_cols = ListedColormap(_vwp_colors)
x_start = 0.03           # Where to plot last VWP column on image
max_alt = 10.            # Top altitude (in km) of the VWP
_alt_labs = np.arange(1, max_alt, 1)
km2kft = 3.28084
_alt_labs_kft = np.arange(5, max_alt*km2kft, 5)
_bad_rms = 10.

def roundup(x):
    """Round to the nearest 10s"""
    import math
    return int(math.ceil(x / 10.0)) * 10

def _total_seconds(td):
    return td.days * 24 * 3600 + td.seconds + td.microseconds * 1e-6

def _fmt_timedelta(td):
    seconds = int(_total_seconds(td))
    periods = [
            ('dy', 60*60*24),
            ('hr',    60*60),
            ('min',      60),
            ('sec',       1)
            ]

    strings=[]
    for period_name,period_seconds in periods:
            if seconds > period_seconds:
                    period_value, seconds = divmod(seconds,period_seconds)
                    strings.append("%s %s" % (period_value, period_name))

    return " ".join(strings)


def _plot_param_table(parameters, web=False):
    storm_dir, storm_spd = parameters['storm_motion']
    trans = pylab.gca().transAxes
    line_space = 0.033
    start_x = 1.02
    start_y = 1.0 - line_space

    line_y = start_y

    kwargs = {'color':'k', 'fontsize':10, 'clip_on':False, 'transform':trans}

    pylab.text(start_x + 0.175, start_y, "Parameter Table", ha='center', fontweight='bold', **kwargs)

    spacer = Line2D([start_x, start_x + 0.361], [line_y - line_space * 0.48] * 2, color='k', linestyle='-', transform=trans, clip_on=False)
    pylab.gca().add_line(spacer)
    line_y -= line_space * 1.5

    pylab.text(start_x + 0.095, line_y - 0.0025, "BWD (kts)", fontweight='bold', **kwargs)
    if not web:
        pylab.text(start_x + 0.22,  line_y - 0.0025, "SRH (m$^2$s$^{-2}$)", fontweight='bold', **kwargs)
    else:
        # Awful, awful hack for matplotlib without a LaTeX distribution
        pylab.text(start_x + 0.22,  line_y - 0.0025, "SRH (m s  )", fontweight='bold', **kwargs)
        pylab.text(start_x + 0.305,  line_y + 0.009, "2   -2", fontweight='bold', color='k', fontsize=6, clip_on=False, transform=trans)

    line_y -= line_space

    pylab.text(start_x, line_y, "0-1 km", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['shear_mag_1km']) else "%d" % int(parameters['shear_mag_1km'])
    pylab.text(start_x + 0.095, line_y, val, **kwargs)
    val = "--" if np.isnan(parameters['srh_1km']) else "%d" % int(parameters['srh_1km'])
    pylab.text(start_x + 0.22,  line_y, val, **kwargs)

    line_y -= line_space

    pylab.text(start_x, line_y, "0-3 km", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['shear_mag_3km']) else "%d" % int(parameters['shear_mag_3km'])
    pylab.text(start_x + 0.095, line_y, val, **kwargs)
    val = "--" if np.isnan(parameters['srh_3km']) else "%d" % int(parameters['srh_3km'])
    pylab.text(start_x + 0.22,  line_y, val, **kwargs)

    line_y -= line_space

    pylab.text(start_x, line_y, "0-6 km", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['shear_mag_6km']) else "%d" % int(parameters['shear_mag_6km'])
    pylab.text(start_x + 0.095, line_y, val, **kwargs)

    spacer = Line2D([start_x, start_x + 0.361], [line_y - line_space * 0.48] * 2, color='k', linestyle='-', transform=trans, clip_on=False)
    pylab.gca().add_line(spacer)
    line_y -= 1.5 * line_space

    pylab.text(start_x, line_y, "Storm Motion:", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['storm_motion']).any() else "%03d/%02d kts" % (storm_dir, storm_spd)
    pylab.text(start_x + 0.26, line_y + 0.001, val, **kwargs)

    line_y -= line_space

    bl_dir, bl_spd = parameters['bunkers_left']
    pylab.text(start_x, line_y, "Bunkers Left Mover:", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['bunkers_left']).any() else "%03d/%02d kts" % (bl_dir, bl_spd)
    pylab.text(start_x + 0.26, line_y + 0.001, val, **kwargs)

    line_y -= line_space

    br_dir, br_spd = parameters['bunkers_right']
    if not web:
        pylab.text(start_x, line_y, "Bunkers Right Mover:", fontweight='bold', **kwargs)
    else:
        pylab.text(start_x, line_y - 0.005, "Bunkers Right Mover:", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['bunkers_right']).any() else "%03d/%02d kts" % (br_dir, br_spd)
    if not web:
        pylab.text(start_x + 0.26, line_y + 0.001, val, **kwargs)
    else:
        pylab.text(start_x + 0.26, line_y - 0.001, val, **kwargs)

    line_y -= line_space

    mn_dir, mn_spd = parameters['mean_wind']
    pylab.text(start_x, line_y, "0-6 km Mean Wind:", fontweight='bold', **kwargs)
    val = "--" if np.isnan(parameters['mean_wind']).any() else "%03d/%02d kts" % (mn_dir, mn_spd)
    pylab.text(start_x + 0.26, line_y + 0.001, val, **kwargs)

    spacer = Line2D([start_x, start_x + 0.361], [line_y - line_space * 0.48] * 2, color='k', linestyle='-', transform=trans, clip_on=False)
    pylab.gca().add_line(spacer)
    line_y -= 1.5 * line_space

    if not web:
        pylab.text(start_x, line_y, "Critical Angle:", fontweight='bold', **kwargs)
        val = "--" if np.isnan(parameters['critical']) else "%d$^{\circ}$" % int(parameters['critical'])
        pylab.text(start_x + 0.18, line_y - 0.0025, val, **kwargs)
    else:
        pylab.text(start_x, line_y - 0.0075, "Critical Angle:", fontweight='bold', **kwargs)
        val = "--" if np.isnan(parameters['critical']) else "%d deg" % int(parameters['critical'])
        pylab.text(start_x + 0.18, line_y - 0.0075, val, **kwargs)


def _plot_data(data, parameters):
    storm_dir, storm_spd = parameters['storm_motion']
    bl_dir, bl_spd = parameters['bunkers_left']
    br_dir, br_spd = parameters['bunkers_right']
    mn_dir, mn_spd = parameters['mean_wind']

    u, v = vec2comp(data['wind_dir'], data['wind_spd'])
    alt = data['altitude']

    storm_u, storm_v = vec2comp(storm_dir, storm_spd)
    bl_u, bl_v = vec2comp(bl_dir, bl_spd)
    br_u, br_v = vec2comp(br_dir, br_spd)
    mn_u, mn_v = vec2comp(mn_dir, mn_spd)

    seg_idxs = np.searchsorted(alt, _seg_hghts)
    try:
        seg_u = np.interp(_seg_hghts, alt, u, left=np.nan, right=np.nan)
        seg_v = np.interp(_seg_hghts, alt, v, left=np.nan, right=np.nan)
        ca_u = np.interp(0.5, alt, u, left=np.nan, right=np.nan)
        ca_v = np.interp(0.5, alt, v, left=np.nan, right=np.nan)
    except ValueError:
        seg_u = np.nan * np.array(_seg_hghts)
        seg_v = np.nan * np.array(_seg_hghts)
        ca_u = np.nan
        ca_v = np.nan

    mkr_z = np.arange(16)
    mkr_u = np.interp(mkr_z, alt, u, left=np.nan, right=np.nan)
    mkr_v = np.interp(mkr_z, alt, v, left=np.nan, right=np.nan)

    for idx in range(len(_seg_hghts) - 1):
        idx_start = seg_idxs[idx]
        idx_end = seg_idxs[idx + 1]

        if not np.isnan(seg_u[idx]):
            pylab.plot([seg_u[idx], u[idx_start]], [seg_v[idx], v[idx_start]], '-', color=_seg_colors[idx], linewidth=1.5)

        if idx_start < len(data['rms_error']) and data['rms_error'][idx_start] == 0.:
            # The first segment is to the surface wind, draw it in a dashed line
            pylab.plot(u[idx_start:(idx_start + 2)], v[idx_start:(idx_start + 2)], '--', color=_seg_colors[idx], linewidth=1.5)
            pylab.plot(u[(idx_start + 1):idx_end], v[(idx_start + 1):idx_end], '-', color=_seg_colors[idx], linewidth=1.5)
        else:
            pylab.plot(u[idx_start:idx_end], v[idx_start:idx_end], '-', color=_seg_colors[idx], linewidth=1.5)

        if not np.isnan(seg_u[idx + 1]):
            pylab.plot([u[idx_end - 1], seg_u[idx + 1]], [v[idx_end - 1], seg_v[idx + 1]], '-', color=_seg_colors[idx], linewidth=1.5)

        for upt, vpt, rms in list(zip(u, v, data['rms_error']))[idx_start:idx_end]:
            rad = np.sqrt(2) * rms
            circ = Circle((upt, vpt), rad, color=_seg_colors[idx], alpha=0.05)
            pylab.gca().add_patch(circ)

    pylab.plot(mkr_u, mkr_v, 'ko', ms=10)
    for um, vm, zm in zip(mkr_u, mkr_v, mkr_z):
        if not np.isnan(um):
            pylab.text(um, vm - 0.1, str(zm), va='center', ha='center', color='white', size=6.5, fontweight='bold')

    try:
        pylab.plot([storm_u, u[0]], [storm_v, v[0]], 'c-', linewidth=0.75)
        pylab.plot([u[0], ca_u], [v[0], ca_v], 'm-', linewidth=0.75)
    except IndexError:
        pass

    if not (np.isnan(bl_u) or np.isnan(bl_v)):
        pylab.plot(bl_u, bl_v, 'ko', markersize=5, mfc='none')
        pylab.text(bl_u + 0.5, bl_v - 0.5, "LM", ha='left', va='top', color='k', fontsize=10)

    if not (np.isnan(br_u) or np.isnan(br_v)):
        pylab.plot(br_u, br_v, 'ko', markersize=5, mfc='none')
        pylab.text(br_u + 0.5, br_v - 0.5, "RM", ha='left', va='top', color='k', fontsize=10)

    if not (np.isnan(mn_u) or np.isnan(mn_v)):
        pylab.plot(mn_u, mn_v, 's', color='#a04000', markersize=5, mfc='none')
        pylab.text(mn_u + 0.6, mn_v - 0.6, "MEAN", ha='left', va='top', color='#a04000', fontsize=10)

    smv_is_brm = (storm_u == br_u and storm_v == br_v)
    smv_is_blm = (storm_u == bl_u and storm_v == bl_v)
    smv_is_mnw = (storm_u == mn_u and storm_v == mn_v)

    if not (np.isnan(storm_u) or np.isnan(storm_v)) and not (smv_is_brm or smv_is_blm or smv_is_mnw):
        pylab.plot(storm_u, storm_v, 'k+', markersize=6)
        pylab.text(storm_u + 0.5, storm_v - 0.5, "SM", ha='left', va='top', color='k', fontsize=10)


def _plot_background(min_u, max_u, min_v, max_v):
    max_ring = int(np.ceil(max(
        np.hypot(min_u, min_v),
        np.hypot(min_u, max_v),
        np.hypot(max_u, min_v),
        np.hypot(max_u, max_v)
    )))

    pylab.axvline(x=0, linestyle='-', color='#999999')
    pylab.axhline(y=0, linestyle='-', color='#999999')

    for irng in range(10, max_ring, 10):
        ring = Circle((0., 0.), irng, linestyle='dashed', fc='none', ec='#999999')
        pylab.gca().add_patch(ring)

        if irng <= max_u - 10:
            rng_str = "%d kts" % irng if max_u - 20 < irng <= max_u - 10 else "%d" % irng

            pylab.text(irng + 0.5, -0.5, rng_str, ha='left', va='top', fontsize=9, color='#999999', clip_on=True, clip_box=pylab.gca().get_clip_box())


def plot_hodograph(data, parameters, fname=None, web=False, fixed=False, archive=False):
    img_title = "%s VWP valid %s" % (data.rid, data['time'].strftime("%d %b %Y %H%M UTC"))
    if fname is not None:
        img_file_name = fname
    else:
        img_file_name = "%s_vad.png" % data.rid

    u, v = vec2comp(data['wind_dir'], data['wind_spd'])

    sat_age = 6 * 3600
    if fixed or len(u) == 0:
        ctr_u, ctr_v = 20, 20
        size = 120
    else:
        ctr_u = u.mean()
        ctr_v = v.mean()
        size = max(u.max() - u.min(), v.max() - v.min()) + 20
        size = max(120, size)

    min_u = ctr_u - size / 2
    max_u = ctr_u + size / 2
    min_v = ctr_v - size / 2
    max_v = ctr_v + size / 2

    now = datetime.utcnow()
    img_age = now - data['time']
    age_cstop = min(_total_seconds(img_age) / sat_age, 1) * 0.4
    age_color = mpl.cm.get_cmap('hot')(age_cstop)[:-1]

    age_str = "Image created on %s (%s old)" % (now.strftime("%d %b %Y %H%M UTC"), _fmt_timedelta(img_age))

    pylab.figure(figsize=(10, 7.5), dpi=150)
    fig_wid, fig_hght = pylab.gcf().get_size_inches()
    fig_aspect = fig_wid / fig_hght

    axes_left = 0.05
    axes_bot = 0.05
    axes_hght = 0.9
    axes_wid = axes_hght / fig_aspect
    pylab.axes((axes_left, axes_bot, axes_wid, axes_hght))

    _plot_background(min_u, max_u, min_v, max_v)
    _plot_data(data, parameters)
    _plot_param_table(parameters, web=web)

    pylab.xlim(min_u, max_u)
    pylab.ylim(min_v, max_v)
    pylab.xticks([])
    pylab.yticks([])

    if not archive:
        pylab.title(img_title, color=age_color)
        pylab.text(0., -0.01, age_str, transform=pylab.gca().transAxes, ha='left', va='top', fontsize=9, color=age_color)
    else:
        pylab.title(img_title)

    if web:
        web_brand = "http://www.autumnsky.us/vad/"
        pylab.text(1.0, -0.01, web_brand, transform=pylab.gca().transAxes, ha='right', va='top', fontsize=9)

    pylab.savefig(img_file_name, dpi=pylab.gcf().dpi)
    pylab.close()

    if web:
        bounds = {'min_u':min_u, 'max_u':max_u, 'min_v':min_v, 'max_v':max_v}
        print(json.dumps(bounds)) 

#...
#...Additional functions to plot VWPs
#...
def _plot_vwp_background(times):
    pylab.axvline(x=x_start, linestyle='-', linewidth=1, color='#b50000')
    ivals = [x*((1-x_start)/(len(times))) for x in range(0, len(times))]
    knt = 0
    for iline in ivals:
        pylab.axvline(x=iline+x_start, linestyle='-', linewidth=0.25, color='#cbcbcb')
        slice_time = times[knt].strftime("%H%M")
        pylab.text(iline+x_start, -0.017, slice_time, transform=pylab.gca().transAxes, fontsize=8, ha='center')
        knt += 1

    rect = Rectangle((x_start,0.), 1.1, 0.02, color='#c0adac')   
    pylab.gca().add_patch(rect)

    # Plot the vertical coordinate reference bar
    pylab.axvline(x=x_start-0.025, linestyle='-', linewidth=1, color='k')
    x_vals = np.empty_like(_alt_labs)
    x_vals.fill(x_start)
    for klev in range(0, len(_alt_labs)):
        pylab.text(x_vals[klev]-0.035, (_alt_labs[klev]/max_alt)+0.03, str(int(_alt_labs[klev])), transform=pylab.gca().transAxes, color='k', fontsize=10, ha='left')
    for klev in range(0, len(_alt_labs_kft)):
        pylab.text(x_vals[klev]-0.02, (_alt_labs_kft[klev]/(max_alt*km2kft))+0.03, str(int(_alt_labs_kft[klev])), transform=pylab.gca().transAxes, color='k', fontsize=10, ha='left')

    pylab.text(0.003, 0, 'KM', color='k', fontsize=10, fontweight='bold', ha='right')
    pylab.text(0.0222, 0, 'KFT', color='k', fontsize=10, fontweight='bold', ha='right')


def _plot_vwp_data(data):
    ivals = [x*((1-x_start)/(len(data))) for x in range(0, len(data))]
    knt = 0
    for iline in ivals:
        u, v = vec2comp(data[knt]['wind_dir'], data[knt]['wind_spd'])
        alt = data[knt]['altitude']
        x = np.empty_like(alt)
        x.fill(iline)
        mpl.pyplot.barbs(x+x_start, (alt/max_alt)+0.03, u, v, data[knt]['wind_spd'], length=6, cmap=_vwp_cols, clim=(_vwp_levs[0],_vwp_levs[-1]), transform=pylab.gca().transAxes, clip_on=True, zorder=4, linewidth=1.)
        # If the RMS exceeds _bad_rms, highlight with a red circle. Also, plot 
        # the wind speeds as color-coded text next to the barbs
        for klev in range(0, len(data[knt]['wind_spd'])):
            rms = data[knt]['rms_error'][klev]
            x_loc = x[klev]+(x_start + 0.002)
            y_loc = (alt[klev]/max_alt) + 0.02
            if rms >= _bad_rms:
                ring = Circle((x_loc, y_loc+0.01), 0.01, linestyle='solid', fc='none', ec='red', linewidth=2)
                pylab.gca().add_patch(ring)
            spd = data[knt]['wind_spd'][klev]
            text_spd = roundup(spd)
            spd_idx = np.where(text_spd > _vwp_levs)[0]
            if len(spd_idx) == 0:
                spd_idx = 0
            else:
                spd_idx = spd_idx[-1]
            spd_idx = np.clip(spd_idx, 0, len(_vwp_colors)-1) 
            pylab.text(x_loc, y_loc, str(int(spd)), transform=pylab.gca().transAxes, fontsize=9, color=_vwp_colors[spd_idx], va='bottom')
        knt += 1

def plot_vwp(data, times, parameters, fname=None, add_hodo=False, fixed=False, web=False, archive=False):
    img_title = "%s VWP valid ending %s" % (data[0].rid, times[0].strftime("%d %b %Y %H%M UTC"))
    if fname is not None:
        img_file_name = fname
    else:
        img_file_name = "%s_vwp.png" % data[0].rid

    sat_age = 6 * 3600
    now = datetime.utcnow()
    img_age = now - times[0]
    age_cstop = min(_total_seconds(img_age) / sat_age, 1) * 0.4
    age_color = mpl.cm.get_cmap('hot')(age_cstop)[:-1]

    age_str = "Image created on %s (%s old)" % (now.strftime("%d %b %Y %H%M UTC"), _fmt_timedelta(img_age))

    fig_aspect = 2.5714
    fig_wid = 24
    fig_hght = fig_wid / fig_aspect
    pylab.figure(figsize=(fig_wid, fig_hght), dpi=200)

    axes_left = 0.01
    axes_bot = 0.02
    axes_hght = 0.94
    axes_wid = axes_hght / fig_aspect
    pylab.axes((axes_left, axes_bot, 0.99, axes_hght))

    _plot_vwp_background(times)
    _plot_vwp_data(data)
    #_plot_param_table(parameters, web=web)

    pylab.xlim(0, 1.)
    pylab.ylim(0, 1.)
    pylab.xticks([])
    pylab.yticks([])
    pylab.box(False)

    if not archive:
        pylab.title(img_title, color=age_color)
        pylab.text(x_start, 1.03, age_str, transform=pylab.gca().transAxes, ha='left', va='top', fontsize=9, color=age_color)
    else:
        pylab.title(img_title)

    if web:
        web_brand = "http://www.autumnsky.us/vad/"
        pylab.text(1.0, -0.01, web_brand, transform=pylab.gca().transAxes, ha='right', va='top', fontsize=9)

    if add_hodo:
        inset_ax = inset_axes(pylab.gca(), width="30%", height="55%", loc='upper left', bbox_to_anchor=(0.63,0,0.85,1), bbox_transform=pylab.gca().transAxes)
        u, v = vec2comp(data[0]['wind_dir'], data[0]['wind_spd'])

        if fixed or len(u) == 0:
            ctr_u, ctr_v = 20, 20
            size = 120
        else:
            ctr_u = u.mean()
            ctr_v = v.mean()
            size = max(u.max() - u.min(), v.max() - v.min()) + 20
            size = max(120, size)

        min_u = ctr_u - size / 2
        max_u = ctr_u + size / 2
        min_v = ctr_v - size / 2
        max_v = ctr_v + size / 2
        
        _plot_background(min_u, max_u, min_v, max_v)
        _plot_data(data[0], parameters)
        _plot_param_table(parameters, web=web)


        inset_ax.set_xlim(min_u, max_u)
        inset_ax.set_ylim(min_v, max_v)
        inset_ax.set_xticks([])
        inset_ax.set_yticks([])

    pylab.savefig(img_file_name, dpi=pylab.gcf().dpi)
    pylab.close()

    if web:
        bounds = {'min_u':min_u, 'max_u':max_u, 'min_v':min_v, 'max_v':max_v}
        print(json.dumps(bounds)) 