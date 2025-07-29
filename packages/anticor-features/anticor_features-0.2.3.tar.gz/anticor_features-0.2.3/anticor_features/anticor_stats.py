#!/usr/bin/env python3
from __future__ import division, print_function, absolute_import

import warnings
import math
from collections import namedtuple

# Scipy imports.
try:
    from scipy._lib.six import callable, string_types, xrange
except:
    pass
try:
    from scipy._lib._version import NumpyVersion
except:
    pass
import psutil
from numpy import array, asarray, ma, zeros, var, average
import multiprocessing
from multiprocessing.dummy import Pool as ThreadPool
import scipy.special as special
import scipy.linalg as linalg
import numpy as np
from scipy.stats import rankdata
from copy import deepcopy
import h5py
from math import floor
from scipy.stats import mstats_basic, rankdata
from scipy.sparse import csr_matrix
import ray


__all__ = []

###############################################################################################################

class poop(object):
    def get_anti_cor_feature_mat(self):
        ## get the full spearman matrix
        ## first set up the hdf5 file to take in the spearman values
        if self.no_h5 and self.processes >2:
            ## first make dummy variables so there aren't any errors later
            self.hdf5_spear_out_file = None
            self.spear_f = None
            self.spear_out_hdf5 = None
            self.get_anti_cor_features_no_h5()
            return()
        else:
            if self.no_h5:
                print('-no_h5 requires >=3 processes - defaulting to h5 non-parallel')
            start = time()
            self.make_spearman_out()

            ## then populate it 
            self.add_to_spear_mat()

            ## get the total number of negative correlations
            ## and get the total number less than the cutoff of these negatives
            self.get_anti_cor_features()

            ## don't forget to close the spearman file when you're done with it
            self.spear_f.close()
        return()


    def get_anti_correlated_features(self, cutoff_multiplier = 15, min_num_features = 20):
        print('original in mat shape:',self.in_mat.shape)
        if self.in_mat.shape[0] > min_num_features:
            ## get the bootstrap shuffled null distribution
            rand_mat = get_shuffled(self, bin_size = self.bin_size)
            random_rhos = no_p_spear(rand_mat,axis=1).flatten()
            print(random_rhos)
            print(np.shape(random_rhos))
            random_pos_rhos = random_rhos[random_rhos>0]
            random_neg_rhos = random_rhos[random_rhos<0]
            print(random_neg_rhos)
            self.neg_cutoff, self.expected_prob = get_Z_cutoff(random_neg_rhos)
            #self.expected_number_exceeding = int(self.in_mat.shape[0])/self.expected_freq
            #self.cutoff_for_inclusion = expected_number_exceeding * cutoff_multiplier
            #print("features must have this many negative corrs:",self.cutoff_for_inclusion)
            print('in mat shape:',self.in_mat.shape)
            start = time()
            self.get_anti_cor_feature_mat()
            print('\n\nFinished feature selection\n\n',(time()-start)/60,"minutes\n\n")
            #sys.exit()
        else:
            print("not enough variables to do feature selection - skipping with this dataset.")
            self.anti_cor_indices = np.arange(self.in_mat.shape[0])
            print('in mat shape:',self.in_mat.shape)
        return(self.anti_cor_indices)

    def set_spear_bins(self, r, i, j):
        ## top left
        self.spear_out_hdf5[self.bins[i]:self.bins[i+1],self.bins[i]:self.bins[i+1]] = r[:self.bin_size,:self.bin_size]
        ## top right
        self.spear_out_hdf5[self.bins[i]:self.bins[i+1],self.bins[j]:self.bins[j+1]] = r[:self.bin_size,self.bin_size:]
        ## bottom left
        self.spear_out_hdf5[self.bins[j]:self.bins[j+1],self.bins[i]:self.bins[i+1]] = r[self.bin_size:,:self.bin_size]
        ## bottom right
        self.spear_out_hdf5[self.bins[j]:self.bins[j+1],self.bins[j]:self.bins[j+1]] = r[self.bin_size:,self.bin_size:]
        #print(self.spear_out_hdf5 == 0)
        #print(np.sum(self.spear_out_hdf5, axis=1))
        return()







    def add_to_spear_mat(self):
        if self.processes <= 2:
            for i in range(0,(len(self.bins)-1)):
                for j in range(i,(len(self.bins)-1)):
                    if (i!=j) or (len(self.bins) == 2):
                        print('working on',self.bins[i],self.bins[i+1],'vs',self.bins[j],self.bins[j+1])
                        r=no_p_spear(self.in_mat[self.bins[i]:self.bins[i+1],:],self.in_mat[self.bins[j]:self.bins[j+1],:], axis = 1)
                        self.set_spear_bins(r, i, j)
        else:
            ## use Ray package to do multi-processing
            import ray
            if self.process_mem != None:
                try:
                    ray.init(object_store_memory=int(self.process_mem*1000000000))
                except:
                    ray.init()
            else:
                ray.init()
            @ray.remote
            def get_remote_spear(in_mat1, in_mat2, force = True):
                return(no_p_spear(in_mat1,in_mat2, axis = 1))


            ## set up the intermediate numpy matrix saving directory
            #save_dir = process_dir(self.infile+"_rho_pieces/")
            ## make the i, j pairs
            r_jobs = []
            all_i_j = []
            cur_i_j = []
            ## this will make a list leading to the paths of all of the saved matrices
            r_paths = []
            num_blocks = len(self.bins)
            total_num_block_pair_estimate = (num_blocks**2 / 2 - num_blocks)
            for i in range(0,(len(self.bins)-1)):
                for j in range(i,(len(self.bins)-1)):
                    if (i!=j) or (len(self.bins) == 2):
                        all_i_j.append([i,j])
                        #save_path = save_dir+str(i)+"_"+str(j)+".npy"
                        ## if the number of jobs exceeds the total number of processes, start a new job queue
                        if len(r_jobs) == self.processes:
                            print("submitting jobset for next",len(r_jobs))
                            temp_r_results = ray.get(r_jobs)
                            print("\t~ %",len(all_i_j)/total_num_block_pair_estimate * 100)
                            print("\tfinished gathering results, now we're saving")
                            for w in range(len(cur_i_j)):
                                i, j = cur_i_j[w]
                                start = time()
                                self.set_spear_bins(temp_r_results[w], i, j)
                                print('\t\tsetting bin took:',(time()-start),'seconds')
                            r_jobs = []
                            cur_i_j = []
                        r_jobs.append(get_remote_spear.remote(self.in_mat[self.bins[i]:self.bins[i+1],:], self.in_mat[self.bins[j]:self.bins[j+1],:], force = self.force))
                        cur_i_j.append([i, j])
            
            ## if there are leftover jobs not done yet, do them
            if len(r_jobs) > 0:
                print("submitting jobset for next",len(r_jobs))
                temp_r_results = ray.get(r_jobs)
                print("\t~ %",len(all_i_j)/total_num_block_pair_estimate * 100)
                print("\tfinished gathering results, now we're saving")
                for w in range(len(cur_i_j)):
                    i, j = cur_i_j[w]
                    self.set_spear_bins(temp_r_results[w], i, j)
                
            ray.shutdown()
            
        return()


###############################################################################################################




###############################################################################################################

def get_shuffled(in_mat, bin_size = 5000):
    if in_mat.shape[0] <= bin_size:
        shuff_mat = deepcopy(np.array(in_mat))
    else:
        ## get a random sample of the matrix
        neg_control_sample_idxs = np.arange(in_mat.shape[0])
        np.random.shuffle(neg_control_sample_idxs)
        sample_idxs = np.sort(neg_control_sample_idxs[:bin_size])
        shuff_mat = deepcopy(np.array(in_mat[sample_idxs,:]))
        #print(shuff_mat)
    ## now shuffle it
    for i in range(shuff_mat.shape[0]):
        np.random.shuffle(shuff_mat[i,:])
    return(shuff_mat)




def _chk_asarray(a, axis):
    if axis is None:
        a = np.ravel(a)
        outaxis = 0
    else:
        a = np.asarray(a)
        outaxis = axis
    if a.ndim == 0:
        a = np.atleast_1d(a)
    return a, outaxis


def _chk2_asarray(a, b, axis):
    if axis is None:
        a = np.ravel(a)
        b = np.ravel(b)
        outaxis = 0
    else:
        a = np.asarray(a)
        b = np.asarray(b)
        outaxis = axis
    if a.ndim == 0:
        a = np.atleast_1d(a)
    if b.ndim == 0:
        b = np.atleast_1d(b)
    return a, b, outaxis


def _contains_nan(a, nan_policy='propagate'):
    policies = ['propagate', 'raise', 'omit']
    if nan_policy not in policies:
        raise ValueError("nan_policy must be one of {%s}" %
                         ', '.join("'%s'" % s for s in policies))
    try:
        # Calling np.sum to avoid creating a huge array into memory
        # e.g. np.isnan(a).any()
        with np.errstate(invalid='ignore'):
            contains_nan = np.isnan(np.sum(a))
    except TypeError:
        # If the check cannot be properly performed we fallback to omiting
        # nan values and raising a warning. This can happen when attempting to
        # sum things that are not numbers (e.g. as in the function `mode`).
        contains_nan = False
        nan_policy = 'omit'
        warnings.warn("The input array could not be properly checked for nan "
                      "values. nan values will be ignored.", RuntimeWarning)
    if contains_nan and nan_policy == 'raise':
        raise ValueError("The input contains nan values")
    return (contains_nan, nan_policy)

def make_dense(b):
    if b is not None:
        if "todense" in dir(b):
            b=b.todense()
    return(b)


def dense_rank(a):
    return(rankdata(a,method="dense"))
    

def no_p_spear(a, b=None, axis=0, nan_policy='propagate', rm_nans_by_col = False, prop = False, log_odds = False, shuffle = False, log_odds_correction = 0):
    a=make_dense(a)
    b=make_dense(b)
    return(no_p_pear(a, b=None, axis=0, nan_policy='propagate', rm_nans_by_col = rm_nans_by_col, prop = prop, log_odds = log_odds, shuffle = shuffle, log_odds_correction = log_odds_correction ))


def no_p_pear(a, b=None, axis=0, nan_policy='propagate', rm_nans_by_col = False, prop = False, log_odds = False, shuffle = False, log_odds_correction = 0):
    a, axisout = _chk_asarray(a, axis)
    
    contains_nan, nan_policy = _contains_nan(a, nan_policy)

    if contains_nan and rm_nans_by_col:
        ### FINISH THIS
        rm_idxs = np.isna(a)
    
    if contains_nan and nan_policy == 'omit':
        a = ma.masked_invalid(a)
        b = ma.masked_invalid(b)
        return no_p_spear(a, b, axis)
    
    if a.size <= 1:
        return(np.nan, np.nan)
    #ar = np.apply_along_axis(rankdata, axisout, a)
    if not log_odds:
        ar = np.apply_along_axis(dense_rank, axisout, a)
    
    br = None
    if b is not None:
        b, axisout = _chk_asarray(b, axis)
        
        contains_nan, nan_policy = _contains_nan(b, nan_policy)
        
        if contains_nan and nan_policy == 'omit':
            b = ma.masked_invalid(b)
            return no_p_spear(a, b, axis)
        
        #br = np.apply_along_axis(rankdata, axisout, b)
        if not log_odds:
            br = np.apply_along_axis(dense_rank, axisout, b)
    n = a.shape[axisout]
    if prop:
        rs = pp_equivalent_to_cov(ar, br)
    elif log_odds:
        rs = log_odds_equivalent_to_cov(a, b, shuffle = shuffle, log_odds_correction = log_odds_correction)
        print("max of no_p_spear:",np.max(rs))
        return(rs)#, log_odds_correction = log_odds_correction)
    else:
        ## finally, the default is spearman
        #print("\tgetting correlation")
        rs = np.corrcoef(ar, br, rowvar=axisout)
    
    olderr = np.seterr(divide='ignore')  # rs can have elements equal to 1
    try:
        # clip the small negative values possibly caused by rounding
        # errors before taking the square root
        t = rs * np.sqrt(((n-2)/((rs+1.0)*(1.0-rs))).clip(0))
    finally:
        np.seterr(**olderr)
    
    if rs.shape == (2, 2):
        return rs[1, 0]
    else:
        return rs


def fast_single_spear(a,b,shuffle = False):
    ## first remove nans
    a_keep = np.logical_not(np.isnan(a))
    b_keep = np.logical_not(np.isnan(b))
    keep = a_keep * b_keep
    a=a[keep]
    b=b[keep]
    ar = rankdata(a,method='dense')
    br = rankdata(b,method='dense')
    if shuffle:
        s_ar = deepcopy(ar)
        np.random.shuffle(s_ar)
        return(np.corrcoef(ar,br)[1,0], np.corrcoef(s_ar,br)[1,0])
    else:
        return(np.corrcoef(ar,br)[1,0])
# def no_p_spear_pairwise(a, b=None, axis=0, nan_policy='propagate', rm_nans_by_col = False, prop = False):
#     ## axis: 1 is row, by row, 0 is column by column
#     if rm_nans_by_col:


#     ar = np.apply_along_axis(rankdata, axisout, a)    
#     br = np.apply_along_axis(rankdata, axisout, b)

#     n = a.shape[axisout]
#     if not prop:
#         rs = np.corrcoef(ar, br, rowvar=axisout)
#     else:
#         rs = pp_equivalent_to_cov(ar, br)
    
#     olderr = np.seterr(divide='ignore')  # rs can have elements equal to 1
#     try:
#         # clip the small negative values possibly caused by rounding
#         # errors before taking the square root
#         t = rs * np.sqrt(((n-2)/((rs+1.0)*(1.0-rs))).clip(0))
#     finally:
#         np.seterr(**olderr)
    
#     if rs.shape == (2, 2):
#         return rs[1, 0]
#     else:
#         return rs

########################################################
########################################################
########################################################
########## bayesean co-occurance functions #############
########################################################
########################################################
########################################################
# def get_log_odds_mat(a, b):
#     ## should try to make a faster version...
#     v1_and_v2 = a * b[:,:,None]
#     ####....
#     v1_only = np.sum((vect1 ^ vect2)==1)## ^ is xor instead of - for boolean
#     v2_only = np.sum((vect2 ^ vect1)==1)## ^ is xor instead of - for boolean
#     neither = np.sum((vect2 + vect1)==0)
#     #proportion_mat = np.array([[v1_only,v1_and_v2],[neither,v2_only]])
#     #log_odds_ratio = np.log((v1_and_v2*neither)/(v1_only*v2_only))
#     log_odds_ratio = np.log10(((v1_and_v2+1)*(neither+1))/((v1_only+1)*(v2_only+1)))
def get_linear_triangle(in_mat, bin_size):
    upper_tiangle_indices = np.triu_indices(bin_size,k=1)
    ## this means that we just have a single negative rho cutoff for all genes
    ## subset the negative ones
    linear_rho = np.array(in_mat[upper_tiangle_indices]).squeeze()
    return(linear_rho)



def get_log_odds(vect1, vect2, already_bool = False, i=0 , j=0, shuffle = False):
    ## Returns the UNCORRECTED log odds
    if not already_bool:
        if type(vect1)!=np.ndarray:
            vect1 = np.array(vect1)
        if type(vect2)!=np.ndarray:
            vect2 = np.array(vect2)
        vect1 = vect1.squeeze()
        vect2 = vect2.squeeze()
        vect1_bool = np.array(vect1>0,dtype = bool)
        vect2_bool = np.array(vect2>0,dtype = bool)
    else:
        vect1_bool = vect1.squeeze()
        vect2_bool = vect2.squeeze()
    if shuffle:
        np.random.shuffle(vect1_bool)
        np.random.shuffle(vect2_bool)
    v1_and_v2 = np.sum(vect1_bool * vect2_bool)
    v1_only = np.sum(np.array(vect1_bool==1, dtype = bool) * np.array(vect2_bool==0, dtype = bool))
    v2_only = np.sum(np.array(vect2_bool==1, dtype = bool) * np.array(vect1_bool==0, dtype = bool))
    # if (v1_and_v2+v1_only==1) or (v1_and_v2+v2_only==1):
    #     return(0)
    neither = np.sum((vect1_bool + vect1_bool)==0)
    #proportion_mat = np.array([[v1_only,v1_and_v2],[neither,v2_only]])
    #log_odds_ratio = np.log((v1_and_v2*neither)/(v1_only*v2_only))
    log_odds_ratio = np.log2(((v1_and_v2+1)*(neither+1))/((v1_only+1)*(v2_only+1)))
    # if v1_and_v2 == 0 and log_odds_ratio>0:
    #     return(0)
    ###################
    ## calculate expected
    total_events = v1_and_v2+v1_only+v2_only+neither
    v1_percent = (v1_and_v2+v1_only)/total_events
    v2_percent = (v1_and_v2+v2_only)/total_events
    v1_and_v2_expected = total_events * (v1_percent * v2_percent)
    v1_only_expected = v1_percent*total_events - v1_and_v2_expected
    v2_only_expected = v2_percent*total_events - v1_and_v2_expected
    neither_expected = total_events - (v1_and_v2_expected + v1_only_expected + v2_only_expected)
    log_odds_ratio_expected = np.log10(((v1_and_v2_expected+1)*(neither_expected+1))/((v1_only_expected+1)*(v2_only_expected+1)))
    if False:#log_odds_ratio > 10:
        pass
    ###
    delta_log_odds = log_odds_ratio - log_odds_ratio_expected
    if np.isnan(delta_log_odds):
        print("i", i)
        print("j", j)
        print("v1_and_v2",v1_and_v2)
        print("v1_only", v1_only)
        print("v2_only", v2_only)
        print("neither", neither)
        print("vect1_bool", np.sum(vect1_bool), vect1_bool)
        print("vect2_bool", np.sum(vect2_bool), vect2_bool)
        print("log_odds_ratio", log_odds_ratio)
        print("v1_and_v2_expected",v1_and_v2_expected)
        print("v1_only", v1_only_expected)
        print("v2_only", v2_only_expected)
        print("neither", neither_expected)
        print("log_odds_ratio_expected", log_odds_ratio_expected)
        return(0)
    else:
        return(delta_log_odds)
    # ############################
    # ## thought about implementing something like a lod score, but haven't tested it yet
    # #R = v1_and_v2+neither +1
    # #NR = v1_only+v2_only +1
    # #print(R, NR)
    # #lod_score = np.log10(((R/(R+NR))**R)*((1-(R/(R+NR)))**NR) / 0.5**(NR+R))
    # return(delta_log_odds)#log_odds_ratio)#, lod_score)


@ray.remote
def ray_log_odds(c, index_pairs, start, end, shuffle = False):
    #print(start, end)
    num_compare = end-start
    job_results = np.zeros(num_compare)
    #job_results = []
    for n in range(start, end):
        i = index_pairs[0][n]
        j = index_pairs[1][n]
        #job_results.append("n:"+str(n)+","+str(i)+"_"+str(j))
        #job_results.append(get_log_odds(c[i],c[j]))
        job_results[n-start]=get_log_odds(c[i],c[j], already_bool = True, i=i, j=j, shuffle = shuffle)
        # if job_results[n-start] > 15:
        #     print("\t",job_results[n-start], i,j)
        #print(num_compare, n)
        #print(job_results[n])
    #print("max ray_log_odds:",np.max(job_results))
    return(job_results)


def do_ray_log_odds(a, b=None, threads = None, verbose = False, shuffle = False):
    if b is None:
        c = a
    else:
        ## concatenate them
        c = np.concatenate((a,b))
    c = np.array(c>0,dtype = bool)
    ## then figure out the pairs to do
    index_pairs = np.triu_indices(c.shape[0], k=1)## k=1 for offsetting so we don't self-compare
    ## allocate the pairs to jobs
    if threads == None:
        threads = min([index_pairs[0].shape[0], multiprocessing.cpu_count()-1])
    events_per_bin = int(index_pairs[0].shape[0]/threads)
    end_indices = [(i+1)*events_per_bin for i in range(int(threads))] + [index_pairs[0].shape[0]]
    start_indices = [0] + end_indices[:-1]
    if verbose:
        print("start_indices:", start_indices)
        print("end_indices:", end_indices)
        print("index pairs:", index_pairs)
        print("num pairs:", index_pairs[0].shape[0])
    ## start ray and allocate the jobs
    mem = psutil.virtual_memory()
    used_mem = mem[2]## 2 is used
    #psutil.virtual_memory()[2]## 2 is used
    process_mem = 6#Gigs
    total_mem = 24
    print("getting delta_log_odds")
    try:
        ray.init(memory = int(total_mem*1000000000), object_store_memory=int(process_mem*1000000000))
    except:
        ray.init()
    ray_c = ray.put(c)
    ray_jobs = []
    for thread in range(threads+1):
        ray_jobs.append(ray_log_odds.remote(ray_c, index_pairs, start_indices[thread], end_indices[thread], shuffle = shuffle))
    ray_sults = ray.get(ray_jobs)
    ray.shutdown()
    data = np.concatenate(ray_sults)
    #return(data, index_pairs[0], index_pairs[1])
    final_results = csr_matrix((data, (index_pairs[0],index_pairs[1])), shape=(c.shape[0], c.shape[0])).toarray()
    final_results += final_results.T
    print("max of do_ray_log_odds:",np.max(final_results))
    return(final_results)


def do_ray_log_odds_test():
    a=np.random.poisson(10,size=(50000)).reshape(10,5000)
    res = do_ray_log_odds(a)
    return



def log_odds_equivalent_to_cov(m, 
                               y=None, 
                               rowvar=True, 
                               bias=False, 
                               ddof=None, 
                               fweights=None,
                               aweights=None,
                               log_odds_correction = 0,
                               shuffle = False):
    # Check inputs
    if ddof is not None and ddof != int(ddof):
        raise ValueError("ddof must be integer")
    # Handles complex arrays too
    m = np.asarray(m)
    if m.ndim > 2:
        raise ValueError("m has more than 2 dimensions")
    if y is None:
        dtype = np.result_type(m, np.float64)
    else:
        y = np.asarray(y)
        if y.ndim > 2:
            raise ValueError("y has more than 2 dimensions")
        dtype = np.result_type(m, y, np.float64)
    X = array(m, ndmin=2, dtype=dtype)
    if not rowvar and X.shape[0] != 1:
        X = X.T
    if X.shape[0] == 0:
        return np.array([]).reshape(0, 0)
    if y is not None:
        y = array(y, copy=False, ndmin=2, dtype=dtype)
        if not rowvar and y.shape[0] != 1:
            y = y.T
        X = np.concatenate((X, y), axis=0)
    if ddof is None:
        if bias == 0:
            ddof = 1
        else:
            ddof = 0
    # Get the product of frequencies and weights
    w = None
    if fweights is not None:
        fweights = np.asarray(fweights, dtype=float)
        if not np.all(fweights == np.around(fweights)):
            raise TypeError(
                "fweights must be integer")
        if fweights.ndim > 1:
            raise RuntimeError(
                "cannot handle multidimensional fweights")
        if fweights.shape[0] != X.shape[1]:
            raise RuntimeError(
                "incompatible numbers of samples and fweights")
        if any(fweights < 0):
            raise ValueError(
                "fweights cannot be negative")
        w = fweights
    if aweights is not None:
        aweights = np.asarray(aweights, dtype=float)
        if aweights.ndim > 1:
            raise RuntimeError(
                "cannot handle multidimensional aweights")
        if aweights.shape[0] != X.shape[1]:
            raise RuntimeError(
                "incompatible numbers of samples and aweights")
        if any(aweights < 0):
            raise ValueError(
                "aweights cannot be negative")
        if w is None:
            w = aweights
        else:
            w *= aweights
    avg, w_sum = average(X, axis=1, weights=w, returned=True)
    w_sum = w_sum[0]
    # Determine the normalization
    if w is None:
        fact = X.shape[1] - ddof
    elif ddof == 0:
        fact = w_sum
    elif aweights is None:
        fact = w_sum - ddof
    else:
        fact = w_sum - ddof*sum(w*aweights)/w_sum
    if fact <= 0:
        warnings.warn("Degrees of freedom <= 0 for slice",
                      RuntimeWarning, stacklevel=3)
        fact = 0.0
    X -= avg[:, None]
    if w is None:
        X_T = X.T
    else:
        X_T = (X*w).T
    c = do_ray_log_odds(X,)
    print("max of log_odds_equivalent_to_cov1:",np.max(c))
    return c.squeeze()-log_odds_correction




# def bayes_co_occur_mat(vect1, vect2):
#     vect1_bool = np.array(vect1>0,dtype = bool)
#     vect2_bool = np.array(vect2>0,dtype = bool)
#     v1_percent = np.sum(vect1_bool)


########################################################
########################################################
########################################################
####### proportaionality statistic functions ###########
########################################################
########################################################
########################################################

dummy_array = None
def multi_pp(i):
    global dummy_array
    return(var(dummy_array[i,:] - dummy_array[:,:],axis = 1))

def get_pp(in_mat, verbose = False, do_multi = True):
    ## first get the variance of all genes
    if do_multi:
        threads = multiprocessing.cpu_count()
    else:
        threads = 1
    all_var = var(in_mat, axis = 1)
    if verbose:
        print(all_var)
    ## then get the distance matrix
    ## TODO - make multi-threaded version!
    if do_multi and threads > 1:
        global dummy_array
        dummy_array = in_mat
        indices = list(range(0,in_mat.shape[0]))
        ## set up multi-threaded pool
        pool = ThreadPool(threads)
        all_diff_var = pool.map(multi_pp,indices)
        pool.close()
        pool.join()
        all_diff_var = np.array(all_diff_var)
    else:
        all_diff_var = np.zeros((in_mat.shape[0],in_mat.shape[0]))
        for i in range(0,in_mat.shape[0]):
            all_diff_var[i,:] = var(in_mat[i,:] - in_mat[:,:],axis = 1)
    #all_diff_var = var(in_mat[:,:] - in_mat[:,None,:],axis = 2)
    if verbose:
        print("all_diff_var")
        print(all_diff_var)
    ## then get the pairwise added variance of the original vectors
    all_added_var = all_var + all_var[:,None]
    if verbose:
        print(all_added_var)
    ## then just divide the two matrices by each other
    pp_mat = 1 - (all_diff_var/all_added_var)
    return pp_mat


def get_pp_2(in_mat_a, in_mat_b, verbose = False):
    in_mat_a=make_dense(in_mat_a)
    in_mat_b=make_dense(in_mat_b)
    ## first get the variance of all genes
    all_var_a = var(in_mat_a, axis = 1)
    all_var_b = var(in_mat_b, axis = 1)
    ## then get the distance matrix
    all_diff_var = np.zeros((in_mat_a.shape[0],in_mat_b.shape[0]))
    for i in range(0,in_mat_a.shape[0]):
        all_diff_var[i,:] = var(in_mat_a[i,:] - in_mat_b[:,:],axis = 1)
    #all_diff_var = var(in_mat[:,:] - in_mat[:,None,:],axis = 2)
    if verbose:
        print("all_diff_var")
        print(all_diff_var)
    ## then get the pairwise added variance of the original vectors
    all_added_var = all_var_a[:,None] + all_var_b[None,:]
    if verbose:
        print(all_added_var)
    ## then just divide the two matrices by each other
    pp_mat = 1 - (all_diff_var/all_added_var)
    return pp_mat


def pp_equivalent_to_cov(m, y=None, rowvar=True, bias=False, ddof=None, fweights=None,
        aweights=None):
    """ ## I copied this from covariance function as a template, disregard.
    Estimate a proportionality matrix, given data and weights.
    Proportionality indicates the level to which two variables are proportional together.
    See the notes for an outline of the algorithm.
    Parameters
    ----------
    m : array_like
        A 1-D or 2-D array containing multiple variables and observations.
        Each row of `m` represents a variable, and each column a single
        observation of all those variables. Also see `rowvar` below.
    y : array_like, optional
        An additional set of variables and observations. `y` has the same form
        as that of `m`.
    rowvar : bool, optional
        If `rowvar` is True (default), then each row represents a
        variable, with observations in the columns. Otherwise, the relationship
        is transposed: each column represents a variable, while the rows
        contain observations.
    bias : bool, optional
        Default normalization (False) is by ``(N - 1)``, where ``N`` is the
        number of observations given (unbiased estimate). If `bias` is True,
        then normalization is by ``N``. These values can be overridden by using
        the keyword ``ddof`` in numpy versions >= 1.5.
    ddof : int, optional
        If not ``None`` the default value implied by `bias` is overridden.
        Note that ``ddof=1`` will return the unbiased estimate, even if both
        `fweights` and `aweights` are specified, and ``ddof=0`` will return
        the simple average. See the notes for the details. The default value
        is ``None``.
        .. versionadded:: 1.5
    fweights : array_like, int, optional
        1-D array of integer frequency weights; the number of times each
        observation vector should be repeated.
        .. versionadded:: 1.10
    aweights : array_like, optional
        1-D array of observation vector weights. These relative weights are
        typically large for observations considered "important" and smaller for
        observations considered less "important". If ``ddof=0`` the array of
        weights can be used to assign probabilities to observation vectors.
        .. versionadded:: 1.10
    Returns
    -------
    out : ndarray
        The covariance matrix of the variables.
    See Also
    --------
    corrcoef : Normalized covariance matrix
    Notes
    -----
    Assume that the observations are in the columns of the observation
    array `m` and let ``f = fweights`` and ``a = aweights`` for brevity. The
    steps to compute the weighted covariance are as follows::
        >>> m = np.arange(10, dtype=np.float64)
        >>> f = np.arange(10) * 2
        >>> a = np.arange(10) ** 2.
        >>> ddof = 9 # N - 1
        >>> w = f * a
        >>> v1 = np.sum(w)
        >>> v2 = np.sum(w * a)
        >>> m -= np.sum(m * w, axis=None, keepdims=True) / v1
        >>> cov = np.dot(m * w, m.T) * v1 / (v1**2 - ddof * v2)
    Note that when ``a == 1``, the normalization factor
    ``v1 / (v1**2 - ddof * v2)`` goes over to ``1 / (np.sum(f) - ddof)``
    as it should.
    Examples
    --------
    Consider two variables, :math:`x_0` and :math:`x_1`, which
    correlate perfectly, but in opposite directions:
    >>> x = np.array([[0, 2], [1, 1], [2, 0]]).T
    >>> x
    array([[0, 1, 2],
           [2, 1, 0]])
    Note how :math:`x_0` increases while :math:`x_1` decreases. The covariance
    matrix shows this clearly:
    >>> np.cov(x)
    array([[ 1., -1.],
           [-1.,  1.]])
    Note that element :math:`C_{0,1}`, which shows the correlation between
    :math:`x_0` and :math:`x_1`, is negative.
    Further, note how `x` and `y` are combined:
    >>> x = [-2.1, -1,  4.3]
    >>> y = [3,  1.1,  0.12]
    >>> X = np.stack((x, y), axis=0)
    >>> np.cov(X)
    array([[11.71      , -4.286     ], # may vary
           [-4.286     ,  2.144133]])
    >>> np.cov(x, y)
    array([[11.71      , -4.286     ], # may vary
           [-4.286     ,  2.144133]])
    >>> np.cov(x)
    array(11.71)
    """
    # Check inputs
    if ddof is not None and ddof != int(ddof):
        raise ValueError(
            "ddof must be integer")
    # Handles complex arrays too
    m = np.asarray(m)
    if m.ndim > 2:
        raise ValueError("m has more than 2 dimensions")

    if y is None:
        dtype = np.result_type(m, np.float64)
    else:
        y = np.asarray(y)
        if y.ndim > 2:
            raise ValueError("y has more than 2 dimensions")
        dtype = np.result_type(m, y, np.float64)

    X = array(m, ndmin=2, dtype=dtype)
    if not rowvar and X.shape[0] != 1:
        X = X.T
    if X.shape[0] == 0:
        return np.array([]).reshape(0, 0)
    if y is not None:
        y = array(y, copy=False, ndmin=2, dtype=dtype)
        if not rowvar and y.shape[0] != 1:
            y = y.T
        X = np.concatenate((X, y), axis=0)

    if ddof is None:
        if bias == 0:
            ddof = 1
        else:
            ddof = 0

    # Get the product of frequencies and weights
    w = None
    if fweights is not None:
        fweights = np.asarray(fweights, dtype=float)
        if not np.all(fweights == np.around(fweights)):
            raise TypeError(
                "fweights must be integer")
        if fweights.ndim > 1:
            raise RuntimeError(
                "cannot handle multidimensional fweights")
        if fweights.shape[0] != X.shape[1]:
            raise RuntimeError(
                "incompatible numbers of samples and fweights")
        if any(fweights < 0):
            raise ValueError(
                "fweights cannot be negative")
        w = fweights
    if aweights is not None:
        aweights = np.asarray(aweights, dtype=float)
        if aweights.ndim > 1:
            raise RuntimeError(
                "cannot handle multidimensional aweights")
        if aweights.shape[0] != X.shape[1]:
            raise RuntimeError(
                "incompatible numbers of samples and aweights")
        if any(aweights < 0):
            raise ValueError(
                "aweights cannot be negative")
        if w is None:
            w = aweights
        else:
            w *= aweights

    avg, w_sum = average(X, axis=1, weights=w, returned=True)
    w_sum = w_sum[0]

    # Determine the normalization
    if w is None:
        fact = X.shape[1] - ddof
    elif ddof == 0:
        fact = w_sum
    elif aweights is None:
        fact = w_sum - ddof
    else:
        fact = w_sum - ddof*sum(w*aweights)/w_sum

    if fact <= 0:
        warnings.warn("Degrees of freedom <= 0 for slice",
                      RuntimeWarning, stacklevel=3)
        fact = 0.0

    X -= avg[:, None]
    if w is None:
        X_T = X.T
    else:
        X_T = (X*w).T
    c = get_pp(X)
    c *= np.true_divide(1, fact)
    return c.squeeze()


########################################################
########################################################
########################################################


def get_Z_cutoff(vect, z=4.5,positive = False, cap = 0.9):
    ## this is for a half distribution, so mult by -1 to make it 'normal'
    vect_original = np.array(deepcopy(vect))
    keep = np.logical_not(np.isnan(vect_original))
    vect_original = vect_original[keep]
    vect = deepcopy(vect_original)
    vect = list(vect)
    vect += list(np.array(vect)*-1)
    vect = np.array(vect)
    ## get the mean, & SD
    v_mean = np.mean(vect)
    v_std = np.std(vect)
    cutoff = v_std * z
    if not positive:
        cutoff *= -1
    if cap is not None:
        if not positive:
            cutoff = max([-1*cap,cutoff])
        else:
            cutoff = min([cap,cutoff])
    print('cutoff:',cutoff)
    if not positive:
        num_sig = np.sum(np.array(vect_original<cutoff,dtype = bool))
        total_num = vect_original.shape[0]
        print(num_sig, "/", total_num, 'significant')
        FPR = max([1,total_num])/num_sig
        return(cutoff, FPR)
    else:
        return(cutoff)



def get_empiric_FPR(vect, FPR=1000, positive = False):
    ## this is for a half distribution, so mult by -1 to make it 'normal'
    if positive:
        vect = vect * -1
    vect_original = np.array(deepcopy(vect))
    keep_not_nan = np.logical_not(np.isnan(vect_original))
    keep_not_zero = vect_original!=0
    keep_not_one = vect_original!=1
    keep_not_neg_one = vect_original!=-1
    keep = keep_not_nan * keep_not_zero * keep_not_one * keep_not_neg_one
    ## remove zeros, 1s and -1s
    vect_original = vect_original[keep]
    ## either this
    target_index = floor(vect_original.shape[0]/FPR)
    print("target index:",target_index)
    #if not positive:
    #    vect_original = vect_original * -1
    sort_order = np.sort(vect_original)
    if sort_order.shape[0]==0:
        cutoff=0
    else:
        cutoff = sort_order[target_index]
    print('cutoff:',cutoff)
    if not positive:
        num_sig = np.sum(np.array(vect_original<cutoff,dtype = bool))
        total_num = vect_original.shape[0]
        print(num_sig, "/", total_num, 'significant')
        FPR = max([1,total_num])/num_sig
        return(cutoff, FPR)
    else:
        return(cutoff * -1)




# def get_empiric_log_odds_FPR(vect, ):
#     cutoff
