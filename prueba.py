import nibabel as nib
import numpy as np

# Load the .nii file
img = nib.load('sub-01_T1w.nii')

# Modify the image data as needed
data = img.get_fdata()

# Set all values in layer 88 of dimension 1 to black
data[:, :, 88] = 0  # Set all voxels in layer 88 to zero (black)

# Update header information if necessary
# For example, modifying the affine transformation matrix
# img.affine = new_affine_matrix

# Create a new nibabel image object with modified data and header
modified_img = nib.Nifti1Image(data, img.affine)

# Save the modified image to a new file
nib.save(modified_img, 'modified_image.nii')
