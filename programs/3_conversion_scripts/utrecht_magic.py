#!/usr/bin/env python
"""
NAME
    utrecht_magic.py

DESCRIPTION
    converts Utrecht magnetometer data files to magic_measurements files

SYNTAX
    utrecht_magic.py [command line options]

OPTIONS
    -h: prints the help message and quits.
    -ID: directory for input file if not included in -f flag
    -f FILE: specify  input file, required
    -WD: directory to output files to (default : current directory)
    -F FILE: specify output  measurements file, default is measurements.txt
    -Fsp FILE: specify output specimens.txt file, default is specimens.txt
    -Fsa FILE: specify output samples.txt file, default is samples.txt 
    -Fsi FILE: specify output sites.txt file, default is sites.txt # LORI
    -Flo FILE: specify output locations.txt file, default is locations.txt
    -ncn: Site Naming Convention
     Site to Sample naming convention:
        [1] XXXXY: where XXXX is an arbitrary length site designation and Y
            is the single character sample designation.  e.g., TG001a is the
            first sample from site TG001.    [default]
        [2: default] XXXX-YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [3] XXXX.YY: YY sample from site XXXX (XXX, YY of arbitary length)
        [4-Z] XXXX[YYY]:  YYY is sample designation with Z characters from site XXX
        [5] site name = sample name
        [6] site name entered in site_name column in the orient.txt format input file  -- NOT CURRENTLY SUPPORTED
        [7-Z] [XXX]YYY:  XXX is site designation with Z characters from samples  XXXYYY
    -spc: number of characters to remove to generate sample names from specimen names
    -loc LOCNAME : specify location/study name
    -lat latitude of site (also used as bounding latitude for location)
    -lon longitude of site (also used as bounding longitude for location)
    -A: don't average replicate measurements
    -mcd: [SO-MAG,SO-SUN,SO-SIGHT...] supply how these samples were oriented
    -dc B PHI THETA: dc lab field (in microTesla), phi,and theta (in degrees) must be spaced after flag (i.e -dc 30 0 -90)
    -mno: number of orientations measured (default=8)

INPUT
    Utrecht magnetometer data file
"""
import os,sys
import pmagpy.pmag as pmag
import pmagpy.new_builder as nb
from pandas import DataFrame
from numpy import array
import pytz, datetime


def main(**kwargs):

    # initialize some stuff
    version_num = pmag.get_version()
    MagRecs,SpecOuts,SampOuts,SiteOuts,LocOuts = [],[],[],[],[]

    dir_path = kwargs.get('dir_path', '.')
    input_dir_path = kwargs.get('input_dir_path', dir_path)
    output_dir_path = dir_path
    meas_file = kwargs.get('meas_file', 'measurements.txt')
    mag_file = kwargs.get('mag_file')
    spec_file = kwargs.get('spec_file', 'specimens.txt') # specimen outfile
    samp_file = kwargs.get('samp_file', 'samples.txt')
    site_file = kwargs.get('site_file', 'sites.txt') # site outfile
    loc_file = kwargs.get('loc_file', 'locations.txt') # site outfile
    location = kwargs.get('location', 'unknown')
    dmy_flag = kwargs.get('dmy_flag', False)
    lat = kwargs.get('lat', '')
    lon = kwargs.get('lon', '')
    #oave = kwargs.get('noave', 0) # default (0) means DO average
    meth_code = kwargs.get('meth_code', "LP-NO")
    specnum = -int(kwargs.get('specnum', 0))
    samp_con = kwargs.get('samp_con', '2')
    if "4" in samp_con:
        if "-" not in samp_con:
            print "option [4] must be in form 4-Z where Z is an integer"
            return False, "naming convention option [4] must be in form 4-Z where Z is an integer"
        else:
            site_num=samp_con.split("-")[1]
            samp_con="4"
    elif "7" in samp_con:
        if "-" not in samp_con:
            print "option [7] must be in form 7-Z where Z is an integer"
            return False, "naming convention option [7] must be in form 7-Z where Z is an integer"
        else:
            site_num=samp_con.split("-")[1]
            samp_con="7"
    else: site_num=1
    try:
        DC_FIELD = float(kwargs.get('labfield',0))*1e-6
        DC_PHI = float(kwargs.get('phi',0))
        DC_THETA = float(kwargs.get('theta',0))
    except ValueError: raise ValueError('problem with your dc parameters. please provide a labfield in microTesla and a phi and theta in degrees.')
    noave = kwargs.get('noave', False)
    dmy_flag = kwargs.get('dmy_flag', False)
    meas_n_orient = kwargs.get('meas_n_orient', '8')

    # format variables
    if not mag_file:
        return False, 'You must provide a Utrecht formated file'
    mag_file = os.path.join(input_dir_path, mag_file)

    # parse data

    # Open up the Utrecht file and read the header information
    print 'mag_file in utrecht_file', mag_file
    AF_or_T = mag_file.split('.')[-1]
    data = open(mag_file, 'rU')
    line = data.readline()
    line_items = line.split(',')
    operator=line_items[0]
    operator=operator.replace("\"","")
    machine=line_items[1]
    machine=machine.replace("\"","")
    machine=machine.rstrip('\n')
    print "operator=", operator
    print "machine=", machine

    #read in measurement data
    line = data.readline()
    while line != "END" and line != '"END"':
        SpecRec,SampRec,SiteRec,LocRec = {},{},{},{}
        line_items = line.split(',')
        spec_name=line_items[0]
        spec_name=spec_name.replace("\"","")
        print "spec_name=", spec_name
        free_string=line_items[1]
        free_string=free_string.replace("\"","")
        print "free_string=", free_string
        dec=line_items[2]
        print "dec=", dec
        inc=line_items[3]
        print "inc=", inc
        volume=float(line_items[4])
        volume=volume * 1e-6 # enter volume in cm^3, convert to m^3
        print "volume=", volume
        bed_plane=line_items[5]
        print "bed_plane=", bed_plane
        bed_dip=line_items[6]
        print "bed_dip=", bed_dip

        # Configure et er_ tables
        if specnum==0: sample_name = spec_name
        else: sample_name = spec_name[:specnum]
        site = pmag.parse_site(sample_name,samp_con,site_num)
        SpecRec['specimen'] = spec_name
        SpecRec['sample'] = sample_name
        SpecOuts.append(SpecRec)
        if sample_name!="" and sample_name not in map(lambda x: x['sample'] if 'sample' in x.keys() else "", SampOuts):
            SampRec['sample'] = sample_name
            SampRec['azimuth'] = dec
            SampRec['dip'] = str(float(inc)-90)
            SampRec['bed_dip_direction'] = bed_plane
            SampRec['bed_dip'] = bed_dip
            SampRec['method_codes'] = meth_code
            SampRec['site'] = site
            SampOuts.append(SampRec)
        if site!="" and site not in map(lambda x: x['site'] if 'site' in x.keys() else "", SiteOuts):
            SiteRec['site'] = site
            SiteRec['location'] = location
            SiteRec['lat'] = lat
            SiteRec['lon'] = lon
            SiteOuts.append(SiteRec)
        if location!="" and location not in map(lambda x: x['location'] if 'location' in x.keys() else "", LocOuts):
            LocRec['location']=location
            LocRec['lat_n'] = lat
            LocRec['lon_e'] = lon
            LocRec['lat_s'] = lat
            LocRec['lon_w'] = lon
            LocOuts.append(LocRec)

        #measurement data
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")
        while line != '9999':
            print line
            step=items[0]
            step=step.split('.')
            step_value=step[0]
            step_type = ""
            if len(step) == 2:
                step_type=step[1]
            if step_type=='5':
                step_value = items[0]
            A=float(items[1])
            B=float(items[2])
            C=float(items[3])
#  convert to MagIC coordinates
            Z=-A
            X=-B
            Y=C
            cart = array([X, Y, Z]).transpose()
            direction = pmag.cart2dir(cart).transpose()
            measurement_dec = direction[0]
            measurement_inc = direction[1]
            magn_moment = direction[2] * 1.0e-12 # the data are in pico-Am^2 - this converts to Am^2
            magn_volume = direction[2] * 1.0e-12 / volume # data volume normalized - converted to A/m
            print "magn_moment=", magn_moment
            print "magn_volume=", magn_volume
            error = items[4]
            date=items[5]
            date=date.strip('"')
            if date.count("-") > 0:
                date=date.split("-")
            elif date.count("/") > 0:
                date=date.split("/")
            else: print("date format seperator cannot be identified")
            print date
            time=items[6]
            time=time.strip('"')
            time=time.split(":")
            print time
            dt = date[0] + ":" + date[1] + ":" + date[2] + ":" + time[0] + ":" + time[1] + ":" + "0"
            local = pytz.timezone("Europe/Amsterdam")
            if dmy_flag: naive = datetime.datetime.strptime(dt, "%d:%m:%Y:%H:%M:%S")
            else: naive = datetime.datetime.strptime(dt, "%m:%d:%Y:%H:%M:%S")
            local_dt = local.localize(naive, is_dst=None)
            utc_dt = local_dt.astimezone(pytz.utc)
            timestamp=utc_dt.strftime("%Y-%m-%dT%H:%M:%S")+"Z"
            print timestamp

            MagRec = {}
            MagRec["timestamp"]=timestamp
            MagRec["analysts"] = operator
            MagRec["instrument_codes"] = "Utrecht_" + machine
            MagRec["description"] = "free string = " + free_string 
            MagRec["citation"] = "This study"
            MagRec['software_packages'] = version_num
            MagRec["meas_temp"] = '%8.3e' % (273) # room temp in kelvin
            MagRec["quality"] = 'g'
            MagRec["standard"] = 'u'
            MagRec["experiments"] = location + site + spec_name
            MagRec["number"] = location + site + spec_name + items[0]
            MagRec["specimen"] = spec_name
            # MagRec["treat_ac_field"] = '0'
            if AF_or_T.lower() == "th":
                MagRec["treat_temp"] = '%8.3e' % (float(step_value)+273.) # temp in kelvin
                MagRec['treat_ac_field']='0'
                meas_type = "LP-DIR-T:LT-T-Z"
            else:
                MagRec['treat_temp']='273'
                MagRec['treat_ac_field']='%10.3e'%(float(step_value)*1e-3)
                meas_type = "LP-DIR-AF:LT-AF-Z"
            MagRec['treat_dc_field']='0'
            if step_value == '0':
                meas_type = "LT-NO"
            print "step_type=", step_type
            if step_type == '0' and AF_or_T.lower() == 'th':
                if meas_type == "":
                    meas_type = "LT-T-Z"
                else:
                    meas_type = meas_type + ":" + "LT-T-Z"
            elif step_type == '1':
                if meas_type == "":
                    meas_type = "LT-T-I"
                else:
                    meas_type = meas_type + ":" + "LT-T-I"
                MagRec['treat_dc_field']='%1.2e'%DC_FIELD
            elif step_type == '2':
                if meas_type == "":
                    meas_type = "LT-PTRM-I"
                else:
                    meas_type = meas_type + ":" + "LT-PTRM-I"
                MagRec['treat_dc_field']='%1.2e'%DC_FIELD
            elif step_type == '3':
                if meas_type == "" :
                    meas_type = "LT-PTRM-Z"
                else:
                    meas_type = meas_type + ":" + "LT-PTRM-Z"
            print "meas_type=", meas_type
            MagRec['treat_dc_field_phi'] = '%1.2f'%DC_PHI
            MagRec['treat_dc_field_theta'] = '%1.2f'%DC_THETA
            MagRec['method_codes'] = meas_type
            MagRec["magn_moment"] = magn_moment
            MagRec["magn_volume"] = magn_volume
            MagRec["dir_dec"] = measurement_dec
            MagRec["dir_inc"] = measurement_inc
            MagRec['dir_csd'] = error 
            MagRec['meas_n_orient'] = meas_n_orient
            MagRecs.append(MagRec)

            line = data.readline()
            line = line.rstrip("\n")
            items = line.split(",")
        line = data.readline()
        line = line.rstrip("\n")
        items = line.split(",")

    con = nb.Contribution(output_dir_path,read_tables=[])

    con.add_empty_magic_table('specimens')
    con.add_empty_magic_table('samples')
    con.add_empty_magic_table('sites')
    con.add_empty_magic_table('locations')
    con.add_empty_magic_table('measurements')

    con.tables['specimens'].df = DataFrame(SpecOuts)
    con.tables['samples'].df = DataFrame(SampOuts)
    con.tables['sites'].df = DataFrame(SiteOuts)
    con.tables['locations'].df = DataFrame(LocOuts)
    Fixed=pmag.measurements_methods3(MagRecs,noave)
    con.tables['measurements'].df = DataFrame(Fixed)

    con.tables['specimens'].write_magic_file(custom_name=spec_file)
    con.tables['samples'].write_magic_file(custom_name=samp_file)
    con.tables['sites'].write_magic_file(custom_name=site_file)
    con.tables['locations'].write_magic_file(custom_name=loc_file)
    con.tables['measurements'].write_magic_file(custom_name=meas_file)

    return True, meas_file

def do_help():
    return __doc__

if  __name__ == "__main__":
    #
    # get command line arguments
    #
    kwargs={}
    if "-h" in sys.argv:
        help(__name__)
        sys.exit()
    if '-WD' in sys.argv:
        ind = sys.argv.index('-WD')
        kwargs['dir_path'] = sys.argv[ind+1]
    if '-ID' in sys.argv:
        ind = sys.argv.index('-ID')
        kwargs['input_dir_path'] = sys.argv[ind+1]
    if '-F' in sys.argv:
        ind = sys.argv.index("-F")
        kwargs['meas_file'] = sys.argv[ind+1]
    if '-Fsp' in sys.argv:
        ind=sys.argv.index("-Fsp")
        kwargs['spec_file']=sys.argv[ind+1]
    if '-Fsa' in sys.argv:
        ind = sys.argv.index("-Fsa")
        kwargs['samp_file'] = sys.argv[ind+1]
    if '-Fsi' in sys.argv: # LORI addition
        ind=sys.argv.index("-Fsi")
        kwargs['site_file']=sys.argv[ind+1]
    if '-Flo' in sys.argv: # Kevin addition
        ind=sys.argv.index("-Flo")
        kwargs['loc_file']=sys.argv[ind+1]
    if '-f' in sys.argv:
        ind = sys.argv.index("-f")
        kwargs['mag_file'] = sys.argv[ind+1]
    if "-loc" in sys.argv:
        ind = sys.argv.index("-loc")
        kwargs['location'] = sys.argv[ind+1]
    if "-lat" in sys.argv:
        ind = sys.argv.index("-lat")
        kwargs['lat'] = sys.argv[ind+1]
    if "-lon" in sys.argv:
        ind = sys.argv.index("-lon")
        kwargs['lon'] = sys.argv[ind+1]
    if "-A" in sys.argv:
        kwargs['noave'] = True
    if "-mcd" in sys.argv:
        ind = sys.argv.index("-mcd")
        kwargs['meth_code'] = sys.argv[ind+1]
    if "-ncn" in sys.argv:
        ind=sys.argv.index("-ncn")
        kwargs['samp_con']=sys.argv[ind+1]
    if '-dc' in sys.argv:
        ind=sys.argv.index('-dc')
        kwargs['labfield']=sys.argv[ind+1]
        kwargs['phi']=sys.argv[ind+2]
        kwargs['theta']=sys.argv[ind+3]
    if '-spc' in sys.argv:
        ind=sys.argv.index("-spc")
        kwargs['specnum']=sys.argv[ind+1]
    if '-mno' in sys.argv:
        ind=sys.argv.index('-mno')
        kwargs['meas_n_orient']=sys.argv[ind+1]
    if 'dmy' in sys.argv:
        kwargs['dmy_flag']=True

    main(**kwargs)