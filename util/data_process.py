import os    
import nibabel
import numpy as np
import random
from scipy import ndimage

def search_file_in_folder_list(folder_list, file_name):
    """
    Find the full filename from a list of folders
    inputs:
        folder_list: a list of folders
        file_name:  filename
    outputs:
        full_file_name: the full filename
    """
    file_exist = False
    for folder in folder_list:
        full_file_name = os.path.join(folder, file_name)
        if(os.path.isfile(full_file_name)):
            file_exist = True
            break
    if(file_exist == False):
        raise ValueError('file not exist: {0:}'.format(file_name))
    return full_file_name

def load_nifty_volume_as_array(filename):
    """
    load nifty image into numpy array, and transpose it based on the [z,y,x] axis order
    The output array shape is like [Depth, Height, Width]
    inputs:
        filename: the input file name, should be *.nii or *.nii.gz
    outputs:
        data: a numpy data array
    """
    img = nibabel.load(filename)
    data = img.get_data()
    data = np.transpose(data, [2,1,0])
    return data

def save_array_as_nifty_volume(data, filename):
    """
    save a numpy array as nifty image
    inputs:
        data: a numpy array with shape [Depth, Height, Width]
        filename: the ouput file name
    outputs: None
    """
    data = np.transpose(data, [2, 1, 0])
    img = nibabel.Nifti1Image(data, np.eye(4))
    nibabel.save(img, filename)

def itensity_normalize_one_volume(volume):
    """
    normalize the itensity of an nd volume based on the mean and std of nonzeor region
    inputs:
        volume: the input nd volume
    outputs:
        out: the normalized nd volume
    """
    
    pixels = volume[volume > 0]
    mean = pixels.mean()
    std  = pixels.std()
    out = (volume - mean)/std
    out_random = np.random.normal(0, 1, size = volume.shape)
    out[volume == 0] = out_random[volume == 0]
    return out

def convert_label(in_volume, label_convert_source, label_convert_target):
    """
    convert the label value in a volume
    inputs:
        in_volume: input nd volume with label set label_convert_source
        label_convert_source: a list of integers denoting input labels, e.g., [0, 1, 2, 4]
        label_convert_target: a list of integers denoting output labels, e.g.,[0, 1, 2, 3]
    outputs:
        out_volume: the output nd volume with label set label_convert_target
    """
    mask_volume = np.zeros_like(in_volume)
    convert_volume = np.zeros_like(in_volume)
    for i in range(len(label_convert_source)):
        source_lab = label_convert_source[i]
        target_lab = label_convert_target[i]
        if(source_lab != target_lab):
            temp_source = np.asarray(in_volume == source_lab)
            temp_target = target_lab * temp_source
            mask_volume = mask_volume + temp_source
            convert_volume = convert_volume + temp_target
    out_volume = in_volume * 1
    out_volume[mask_volume>0] = convert_volume[mask_volume>0]
    return out_volume
        
def get_random_roi_sampling_center(input_shape, output_shape, sample_mode, bounding_box = None):
    """
    get a random coordinate representing the center of a roi for sampling
    inputs:
        input_shape: the shape of sampled volume
        output_shape: the desired roi shape
        sample_mode: 'full': the entire roi should be inside the input volume
                     'valid': only the roi centre should be inside the input volume
        bounding_box: the bounding box which the roi center should be limited to
    outputs:
        center: the output center coordinate of a roi
    """
    center = []
    for i in range(len(input_shape)):
        if(sample_mode[i] == 'full'):
            if(bounding_box):
                x0 = bounding_box[i*2]; x1 = bounding_box[i*2 + 1]
            else:
                x0 = 0; x1 = input_shape[i]
        else:
            if(bounding_box):
                x0 = bounding_box[i*2] + int(output_shape[i]/2)   
                x1 = bounding_box[i*2+1] - int(output_shape[i]/2)   
            else:
                x0 = int(output_shape[i]/2)   
                x1 = input_shape[i] - x0
        if(x1 <= x0):
            centeri = int((x0 + x1)/2)
        else:
            centeri = random.randint(x0, x1)
        center.append(centeri)
    return center    

def transpose_volumes(volumes, slice_direction):
    """
    transpose a list of volumes
    inputs:
        volumes: a list of nd volumes
        slice_direction: 'axial', 'sagittal', or 'coronal'
    outputs:
        tr_volumes: a list of transposed volumes
    """
    if (slice_direction == 'axial'):
        tr_volumes = volumes
    elif(slice_direction == 'sagittal'):
        tr_volumes = [np.transpose(x, (2, 0, 1)) for x in volumes]
    elif(slice_direction == 'coronal'):
        tr_volumes = [np.transpose(x, (1, 0, 2)) for x in volumes]
    else:
        print('undefined slice direction:', slice_direction)
        tr_volumes = volumes
    return tr_volumes


def resize_ND_volume_to_given_shape(volume, out_shape, order = 3):
    """
    resize an nd volume to a given shape
    inputs:
        volume: the input nd volume, an nd array
        out_shape: the desired output shape, a list
        order: the order of interpolation
    outputs:
        out_volume: the reized nd volume with given shape
    """
    shape0=volume.shape
    assert(len(shape0) == len(out_shape))
    scale = [(out_shape[i] + 0.0)/shape0[i] for i in range(len(shape0))]
    out_volume = ndimage.interpolation.zoom(volume, scale, order = order)
    return out_volume

def extract_roi_from_volume(volume, in_center, output_shape, fill = 'random'):
    """
    extract a roi from a 3d volume
    inputs:
        volume: the input 3D volume
        in_center: the center of the roi
        output_shape: the size of the roi
        fill: 'random' or 'zero', the mode to fill roi region where is outside of the input volume
    outputs:
        output: the roi volume
    """
    input_shape = volume.shape   
    if(fill == 'random'):
        output = np.random.normal(0, 1, size = output_shape)
    else:
        output = np.zeros(output_shape)
    r0max = [int(x/2) for x in output_shape]
    r1max = [output_shape[i] - r0max[i] for i in range(len(r0max))]
    r0 = [min(r0max[i], in_center[i]) for i in range(len(r0max))]
    r1 = [min(r1max[i], input_shape[i] - in_center[i]) for i in range(len(r0max))]
    out_center = r0max

    output[np.ix_(range(out_center[0] - r0[0], out_center[0] + r1[0]),
                  range(out_center[1] - r0[1], out_center[1] + r1[1]),
                  range(out_center[2] - r0[2], out_center[2] + r1[2]))] = \
        volume[np.ix_(range(in_center[0] - r0[0], in_center[0] + r1[0]),
                      range(in_center[1] - r0[1], in_center[1] + r1[1]),
                      range(in_center[2] - r0[2], in_center[2] + r1[2]))]
    return output

def set_roi_to_volume(volume, center, sub_volume):
    """
    set the content of an roi of a 3d/4d volume to a sub volume
    inputs:
        volume: the input 3D/4D volume
        center: the center of the roi
        sub_volume: the content of sub volume
    outputs:
        output_volume: the output 3D/4D volume
    """
    volume_shape = volume.shape   
    patch_shape = sub_volume.shape
    output_volume = volume
    for i in range(len(center)):
        if(center[i] >= volume_shape[i]):
            return output_volume
    r0max = [int(x/2) for x in patch_shape]
    r1max = [patch_shape[i] - r0max[i] for i in range(len(r0max))]
    r0 = [min(r0max[i], center[i]) for i in range(len(r0max))]
    r1 = [min(r1max[i], volume_shape[i] - center[i]) for i in range(len(r0max))]
    patch_center = r0max

    if(len(center) == 3):
        output_volume[np.ix_(range(center[0] - r0[0], center[0] + r1[0]),
                             range(center[1] - r0[1], center[1] + r1[1]),
                             range(center[2] - r0[2], center[2] + r1[2]))] = \
            sub_volume[np.ix_(range(patch_center[0] - r0[0], patch_center[0] + r1[0]),
                              range(patch_center[1] - r0[1], patch_center[1] + r1[1]),
                              range(patch_center[2] - r0[2], patch_center[2] + r1[2]))]
    elif(len(center) == 4):
        output_volume[np.ix_(range(center[0] - r0[0], center[0] + r1[0]),
                             range(center[1] - r0[1], center[1] + r1[1]),
                             range(center[2] - r0[2], center[2] + r1[2]),
                             range(center[3] - r0[3], center[3] + r1[3]))] = \
            sub_volume[np.ix_(range(patch_center[0] - r0[0], patch_center[0] + r1[0]),
                              range(patch_center[1] - r0[1], patch_center[1] + r1[1]),
                              range(patch_center[2] - r0[2], patch_center[2] + r1[2]),
                              range(patch_center[3] - r0[3], patch_center[3] + r1[3]))]
    else:
        raise ValueError("array dimension should be 3 or 4")        
    return output_volume  


def get_roi(volume, margin):
    """
    get the roi bounding box of a 3D volume
    inputs:
        volume: the input 3D volume
        margin: an integer margin along each axis
    output:
        [mind, maxd, minh, maxh, minw, maxw]: a list of lower and upper bound along each dimension
    """
    [d_idxes, h_idxes, w_idxes] = np.nonzero(volume)
    [D, H, W] = volume.shape
    mind = max(d_idxes.min() - margin, 0)
    maxd = min(d_idxes.max() + margin, D)
    minh = max(h_idxes.min() - margin, 0)
    maxh = min(h_idxes.max() + margin, H)
    minw = max(w_idxes.min() - margin, 0)
    maxw = min(w_idxes.max() + margin, W)   
    return [mind, maxd, minh, maxh, minw, maxw]

def get_largest_two_component(img, threshold = None):
    """
    Get the largest two components of a binary volume
    inputs:
        img: the input 3D volume
        threshold: a size threshold
    outputs:
        out_img: the output volume 
    """
    s = ndimage.generate_binary_structure(3,2) # iterate structure
    labeled_array, numpatches = ndimage.label(img,s) # labeling
    sizes = ndimage.sum(img,labeled_array,range(1,numpatches+1)) 
    sizes_list = [sizes[i] for i in range(len(sizes))]
    sizes_list.sort()
    print('component size', sizes_list)
    if(len(sizes) == 1):
        out_img = img
    else:
        if(threshold):
            out_img = np.zeros_like(img)
            for temp_size in sizes_list:
                if(temp_size > threshold):
                    temp_lab = np.where(sizes == temp_size)[0] + 1
                    temp_cmp = labeled_array == temp_lab
                    out_img = (out_img + temp_cmp) > 0
            return out_img
        else:    
            max_size1 = sizes_list[-1]
            max_size2 = sizes_list[-2]
            max_label1 = np.where(sizes == max_size1)[0] + 1
            max_label2 = np.where(sizes == max_size2)[0] + 1
            component1 = labeled_array == max_label1
            component2 = labeled_array == max_label2
            if(max_size2*10 > max_size1):
                component1 = (component1 + component2) > 0
            out_img = component1
    return out_img

def fill_holes(img):
    """
    filling small holes of a binary volume with morphological operations
    """
    neg = 1 - img
    s = ndimage.generate_binary_structure(3,1) # iterate structure
    labeled_array, numpatches = ndimage.label(neg,s) # labeling
    sizes = ndimage.sum(neg,labeled_array,range(1,numpatches+1)) 
    sizes_list = [sizes[i] for i in range(len(sizes))]
    sizes_list.sort()
    max_size = sizes_list[-1]
    max_label = np.where(sizes == max_size)[0] + 1
    component = labeled_array == max_label
    return 1 - component


def remove_external_core(lab_main, lab_ext):
    """
    remove the core region that is outside of whole tumor
    """
    
    # for each component of lab_ext, compute the overlap with lab_main
    s = ndimage.generate_binary_structure(3,2) # iterate structure
    labeled_array, numpatches = ndimage.label(lab_ext,s) # labeling
    sizes = ndimage.sum(lab_ext,labeled_array,range(1,numpatches+1)) 
    sizes_list = [sizes[i] for i in range(len(sizes))]
    new_lab_ext = np.zeros_like(lab_ext)
    for i in range(len(sizes)):
        sizei = sizes_list[i]
        labeli =  np.where(sizes == sizei)[0] + 1
        componenti = labeled_array == labeli
        overlap = componenti * lab_main
        if((overlap.sum()+ 0.0)/sizei >= 0.5):
            new_lab_ext = np.maximum(new_lab_ext, componenti)
    return new_lab_ext
