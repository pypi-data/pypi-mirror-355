import os
import warnings
import h5py
import time
import shutil
import random
import requests
import tempfile
import fileinput
import numpy as np
import pandas as pd
from math import floor
from copy import deepcopy
from numba import njit
from gprofiler import GProfiler
from scipy.sparse import csr_matrix, csc_matrix, coo_matrix
from anticor_features.anticor_stats import no_p_pear, dense_rank, get_shuffled

###########################
def strip_split(line, delim='\t'):
    return line.strip('\n').split(delim)


def fast_read_mat(source_file):
    row_labs = []
    col_labs = []
    first = True
    for line in fileinput.input(source_file):
        temp_line = strip_split(line)
        if first:
            first = False
            col_labs = temp_line[1:]
        else:
            row_labs.append(temp_line[0])
    fileinput.close()
    out_mat = np.zeros((len(row_labs),len(col_labs)))
    first = True
    counter=0
    for line in fileinput.input(source_file):
        if first:
            first = False
        else:
            temp_line = list(map(float,strip_split(line)[1:]))
            out_mat[counter,:]=temp_line
            counter+=1
    fileinput.close()
    return(row_labs, col_labs, out_mat)


#####################
def process_dict(in_file, ensg_idx):
    out_dict = {}
    for i in range(0,len(in_file)):
        out_dict[in_file[i][ensg_idx]]=True
    #print(out_dict)
    return(out_dict)


def quick_search(in_dict,key):
    try:
        in_dict[key]
    except:
        return(False)
    else:
        return(True)




def get_temp_dir(temp_dir):
    if temp_dir == None:
        temp_dir = tempfile.gettempdir()
    if not os.path.isdir(str(temp_dir)):
        if not os.path.isdir(temp_dir):
            print("Couldn't find the supplied temp_dir, using the system temp_dir instead")
        temp_dir = tempfile.gettempdir()
    free_temp_space = shutil.disk_usage(temp_dir)[2]
    print("found",free_temp_space/1000000000,"free Gb in",temp_dir)
    return(temp_dir, free_temp_space)


##############################

def gprof_pathways_to_genes(rm_paths, species):
    #gp = GProfiler('anticor_'+str(random.randint(0,int(1e6))), want_header = True)
    #results = gp.gconvert(rm_paths,organism=species, target="ENSG")
    r = requests.post(
        url='https://biit.cs.ut.ee/gprofiler/api/convert/convert/',
        json={
            'organism':species,
            'target':'ENSG',
            'query':rm_paths
        }
    )
    results = pd.DataFrame(r.json()['result'])
    return results


def get_ensg_of_ref(species, all_features):
    print("get_ensg_of_ref")
    #gp = GProfiler('anticor_'+str(random.randint(0,int(1e6))), want_header = True)
    if species == 'hsapiens':
        #annotations = gp.gconvert(all_features, 
        #    organism = species, target='ENSG',numeric_ns="ENTREZGENE_ACC")
        #ensg_idx = 3
        annotations = gprof_pathways_to_genes(all_features, species)
        ensg_idx = int(np.where(annotations.columns=="converted")[0][0])
        annotations = annotations.values.tolist()
    else:
        # TODO: Seems to be broken b/c gprofiler people broke reverse compatibility
        annotations = gp.gorth(all_features, 
            source_organism = species,
            target_organism="hsapiens")
        ensg_idx = 2
    ## the first column
    return(annotations, ensg_idx)


def ensg_list_to_orig(annotations, ensg_idx, rm_features_ensg):
    ensg_to_orig_lookup={}
    #for i in range(1,len(annotations)):
    for i in range(len(annotations)):# Previous was 
        temp_ensg = annotations[i][ensg_idx]
        temp_ensg_orig = deepcopy(temp_ensg)
        if temp_ensg is None:
            ## this resets it to the original
            temp_ensg = annotations[i][2]
        ensg_to_orig_lookup[temp_ensg]=annotations[i][2]
    out_converted = []
    for gene in rm_features_ensg:
        if quick_search(ensg_to_orig_lookup,gene):
            out_converted.append(ensg_to_orig_lookup[gene])
    return out_converted



def pathways_to_genes(rm_paths, species, all_features):
    print("pathways_to_genes")
    results = gprof_pathways_to_genes(rm_paths, species).values.tolist()
    print(pd.DataFrame(results).head())
    remove_dict=process_dict(results,0)# This is a risky hardcode to the ensembl ID locations
    #print(list(remove_dict.keys())[:5])
    ## first go to the annotations, and make sure that
    #############################################################
    annotations, ensg_idx = get_ensg_of_ref(species, all_features)
    print(pd.DataFrame(annotations).head())
    new_remove_features = []
    for line in annotations:#[1:]:Was 1 with old gprofiler
        temp_id = line[ensg_idx]
        #print(temp_id)
        temp_id_orig = deepcopy(temp_id)
        #print(temp_id_orig)
        if temp_id == None:
            temp_id = line[2]
        if temp_id in remove_dict:
            #print("success")
            new_remove_features.append(temp_id)
    new_remove_features_ensg = list(set(new_remove_features))
    #print("new_remove_features_ensg:")
    #print(new_remove_features_ensg)
    ## now we have to map it back to the original ids
    final_remapped_genes = ensg_list_to_orig(annotations, ensg_idx, new_remove_features_ensg)
    return(final_remapped_genes)


@njit
def get_num_mean_exprs(indices,data,num_genes):
    idx_count = np.zeros((num_genes))
    idx_sum = np.zeros((num_genes))
    for i in range(len(indices)):
        if data[i]>0:
            idx_count[indices[i]]+=1
            idx_sum[indices[i]]+=data[i]
    return(idx_count, idx_sum/idx_count)


def get_n_expressed(exprs, cell_axis, all_features):
    print("get_n_expressed")
    if cell_axis == 1:
        exprs = coo_matrix(exprs)
    else:
        print("cells in rows is not yet supported")
        exprs = coo_matrix(exprs)
    num_exprs, mean_nz = get_num_mean_exprs(exprs.row, exprs.data, len(all_features))
    mean_nz[np.isnan(mean_nz)]=0
    # num_exprs = np.zeros(len(all_features))
    # mean_nz = np.zeros(len(all_features))
    # for i in range(len(all_features)):
    #     ## with dense
    #     # if cell_axis==1:
    #     #     temp_exprs_vect = np.array(exprs[i,:])
    #     # else:
    #     #     temp_exprs_vect = np.array(exprs[:,i])
    #     # exprs_idxs = np.where(np.array(temp_exprs_vect)>0)[0]
    #     # num_exprs[i] = exprs_idxs.shape[0]
    #     ## /with_dense
    #     exprs_idxs = np.where(exprs.indices==i)[0]
    #     num_exprs[i] = exprs_idxs.shape[0]
    #     if exprs_idxs.shape[0]>0:
    #         mean_nz[i] = np.mean(exprs.data[exprs_idxs])
    return(num_exprs, mean_nz)


def get_all_remove_genes(pre_remove_features,
                         pre_remove_pathways, 
                         species, 
                         min_express_n, 
                         cell_axis, 
                         exprs, 
                         all_features):
    print("get_all_remove_genes")
    pre_rm_bool = []
    for feat in all_features:
        if feat in pre_remove_features:
            pre_rm_bool.append(True)
        else:
            pre_rm_bool.append(False)
    if min_express_n==None:
        print(exprs.shape[cell_axis], int(0.05*exprs.shape[cell_axis]))
        min_express_n=max(3,min(50,int(0.05*exprs.shape[cell_axis])))
    print("min_express_n",min_express_n)
    n_exprs, mean_nz = get_n_expressed(exprs, cell_axis, all_features)
    low_express_bool = n_exprs<min_express_n
    idxs_to_rm = np.where(low_express_bool)[0]
    exprs_rm_filter = np.array(all_features)[idxs_to_rm].tolist()
    ## add the features we need to remove from the pathway list
    if pre_remove_pathways != []:
        ## only bother if there are actually pathways to remove - otherwise, just wasted time
        pathway_removed_genes = pathways_to_genes(pre_remove_pathways, species, all_features)
    else:
        pathway_removed_genes = []
    #print(pathway_removed_genes)
    pathway_removed_genes_bool = []
    all_features_upper = [gene.upper() for gene in all_features]
    pathway_removed_genes_upper = [gene.upper() for gene in pathway_removed_genes]
    for gene_idx in range(len(all_features_upper)):
        gene = all_features_upper[gene_idx]
        if gene in pathway_removed_genes_upper:
            pathway_removed_genes_bool.append(True)
        else:
            pathway_removed_genes_bool.append(False)
    annotation_df = pd.DataFrame({"gene":all_features,
                  "pre_remove_feature":pre_rm_bool,
                  "pre_remove_pathway":pathway_removed_genes_bool,
                  "pre_remove_low_express":low_express_bool,
                  "n_expressed":n_exprs,
                  "percent_expressed":n_exprs/exprs.shape[cell_axis],
                  "non_zero_mean":mean_nz})
    #print(annotation_df.head(15))
    #print(annotation_df.tail(15))
    bool_mat = annotation_df[["pre_remove_feature",
                  "pre_remove_pathway",
                  "pre_remove_low_express"]].to_numpy(dtype=int)
    rm_idxs = np.where(np.sum(bool_mat,axis=1) > 0 )[0]
    print("pre_remove_feature:",np.sum(annotation_df["pre_remove_feature"]))
    print("pre_remove_pathway:",np.sum(annotation_df["pre_remove_pathway"]))
    print("pre_remove_low_express:",np.sum(annotation_df["pre_remove_low_express"]))
    rm_genes = np.array(all_features)[rm_idxs].tolist()
    print(len(rm_genes)," genes to remove out of ",len(all_features))
    return(rm_genes, annotation_df)


def rewrite_full_dset(exprs, feature_ids, pre_remove_features, scratch_dir, cell_axis, method="spear"):
    print('rewriting the filtered dataset')
    ## make the hdf5 output file
    exprs_out_file = os.path.join(scratch_dir,"exprs.hdf5")
    print(exprs_out_file)
    exprs_f = h5py.File(exprs_out_file, "w")
    # If exprs is a pandas DataFrame, convert to numpy array for safe positional indexing
    if isinstance(exprs, pd.DataFrame):
        exprs = exprs.values
    exprs_out_mat = exprs_f.create_dataset("infile", (len(feature_ids),exprs.shape[cell_axis]), dtype=np.float32)
    remove_hash = {feat:None for feat in pre_remove_features}
    original_idx_hash = {key:value for value, key in enumerate(feature_ids)}
    counter = 0
    kept_features = []
    if "toarray" in dir(exprs):
        if cell_axis==1:
            exprs = csr_matrix(exprs)
        else:
            exprs = csc_matrix(exprs)
    for feat in feature_ids:
        if feat not in remove_hash:## this means that it's to be removed & we'll skip it
            ## this means we keep it
            if cell_axis==1:
                ## genes are in rows
                if False:#if "toarray" in dir(exprs):
                    temp_vect = exprs[original_idx_hash[feat],:].toarray()
                else:
                    temp_vect = exprs[original_idx_hash[feat],:]
            else:
                ## genes are in cols
                if False:#"toarray" in dir(exprs):
                    temp_vect = exprs[:,original_idx_hash[feat]].toarray()
                else:
                    temp_vect = exprs[:,original_idx_hash[feat]]
            ## here we do the dense rank transformation so that we don't have to do it over and over 
            ## when calculating the Spearman correlation, this way we can call "no_p_pear" instead of "no_p_spear"
            #print("vector type:",type(temp_vect))
            if method=="spear":
                if "toarray" in dir(temp_vect):
                    temp_vect.data = dense_rank(temp_vect.data)
                    #print(min(temp_vect.data))
                else:
                    temp_vect = dense_rank(temp_vect)
            exprs_out_mat[counter,:] += temp_vect
            kept_features.append(feat)
            counter+=1
    exprs_f.close()
    return(exprs_out_file, kept_features)




def get_bins(IDlist, bin_size):
    total_vars = len(IDlist)
    print("total_vars",total_vars)
    bins = []
    cur_bin = 0
    while cur_bin<total_vars:
        bins.append(min(cur_bin, total_vars))
        cur_bin+=bin_size
    bins.append(total_vars)
    return(bins)


def make_spear(scratch_dir, total_vars):
    print('making the hdf5 spearman output file')
    ## make the hdf5 output file
    hdf5_spear_out_file = os.path.join(scratch_dir,"spearman.hdf5")
    print(hdf5_spear_out_file)
    spear_f = h5py.File(hdf5_spear_out_file, "a")
    try:
        spear_out_hdf5 = spear_f.create_dataset("infile", (total_vars,total_vars), dtype=np.float16)
    except:
        spear_out_hdf5 = spear_f["infile"]
    spear_f.close()
    return(hdf5_spear_out_file)


##########################################
def get_empiric_FPR_cutoff_pos(in_vect, FPR, cap = 0.9):
    target_index = min(len(in_vect),floor(in_vect.shape[0]*FPR))
    if target_index==0:
        return(1)
    cutoff = np.sort(in_vect)[-target_index]
    print("empirically determined Cpos cutoff:",cutoff," for FPR of:",FPR)
    return(cutoff)


def get_empiric_FPR_cutoff(in_vect, FPR, cap = 0.9):
    target_index = min(len(in_vect),floor(in_vect.shape[0]*FPR))
    cutoff = np.sort(in_vect)[target_index]
    if target_index==0:
        return(-1)
    print("empirically determined Cneg cutoff:",cutoff," for FPR of:",FPR)
    return(cutoff)


def get_positive_negative_cutoffs(shuffled_mat, FPR):
    null_rhos = no_p_pear(shuffled_mat,axis=1)
    null_trilu = np.triu_indices(null_rhos.shape[0],1)
    null_vect = null_rhos[null_trilu]
    null_vect_neg = null_vect[null_vect<0]
    neg_cut = get_empiric_FPR_cutoff(null_vect_neg, FPR)
    null_vect_pos = null_vect[null_vect>0]
    pos_cut = get_empiric_FPR_cutoff_pos(null_vect_pos, FPR)
    # sns.distplot(null_vect_neg*-1)
    # sns.distplot(null_vect_pos)
    # plt.show()
    return(neg_cut, pos_cut)


##########################################
def get_real_spear(exprs_file, spear_file, bins):
    print("get_real_spear")
    print(bins)
    if len(bins)>1:
        bin_size = bins[1]-bins[0]
    exprs_f = h5py.File(exprs_file,'r')
    in_mat = exprs_f["infile"]
    spear_f = h5py.File(spear_file,'a')
    spear_mat = spear_f["infile"]
    #if bin_size != bins[-1]:
    for i in range(0,(len(bins)-1)):
        for j in range(i,(len(bins)-1)):
            if (i!=j) or (len(bins) == 2):
                print('working on',bins[i],bins[i+1],'vs',bins[j],bins[j+1])
                r=no_p_pear(in_mat[bins[i]:bins[i+1],:],in_mat[bins[j]:bins[j+1],:], axis = 1)
                ## top left
                spear_mat[bins[i]:bins[i+1],bins[i]:bins[i+1]] = r[:bin_size,:bin_size]
                ## top right
                spear_mat[bins[i]:bins[i+1],bins[j]:bins[j+1]] = r[:bin_size,bin_size:]
                ## bottom left
                spear_mat[bins[j]:bins[j+1],bins[i]:bins[i+1]] = r[bin_size:,:bin_size]
                ## bottom right
                spear_mat[bins[j]:bins[j+1],bins[j]:bins[j+1]] = r[bin_size:,bin_size:]
    # else:
    #     spear_mat[:,:]=no_p_pear(in_mat)
    spear_f.close()
    exprs_f.close()
    return


def annotate_final_from_spears(spear_file, kept_features, c_neg, c_pos, FPR, FDR, annotation_df, num_pos_cor=10):
    spear_f = h5py.File(spear_file,'r+')
    spear_mat = spear_f["infile"]
    spear_mat.attrs["Cneg"]=c_neg
    spear_mat.attrs["Cpos"]=c_pos
    all_neg_vect = np.zeros((spear_mat.shape[0]))
    all_sig_neg_vect = np.zeros((spear_mat.shape[0]))
    FP_hat_vect = np.zeros((spear_mat.shape[0]))
    FDR_vect = np.zeros((spear_mat.shape[0]))
    all_sig_pos_vect = np.zeros((spear_mat.shape[0]))
    selected_vect = np.zeros((spear_mat.shape[0]),dtype=bool)
    rolling_select_count = 0
    for i in range(spear_mat.shape[0]):
        spear_vect = spear_mat[i,:]
        temp_feat = kept_features[i]
        all_neg_vect[i] = np.sum(spear_vect<0)
        all_sig_neg_vect[i] = np.sum(spear_vect<c_neg)
        FP_hat_vect[i] = all_neg_vect[i]*FPR
        FDR_vect[i] = FP_hat_vect[i]/all_sig_neg_vect[i]
        all_sig_pos_vect[i] = np.sum(spear_vect>c_pos)
        if (all_sig_pos_vect[i]>num_pos_cor) and (FDR_vect[i]<FDR):
            selected_vect[i] = True
            rolling_select_count+=1
    if rolling_select_count < num_pos_cor:
        selected_vect = np.zeros((spear_mat.shape[0]),dtype=bool)
    annotation_df2 = pd.DataFrame({"gene":kept_features})
    annotation_df2["num_neg"]=all_neg_vect
    annotation_df2["num_sig_neg"]=all_sig_neg_vect
    annotation_df2["FP_hat"]=FP_hat_vect
    annotation_df2["FDR"]=FDR_vect
    annotation_df2["num_sig_pos_cor"]=all_sig_pos_vect
    annotation_df2["selected"]=selected_vect
    annotation_df=annotation_df.merge(annotation_df2, how="left", on="gene")
    spear_f.close()
    return(annotation_df)


def get_the_spears(exprs_subset_file, spear_file, kept_features, bin_size, n_rand_feat, FPR, FDR, annotation_df, num_pos_cor=10):
    print("Getting the Spearman correlations")
    bins = get_bins(kept_features, bin_size)
    n_rand_feat = min(n_rand_feat, len(kept_features))
    ##################
    ## open the exprs and spear mats
    exprs_f = h5py.File(exprs_subset_file,'r')
    exprs_mat = exprs_f["infile"]
    ##################
    shuffled_mat = get_shuffled(exprs_mat, bin_size = bin_size)
    c_neg, c_pos = get_positive_negative_cutoffs(shuffled_mat, FPR)
    ##################
    ## get the real correlation matrix
    exprs_f.close()
    get_real_spear(exprs_subset_file, spear_file, bins)
    feature_table = annotate_final_from_spears(spear_file, kept_features, c_neg, c_pos, FPR, FDR, annotation_df, num_pos_cor=num_pos_cor)
    return(feature_table, c_neg, c_pos)


def lin_norm_mat(temp_mat):
    for i in range(temp_mat.shape[0]):
        temp_mat[i,:]-=min(temp_mat[i,:])
        temp_mat[i,:]/=max(temp_mat[i,:])
    return(temp_mat)


def fix_users_feature_ids(in_ids):
    out_id_dict = {temp_id:0 for temp_id in in_ids}
    out_ids = []
    for temp_id in in_ids:
        if out_id_dict[temp_id]==0:
            out_ids.append(temp_id)
        else:
            out_ids.append(temp_id+"."+str(int(out_id_dict[temp_id])))
            print("\t\tfound duplicate:",out_ids[-1])
        out_id_dict[temp_id] = out_id_dict[temp_id]+1
    return(out_ids)



def get_anti_cor_genes(exprs,
                       feature_ids,
                       pre_remove_features=[],
                       pre_remove_pathways=None,
                       species="hsapiens",
                       n_rand_feat=5000,
                       FPR = 0.001,
                       FDR = 1/15,
                       num_pos_cor = 10,
                       min_express_n=None,
                       bin_size=5000,
                       scratch_dir=None,
                       cell_axis=1):## this assumes cells are in columns
    # Double check that the feature IDs are actually unique
    if not len(feature_ids)==len(set(feature_ids)):
        warnings.warn("\n\nWARNING: YOUR INPUT IDs HAVE DUPLICATE ENTRIES!\nWe'll add an X(for the first), then X.1, X.2 (for subsequent), but this can lead to\nunexpected behavior, bad mapping, and errors in data frame merges.\nIt's better to use something like ensembl IDs.\n\n")
    feature_ids_original = fix_users_feature_ids(deepcopy(feature_ids))
    feature_ids = [str(g).upper() for g in feature_ids]
    pre_remove_features = [str(g).upper() for g in pre_remove_features]
    if pre_remove_pathways is None:
        pre_remove_pathways = ["GO:0044429","GO:0006390","GO:0005739","GO:0005743",
                                             "GO:0070125","GO:0070126","GO:0005759","GO:0032543",
                                             "GO:0044455","GO:0005761","GO:0005840","GO:0003735","GO:0022626","GO:0044391","GO:0006614",
                                             "GO:0006613","GO:0045047","GO:0000184","GO:0043043","GO:0006413",
                                             "GO:0022613","GO:0043604","GO:0015934","GO:0006415","GO:0015935",
                                             "GO:0072599","GO:0071826","GO:0042254","GO:0042273","GO:0042274",
                                             "GO:0006364","GO:0022618","GO:0005730","GO:0005791","GO:0098554",
                                             "GO:0019843","GO:0030492"]
    scratch_dir, scratch_space=get_temp_dir(scratch_dir)
    n_cells = exprs.shape[cell_axis]
    #print(pre_remove_pathways)
    remove_genes, annotation_df = get_all_remove_genes(pre_remove_features,
                                                 pre_remove_pathways, 
                                                 species, 
                                                 min_express_n, 
                                                 cell_axis, 
                                                 exprs, 
                                                 feature_ids)
    exprs_subset_file, kept_features = rewrite_full_dset(exprs, feature_ids, remove_genes, scratch_dir, cell_axis, method="spear")
    total_vars = len(kept_features)
    print("total_vars:",total_vars)
    ############################################
    ## make the 
    spear_file = make_spear(scratch_dir, len(kept_features))
    spear_f = h5py.File(spear_file, "w")
    try:
        spear_out_hdf5 = spear_f.create_dataset("infile", (total_vars,total_vars), dtype=np.float16)
    except:
        spear_out_hdf5 = spear_f["infile"]
    spear_f.close()
    ##########
    feature_table, c_neg, c_pos = get_the_spears(exprs_subset_file, spear_file, kept_features, bin_size, n_rand_feat, FPR, FDR, annotation_df, num_pos_cor=num_pos_cor)
    cutoff_string="Cneg="+str(c_neg)+"\nCpos="+str(c_pos)
    feature_table.index=feature_ids_original
    ##########
    selected_table = feature_table[feature_table["selected"]==True]
    plot_heatmap=True
    if plot_heatmap:
        temp_hash = {key:value for value, key in enumerate(kept_features)}
        keep_idxs = sorted([temp_hash[gene] for gene in selected_table["gene"]])
        exprs_f = h5py.File(exprs_subset_file,'r')
        in_mat = exprs_f["infile"]
        # sns.clustermap(lin_norm_mat(in_mat[keep_idxs,:]))
        # plt.show()
        exprs_f.close()
    ## restore the genes to their exact original form (not necessarily upper)
    feature_table["gene"]=feature_ids_original
    return(feature_table)



# pre_remove_features=[]
# pre_remove_pathways=["GO:0044429","GO:0006390","GO:0005739","GO:0005743",
#                      "GO:0070125","GO:0070126","GO:0005759","GO:0032543",
#                      "GO:0044455","GO:0005761","GO:0005840","GO:0003735","GO:0022626","GO:0044391","GO:0006614",
#                      "GO:0006613","GO:0045047","GO:0000184","GO:0043043","GO:0006413",
#                      "GO:0022613","GO:0043604","GO:0015934","GO:0006415","GO:0015935",
#                      "GO:0072599","GO:0071826","GO:0042254","GO:0042273","GO:0042274",
#                      "GO:0006364","GO:0022618","GO:0005730","GO:0005791","GO:0098554",
#                      "GO:0019843"]
# rm_paths=pre_remove_pathways
# species="hsapiens"
# species="mmusculus"
# n_rand_feat=5000
# FPR = 0.001
# FDR = 1/15
# min_express_n=None
# bin_size=5000
# ##scratch_dir=None
# cell_axis=1


# infile= '/media/scott/ssd_2tb/tab_mur/analysis/tabula-muris-senis-droplet-official-raw-obj_ds2500_log2.hdf5' 
# hdf5 =True 
# cols = '/media/scott/ssd_2tb/tab_mur/analysis/columns.txt'
# ids = '/media/scott/ssd_2tb/tab_mur/analysis/ID_list.txt' 
# species = "mmusculus"
# scratch_dir ='/media/scott/ssd_2tb/tab_mur/analysis/scratch/'


# import gc
# for obj in gc.get_objects():   # Browse through ALL objects
#     if isinstance(obj, h5py.File):   # Just HDF5 files
#         try:
#             obj.close()
#         except:
#             pass # Was already closed



# if not hdf5:
#     all_features, all_cells, in_mat = fast_read_mat(args.infile)
# else:
#     exprs_f = h5py.File(infile,'r')
#     in_mat = exprs_f["infile"]
#     all_cells = [strip_split(line)[0] for line in fileinput.input(cols)]
#     all_cells = all_cells[1:]
#     fileinput.close()
#     all_features = [strip_split(line)[0] for line in fileinput.input(ids)]
#     fileinput.close()


# #########
# start = time.time()
# anti_cor_table = get_anti_cor_genes(in_mat,
#                                     all_features,
#                                     species=species,
#                                     pre_remove_pathways = pre_remove_pathways,
#                                     scratch_dir=scratch_dir)

# print((time.time()-start)/60, "minutes total")


# anti_cor_table = get_anti_cor_genes(in_mat,
#                                         all_features,
#                                         species=species)


# anti_cor_table[anti_cor_table["gene"]=="ENSG00000008988"]
# anti_cor_table[anti_cor_table["gene"]=="ENSMUSG00000000740"]

# expressed = anti_cor_table.dropna()["gene"]#anti_cor_table[(anti_cor_table["n_expressed"]>0) & (anti_cor_table["pre_remove_pathway"]==False)]["gene"]
# selected = anti_cor_table[anti_cor_table["selected"]==True]["gene"]
# gp = GProfiler('anticor_'+str(random.randint(0,int(1e6))), want_header = True)
# res = pd.DataFrame(gp.gprofile(selected, custom_bg = expressed, organism = species))



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-infile", '-i',
                        help="the input expression matrix")
    parser.add_argument("-species",
                        default = "hsapiens",
                        help="gProfiler compatible species code")
    parser.add_argument("-out_file",
                        help="the output file for the anti_cor_feature table")
    parser.add_argument("-hdf5",
                        action = "store_true",
                        help="if the input is an hdf5 file. Note that if it's an hdf5 file, you need to also provide arguments to -ID_list and -columns")
    parser.add_argument("-ID_list","-ids",
                        help="if it's an hdf5 file, provide the feature IDs (rows in the matrix). This expects NO header line!")
    parser.add_argument("-columns","-cols",
                        help="if it's an hdf5 file, provide the sample IDs (cols in the matrix). This expects a header line!")
    parser.add_argument("-scratch_dir",
                        help="We'll need some hard drive space, so if you have a good (and fast!) spot to put temporary files, feed in that directory here.")
    parser.add_argument("-use_default_pathway_removal",
                        action = "store_true",
                        help="this will automatically filter out mitochondrial and ribosomal genes")
    args = parser.parse_args()
    #########
    if args.use_default_pathway_removal:
        pre_remove_pathways=None
    else:
        pre_remove_pathways=[]
    #########
    if not args.hdf5:
        all_features, all_cells, in_mat = fast_read_mat(args.infile)
    else:
        exprs_f = h5py.File(args.infile,'r')
        in_mat = exprs_f["infile"]
        all_cells = [strip_split(line)[0] for line in fileinput.input(args.columns)]
        all_cells = all_cells[1:]
        fileinput.close()
        all_features = [strip_split(line)[0] for line in fileinput.input(args.ID_list)]
        fileinput.close()
    #########
    start = time.time()
    anti_cor_table = get_anti_cor_genes(in_mat,
                                        all_features,
                                        species=args.species,
                                        pre_remove_pathways = pre_remove_pathways)
    print((time.time()-start)/60, "minutes total")
    anti_cor_table.to_csv(os.path.join(os.path.dirname(args.infile),"anti_cor_features.tsv"),sep="\t",na_rep="NA")
    #########
    if args.hdf5:
        exprs_f.close()





