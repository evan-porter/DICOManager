# DICOM Pre-processing Library

## Purpose
To take DICOM files, imported to /data/imported_data (or another specified location)
and sorts based by provided MRN list.

User can then reconstruct volumes with the reconstruct.py functions or deconstruct
binary masks into RTSTRUCT files with deconstruction.py.

Note: reconstuction.py is functional, but in need of refactoring. 

## Prerequisites
### Packages
Package requirements are specified in requirements.txt
These requirements can be installed with
```
pip install -r requirements.txt
```

### File Tree Structure
This library is designed to function with the following directory tree. Any
alterations will require changing directory locations within file_sorting.py.

Any non-DICOM files, or those with corrupted headers will be moved to the
'rejected_files' director

Future versions may include a script to create the proper file tree in
linux / unix systems.

```
data / base directory
├── imported_data
│   └──  <file>.dcm
├── DICOManager
|   ├── <project>.csv
│   ├── clean_rtstructs.csv
│   ├── deconstruction.py
│   ├── file_sorting.py
│   ├── modality.csv
│   ├── reconstruction.py
│   ├── recon_sorted.py
|   └── utils.py
├── rejected_files
|   └── *.dcm
└── sorted_data
    └── <project>
        └── MRN0
            ├── MODALITY0
            └── MODALITY1
                └── *.dcm
 ```

## Project Overview
### requirements.txt
Required libraries for pip install, see above for guide

### file_sorting.py
Initially imported data of just DICOM files will be dumped into imported_data.
From which, sorting cam be completed for a given <project>. Sorting is completed
via a <project>.csv of MRN values and sorts them by MRN and date (if desired),
and then modality. It is recommended for PHI confidentiality, that MRNs are
replaced by anonymously coded numbers per patient.

Modalities are chosen from the modality.csv. Unique encodings can be provided,
with mapping of first row to directories of the second row.

Modalities will be chosen from the standard DICOM modalities, unless 'CBCT' is
in the SeriesDescription, in which the .dcm files will be stored under CBCT.

Parsed arguments for this function include:
```
-b, --base: str (Default : pwd)
    Specify the base directory that sorting is occurring.
-c, --csv: str
    Specify the path to a .csv file contained within sort_csv directory
-m, --move: bool
    Specify if the dicom files are moved or copied to the sorted directory
-p, --project-dest: str (Default : '/data/sorted_data/')
    Specify the location of the sorted dicom directory
```


### recon_sorted.py
This function is a script to apply the reconstruction.py functions to a
sorted project directory.

Parsed arguments for this function include:
```
-b, --base: str
        A path to the sorted project directory
-c, --csv: str
        A path to a .csv file in the format of example.csv, indicating
        the MRN values to be reconstructed
-d, --dest_dir: str
        A path to a file where the final .npy volumes will be stored
-j, --json: str
        A path to a .json file for the contour name dictionary to
        map contour names to a common name
-p, --project_name: str
        A string representing the name to append to the front of the
        saved .npy volume
```

### clean_rtstructs.py
If specified, this function will move all but the newest RTSTRUCT from a
sorted patient directory for simpler management of redundant outdate rt files.
If specified the remaining structures and be printed.

Parsed arguments for this function include:
```
-b, --base: str
        A path to the sorted project directory
-c, --csv: str
        A path to a .csv file in the format of example.csv, indicating
        the MRN values to be reconstructed
-d, --dest_dir: str
        A path to a file where the final .npy volumes will be stored
-j, --json: str
        A path toa .json file for the contour name dictionary to
        map contour names to a common name
-s, --summary: bool
        Prints the names of the remaining RTSTRUCT ROIs
-v, --verbose: bool
        Prints the files and their relocated path
-r, --read_only: bool
        Only lists the ROIs in the RTSTRUCTs in the base directory
```

### reconstruction.py
Reconstructs PET, CT, CBCT, RTSTRUCT, RTDOSE DICOM formats into float32 numpy
arrays of original coordinate systems. Each function takes a specified list of
patient .dcm files of a given modality and returns a reconstructed volume.

#### PET: reconstruction.pet
Calculates the time corrected SUVbw PET value for the registered CT coordinate
system. Returns a numpy array of float32 values.

#### CBCT / CT : reconstruction.ct
Both CBCT and CT perform similarly, they are simply stored under different names.
Reconstruction is done at original image coordinates. Future work will include
projection of CBCT into CT coordinate space.

#### DOSE : reconstruction.dose
Reconstruction of Pinnacle 11.0 dose files into registered CT coordinate space.

#### RTSTRUCT : reconstruction.struct
RTSTRUCT files are saved as a list of arrays, but the dimensions are
(number-of-masks, x, y, z). Each element in the arrays are boolean. Masks are
returned in order as specified, except in cases where mask is not present in
the RTDOSE file.

#### MRI: reconstruction.mri
Creates an MRI volume and returns a numpy array of float32 values.

#### NM: reconstruction.nm
Creates a Nuclear Medicine (NM) volume and returns a numpy array of 
float32 values. Unlike other DICOM reconstruction functions, NM files store
the entire 3D volume within a single DICOM file

### deconstruction.py
Deconstruct boolean mask numpy arrays into DICOM compliant RTSTRUCT files
with reference to a series of registered CT DICOM files. Can generate both
MIM and Pinnacle style contours, as specified. Default is MIM compliant.

#### deconstruction.to_rt
Appends a boolean numpy array to a provided rtstruct DICOM file with the
corresponding CT DICOMs.

#### deconstruction.from_rt
Creates a new RTSTRUCT DICOM file from a provided RTSTRUCT file with the
corresponding CT DICOMs. Then appends a boolean numpy array to the created
DICOM file.

#### deconstruction.from_ct
Creates a new RTSTRUCT DICOM file from the corresponding CT DICOMs. Appends
a boolean numpy array to the created DICOM file.

#### deconstruction.save_rt
Saves a provided pydicom.dataset object to the specified posix path or filename
