#!/usr/bin/env python
import sys,pmag,math

def main():
    """
    NAME
	specimens_results_magic.py

    DESCRIPTION
	combines pmag_specimens.txt file with age, location, acceptance criteria and
	outputs pmag_results table along with other MagIC tables necessary for uploading to the database

    SYNTAX
	specimens_results_magic.py [command line options]

    OPTIONS
	-h prints help message and quits
	-usr USER:   identify user, default is ""
	-f: specimen input magic_measurements format file, default is "magic_measurements.txt"
	-fsp: specimen input pmag_specimens format file, default is "pmag_specimens.txt"
	-fsm: sample input er_samples format file, default is "er_samples.txt"
	-fsi: specimen input er_sites format file, default is "er_sites.txt"
	-fla: specify a file with paleolatitudes for calculating VADMs, default is not to calculate VADMS
	-fa AGES: specify er_ages format file with age information
	-crd [s,g,t,b]:   specify coordinate system
	    (s, specimen, g geographic, t, tilt corrected, b, geographic and tilt corrected)
	    Default is to assume geographic
	    NB: only the tilt corrected data will appear on the results table, if both g and t are selected.
	-age MIN MAX UNITS:   specify age boundaries and units
	-exc:  use exiting selection criteria (in pmag_criteria.txt file), default is default criteria
	-C: no acceptance criteria
	-aD:  average directions per sample, default is NOT
	-aI:  average multiple specimen intensities per sample, default is NOT
	-aC:  average all components together, default is NOT
	-pol:  calculate polarity averages
	-sam:  save sample level vgps and v[a]dms, default is NOT
	-p: plot directions and look at intensities by site, default is NOT
	    -fmt: specify output for saved images, default is svg (only if -p set)
	-lat: use present latitude for calculating VADMs, default is not to calculate VADMs
	-xD: skip directions
	-xI: skip intensities
    OUPUT
	writes pmag_samples, pmag_sites, pmag_results tables
    """
# set defaults
    Comps=[] # list of components
    version_num=pmag.get_version()
    args=sys.argv
    DefaultAge=["none"]
    skipdirs,coord,excrit,custom,vgps,average,Iaverage,plotsites,opt=1,0,0,0,0,0,0,0,0
    get_model_lat=0 # this skips VADM calculation altogether, when get_model_lat=1, uses present day
    fmt='svg'
    dir_path="."
    model_lat_file=""
    Caverage=0
    infile='pmag_specimens.txt'
    measfile="magic_measurements.txt"
    sampfile="er_samples.txt"
    sitefile="er_sites.txt"
    agefile="er_ages.txt"
    specout="er_specimens.txt"
    sampout="pmag_samples.txt"
    siteout="pmag_sites.txt"
    resout="pmag_results.txt"
    critout="pmag_criteria.txt"
    instout="magic_instruments.txt"
    sigcutoff,OBJ="",""
    noDir,noInt=0,0
    polarity=0
    coords=['0']
    Dcrit,Icrit,nocrit=0,0,0
# get command line stuff
    if "-h" in args:
	print main.__doc__
	sys.exit()
    if '-f' in args:
	ind=args.index("-f")
	measfile=args[ind+1]
    if '-fsp' in args:
	ind=args.index("-fsp")
	infile=args[ind+1]
    if '-fsi' in args:
	ind=args.index("-fsi")
	sitefile=args[ind+1]
    if "-crd" in args:
	ind=args.index("-crd")
	coord=args[ind+1]
	if coord=='s':coords=['-1']
	if coord=='g':coords=['0']
	if coord=='t':coords=['100']
	if coord=='b':coords=['0','100']
    if "-usr" in args:
	ind=args.index("-usr")
	user=sys.argv[ind+1]
    else: user=""
    if "-C" in args: Dcrit,Icrit,nocrit=1,1,1 # no selection criteria
    if "-sam" in args: vgps=1 # save sample level VGPS/VADMs
    if "-age" in args:
	ind=args.index("-age")
	DefaultAge[0]=args[ind+1]
	DefaultAge.append(args[ind+2])
	DefaultAge.append(args[ind+3])
    Daverage,Iaverage,Caverage=0,0,0
    if "-aD" in args: Daverage=1 # average by sample specimen directions
    if "-aI" in args: Iaverage=1 # average by sample specimen intensities
    if "-aC" in args: Caverage=1 # average all components together ???  why???
    if "-pol" in args: polarity=1 # calculate averages by polarity
    if '-xD' in args:noDir=1
    if '-xI' in args:
	noInt=1
    elif "-fla" in args: 
	if '-lat' in args:
	    print "you should set a paleolatitude file OR use present day lat - not both"
	    sys.exit()
	ind=args.index("-fla")
	model_lat_file=args[ind+1]
	get_model_lat=2
	mlat=open(model_lat_file,'rU')
	ModelLats=[]
	for line in mlat.readlines():
	    ModelLat={}
	    tmp=line.split()
	    ModelLat["er_site_name"]=tmp[0]
	    ModelLat["site_model_lat"]=tmp[1]
	    ModelLats.append(ModelLat)
	get_model_lat=2
    elif '-lat' in args:
	get_model_lat=1
    if "-p" in args: 
	plotsites=1
	if "-fmt" in args: 
	    ind=args.index("-fmt")
	    fmt=args[ind+1]
	if noDir==0: # plot by site - set up plot window
	    import pmagplotlib
	    EQ={}
	    EQ['eqarea']=1
	    pmagplotlib.plot_init(EQ['eqarea'],5,5) # define figure 1 as equal area projection

    if '-WD' in args:
	ind=args.index("-WD")
	dir_path=args[ind+1]
	infile=dir_path+'/'+infile
	measfile=dir_path+'/'+measfile
	instout=dir_path+'/'+instout
	sampfile=dir_path+'/'+sampfile
	sitefile=dir_path+'/'+sitefile
	agefile=dir_path+'/'+agefile
	specout=dir_path+'/'+specout
	sampout=dir_path+'/'+sampout
	siteout=dir_path+'/'+siteout
	resout=dir_path+'/'+resout
	critout=dir_path+'/'+critout
	if model_lat_file!="":model_lat_file=dir_path+'/'+model_lat_file
    if "-exc" in args: # use existing pmag_criteria file 
	if "-C" in args:
	    print 'you can not use both existing and no criteria - choose either -exc OR -C OR neither (for default)'
	    sys.exit()
	crit_data,file_type=pmag.magic_read(critout)
	print "Acceptance criteria read in from ", critout
    else  : # use default criteria (if nocrit set, then get really loose criteria as default)
	crit_data=pmag.default_criteria(nocrit)
	if nocrit==0:
	    print "Acceptance criteria are defaults"
	else:
	    print "No acceptance criteria used "
    for critrec in crit_data: # get the selection criteria sorted out into dictionaries
	if critrec["pmag_criteria_code"]=="DE-SPEC": SpecCrit=critrec
	if critrec["pmag_criteria_code"]=="DE-SAMP": SampCrit=critrec
	if critrec["pmag_criteria_code"]=="IE-SAMP": SampIntCrit=critrec
	if critrec["pmag_criteria_code"]=="IE-SITE": SiteIntCrit=critrec
	if critrec["pmag_criteria_code"]=="DE-SITE": SiteCrit=critrec
	if critrec["pmag_criteria_code"]=="NPOLE": NpoleCrit=critrec
	if critrec["pmag_criteria_code"]=="RPOLE": RpoleCrit=critrec
	if critrec["pmag_criteria_code"]=="IE-SPEC":
	    SpecIntCrit=critrec
	    accept_keys=['specimen_int_ptrm_n','specimen_md','specimen_fvds','specimen_b_beta','specimen_dang','specimen_drats']
	    accept={}
	    accept['specimen_int_ptrm_n']=2.0
	    for critrec in crit_data:
		critrec['er_citation_names']="This study"
		critrec['criteria_definition']="Criteria for selection of specimen direction"
		if critrec["pmag_criteria_code"]=="IE-SPEC":
		    for key in accept_keys:
			if key not in critrec.keys():
			    accept[key]=-1
			else:
			    accept[key]=float(critrec[key])
    TmpCrits=[SpecCrit,SpecIntCrit,SampCrit,SiteIntCrit,SiteCrit,NpoleCrit,RpoleCrit]
    #
    # assemble criteria keys and store in file
    #
    PmagCrits,critkeys=pmag.fillkeys(TmpCrits)
    pmag.magic_write(critout,PmagCrits,'pmag_criteria')
    print "\n Pmag Criteria stored in ",critout,'\n'
#
# now we're done slow dancing
#
    SiteNFO,file_type=pmag.magic_read(sitefile) # read in site data - has the lats and lons
    height_nfo=pmag.get_dictitem(SiteNFO,'site_height','','F') # find all the sites with height info.  
    if agefile !="":AgeNFO,file_type=pmag.magic_read(agefile) # read in the age information
    Data,file_type=pmag.magic_read(infile) # read in specimen interpretations
    IntData=pmag.get_dictitem(Data,'specimen_int','','F') # retrieve specimens with intensity data
    comment,orient="",[]
    samples,sites=[],[]
    for rec in Data: # run through the data filling in missing keys and finding all components, coordinates available
# fill in missing fields, collect unique sample and site names
	if 'er_sample_name' not in rec.keys():
	    rec['er_sample_name']=""
	elif rec['er_sample_name'] not in samples:
	    samples.append(rec['er_sample_name'])
	if 'er_site_name' not in rec.keys():
	    rec['er_site_name']=""
	elif rec['er_site_name'] not in sites:
	    sites.append(rec['er_site_name'])
	if 'specimen_int' not in rec.keys():rec['specimen_int']=''
	if 'specimen_comp_name' not in rec.keys():rec['specimen_comp_name']='A'
	if rec['specimen_comp_name'] not in Comps:Comps.append(rec['specimen_comp_name'])
        rec['specimen_tilt_correction']=rec['specimen_tilt_correction'].strip('\n')
	if "specimen_tilt_correction" not in rec.keys(): rec["specimen_tilt_correction"]="-1" # assume sample coordinates
	if rec["specimen_tilt_correction"] not in orient: orient.append(rec["specimen_tilt_correction"])  # collect available coordinate systems
	if "specimen_direction_type" not in rec.keys(): rec["specimen_direction_type"]='l'  # assume direction is line - not plane
	if "specimen_dec" not in rec.keys(): rec["specimen_direction_type"]=''  # if no declination, set direction type to blank
	if "specimen_n" not in rec.keys(): rec["specimen_n"]=''  # put in n
	if "specimen_alpha95" not in rec.keys(): rec["specimen_alpha95"]=''  # put in alpha95 
	if "magic_method_codes" not in rec.keys(): rec["magic_method_codes"]=''
     #
     # start parsing data into SpecDirs, SpecPlanes, SpecInts 
    SpecInts,SpecDirs,SpecPlanes=[],[],[]
    samples.sort() # get sorted list of samples and sites
    sites.sort()
    if noInt==0: # don't skip intensities
	IntData=pmag.get_dictitem(Data,'specimen_int','','F') # retrieve specimens with intensity data
	if nocrit==0: # use selection criteria
	    for rec in IntData: # do selection criteria
		score,kill=pmag.grade(rec,accept)
		if score==len(accept.keys()): SpecInts.append(rec) # intensity record to be included in sample, site calculations
	else:
	    SpecInts=IntData[:] # take everything - no selection criteria
    if noDir==0: # don't skip directions
	AllDirs=pmag.get_dictitem(Data,'specimen_direction_type','','F') # retrieve specimens with directed lines and planes
	Ns=pmag.get_dictitem(AllDirs,'specimen_n','','F')  # get all specimens with specimen_n information 
	if nocrit!=1: # use selection criteria
	    for rec in Ns: # look through everything with specimen_n for "good" data
		if int(rec["specimen_n"])>=int(SpecCrit["specimen_n"]): # enough measurments
		    if rec["specimen_mad"]!=""  and float(rec["specimen_mad"])<=float(SpecCrit["specimen_mad"]): # good enough MAD
			SpecDirs.append(rec)
		    elif rec["specimen_alpha95"]!="" and  float(rec["specimen_alpha95"])<=float(SpecCrit["specimen_alpha95"]):# good enough a95
			SpecDirs.append(rec)
	else: # no criteria
	    SpecDirs=AllDirs[:] # take them all
# SpecDirs is now the list of all specimen directions (lines and planes) that pass muster
#
    PmagSamps,SampDirs=[],[] # list of all sample data and list of those that pass the DE-SAMP criteria
    PmagSites,PmagResults=[],[] # list of all site data and selected results
    for samp in samples: # run through the sample names
	if Daverage==1: #  average by sample if desired
	   SampDir=pmag.get_dictitem(SpecDirs,'er_sample_name',samp,'T') # get all the directional data for this sample
	   if len(SampDir)>0: # there are some directions
	       for coord in coords: # step through desired coordinate systems
		   CoordDir=pmag.get_dictitem(SampDir,'specimen_tilt_correction',coord,'T') # get all the directions for this sample
		   if len(CoordDir)>0: # there are some with this coordinate system
		       if Caverage==0: # look component by component
			   for comp in Comps:
			       CompDir=pmag.get_dictitem(CoordDir,'specimen_comp_name',comp,'T') # get all directions from this component
			       if len(CompDir)>0: # there are some
				   PmagSampRec=pmag.lnpbykey(CompDir,'sample','specimen') # get a sample average from all specimens
				   PmagSampRec["er_location_name"]=CompDir[0]['er_location_name'] # decorate the sample record
				   PmagSampRec["er_site_name"]=CompDir[0]['er_site_name']
				   PmagSampRec["er_sample_name"]=samp
				   PmagSampRec["er_citation_names"]="This study"
				   PmagSampRec["er_analyst_mail_names"]=user
				   PmagSampRec['magic_software_packages']=version_num
				   if nocrit!=1:PmagSampRec['pmag_criteria_codes']="DE-SPEC"
				   if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
				   site_height=pmag.get_dictitem(height_nfo,'er_site_name',PmagSampRec['er_site_name'],'T')
				   if len(site_height)>0:PmagSampRec["sample_height"]=site_height[0]['site_height'] # add in height if available
				   PmagSampRec['sample_comp_name']=comp
				   PmagSampRec['sample_tilt_correction']=coord
				   PmagSampRec['er_specimen_names']= pmag.getlist(CompDir,'er_specimen_name') # get a list of the specimen names used
				   PmagSampRec['magic_method_codes']= pmag.getlist(CompDir,'magic_method_codes') # get a list of the methods used
				   if nocrit!=1: # apply selection criteria
				       if PmagSampRec['sample_alpha95']!="" and float(PmagSampRec['sample_alpha95'])<=SampCrit['sample_alpha95']:
					   SampDirs.append(PmagSampRec)
					   if vgps==1: # if sample level VGP info desired, do that now
					       PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
					       if PmagResRec!="":PmagResults.append(PmagResRec)
				       elif PmagSampRec['sample_alpha95']=="" and SampCrit['sample_alpha95']=="":
					   SampDirs.append(PmagSampRec)
					   if vgps==1: # if sample level VGP info desired, do that now
					       PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
					       if PmagResRec!="":PmagResults.append(PmagResRec)
				   else: # no selection criteria
					   SampDirs.append(PmagSampRec)
					   if vgps==1: # if sample level VGP info desired, do that now
					       PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
					       if PmagResRec!="":PmagResults.append(PmagResRec)
				   PmagSamps.append(PmagSampRec)
		       if Caverage==1: # average all components together  basically same as above
			   PmagSampRec=pmag.lnpbykey(CoordDir,'sample','specimen')
			   PmagSampRec["er_location_name"]=CoordDir[0]['er_location_name']
			   PmagSampRec["er_site_name"]=CoordDir[0]['er_site_name']
			   PmagSampRec["er_sample_name"]=samp
			   PmagSampRec["er_citation_names"]="This study"
			   PmagSampRec["er_analyst_mail_names"]=user
			   PmagSampRec['magic_software_packages']=version_num
			   if nocrit!=1:PmagSampRec['pmag_criteria_codes']="DE-SPEC"
			   if agefile != "": PmagSampRec= pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_",AgeNFO,DefaultAge)
			   site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
			   if len(site_height)>0:PmagSampRec["sample_height"]=site_height[0]['site_height'] # add in height if available
			   PmagSampRec['sample_tilt_correction']=coord
			   PmagSampRec['sample_comp_name']= pmag.getlist(CoordDir,'specimen_comp_name') # get components used
			   PmagSampRec['er_specimen_names']= pmag.getlist(CoordDir,'er_specimen_name') # get specimne names averaged
			   PmagSampRec['magic_method_codes']= pmag.getlist(CoordDir,'magic_method_codes') # assemble method codes
			   if nocrit!=1: # apply selection criteria
			       if float(PmagSampRec['sample_alpha95'])<=SampCrit['sample_alpha95']: 
				   SampDirs.append(PmagSampRec)
				   if vgps==1:
				       PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
				       if PmagResRec!="":PmagResults.append(PmagResRec)
			   else: # take everything
			       SampDirs.append(PmagSampRec)
			       if vgps==1:
				   PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO)
				   if PmagResRec!="":PmagResults.append(PmagResRec)
			   PmagSamps.append(PmagSampRec)
	if Iaverage==1: #  average by sample if desired
	   SampInts=[] # list of pmag sample records with intensity data
	   SampI=pmag.get_dictitem(SpecInts,'er_sample_name',samp,'T') # get all the intensity data for this sample
	   if len(SampI)>0: # there are some
	       PmagSampRec=pmag.average_int(SampI,'specimen','sample') # get average intensity stuff
	       PmagSampRec["sample_description"]="sample intensity" # decorate sample record
	       PmagSampRec["sample_direction_type"]=""
	       PmagSampRec['er_site_name']=SampI[0]["er_site_name"]
	       PmagSampRec['er_sample_name']=samp
	       PmagSampRec['er_location_name']=SampI[0]["er_location_name"]
	       PmagSampRec["er_citation_names"]="This study"
	       PmagSampRec["er_analyst_mail_names"]=user
	       if agefile != "":   PmagSampRec=pmag.get_age(PmagSampRec,"er_site_name","sample_inferred_", AgeNFO,DefaultAge)
	       site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
	       if len(site_height)>0:PmagSampRec["sample_height"]=site_height[0]['site_height'] # add in height if available
	       if nocrit!=1: PmagSampRec['pmag_criteria_codes']="IE-SPEC"
	       PmagSampRec['er_specimen_names']= pmag.getlist(SampInts,'er_specimen_name')
	       PmagSampRec['magic_method_codes']= pmag.getlist(SampInts,'magic_method_codes')
	       if vgps==1 and get_model_lat!=0: #
		  if get_model_lat==1:
		      PmagResRec=pmag.getsampVGP(PmagSampRec,SiteNFO,'vadm')
		  elif get_model_lat==2:
		      PmagResRec=pmag.getsampVGP(PmagSampRec,ModelLats,'vadm')
		      if PmagResRec!="":PmagResRec['magic_method_codes']=PmagResRec['magic_method_codes']+":IE-MLAT"
		  if PmagResRec!="":PmagResults.append(PmagResRec)
	       PmagSamps.append(PmagSampRec)
    if len(PmagSamps)>0:
	TmpSamps,keylist=pmag.fillkeys(PmagSamps) # fill in missing keys from different types of records       
	pmag.magic_write(sampout,TmpSamps,'pmag_samples') # save in sample output file
	print ' sample averages written to ',sampout
   
#
#create site averages from specimens or samples as specified
#
    for site in sites:
	if Daverage==0: key,dirlist,crit='specimen',SpecDirs,'DE-SPEC' # if specimen averages at site level desired
	if Daverage==1: key,dirlist,crit='sample',SampDirs,'DE-SAMP' # if sample averages at site level desired
	tmp=pmag.get_dictitem(dirlist,'er_site_name',site,'T') # get all the sites with  directions
	tmp1=pmag.get_dictitem(tmp,key+'_tilt_correction',coords[-1],'T') # use only the last coordinate if Caverage==0
	sd=pmag.get_dictitem(SiteNFO,'er_site_name',site,'T') # fish out site information (lat/lon, etc.)
	if len(sd)>0:
            sitedat=sd[0]
	    if Caverage==0: # do component wise averaging
		for comp in Comps:
		    siteD=pmag.get_dictitem(tmp1,key+'_comp_name',comp,'T') # get all components comp
		    if len(siteD)>0: # there are some for this site and component name
			PmagSiteRec=pmag.lnpbykey(siteD,'site',key) # get an average for this site
			PmagSiteRec['site_comp_name']=comp # decorate the site record
			PmagSiteRec["er_location_name"]=siteD[0]['er_location_name']
			PmagSiteRec["er_site_name"]=siteD[0]['er_site_name']
			PmagSiteRec['site_tilt_correction']=coords[-1]
			PmagSiteRec['site_comp_name']= pmag.getlist(siteD,key+'_comp_name')
			PmagSiteRec['er_'+key+'_names']= pmag.getlist(siteD,'er_'+key+'_name')
# determine the demagnetization code (DC3,4 or 5) for this site
			AFnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-AF','has'))
			Tnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-T','has'))
			DC=3
			if AFnum>0:DC+=1
			if Tnum>0:DC+=1
			PmagSiteRec['magic_method_codes']= pmag.getlist(siteD,'magic_method_codes')+':'+ 'LP-DC'+str(DC)
			PmagSiteRec['magic_method_codes'].strip(":")
			if plotsites==1:
                            print PmagSiteRec['er_site_name']
                            pmagplotlib.plotSITE(EQ['eqarea'],PmagSiteRec,siteD,key) # plot and list the data
			PmagSites.append(PmagSiteRec) 
	    else: # last component only
	        siteD=tmp1[:] # get the last orientation system specified
	        if len(siteD)>0: # there are some
	            PmagSiteRec=pmag.lnpbykey(siteD,'site',key) # get the average for this site 
	            PmagSiteRec["er_location_name"]=siteD[0]['er_location_name'] # decorate the record
    		    PmagSiteRec["er_site_name"]=siteD[0]['er_site_name']
		    PmagSiteRec['site_comp_name']=comp
		    PmagSiteRec['site_tilt_correction']=coords[-1]
		    PmagSiteRec['site_comp_name']= pmag.getlist(siteD,key+'_comp_name')
		    PmagSiteRec['er_'+key+'_names']= pmag.getlist(siteD,'er_'+key+'_name')
    		    AFnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-AF','has'))
    	    	    Tnum=len(pmag.get_dictitem(siteD,'magic_method_codes','LP-DIR-T','has'))
	    	    DC=3
		    if AFnum>0:DC+=1
		    if Tnum>0:DC+=1
		    PmagSiteRec['magic_method_codes']= pmag.getlist(siteD,'magic_method_codes')+':'+ 'LP-DC'+str(DC)
		    PmagSiteRec['magic_method_codes'].strip(":")
		    if Daverage==0:PmagSiteRec['site_comp_name']= pmag.getlist(siteD,key+'_comp_name')
	    	    if plotsites==1:pmagplotlib.plotSITE(EQ['eqarea'],PmagSiteRec,siteD,key)
		    PmagSites.append(PmagSiteRec)
        else:
            print 'site information not found in er_sites for site, ',site,' site will be skipped'
    for PmagSiteRec in PmagSites: # now decorate each dictionary some more, and calculate VGPs etc. for results table
	PmagSiteRec["er_citation_names"]="This study"
	PmagSiteRec["er_analyst_mail_names"]=user
	PmagSiteRec['magic_software_packages']=version_num
	if nocrit!=1:PmagSiteRec['pmag_criteria_codes']=crit
	if agefile != "": PmagSiteRec= pmag.get_age(PmagSiteRec,"er_site_name","site_inferred_",AgeNFO,DefaultAge)
	PmagSiteRec['pmag_criteria_codes']=crit
	if 'site_n_lines' in PmagSiteRec.keys() and 'site_n_planes' in PmagSiteRec.keys() and PmagSiteRec['site_n_lines']!="" and PmagSiteRec['site_n_planes']!="":
	    if int(PmagSiteRec["site_n_planes"])>0:
		PmagSiteRec["magic_method_codes"]=PmagSiteRec['magic_method_codes']+":DE-FM-LP"
	    elif int(PmagSiteRec["site_n_lines"])>2:
		PmagSiteRec["magic_method_codes"]=PmagSiteRec['magic_method_codes']+":DE-FM"
	    if 'site_n' in PmagSiteRec.keys() and int(PmagSiteRec["site_n"]) >= int(SiteCrit['site_n']) and int(PmagSiteRec["site_n_lines"]) >= int(SiteCrit['site_n_lines']) and float(PmagSiteRec["site_k"]) >= float(SiteCrit["site_k"]) and float(PmagSiteRec["site_alpha95"]) <= float(SiteCrit["site_alpha95"]): # acceptible site mean
		PmagResRec={} # set up dictionary for the pmag_results table entry
		PmagResRec['data_type']='i' # decorate it a bit
		PmagResRec['magic_software_packages']=version_num
		PmagSiteRec['site_description']='Site direction included in results table' 
		PmagResRec['pmag_criteria_codes']=PmagSiteRec['pmag_criteria_codes']+':DE-SITE'
		dec=float(PmagSiteRec["site_dec"])
		inc=float(PmagSiteRec["site_inc"])
		a95=float(PmagSiteRec["site_alpha95"])
	        sitedat=pmag.get_dictitem(SiteNFO,'er_site_name',PmagSiteRec['er_site_name'],'T')[0] # fish out site information (lat/lon, etc.)
		lat=float(sitedat['site_lat'])
		lon=float(sitedat['site_lon'])
		plong,plat,dp,dm=pmag.dia_vgp(dec,inc,a95,lat,lon) # get the VGP for this site
		if PmagSiteRec['site_tilt_correction']=='-1':C=' (spec coord) '
		if PmagSiteRec['site_tilt_correction']=='0':C=' (geog. coord) '
		if PmagSiteRec['site_tilt_correction']=='100':C=' (strat. coord) '
		PmagResRec["pmag_result_name"]="VGP Site: "+PmagSiteRec["er_site_name"] # decorate some more
		PmagResRec["result_description"]="Site VGP, coord system = "+coord+' component: '+comp
		PmagResRec['er_site_names']=PmagSiteRec['er_site_name']
		PmagResRec['pmag_criteria_codes']=PmagSiteRec["pmag_criteria_codes"]+":DE-SITE"
		PmagResRec['er_citation_names']='This study'
		PmagResRec['er_analyst_mail_names']=user
		PmagResRec["er_location_names"]=PmagSiteRec["er_location_name"]
		PmagResRec["er_"+key+"_names"]=PmagSiteRec["er_"+key+"_names"]
		PmagResRec["tilt_correction"]=PmagSiteRec['site_tilt_correction']
		PmagResRec["pole_comp_name"]=PmagSiteRec['site_comp_name']
		PmagResRec["average_dec"]=PmagSiteRec["site_dec"]
		PmagResRec["average_inc"]=PmagSiteRec["site_inc"]
		PmagResRec["average_alpha95"]=PmagSiteRec["site_alpha95"]
		PmagResRec["average_n"]=PmagSiteRec["site_n"]
		PmagResRec["average_n_lines"]=PmagSiteRec["site_n_lines"]
		PmagResRec["average_n_planes"]=PmagSiteRec["site_n_planes"]            
		PmagResRec["vgp_n"]=PmagSiteRec["site_n"]
		PmagResRec["average_k"]=PmagSiteRec["site_k"]
		PmagResRec["average_r"]=PmagSiteRec["site_r"]
		PmagResRec["average_lat"]='%10.4f ' %(lat)
		PmagResRec["average_lon"]='%10.4f ' %(lon)
		if agefile != "": PmagResRec= pmag.get_age(PmagResRec,"er_site_names","average_",AgeNFO,DefaultAge)
		site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
		if len(site_height)>0:PmagResRec["average_height"]=site_height[0]['site_height']
		PmagResRec["vgp_lat"]='%7.1f ' % (plat)
		PmagResRec["vgp_lon"]='%7.1f ' % (plong)
		PmagResRec["vgp_dp"]='%7.1f ' % (dp)
		PmagResRec["vgp_dm"]='%7.1f ' % (dm)
		PmagResRec["magic_method_codes"]= PmagSiteRec["magic_method_codes"]
		if PmagSiteRec['site_tilt_correction']=='0':PmagSiteRec['magic_method_codes']=PmagSiteRec['magic_method_codes']+":DA-DIR-GEO"
                if PmagSiteRec['site_tilt_correction']=='100':PmagSiteRec['magic_method_codes']=PmagSiteRec['magic_method_codes']+":DA-DIR-TILT"
                PmagSiteRec['site_polarity']=""
                if polarity==1: # assign polarity based on angle of pole lat to spin axis - may want to re-think this sometime
                      angle=pmag.angle([0,0],[0,(90-plat)])
                      if angle <= 55.: PmagSiteRec["site_polarity"]='n'
                      if angle > 55. and angle < 125.: PmagSiteRec["site_polarity"]='t'
                      if angle >= 125.: PmagSiteRec["site_polarity"]='r'
            PmagResults.append(PmagResRec)
    if noInt!=1:
      for site in sites: # now do intensities for each site
        if plotsites==1:print site
        if Iaverage==0: key,intlist,crit='specimen',SpecInts,'IE-SPEC' # if using specimen level data
        if Iaverage==1: key,intlist,crit='sample',SampInts,'IE-SPEC' # if using sample level data
        Ints=pmag.get_dictitem(intlist,'er_site_name',site,'T') # get all the intensities  for this site
        if len(Ints)>0: # there are some
            PmagSiteRec=pmag.average_int(Ints,key,'site') # get average intensity stuff for site table
            PmagResRec=pmag.average_int(Ints,key,'average') # get average intensity stuff for results table
            if plotsites==1: # if site by site examination requested - print this site out to the screen
                for rec in Ints:print rec['er_'+key+'_name'],' %7.1f'%(1e6*float(rec[key+'_int']))
                if len(Ints)>1:
                    print 'Average: ','%7.1f'%(1e6*float(PmagResRec['average_int'])),'N: ',len(Ints)
                    print 'Sigma: ','%7.1f'%(1e6*float(PmagResRec['average_int_sigma'])),'Sigma %: ',PmagResRec['average_int_sigma_perc']
                print ""
                raw_input()
            er_location_name=Ints[0]["er_location_name"] 
            PmagSiteRec["er_location_name"]=er_location_name # decorate the records
            PmagSiteRec["er_citation_names"]="This study"
            PmagResRec["er_location_names"]=er_location_name
            PmagResRec["er_citation_names"]="This study"
            PmagSiteRec["er_analyst_mail_names"]=user
            PmagResRec["er_analyst_mail_names"]=user
            PmagResRec["data_type"]='i'
            if Iaverage==0:
                PmagSiteRec['er_specimen_names']= pmag.getlist(Ints,'er_specimen_name') # list of all specimens used
                PmagResRec['er_specimen_names']= pmag.getlist(Ints,'er_specimen_name')
            if Iaverage==1:
                PmagSiteRec['er_sample_names']= pmag.getlist(Ints,'er_sample_name') # list of all samples used
                PmagResRec['er_sample_names']= pmag.getlist(Ints,'er_sample_name')
            PmagSiteRec['er_site_name']= site
            PmagResRec['er_site_names']= site
            PmagSiteRec['magic_method_codes']= pmag.getlist(Ints,'magic_method_codes')
            PmagResRec['magic_method_codes']= pmag.getlist(Ints,'magic_method_codes')
            if int(PmagResRec["average_int_n"]) >= int(SiteIntCrit['site_int_n']) or nocrit==1: # apply criteria or NOT
                if nocrit==1 or (float(PmagResRec["average_int_sigma"]) <=float(SiteIntCrit['site_int_sigma']) or float(PmagResRec['average_int_sigma_perc']) <= float(SiteIntCrit['site_int_sigma_perc'])): 
                  b,sig=float(PmagResRec['average_int']),""
                  if(PmagResRec['average_int_sigma'])!="":sig=float(PmagResRec['average_int_sigma'])
                  sdir=pmag.get_dictitem(PmagResults,'er_site_names',site,'T') # fish out site direction
                  if len(sdir)>0 and  sdir[-1]['average_inc']!="": # get the VDM for this record using last average inclination (hope it is the right one!)
                        inc=float(sdir[0]['average_inc']) # 
                        mlat=pmag.magnetic_lat(inc) # get magnetic latitude using dipole formula
                        PmagResRec["vdm"]='%8.3e '% (pmag.b_vdm(b,mlat)) # get VDM with magnetic latitude
                        PmagResRec["vdm_n"]=PmagResRec['average_int_n']
                        if sig=="":
                            vdm_sig=pmag.b_vdm(float(PmagResRec['averge_int_sigma']),mlat)
                            PmagResRec["vdm_sigma"]='%8.3e '% (vdm_sig)
                        else:
                            PmagResRec["vdm_sigma"]=""
                  mlat="" # define a model latitude
                  if get_model_lat==1: # use present site latitude
                    mlats=pmag.get_dictitem(SiteNFO,'er_site_name',site,'T')
                    if len(mlats)>0: mlat=mlats[0]['site_lat']
                  elif get_model_lat==2: # use a model latitude from some plate reconstruction model (or something)
                    mlats=pmag.get_dictitem(ModelLats,'er_site_name',site,'T')
                    if len(mlats)>0: PmagResRec['model_lat']=mlats[0]['site_model_lat']
                    mlat=PmagResRec['model_lat']
                  if mlat!="":
                    PmagResRec["vadm"]='%8.3e '% (pmag.b_vdm(b,float(mlat))) # get the VADM using the desired latitude
                    if sig!="":
                        vdm_sig=pmag.b_vdm(float(PmagResRec['average_int_sigma']),float(mlat))
                        PmagResRec["vadm_sigma"]='%8.3e '% (vdm_sig)
                        PmagResRec["vadm_n"]=PmagResRec['average_int_n']
                    else:
                        PmagResRec["vadm_sigma"]=""
            PmagResRec['magic_software_packages']=version_num
            PmagResRec["pmag_result_name"]="V[A]DM: Site "+site
            PmagResRec["result_description"]="V[A]DM of site"
            PmagResRec["pmag_criteria_codes"]="IE-SITE"
            if agefile != "": PmagResRec= pmag.get_age(PmagResRec,"er_site_names","average_",AgeNFO,DefaultAge)
            site_height=pmag.get_dictitem(height_nfo,'er_site_name',site,'T')
            if len(site_height)>0:PmagResRec["average_height"]=site_height[0]['site_height']
            PmagSites.append(PmagSiteRec)
            PmagResults.append(PmagResRec)
    if len(PmagSites)>0:
        Tmp,keylist=pmag.fillkeys(PmagSites)         
        pmag.magic_write(siteout,Tmp,'pmag_sites')
        print ' sites written to ',siteout
    else: print "No Site level table"
    if len(PmagResults)>0:
        TmpRes,keylist=pmag.fillkeys(PmagResults)         
        pmag.magic_write(resout,TmpRes,'pmag_results')
        print ' results written to ',resout
    else: print "No Results level table"
# do average by polarity if desired
main()
