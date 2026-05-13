They have several imaging techniques in Radiology, including X-rays, CT, MRI, Ultrasound (Sonography), Nuclear Medicine Imaging, and Interventional Radiology. While we will be more focused on MRI imaging techniques. The main MRI modalities are:
1.	Structured Imaging (sMRI): 
a.	T1-weighted: Highlighting soft tissues like the brain, muscle, and spinal cord
b.	T2-weighted: Detecting fluid and abnormalities like tumors, cysts, and edema
c.	Fluid-Attenuated Inversion Recovery (FLAIR): Suppressing the fluid signal for better visualization of brain lesions
d.	Gradient-Echo: Highlighting blood vessels and bone marrow
2.	Functional Imaging (fMRI):
a.	Diffusion-Weighted Imaging (DWI): Assessing water diffusion in tissues to detect stroke or tumors
b.	Magnetic Resonance Angiography (MRA): Imaging blood vessels without the need for contrast dye
c.	Functional MRI (fMRI): Detecting the brain activity by measuring blood flow changes
3.	Contrast-Enhanced Imaging: 
a.	Gadolinium-Enhanced MRI: Injecting a contrast agent to enhance the visibility of certain tissues, such as tumors or inflammation
4.	Others include Interventional MRI, Spectroscopy, Hybrid Imaging, etc.

The Neuroimaging software to analyze MRI images are AFNI, FSL, FreeSurfer, Brain Voyager, ExploreDTI, DSI Studio, BrainSuite, etc. The FreeSurfer provided a full processing stream for structural MRI data (skull stripping, reconstruction of cortical surface models, labeling of regions on the cortical surface, nonlinear registration, statistical analysis), while FreeSurfer Functional Analysis Stream (FS-FAST) is a set of tools for performing functional MRI data analyses on the cortical surface. For Diffusion MRI, they have TRACULA, AnatomiCuts, and DiffusionTool. For performing ROI-based whole-brain analysis of PET data, they have PETSurfer.
The recently developed DeepPrep replaced the time-consuming steps of FreeSurfer with deep-learning-based methods like, 
-	For segmentation, instead of using the atlas-based method of FreeSurfer workflow, DeepPrep utilized FastSurferCNN, a deep learning model for rapid segmentation of cortical and subcortical regions.
-	For surface reconstruction, DeepPrep uses FastCSR, a deep learning model that accelerates the creation of cortical surfaces using implicit representations, drastically cutting down the processing time.
-	For surface registration, DeepPrep uses SUGAR, a deep learning-based framework that achieved accurate registration in seconds compared to the hours of computation traditionally required.
Note: The current version of DeepPrep does not support DWI format, but developers are actively working on it. 
Datasets: 
Dataset-1: Professional Chess Players - data 29-Players data – sMRI and fMRI data (http://fcon_1000.projects.nitrc.org/indi/pro/wchsu_li_index.html) 
