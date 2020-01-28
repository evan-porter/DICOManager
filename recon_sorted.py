#!/usr/bin/python3

import os
import csv
import optparse
import json
import reconstruction
import pydicom
import numpy as np
from glob import glob as glob
from tqdm import tqdm
from pathlib import Path
from dataclasses import dataclass
from dataclasses import fields

__author__ = ["Evan Porter", "Ron Levitin"]
__license__ = "Beaumont Artificial Intelligence Research Lab"
__email__ = "evan.porter@beaumont.org"
__status__ = "Research"

def _img_dims(file_path, modality):
    """
    _img_dims gets the aspect ratio
    
    Parameters
    ----------
    file_path : str or pathlib.PosixPath
        Path to patient directory with volumes
    modality : str
        String of the modality type to insert into the directory structure
    
    Returns
    -------
    asepct : Tuple
        (*Pixel Spacing, SliceThickness) for use in setting aspect ratio in saggital/coronal plots
    """
    # If path is a string, convert to pathlib.Path
    if not isinstance(file_path, Path):
        file_path = Path(file_path).expanduser()

    # find the RTSTRUCT dcm file
    if file_path.is_file() and file_path.suffix == ".dcm":
        struct_file = file_path
    elif file_path.is_dir():
        file_path_sub = file_path.joinpath(modality)
        if file_path_sub.is_dir():
            file_to_read = next(file_path_sub.iterdir())

    ds = pydicom.dcmread(str(file_to_read), stop_before_pixels=True)
    aspect = (*ds.PixelSpacing, ds.SliceThickness)
    return aspect

@dataclass
class FileCollect:
    """
    Function
    ----------
    Takes a path and collects all file types per modality

    Parameters
    ----------
    path : str
        A path to a sorted patient folder
    """
    path: str
    project: str = None
    mrn: str = None
    MR: list = None
    CT: list = None
    PET: list = None
    RTSTRUCT: list = None
    RTDOSE: list = None

    
    def __repr__(self):
        unpack = ":".join(str(len(self[x])) for x in self)
        return (f'{self.mrn}-{unpack}')


    def __getitem__(self, name):
        return self.__dict__[name]


    def __setitem__(self, name, value):
        self.__dict__[name] = value


    def __iter__(self):
        modalities = [x.name for x in fields(self)]
        return iter(modalities[3:])


    def __post_init__(self):
        self.project, _, self.mrn = self.path.rpartition('/')
        paths = [os.path.join(self.path, x, '*.dcm') for x in self]

        for i, mod in enumerate(self):
            self[mod] = glob(paths[i])


usage = "usage: recon_sorted.py [opt1] ... \n Reconstructs from DICOM to Numpy arrays and saves in -d"
parser = optparse.OptionParser(usage)

parser.add_option('-b', '--base', action='store', dest='base_dir',
                  help='Directory with sorted data to reconstruct', default=None)
parser.add_option('-c', '--csv', action='store', dest='csv_file',
                  help='MRN list to reconstruct', default=None)
parser.add_option('-d', '--dest_dir', action='store', dest='dest_dir',
                  help='Directory to save numpy arrays', default=None)
parser.add_option('-j', '--json', action='store', dest='contour_list',
                  help='Path to json of dictionary of RTSTRUCTS to reconstruct', default=None)
parser.add_option('-p', '--project_name', action='store', dest='project',
                    help='Project name to prepend to files', default=None)
 
options, args = parser.parse_args()

if not options.base_dir:
    raise NameError('A sorted project folder must be provided to reconstruct')

if not options.dest_dir:
    options.dest_dir = options.base_dir

file_tree = glob(os.path.join(options.base_dir, '**/*[!.dcm]'), recursive=True)

with open(options.csv_file, mode='r') as MRN_csv:
    filter_list = list(x[0] for x in csv.reader(MRN_csv))[1:]

pat_folders = list(set([df.rpartition('/')[0]
                        for df in file_tree if df.split('/')[-2] in filter_list]))

for path in tqdm(pat_folders):
    patient_group = FileCollect(path)

    mr, ct, pet, rts, dose = [[] for _ in range(5)]

    if patient_group.MR:
        mr = reconstruction.mri(path)
        aspect = _img_dims(path, 'MR') # 
    if patient_group.CT:
        ct = reconstruction.ct(path)
        aspect = _img_dims(path, 'CT')
    if patient_group.PET:
        pet = reconstruction.pet(path)
        aspect = _img_dims(path, 'PET')
    if patient_group.RTSTRUCT:
        if not options.contour_list:
            raise NameError('A .csv of contours must be specified with -l')
        with open(options.contour_list, mode='r') as json_file:
            contour_list = json.load(json_file)
        rts = reconstruction.struct(path, contour_list)
    if patient_group.RTDOSE:
        dose = reconstruction.dose(path)
    pool_dict = {'MR': mr,
                 'CT': ct,
                 'PET': pet,
                 'RTSTRUCT': rts,
                 'RTDOSE': dose,
                 'ASPECT': aspect
                }
    if not os.path.exists(options.dest_dir):
        os.makedirs(options.dest_dir)

    np.save(Path(options.dest_dir) / 
            (options.project + '_' + patient_group.mrn),
            pool_dict)
