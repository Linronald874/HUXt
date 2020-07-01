# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 12:50:49 2020

@author: mathewjowens
"""
import httplib2
import urllib
import HUXt as H
import os
from pyhdf.SD import SD, SDC  
import numpy as np
import astropy.units as u
from scipy.io import netcdf


# <codecell> Get MAS data from MHDweb



def getMASboundaryconditions(cr=np.NaN, observatory='', runtype='', runnumber=''):
    """
    A function to grab the  Vr and Br boundary conditions from MHDweb. An order
    of preference for observatories is given in the function. Checks first if
    the data already exists in the HUXt boundary condition folder

    Parameters
    ----------
    cr : INT
        Carrington rotation number 
    observatory : STRING
        Name of preferred observatory (e.g., 'hmi','mdi','solis',
        'gong','mwo','wso','kpo'). Empty if no preference and automatically selected 
    runtype : STRING
        Name of preferred MAS run type (e.g., 'mas','mast','masp').
        Empty if no preference and automatically selected 
    runnumber : STRING
        Name of preferred MAS run number (e.g., '0101','0201').
        Empty if no preference and automatically selected    

    Returns
    -------
    flag : INT
        1 = successful download. 0 = files exist, -1 = no file found.

    """
    
    assert(np.isnan(cr)==False)
    
    #the order of preference for different MAS run results
    overwrite=False
    if not observatory:
        observatories_order=['hmi','mdi','solis','gong','mwo','wso','kpo']
    else:
        observatories_order=[str(observatory)]
        overwrite=True #if the user wants a specific observatory, overwrite what's already downloaded
        
    if not runtype:
        runtype_order=['masp','mas','mast']
    else:
        runtype_order=[str(runtype)]
        overwrite=True
    
    if not runnumber:
        runnumber_order=['0201','0101']
    else:
        runnumber_order=[str(runnumber)]
        overwrite=True
    
    #get the HUXt boundary condition directory
    dirs = H._setup_dirs_()
    _boundary_dir_ = dirs['boundary_conditions'] 
      
    #example URL: http://www.predsci.com/data/runs/cr2010-medium/mdi_mas_mas_std_0101/helio/br_r0.hdf 
    heliomas_url_front='http://www.predsci.com/data/runs/cr'
    heliomas_url_end='_r0.hdf'
    
    vrfilename = 'HelioMAS_CR'+str(int(cr)) + '_vr'+heliomas_url_end
    brfilename = 'HelioMAS_CR'+str(int(cr)) + '_br'+heliomas_url_end
    
    if (os.path.exists(os.path.join( _boundary_dir_, brfilename)) == False or 
        os.path.exists(os.path.join( _boundary_dir_, vrfilename)) == False or
        overwrite==True): #check if the files already exist
        #Search MHDweb for a HelioMAS run, in order of preference 
        h = httplib2.Http()
        foundfile=False
        for masob in observatories_order:
            for masrun in runtype_order:
                for masnum in runnumber_order:
                    urlbase=(heliomas_url_front + str(int(cr)) + '-medium/' + masob +'_' +
                         masrun + '_mas_std_' + masnum + '/helio/')
                    url=urlbase + 'br' + heliomas_url_end
                    #print(url)
                    
                    #see if this br file exists
                    resp = h.request(url, 'HEAD')
                    if int(resp[0]['status']) < 400:
                        foundfile=True
                        #print(url)
                    
                    #exit all the loops - clumsy, but works
                    if foundfile: 
                        break
                if foundfile:
                    break
            if foundfile:
                break
            
        if foundfile==False:
            print('No data available for given CR and observatory preferences')
            return -1
        
        #download teh vr and br files            
        print('Downloading from: ',urlbase)
        urllib.request.urlretrieve(urlbase+'br'+heliomas_url_end,
                           os.path.join(_boundary_dir_, brfilename) )    
        urllib.request.urlretrieve(urlbase+'vr'+heliomas_url_end,
                           os.path.join(_boundary_dir_, vrfilename) )  
        
        return 1
    else:
         print('Files already exist for CR' + str(int(cr)))   
         return 0


   
def readMASvrbr(cr):
    """
    A function to read in the MAS coundary conditions for a given CR

    Parameters
    ----------
    cr : INT
        Carrington rotation number

    Returns
    -------
    MAS_vr : NP ARRAY (NDIM = 2)
        Solar wind speed at 30rS, in km/s
    MAS_vr_Xa : NP ARRAY (NDIM = 1)
        Carrington longitude of Vr map, in rad
    MAS_vr_Xm : NP ARRAY (NDIM = 1)
        Latitude of Vr as angle down from N pole, in rad
    MAS_br : NP ARRAY (NDIM = 2)
        Radial magnetic field at 30rS, in model units
    MAS_br_Xa : NP ARRAY (NDIM = 1)
        Carrington longitude of Br map, in rad
    MAS_br_Xm : NP ARRAY (NDIM = 1)
       Latitude of Br as angle down from N pole, in rad

    """
    #get the boundary condition directory
    dirs = H._setup_dirs_()
    _boundary_dir_ = dirs['boundary_conditions'] 
    #create the filenames 
    heliomas_url_end='_r0.hdf'
    vrfilename = 'HelioMAS_CR'+str(int(cr)) + '_vr'+heliomas_url_end
    brfilename = 'HelioMAS_CR'+str(int(cr)) + '_br'+heliomas_url_end

    filepath=os.path.join(_boundary_dir_, vrfilename)
    assert os.path.exists(filepath)
    #print(os.path.exists(filepath))

    file = SD(filepath, SDC.READ)
    # print(file.info())
    # datasets_dic = file.datasets()
    # for idx,sds in enumerate(datasets_dic.keys()):
    #     print(idx,sds)
        
    sds_obj = file.select('fakeDim0') # select sds
    MAS_vr_Xa = sds_obj.get() # get sds data
    sds_obj = file.select('fakeDim1') # select sds
    MAS_vr_Xm = sds_obj.get() # get sds data
    sds_obj = file.select('Data-Set-2') # select sds
    MAS_vr = sds_obj.get() # get sds data
    
    #convert from model to physicsal units
    MAS_vr = MAS_vr*481.0 * u.km/u.s
    MAS_vr_Xa=MAS_vr_Xa * u.rad
    MAS_vr_Xm=MAS_vr_Xm * u.rad
    
    
    filepath=os.path.join(_boundary_dir_, brfilename)
    assert os.path.exists(filepath)
    file = SD(filepath, SDC.READ)
   
    sds_obj = file.select('fakeDim0') # select sds
    MAS_br_Xa = sds_obj.get() # get sds data
    sds_obj = file.select('fakeDim1') # select sds
    MAS_br_Xm = sds_obj.get() # get sds data
    sds_obj = file.select('Data-Set-2') # select sds
    MAS_br = sds_obj.get() # get sds data
    
    MAS_br_Xa=MAS_br_Xa * u.rad
    MAS_br_Xm=MAS_br_Xm * u.rad
    
    return MAS_vr, MAS_vr_Xa, MAS_vr_Xm, MAS_br, MAS_br_Xa, MAS_br_Xm


def get_MAS_long_profile(cr, lat=0.0*u.deg):
    """
    a function to download, read and process MAS output to provide HUXt boundary
    conditions at a given latitude

    Parameters
    ----------
    cr : INT
        Carrington rotation number
    lat : FLOAT
        Latitude at which to extract the longitudinal profile, measure up from equator

    Returns
    -------
    vr_in : NP ARRAY (NDIM = 1)
        Solar wind speed as a function of Carrington longitude at solar equator.
        Interpolated to HUXt longitudinal resolution. In km/s
    br_in : NP ARRAY(NDIM = 1)
        Radial magnetic field as a function of Carrington longitude at solar equator.
        Interpolated to HUXt longitudinal resolution. Dimensionless

    """
    
    assert(np.isnan(cr)==False and cr>0)
    assert(lat>= -90.0*u.deg)
    assert(lat<= 90.0*u.deg)
    
    #convert angle from equator to angle down from N pole
    ang_from_N_pole=np.pi/2 - (lat.to(u.rad)).value
    
    #check the data exist, if not, download them
    flag=getMASboundaryconditions(cr)    #getMASboundaryconditions(cr,observatory='mdi')
    assert(flag > -1)
    
    #read the HelioMAS data
    MAS_vr, MAS_vr_Xa, MAS_vr_Xm, MAS_br, MAS_br_Xa, MAS_br_Xm = readMASvrbr(cr)
    
    #extract the value at the given latitude
    vr=np.ones(len(MAS_vr_Xa))
    for i in range(0,len(MAS_vr_Xa)):
        vr[i]=np.interp(ang_from_N_pole,MAS_vr_Xm.value,MAS_vr[i][:].value)
    
    br=np.ones(len(MAS_br_Xa))
    for i in range(0,len(MAS_br_Xa)):
        br[i]=np.interp(ang_from_N_pole,MAS_br_Xm.value,MAS_br[i][:])
        
    #now interpolate on to the HUXt longitudinal grid
    # nlong=H.huxt_constants()['nlong']
    # dphi=2*np.pi/nlong
    # longs=np.linspace(dphi/2 , 2*np.pi -dphi/2,nlong)  
    longs, dlon, nlon = H.longitude_grid(lon_start=0.0 * u.rad, lon_stop=2*np.pi * u.rad)
    vr_in=np.interp(longs.value,MAS_vr_Xa.value,vr)*u.km/u.s
    br_in=np.interp(longs.value,MAS_br_Xa.value,br)
    
    #convert br into +/- 1
    #br_in[br_in>=0.0]=1.0*u.dimensionless_unscaled
    #br_in[br_in<0.0]=-1.0*u.dimensionless_unscaled
    
    return vr_in, br_in


def get_MAS_maps(cr):
    """
    a function to download, read and process MAS output to provide HUXt boundary
    conditions as lat-long maps, along with angle from equator for the maps
    maps returned in native resolution, not HUXt resolution

    Parameters
    ----------
    cr : INT
        Carrington rotation number


    Returns
    -------
    vr_map : NP ARRAY 
        Solar wind speed as a Carrington longitude-latitude map. In km/s   
    vr_lats :
        The latitudes for the Vr map, in radians from trhe equator   
    vr_longs :
        The Carrington longitudes for the Vr map, in radians
    br_map : NP ARRAY
        Br as a Carrington longitude-latitude map. Dimensionless
    br_lats :
        The latitudes for the Br map, in radians from trhe equator
    br_longs :
        The Carrington longitudes for the Br map, in radians 
    """
    
    assert(np.isnan(cr)==False and cr>0)
    
    
    #check the data exist, if not, download them
    flag=getMASboundaryconditions(cr)    #getMASboundaryconditions(cr,observatory='mdi')
    assert(flag > -1)
    
    #read the HelioMAS data
    MAS_vr, MAS_vr_Xa, MAS_vr_Xm, MAS_br, MAS_br_Xa, MAS_br_Xm = readMASvrbr(cr)
    
    vr_map=MAS_vr
    br_map=MAS_br
    
    #convert the lat angles from N-pole to equator centred
    vr_lats= (np.pi/2)*u.rad - MAS_vr_Xm
    br_lats= (np.pi/2)*u.rad - MAS_br_Xm
    
    #flip lats, so they're increasing in value
    vr_lats=np.flipud(vr_lats)
    br_lats=np.flipud(br_lats)
    vr_map=np.fliplr(vr_map)
    br_map=np.fliplr(br_map)
    
    vr_longs=MAS_vr_Xa
    br_longs=MAS_br_Xa

    #convert br into +/- 1
    #br_in[br_in>=0.0]=1.0*u.dimensionless_unscaled
    #br_in[br_in<0.0]=-1.0*u.dimensionless_unscaled
    
    return vr_map, vr_lats, vr_longs, br_map, br_lats, br_longs

# <codecell> Map MAS inputs to smaller radial distances, for starting HUXt below 30 rS

@u.quantity_input(v_outer=u.km / u.s)
@u.quantity_input(r_outer=u.solRad)
@u.quantity_input(lon_outer=u.rad)
@u.quantity_input(r_inner=u.solRad)
def map_v_inwards(v_outer, r_outer, lon_outer, r_inner):
    """
    Function to map v from r_outer (in rs) to r_inner (in rs) accounting for 
    residual acceleration, but neglecting stream interactions.
    
    :param v_outer: Solar wind speed at outer radial distance. Units of km/s.
    :param r_outer: Radial distance at outer radial distance. Units of km.  
    :param lon_outer: Carrington longitude at outer distance. Units of rad
    :param r_inner: Radial distance at inner radial distance. Units of km.
    :return v_inner: Solar wind speed mapped from r_outer to r_inner. Units of km/s.
    :return lon_inner: Carrington longitude at r_inner. Units of rad.
    """

    if r_outer < r_inner:
        raise ValueError("Warning: r_outer < r_inner. Mapping will not work.")

    # get the acceleration parameters
    constants = H.huxt_constants()
    alpha = constants['alpha']  # Scale parameter for residual SW acceleration
    rH = constants['r_accel'].to(u.kilometer).value  # Spatial scale parameter for residual SW acceleration
    Tsyn = constants['synodic_period'].to(u.s).value
    r_outer = r_outer.to(u.km).value
    r_inner = r_inner.to(u.km).value

    # compute the speed at the new inner boundary height (using Vacc term, equation 5 in the paper)
    v0 = v_outer.value / (1 + alpha * (1 - np.exp((r_inner - r_outer) / rH)))

    # compute the transit time from the new to old inner boundary heights (i.e., integrate equations 3 and 4 wrt to r)
    A = v0 + alpha * v0
    term1 = rH * np.log(A * np.exp(r_outer / rH) - 
                      alpha * v0 * np.exp(r_inner / rH)) / A
    term2 = rH * np.log(A * np.exp(r_inner / rH) - 
                      alpha * v0 * np.exp(r_inner / rH)) / A                      
    T_integral = term1 - term2

    # work out the longitudinal shift
    phi_new = H._zerototwopi_(lon_outer.value + (T_integral / Tsyn) * 2 * np.pi)

    return v0*u.km/u.s, phi_new*u.rad


@u.quantity_input(v_outer=u.km / u.s)
@u.quantity_input(r_outer=u.solRad)
@u.quantity_input(r_inner=u.solRad)
def map_v_boundary_inwards(v_outer, r_outer, r_inner):
    """
    Function to map a longitudinal V series from r_outer (in rs) to r_inner (in rs)
    accounting for residual acceleration, but neglecting stream interactions.
    Series return on HUXt longitudinal grid, not input grid
    
    :param v_outer: Solar wind speed at outer radial boundary. Units of km/s.
    :param r_outer: Radial distance at outer radial boundary. Units of km.
    :param r_inner: Radial distance at inner radial boundary. Units of km.
    :return v_inner: Solar wind speed mapped from r_outer to r_inner. Units of km/s.
    """

    if r_outer < r_inner:
        raise ValueError("Warning: r_outer < r_inner. Mapping will not work.")

    # compute the longitude grid from the length of the vouter input variable
    lon, dlon, nlon = H.longitude_grid()   
    #map each point in to a new speed and longitude
    v0, phis_new = map_v_inwards(v_outer, r_outer, lon, r_inner)

    #interpolate the mapped speeds back onto the regular Carr long grid,
    #making boundaries periodic 
    v_inner = np.interp(lon, phis_new, v0, period=2*np.pi) 

    return v_inner

@u.quantity_input(v_outer=u.km / u.s)
@u.quantity_input(r_outer=u.solRad)
@u.quantity_input(r_inner=u.solRad)
def map_ptracer_boundary_inwards(v_outer, r_outer, r_inner, ptracer_outer):
    """
    Function to map a longitudinal V series from r_outer (in rs) to r_inner (in rs)
    accounting for residual acceleration, but neglecting stream interactions.
    Series return on HUXt longitudinal grid, not input grid
    
    :param v_outer: Solar wind speed at outer radial boundary. Units of km/s.
    :param r_outer: Radial distance at outer radial boundary. Units of km.
    :param r_inner: Radial distance at inner radial boundary. Units of km.
    :param p_tracer_outer:  Passive tracer at outer radial boundary. 
    :return ptracer_inner: Passive tracer mapped from r_outer to r_inner. 
    """

    if r_outer < r_inner:
        raise ValueError("Warning: r_outer < r_inner. Mapping will not work.")

    # compute the longitude grid from the length of the vouter input variable
    lon, dlon, nlon = H.longitude_grid()   
    #map each point in to a new speed and longitude
    v0, phis_new = map_v_inwards(v_outer, r_outer, lon, r_inner)

    #interpolate the mapped speeds back onto the regular Carr long grid,
    #making boundaries periodic 
    ptracer_inner = np.interp(lon, phis_new, ptracer_outer, period=2*np.pi) 

    return ptracer_inner

@u.quantity_input(v_map=u.km / u.s)
@u.quantity_input(v_map_lat=u.rad)
@u.quantity_input(v_map_long=u.rad)
@u.quantity_input(r_outer=u.solRad)
@u.quantity_input(r_inner=u.solRad)
def map_vmap_inwards(v_map, v_map_lat, v_map_long, r_outer, r_inner):
    """
    Function to map a V Carrington map from r_outer (in rs) to r_inner (in rs),
    accounting for acceleration, but ignoring stream interaction
    Map returned on input coord system, not HUXT resolution
    
    :param vmap: Solar wind speed Carrington map at outer radial boundary. Units of km/s.
    :param v_map_lat: Latitude (from equator) of vmap positions. Units of radians
    :param v_map_long: Carrington longitude of vmap positions. Units of radians
    :param r_outer: Radial distance at outer radial boundary. Units of km.
    :param r_inner: Radial distance at inner radial boundary. Units of km.
    :return v_map_inner: Solar wind speed map at r_inner. Units of km/s.
    """

    if r_outer < r_inner:
        raise ValueError("Warning: r_outer < r_inner. Mapping will not work.")
    #check the dimensions 
    assert( len(v_map_lat) == len(v_map[1,:]) )
    assert( len(v_map_long) == len(v_map[:,1]) )
    
 
    
    v_map_inner=np.ones((len(v_map_long),len(v_map_lat)))
    for ilat in range(0,len(v_map_lat)):
        #map each point in to a new speed and longitude
        v0, phis_new = map_v_inwards(v_map[:,ilat], r_outer, v_map_long, r_inner)

        #interpolate the mapped speeds back onto the regular Carr long grid,
        #making boundaries periodic * u.km/u.s
        v_map_inner[:,ilat] = np.interp(v_map_long.value, phis_new.value, v0.value, period=2*np.pi)       
    
    
    return v_map_inner *u.km /u.s

@u.quantity_input(v_map=u.km / u.s)
@u.quantity_input(v_map_lat=u.rad)
@u.quantity_input(v_map_long=u.rad)
@u.quantity_input(ptracer_map_lat=u.rad)
@u.quantity_input(ptracer_map_long=u.rad)
@u.quantity_input(r_outer=u.solRad)
@u.quantity_input(r_inner=u.solRad)
def map_ptracer_map_inwards(v_map, v_map_lat, v_map_long, 
                            ptracer_map, ptracer_map_lat, ptracer_map_long,
                            r_outer, r_inner):
    """
    Function to map a a passive tracer (e.g., Br) Carrington map from r_outer (in rs) to r_inner (in rs),
    accounting for acceleration, but ignoring stream interaction.
    Speed and tracer maps do not need ot be on same grid (e.g., MAS)
    Map returned on input coord system, not HUXT resolution
    
    :param vmap: Solar wind speed Carrington map at outer radial boundary. Units of km/s.
    :param v_map_lat: Latitude (from equator) of vmap positions. Units of radians
    :param v_map_long: Carrington longitude of vmap positions. Units of radians
    :param ptracer_map: Tracer (e.g., Br)  Carrington map at outer radial boundary. No units
    :param ptracer_map_lat: Latitude (from equator) of tracer positions. Units of radians
    :param ptracer_map_long: Carrington longitude of tracer positions. Units of radians
    :param r_outer: Radial distance at outer radial boundary. Units of km.
    :param r_inner: Radial distance at inner radial boundary. Units of km.
    :param p_tracer_outer:  Passive tracer at outer radial boundary. 
    :return ptracer_map_inner: Passive tracer mapped from r_outer to r_inner. 
    """
    if r_outer < r_inner:
        raise ValueError("Warning: r_outer < r_inner. Mapping will not work.")
    #check the dimensions 
    assert( len(v_map_lat) == len(v_map[1,:]) )
    assert( len(v_map_long) == len(v_map[:,1]) )
    assert( len(ptracer_map_lat) == len(ptracer_map[1,:]) )
    assert( len(ptracer_map_long) == len(ptracer_map[:,1]) )
    
    ptracer_map_inner=np.ones((len(ptracer_map_long),len(ptracer_map_lat)))
    for ilat in range(0,len(ptracer_map_lat)):
        
        #extract the vr values at the ptracer latitude
        vlong=np.ones(len(v_map_long)) 
        for ilong in range(0,len(v_map_long)):
            vlong[ilong]=np.interp(ptracer_map_lat[ilat].value, v_map_lat.value, v_map[ilong,:].value)
        
        #now interpolate the longitudinal velocity to the same longs as ptracer
        v_plongs=np.interp(ptracer_map_long.value, v_map_long.value, vlong) * u.km/u.s

        #map each point in to a new speed and longitude
        v0, v_phis_new = map_v_inwards(v_plongs, r_outer, ptracer_map_long, r_inner)

        #interpolate the mapped tracer back onto the regular Carr long grid,
        #making boundaries periodic * u.km/u.s
        ptracer_map_inner[:,ilat] = np.interp(ptracer_map_long.value, v_phis_new.value, 
                                              ptracer_map[:,ilat], period=2*np.pi) 
    
    
    return ptracer_map_inner *u.dimensionless_unscaled


# <codecell> PFSSpy inputs

def get_PFSS_maps(filepath):
    """
    a function to load, read and process PFSSpy output to provide HUXt boundary
    conditions as lat-long maps, along with angle from equator for the maps
    maps returned in native resolution, not HUXt resolution

    Parameters
    ----------
    filepath : STR 
        The filepath for the PFSSpy .nc file

    Returns
    -------
    vr_map : NP ARRAY 
        Solar wind speed as a Carrington longitude-latitude map. In km/s   
    vr_lats :
        The latitudes for the Vr map, in radians from trhe equator   
    vr_longs :
        The Carrington longitudes for the Vr map, in radians
    br_map : NP ARRAY
        Br as a Carrington longitude-latitude map. Dimensionless
    br_lats :
        The latitudes for the Br map, in radians from trhe equator
    br_longs :
        The Carrington longitudes for the Br map, in radians 

    """
    
    assert os.path.exists(filepath)
    nc = netcdf.netcdf_file(filepath,'r')
    
    #for i in nc.variables:
    #    print(i, nc.variables[i])
    
    cotheta=nc.variables['cos(th)'].data  
    vr_lats=np.arcsin(cotheta[:,0])*u.rad
    br_lats=vr_lats
    
    phi=nc.variables['ph'].data
    vr_longs = phi[0,:] * u.rad
    br_longs=vr_longs
    
    br_map= np.rot90(nc.variables['br'].data) 
    vr_map= np.rot90(nc.variables['vr'].data) * u.km /u.s
    
    #convert br into +/- 1
    #br_in[br_in>=0.0]=1.0*u.dimensionless_unscaled
    #br_in[br_in<0.0]=-1.0*u.dimensionless_unscaled
    
    return vr_map, vr_lats, vr_longs, br_map, br_lats, br_longs

#filepath=os.environ['DBOX'] + 'Papers_WIP\\_coauthor\\AnthonyYeates\\windbound_b_pfss20181105.12.nc'
#vr_map, vr_lats, vr_longs, br_map, br_lats, br_longs =  get_PFSS_maps(filepath)

