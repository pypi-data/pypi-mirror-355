import subprocess
import os
import numpy as np
from abc import ABC, abstractmethod
import enum
import AOT_biomaps
import matplotlib.pyplot as plt
from tqdm import trange
from .config import config
import matplotlib.animation as animation
from IPython.display import HTML
import sys
from datetime import datetime
from tempfile import gettempdir
from skimage.metrics import structural_similarity as ssim
if config.get_process()  == 'gpu':
    import torch
    try:
        from torch_scatter import scatter
        from torch_sparse import coalesce
    except ImportError:
        raise ImportError("torch_scatter and torch_sparse are required for GPU processing. Please install them using 'pip install torch-scatter torch-sparse' with correct link (follow instructions https://github.com/LucasDuclos/AcoustoOpticTomography/edit/main/README.md).")
from numba import njit, prange
import numba
from skimage.metrics import structural_similarity as ssim
from scipy.integrate import trapz
from .AOT_Experiment import *
from .AOT_Optic import *
from .AOT_Acoustic import *

class ReconType(enum.Enum):
    """
    Enum for different reconstruction types.

    Selection of reconstruction types:
    - Analytic: A reconstruction method based on analytical solutions.
    - Algebraic: A reconstruction method using algebraic techniques.
    - Iterative: A reconstruction method that iteratively refines the solution.
    - Bayesian: A reconstruction method based on Bayesian statistical approaches.
    - DeepLearning: A reconstruction method utilizing deep learning algorithms.
    """

    Analytic = 'analytic'
    """A reconstruction method based on analytical solutions."""
    Iterative = 'iterative'
    """A reconstruction method that iteratively refines the solution."""
    Bayesian = 'bayesian'
    """A reconstruction method based on Bayesian statistical approaches."""
    DeepLearning = 'deep_learning'
    """A reconstruction method utilizing deep learning algorithms."""

class AnalyticType(enum.Enum):
    iFOURIER = 'iFOURIER'
    """
    This analytic reconstruction type uses the inverse Fourier transform to reconstruct the image.
    It is suitable for data that can be represented in the frequency domain.
    It is typically used for data that has been transformed into the frequency domain, such as in Fourier optics.
    It is not suitable for data that has not been transformed into the frequency domain.
    """
    iRADON = 'iRADON'
    """
    This analytic reconstruction type uses the inverse Radon transform to reconstruct the image.
    It is suitable for data that has been transformed into the Radon domain, such as in computed tomography (CT).
    It is typically used for data that has been transformed into the Radon domain, such as in CT.
    It is not suitable for data that has not been transformed into the Radon domain.
    """

class IterativeType(enum.Enum):
    MLEM = 'MLEM'
    """
    This optimizer is the standard MLEM (for Maximum Likelihood Expectation Maximization).
    It is numerically implemented in the multiplicative form (as opposed to the gradient form).
    It truncates negative data to 0 to satisfy the positivity constraint.
    If subsets are used, it naturally becomes the OSEM optimizer.

    With transmission data, the log-converted pre-corrected data are used as in J. Nuyts et al:
    "Iterative reconstruction for helical CT: a simulation study", Phys. Med. Biol., vol. 43, pp. 729-737, 1998.

    The following options can be used (in this particular order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Denominator threshold: Sets the threshold of the data space denominator under which the ratio is set to 1.
    - Minimum image update: Sets the minimum of the image update factor under which it stays constant.
      (0 or a negative value means no minimum, thus allowing a 0 update).
    - Maximum image update: Sets the maximum of the image update factor over which it stays constant.
      (0 or a negative value means no maximum).

    This optimizer is compatible with both histogram and list-mode data.
    This optimizer is compatible with both emission and transmission data.
    """
    MLTR = 'MLTR'
    """
    This optimizer is a version of the MLTR algorithm implemented from equation 16 of the paper from K. Van Slambrouck and J. Nuyts:
    "Reconstruction scheme for accelerated maximum likelihood reconstruction: the patchwork structure",
    IEEE Trans. Nucl. Sci., vol. 61, pp. 173-81, 2014.

    An additional empiric relaxation factor has been added onto the additive update. Its value for the first and last updates
    can be parameterized. Its value for all updates in between is computed linearly from these first and last provided values.

    Subsets can be used.

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Alpha ratio: Sets the ratio between exterior and interior of the cylindrical FOV alpha values (0 value means 0 inside exterior).
    - Initial relaxation factor: Sets the empiric multiplicative factor on the additive update used at the first update.
    - Final relaxation factor: Sets the empiric multiplicative factor on the additive update used at the last update.
    - Non-negativity constraint: 0 if no constraint or 1 to apply the constraint during the image update.

    This optimizer is only compatible with histogram data and transmission data.
    """

    NEGML = 'NEGML'
    """
    This optimizer is the NEGML algorithm from K. Van Slambrouck et al, IEEE TMI, Jan 2015, vol. 34, pp. 126-136.

    Subsets can be used. This implementation only considers the psi parameter, but not the alpha image design parameter,
    which is supposed to be 1 for all voxels. It implements equation 17 of the reference paper.

    This algorithm allows for negative image values.

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Psi: Sets the psi parameter that sets the transition from Poisson to Gaussian statistics (must be positive).
      (If set to 0, then it is taken to infinity and implements equation 21 in the reference paper).

    This optimizer is only compatible with histogram data and emission data.
    """

    OSL = 'OSL'
    """
    This optimizer is the One-Step-Late algorithm from P. J. Green, IEEE TMI, Mar 1990, vol. 9, pp. 84-93.

    Subsets can be used as for OSEM. It accepts penalty terms that have a derivative order of at least one.
    Without penalty, it is strictly equivalent to the MLEM algorithm.

    It is numerically implemented in the multiplicative form (as opposed to the gradient form).

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Denominator threshold: Sets the threshold of the data space denominator under which the ratio is set to 1.
    - Minimum image update: Sets the minimum of the image update factor under which it stays constant (0 or a negative value
                            means no minimum thus allowing a 0 update).
    - Maximum image update: Sets the maximum of the image update factor over which it stays constant (0 or a negative value means
                            no maximum).

    This optimizer is compatible with both histogram and list-mode data, and with both emission and transmission data.
    """

    PPGMLEM = 'PPGML'
    """
    This optimizer is the Penalized Preconditioned Gradient algorithm from J. Nuyts et al, IEEE TNS, Feb 2002, vol. 49, pp. 56-60.

    It is a heuristic but effective gradient ascent algorithm for penalized maximum-likelihood reconstruction.
    It addresses the shortcoming of One-Step-Late when large penalty strengths can create numerical problems.
    Penalty terms must have a derivative order of at least two.

    Subsets can be used as for OSEM. Without penalty, it is equivalent to the gradient ascent form of the MLEM algorithm.

    Based on likelihood gradient and penalty, a multiplicative update factor is computed and its range is limited by provided parameters.
    Thus, negative values cannot occur and voxels cannot be trapped into 0 values, providing the first estimate is strictly positive.

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Denominator threshold: Sets the threshold of the data space denominator under which the ratio is set to 1.
    - Minimum image update: Sets the minimum of the image update factor under which it stays constant (0 or a negative value
                            means no minimum thus allowing a 0 update).
    - Maximum image update: Sets the maximum of the image update factor over which it stays constant (0 or a negative value means
                            no maximum).

    This optimizer is only compatible with histogram data and emission data.
    """

    AML = 'AML'
    """
    This optimizer is the AML algorithm derived from the AB-EMML of C. Byrne, Inverse Problems, 1998, vol. 14, pp. 1455-67.

    The bound B is taken to infinity, so only the bound A can be parameterized.
    This bound must be quantitative (same unit as the reconstructed image).
    It is provided as a single value and thus assuming a uniform bound.

    This algorithm allows for negative image values in case the provided bound is also negative.

    Subsets can be used.

    With a negative or null bound, this algorithm implements equation 6 of A. Rahmim et al, Phys. Med. Biol., 2012, vol. 57, pp. 733-55.
    If a positive bound is provided, then we suppose that the bound A is taken to minus infinity. In that case, this algorithm implements
    equation 22 of K. Van Slambrouck et al, IEEE TMI, Jan 2015, vol. 34, pp. 126-136.

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Denominator threshold: Sets the threshold of the data space denominator under which the ratio is set to 1.
    - Bound: Sets the bound parameter that shifts the Poisson law (quantitative, negative or null for standard AML and positive for infinite AML).

    This optimizer is only compatible with histogram data and emission data.
    """

    BSREM = 'BSREM'
    """
    This optimizer is the BSREM (for Block Sequential Regularized Expectation Maximization) algorithm, in development.
    It follows the definition of BSREM II in Ahn and Fessler 2003.

    This optimizer is the Block Sequential Regularized Expectation Maximization (BSREM) algorithm from S. Ahn and
    J. Fessler, IEEE TMI, May 2003, vol. 22, pp. 613-626. Its abbreviated name in this paper is BSREM-II.

    This algorithm is the only one to have proven convergence using subsets. Its implementation is entirely based
    on the reference paper. It may have numerical problems when a full field-of-view is used, because of the sharp
    sensitivity loss at the edges of the field-of-view. As it is simply based on the gradient, penalty terms must
    have a derivative order of at least one. Without penalty, it reduces to OSEM but where the sensitivity is not
    dependent on the current subset. This is a requirement of the algorithm, explaining why it starts by computing
    the global sensitivity before going through iterations. The algorithm is restricted to histograms.

    Options:
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Minimum image value: Sets the minimum allowed image value (parameter 't' in the reference paper).
    - Maximum image value: Sets the maximum allowed image value (parameter 'U' in the reference paper).
    - Relaxation factor type: Type of relaxation factors (can be one of the following: 'classic').

    Relaxation factors of type 'classic' correspond to what was proposed in the reference paper in equation (31).
    This equation gives: alpha_n = alpha_0 / (gamma * iter_num + 1)
    The iteration number 'iter_num' is supposed to start at 0 so that for the first iteration, alpha_0 is used.
    This parameter can be provided using the following keyword: 'relaxation factor classic initial value'.
    The 'gamma' parameter can be provided using the following keyword: 'relaxation factor classic step size'.

    This optimizer is only compatible with histogram data and emission data.
    """

    DEPIERRO95 = 'DEPIERRO95'
    """
    This optimizer is based on the algorithm from A. De Pierro, IEEE TMI, vol. 14, pp. 132-137, 1995.

    This algorithm uses optimization transfer techniques to derive an exact and convergent algorithm
    for maximum likelihood reconstruction including a MRF penalty with different potential functions.

    The algorithm is convergent and is numerically robust to high penalty strength.
    It is strictly equivalent to MLEM without penalty, but can be unstable with extremely low penalty strength.
    Currently, it only implements the quadratic penalty.

    To be used, a MRF penalty still needs to be defined accordingly (at least to define the neighborhood).
    Subsets can be used as for OSEM, without proof of convergence however.

    The algorithm is compatible with list-mode or histogram data.

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Denominator threshold: Sets the threshold of the data space denominator under which the ratio is set to 1.
    - Minimum image update: Sets the minimum of the image update factor under which it stays constant (0 or a negative value
                            means no minimum thus allowing a 0 update).
    - Maximum image update: Sets the maximum of the image update factor over which it stays constant (0 or a negative value means
                            no maximum).

    This optimizer is compatible with both histogram and list-mode data, and only with emission data.
    """

    LDWB = 'LDWB'
    """
    This optimizer implements the standard Landweber algorithm for least-squares optimization.

    With transmission data, it uses the log-converted model to derive the update.
    Be aware that the relaxation parameter is not automatically set, so it often requires some
    trials and errors to find an optimal setting. Also, remember that this algorithm is particularly
    slow to converge.

    Options (in order when provided as a list):
    - Initial image value: Sets the uniform voxel value for the initial image.
    - Relaxation factor: Sets the relaxation factor applied to the update.
    - Non-negativity constraint: 0 if no constraint or 1 in order to apply the constraint during the image update.

    This optimizer is only compatible with histogram data, and with both emission and transmission data.
    """

class PotentialType(enum.Enum):
    """The potential function actually penalizes the difference between the voxel of interest and a neighbor:
    p(u, v) = p(u - v)

    Descriptions of potential functions:
    - Quadratic: p(u, v) = 0.5 * (u - v)^2
    - Geman-McClure: p(u, v, d) = (u - v)^2 / (d^2 + (u - v)^2)
    - Hebert-Leahy: p(u, v, m) = log(1 + (u - v)^2 / m^2)
    - Green's log-cosh: p(u, v, d) = log(cosh((u - v) / d))
    - Huber piecewise: p(u, v, d) = d * |u - v| - 0.5 * d^2 if |u - v| > d, else 0.5 * (u - v)^2
    - Nuyts relative: p(u, v, g) = (u - v)^2 / (u + v + g * |u - v|)
    """

    QUADRATIC = 'QUADRATIC'
    """
    Quadratic potential:
    p(u, v) = 0.5 * (u - v)^2

    Reference: Geman and Geman, IEEE Trans. Pattern Anal. Machine Intell., vol. PAMI-6, pp. 721-741, 1984.
    """

    GEMAN_MCCLURE = 'GEMAN_MCCLURE'
    """
    Geman-McClure potential:
    p(u, v, d) = (u - v)^2 / (d^2 + (u - v)^2)

    The parameter 'd' can be set using the 'deltaGMC' keyword.

    Reference: Geman and McClure, Proc. Amer. Statist. Assoc., 1985.
    """

    HEBERT_LEAHY = 'HEBERT_LEAHY'
    """
    Hebert-Leahy potential:
    p(u, v, m) = log(1 + (u - v)^2 / m^2)

    The parameter 'm' can be set using the 'muHL' keyword.

    Reference: Hebert and Leahy, IEEE Trans. Med. Imaging, vol. 8, pp. 194-202, 1989.
    """

    GREEN_LOGCOSH = 'GREEN_LOGCOSH'
    """
    Green's log-cosh potential:
    p(u, v, d) = log(cosh((u - v) / d))

    The parameter 'd' can be set using the 'deltaLogCosh' keyword.

    Reference: Green, IEEE Trans. Med. Imaging, vol. 9, pp. 84-93, 1990.
    """

    HUBER_PIECEWISE = 'HUBER_PIECEWISE'
    """
    Huber piecewise potential:
    p(u, v, d) = d * |u - v| - 0.5 * d^2 if |u - v| > d, else 0.5 * (u - v)^2

    The parameter 'd' can be set using the 'deltaHuber' keyword.

    Reference: e.g. Mumcuoglu et al, Phys. Med. Biol., vol. 41, pp. 1777-1807, 1996.
    """

    NUYTS_RELATIVE = 'NUYTS_RELATIVE'
    """
    Nuyts relative potential:
    p(u, v, g) = (u - v)^2 / (u + v + g * |u - v|)

    The parameter 'g' can be set using the 'gammaRD' keyword.

    Reference: Nuyts et al, IEEE Trans. Nucl. Sci., vol. 49, pp. 56-60, 2002.
    """

class ProcessType(enum.Enum):
    CASToR = 'CASToR'
    PYTHON = 'PYTHON'

class Recon:
    def __init__(self, experiment, saveDir):
        self.reconOpticImage = None
        self.experiment = experiment
        self.saveDir = saveDir

        if type(self.experiment) is not AOT_biomaps.AOT_Experiment.Tomography:
            raise TypeError(f"Experiment must be of type {AOT_biomaps.AOT_Experiment.Tomography}")

    @abstractmethod
    def run(self):
        pass
        
    @staticmethod
    def load_recon(hdr_path):
        """
        Lit un fichier Interfile (.hdr) et son fichier binaire (.img) pour reconstruire une image comme le fait Vinci.
        
        Paramètres :
        ------------
        - hdr_path : chemin complet du fichier .hdr
        
        Retour :
        --------
        - image : tableau NumPy contenant l'image
        - header : dictionnaire contenant les métadonnées du fichier .hdr
        """
        header = {}
        with open(hdr_path, 'r') as f:
            for line in f:
                if ':=' in line:
                    key, value = line.split(':=', 1)  # s'assurer qu'on ne coupe que la première occurrence de ':='
                    key = key.strip().lower().replace('!', '')  # Nettoyage des caractères
                    value = value.strip()
                    header[key] = value
        
        # 📘 Obtenez le nom du fichier de données associé (le .img)
        data_file = header.get('name of data file')
        if data_file is None:
            raise ValueError(f"Impossible de trouver le fichier de données associé au fichier header {hdr_path}")
        
        img_path = os.path.join(os.path.dirname(hdr_path), data_file)
        
        # 📘 Récupérer la taille de l'image à partir des métadonnées
        shape = [int(header[f'matrix size [{i}]']) for i in range(1, 4) if f'matrix size [{i}]' in header]
        if shape and shape[-1] == 1:  # Si la 3e dimension est 1, on la supprime
            shape = shape[:-1]  # On garde (192, 240) par exemple
        
        if not shape:
            raise ValueError("Impossible de déterminer la forme de l'image à partir des métadonnées.")
        
        # 📘 Déterminez le type de données à utiliser
        data_type = header.get('number format', 'short float').lower()
        dtype_map = {
            'short float': np.float32,
            'float': np.float32,
            'int16': np.int16,
            'int32': np.int32,
            'uint16': np.uint16,
            'uint8': np.uint8
        }
        dtype = dtype_map.get(data_type)
        if dtype is None:
            raise ValueError(f"Type de données non pris en charge : {data_type}")
        
        # 📘 Ordre des octets (endianness)
        byte_order = header.get('imagedata byte order', 'LITTLEENDIAN').lower()
        endianess = '<' if 'little' in byte_order else '>'
        
        # 📘 Vérifie la taille réelle du fichier .img
        img_size = os.path.getsize(img_path)
        expected_size = np.prod(shape) * np.dtype(dtype).itemsize
        
        if img_size != expected_size:
            raise ValueError(f"La taille du fichier img ({img_size} octets) ne correspond pas à la taille attendue ({expected_size} octets).")
        
        # 📘 Lire les données binaires et les reformater
        with open(img_path, 'rb') as f:
            data = np.fromfile(f, dtype=endianess + np.dtype(dtype).char)
        
        image =  data.reshape(shape[::-1]) 
        
        # 📘 Rescale l'image si nécessaire
        rescale_slope = float(header.get('data rescale slope', 1))
        rescale_offset = float(header.get('data rescale offset', 0))
        image = image * rescale_slope + rescale_offset
        
        return image.T

class IterativeRecon(Recon):
    """
    This class implements the iterative reconstruction process.
    It currently does not perform any operations but serves as a template for future implementations.
    """
    def __init__(self,  **kwargs):
        super().__init__(**kwargs)
        self.theta_matrix = []
        self.MSEArray = []
        self.SSIMArray = []
        self.opti = IterativeType(self.experiment.params.reconstruction['IerativeType'])
        self.numIterations = self.experiment.params.reconstruction['numIterations']
        self.numSubsets = self.experiment.params.reconstruction['numSubsets']

        if self.numIterations <= 0:
            raise ValueError("Number of iterations must be greater than 0.")
        if self.numSubsets <= 0:
            raise ValueError("Number of subsets must be greater than 0.")
        if type(self.numIterations) is not int:
            raise TypeError("Number of iterations must be an integer.")
        if type(self.numSubsets) is not int:
            raise TypeError("Number of subsets must be an integer.")

    def run(self, reconType):
        """
        This method is a placeholder for the iterative reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(reconType == ProcessType.CASToR):
            self._iterativeReconCASToR()
        elif(reconType == ProcessType.PYTHON):
            self._iterativeReconPython()
        else:
            raise ValueError(f"Unknown iterative reconstruction type: {reconType}")
        
        self._MSE_calc()
        self._SSIM_calc()

    def _load_theta_matrix(self):
        for thetaFiles in os.path.join(self.saveDir, 'results'):
            if thetaFiles.endswith('.hdr'):
                theta = AOT_biomaps.AOT_reconstruction.load_recon(thetaFiles)
                self.theta_matrix.append(theta)

    def _iterativeReconPython(self):
        if self.opti.value == IterativeType.MLEM.value:
            self._MLEM()
        self.reconOpticImage = self.theta_matrix[-1]  # Use the last iteration as the final reconstruction

    def _iterativeReconCASToR(self):

        # Define variables
        smatrix = os.path.join(self.saveDir,"system_matrix")

        # Check if input file exists
        if not os.path.isfile(f"{self.saveDir}/AOSignals.cdh"):
            self.experiment._saveAOsignalForCastor(self.saveDir)
        # Check if system matrix directory exists
        elif not os.path.isdir(smatrix):
            os.mkdir(smatrix)
        # check if system matrix is empty
        elif not os.listdir(smatrix):
            self.experiment._saveSMatrixForCastor(self.saveDir)

        # Construct the command
        cmd = [
            self.experiment.params.reconstruction['castor_executable'],
            "-df", f"{self.saveDir}/AOSignals.cdh",
            "-opti", self.opti.value,
            "-it", f"{self.numIterations}:{self.numSubsets}"  ,
            "-proj", "matrix",
            "-dout", os.path.join(self.saveDir, 'results','recon'),
            "-th", f"{ os.cpu_count()}",
            "-vb", "5",
            "-proj-comp", "1",
            "-ignore-scanner",
            "-data-type", "AOT",
            "-ignore-corr", "cali,fdur",
            "-system-matrix", smatrix,
        ]

        # Print the command
        print(" ".join(cmd))

        #save the command to a script file
        recon_script_path = os.path.join(gettempdir(), 'recon.sh')
        with open(recon_script_path, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write(" ".join(cmd) + "\n")

        sys.exit(0)

        # --- Run Reconstruction Script ---
        print(f"Running reconstruction script: {recon_script_path}")
        subprocess.run(["chmod", "+x", recon_script_path], check=True)
        subprocess.run([recon_script_path], check=True)
        print("Reconstruction script executed.")

        self._load_theta_matrix()

    def _MLEM(self):
        """
        This method implements the MLEM algorithm using either basic numpy operations or PyTorch for GPU acceleration.
        It is called by the iterative reconstruction process.
        """
        if config.get_process() == 'gpu':
            self.theta_matrix = IterativeRecon._MLEM_GPU(self.experiment.A_matrix, self.experiment.AOsignal, self.numIterations* self.numSubsets)
        else:
            self.theta_matrix = IterativeRecon._MLEM_CPU(self.experiment.A_matrix, self.experiment.AOsignal, self.numIterations* self.numSubsets)
    
    def _MSE_calc(self):
        """
        Calculate the Mean Squared Error (MSE) of the reconstruction.
        
        Parameters:
            theta_matrix: list of (z, x) ndarray, iterative reconstructions
                          If None, uses the last theta matrix from self.theta_matrix.
        
        Returns:
            mse: float, Mean Squared Error of the reconstruction
        """
        self.MSEArray = []
        for theta in self.theta_matrix:
            if not isinstance(theta, np.ndarray):
                raise TypeError("Theta matrix must be a numpy ndarray.")    
            self.MSEArray.append(np.mean((self.experiment.opticImage - theta) ** 2))

    def _SSIM_calc(self):
        self.SSIMArray = []
        for theta in self.theta_matrix:
            if not isinstance(theta, np.ndarray):
                raise TypeError("Theta matrix must be a numpy ndarray.")
            ssim_value = ssim(self.experiment.opticImage, theta, data_range=theta.max() - theta.min())
            self.SSIMArray.append(ssim_value)

    def plot_MSE(self, isSaving=True):
        """
        Plot the Mean Squared Error (MSE) of the reconstruction.
        
        Parameters:
            MSEArray: list of float, Mean Squared Error values for each iteration
                      If None, uses the MSEArray from self.MSEArray.
        
        Returns:
            None
        """
        if not self.MSEArray:
            raise ValueError("MSEArray is empty. Please calculate MSE first.")
        
        best_idx = np.argmin(self.MSEArray)
        
        print(f"Lowest MSE = {np.min(self.MSEArray):.4f} at iteration {best_idx+1}")

        # Plot MSE curve
        plt.figure(figsize=(7, 5))
        plt.plot(self.MSEArray, 'r-', label="MSE curve")

        # Add blue dashed lines
        plt.axhline(np.min(self.MSEArray), color='blue', linestyle='--', label=f"Min MSE = {np.min(self.MSEArray):.4f}")
        plt.axvline(best_idx+1, color='blue', linestyle='--', label=f"Iteration = {best_idx+1}")

        plt.xlabel("Iteration")
        plt.ylabel("MSE")
        plt.title("MSE vs. Iteration")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        if isSaving:
            now = datetime.now()    
            date_str = now.strftime("%Y_%d_%m_%y")
            SavingFolder = os.path.join(self.saveDir, 'results', f'MSE_plot{date_str}.png')
            plt.savefig(SavingFolder, dpi=300)
            print(f"MSE plot saved to {SavingFolder}")
        
        plt.show()

    def plot_MSE_bestRecon(self, isSaving=True):
        
        if not self.MSEArray:
            raise ValueError("MSEArray is empty. Please calculate MSE first.")

        best_idx = np.argmin(self.MSEArray)
        best_recon = self.theta_matrix[best_idx]

        # ----------------- Plotting -----------------
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))  # 1 row, 3 columns

        # Normalization based on LAMBDA max
        lambda_max = np.max(self.experiment.opticImage)

        # Left: Best reconstructed image (normalized)
        im0 = axs[0].imshow(best_recon / lambda_max, 
                            extent=(self.experiment.params['Xrange'][0], self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                            cmap='hot', aspect='equal', vmin=0, vmax=1)
        axs[0].set_title(f"Min MSE Reconstruction\nIter {best_idx+1}, MSE={np.min(self.MSEArray):.4f}")
        axs[0].set_xlabel("x (mm)")
        axs[0].set_ylabel("z (mm)")
        plt.colorbar(im0, ax=axs[0])

        # Middle: Ground truth (normalized)
        im1 = axs[1].imshow(self.experiment.opticImage / lambda_max, 
                            extent=(self.experiment.params['Xrange'][0], self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                            cmap='hot', aspect='equal', vmin=0, vmax=1)
        axs[1].set_title(r"Ground Truth ($\lambda$)")
        axs[1].set_xlabel("x (mm)")
        axs[1].set_ylabel("z (mm)")
        plt.colorbar(im1, ax=axs[1])

        # Right: Reconstruction at iter 350
        lastRecon = self.theta_matrix[-1] 
        im2 = axs[2].imshow(lastRecon / lambda_max,
                            extent=(self.experiment.params['Xrange'][0], self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                            cmap='hot', aspect='equal', vmin=0, vmax=1)
        axs[2].set_title(f"Last Reconstruction\nIter {self.numIterations * self.numSubsets}, MSE={np.mean((self.experiment.opticImage - lastRecon) ** 2):.4f}")
        axs[2].set_xlabel("x (mm)")
        axs[2].set_ylabel("z (mm)")
        plt.colorbar(im2, ax=axs[2])

        plt.tight_layout()
        if isSaving:
            now = datetime.now()    
            date_str = now.strftime("%Y_%d_%m_%y")
            SavingFolder = os.path.join(self.saveDir, 'results', f'comparison_MSE_BestANDLastRecon{date_str}.png')
            plt.savefig(SavingFolder, dpi=300)
            print(f"MSE plot saved to {SavingFolder}")
        plt.show()

    def plot_theta_animation(self, vmin=None, vmax=None, duration=5000, save_path=None):
        """
        Show theta iteration animation (for Jupyter) and optionally save it as a GIF.
        
        Parameters:
            matrix_theta: list of (z, x) ndarray, iterative reconstructions
            x: 1D array, x-coordinates (in meters)
            z: 1D array, z-coordinates (in meters)
            vmin, vmax: color limits (optional)
            duration: duration of the animation in milliseconds
            save_path: path to save animation (e.g., 'theta.gif' or 'theta.mp4')
        """
        if len(self.theta_matrix) == 0 or len(self.theta_matrix) == 1:
            raise ValueError("No theta matrix available for animation.")

        frames = np.array(self.theta_matrix)
        num_frames = len(frames)

        interval = max(1, int(duration / num_frames))

        if vmin is None:
            vmin = np.min(frames)
        if vmax is None:
            vmax = np.max(frames)

        fig, ax = plt.subplots(figsize=(5, 5))
        im = ax.imshow(frames[0],
                    extent=(self.experiment.params['Xrange'][0],self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                    vmin=vmin, vmax=vmax,
                    aspect='equal', cmap='hot')

        title = ax.set_title("Iteration 0")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("z (mm)")
        plt.tight_layout()

        def update(frame_idx):
            im.set_array(frames[frame_idx])
            title.set_text(f"Iteration {frame_idx}")
            return [im, title]

        ani = animation.FuncAnimation(fig, update, frames=num_frames, interval=interval, blit=False)

        if save_path:
            if save_path.endswith(".gif"):
                ani.save(save_path, writer="pillow", fps=1000 // interval)
            elif save_path.endswith(".mp4"):
                ani.save(save_path, writer="ffmpeg", fps=1000 // interval)
            else:
                raise ValueError("Unsupported file format. Use .gif or .mp4")
            print(f"Animation saved to {save_path}")

        plt.close(fig)
        plt.rcParams["animation.html"] = "jshtml"
        return HTML(ani.to_jshtml())  

    def plot_SSIM(self, isSaving=True):

        if not self.SSIMArray:
            raise ValueError("SSIMArray is empty. Please calculate SSIM first.")
        
        best_idx = np.argmax(self.SSIMArray)
        
        print(f"Highest SSIM = {np.max(self.SSIMArray):.4f} at iteration {best_idx+1}")

        # Plot SSIM curve
        plt.figure(figsize=(7, 5))
        plt.plot(self.SSIMArray, 'r-', label="SSIM curve")

        # Add blue dashed lines
        plt.axhline(np.max(self.SSIMArray), color='blue', linestyle='--', label=f"Max SSIM = {np.max(self.SSIMArray):.4f}")
        plt.axvline(best_idx+1, color='blue', linestyle='--', label=f"Iteration = {best_idx+1}")

        plt.xlabel("Iteration")
        plt.ylabel("SSIM")
        plt.title("SSIM vs. Iteration")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        if isSaving:
            now = datetime.now()    
            date_str = now.strftime("%Y_%d_%m_%y")
            SavingFolder = os.path.join(self.saveDir, 'results', f'SSIM_plot{date_str}.png')
            plt.savefig(SavingFolder, dpi=300)
            print(f"SSIM plot saved to {SavingFolder}")
        
        plt.show()

    def plot_SSIM_bestRecon(self, isSaving=True):
        
        if not self.SSIMArray:
            raise ValueError("SSIMArray is empty. Please calculate SSIM first.")

        best_idx = np.argmax(self.SSIMArray)
        best_recon = self.theta_matrix[best_idx]

        # ----------------- Plotting -----------------
        fig, axs = plt.subplots(1, 3, figsize=(15, 5))  # 1 row, 3 columns

        # Normalization based on LAMBDA max
        lambda_max = np.max(self.experiment.opticImage)

        # Left: Best reconstructed image (normalized)
        im0 = axs[0].imshow(best_recon / lambda_max, 
                            extent=(self.experiment.params['Xrange'][0], self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                            cmap='hot', aspect='equal', vmin=0, vmax=1)
        axs[0].set_title(f"Max SSIM Reconstruction\nIter {best_idx+1}, SSIM={np.min(self.MSEArray):.4f}")
        axs[0].set_xlabel("x (mm)")
        axs[0].set_ylabel("z (mm)")
        plt.colorbar(im0, ax=axs[0])

        # Middle: Ground truth (normalized)
        im1 = axs[1].imshow(self.experiment.opticImage / lambda_max, 
                            extent=(self.experiment.params['Xrange'][0], self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                            cmap='hot', aspect='equal', vmin=0, vmax=1)
        axs[1].set_title(r"Ground Truth ($\lambda$)")
        axs[1].set_xlabel("x (mm)")
        axs[1].set_ylabel("z (mm)")
        plt.colorbar(im1, ax=axs[1])

        # Right: Reconstruction at iter 350
        lastRecon = self.theta_matrix[-1] 
        im2 = axs[2].imshow(lastRecon / lambda_max,
                            extent=(self.experiment.params['Xrange'][0], self.experiment.params['Xrange'][1], self.experiment.params['Zrange'][1], self.experiment.params['Zrange'][0]),
                            cmap='hot', aspect='equal', vmin=0, vmax=1)
        axs[2].set_title(f"Last Reconstruction\nIter {self.numIterations * self.numSubsets}, SSIM={self.SSIMArray[-1]:.4f}")
        axs[2].set_xlabel("x (mm)")
        axs[2].set_ylabel("z (mm)")
        plt.colorbar(im2, ax=axs[2])

        plt.tight_layout()
        if isSaving:
            now = datetime.now()    
            date_str = now.strftime("%Y_%d_%m_%y")
            SavingFolder = os.path.join(self.saveDir, 'results', f'comparison_SSIM_BestANDLastRecon{date_str}.png')
            plt.savefig(SavingFolder, dpi=300)
            print(f"SSIM plot saved to {SavingFolder}")
        plt.show()

    ### ALGORITHMS IMPLEMENTATION ###

    @staticmethod
    def _MLEM_CPU(A_matrix, y, numIterations):
        if os.cpu_count() > 1:
            print(f"Using {os.cpu_count()} CPU cores for MLEM.")
            try:
                recons = IterativeRecon._MLEM_CPU_multi(A_matrix, y, numIterations)
                if recons is None or len(recons) == 0:
                    raise ValueError("Multi-core MLEM returned empty result.")
            except Exception as e:
                print(f"Error using multi-core MLEM: {e}. Falling back to optimized MLEM.")
                try:
                    recons = IterativeRecon._MLEM_CPU_opti(A_matrix, y, numIterations)
                    if recons is None or len(recons) == 0:
                        raise ValueError("Optimized MLEM returned empty result.")
                except Exception as e:
                    print(f"Error using optimized MLEM: {e}. Falling back to basic MLEM.")
                    try:
                        recons = IterativeRecon._MLEM_CPU_basic(A_matrix, y, numIterations)
                        if recons is None or len(recons) == 0:
                            raise ValueError("Basic MLEM returned empty result.")
                    except Exception as e:
                        print(f"Error using basic MLEM: {e}. All methods failed.")
                        raise
        else:
            print("Using optimized MLEM for CPU.")
            try:
                recons = IterativeRecon._MLEM_CPU_opti(A_matrix, y, numIterations)
                if recons is None or len(recons) == 0:
                    raise ValueError("Optimized MLEM returned empty result.")
            except Exception as e:
                print(f"Error using optimized MLEM: {e}. Falling back to basic MLEM.")
                try:
                    recons = IterativeRecon._MLEM_CPU_basic(A_matrix, y, numIterations)
                    if recons is None or len(recons) == 0:
                        raise ValueError("Basic MLEM returned empty result.")
                except Exception as e:
                    print(f"Error using basic MLEM: {e}. All methods failed.")
                    raise

        return recons

    @staticmethod
    def _MLEM_GPU(A_matrix, y, numIterations):
        if not torch.cuda.is_available():
            print("CUDA not available, falling back to CPU.")
            return IterativeRecon._MLEM_CPU(A_matrix, y, numIterations)

        try:
            if torch.cuda.device_count() > 1:
                print(f"Using {torch.cuda.device_count()} GPUs for MLEM.")
                recons = IterativeRecon._MLEM_GPU_multi(A_matrix, y, numIterations)
                if recons is None or len(recons) == 0:
                    raise ValueError("Multi-GPU MLEM returned empty result.")
            else:
                print("Using single GPU for MLEM.")
                recons = IterativeRecon._MLEM_GPU_basic(A_matrix, y, numIterations)
                if recons is None or len(recons) == 0:
                    raise ValueError("Single GPU MLEM returned empty result.")

        except Exception as e:
            print(f"Error using GPU MLEM: {e}. Falling back to CPU.")
            try:
                recons = IterativeRecon._MLEM_CPU(A_matrix, y, numIterations)
                if recons is None or len(recons) == 0:
                    raise ValueError("CPU MLEM returned empty result.")
            except Exception as e:
                print(f"Error using CPU MLEM: {e}. All methods failed.")
                raise

        if not isinstance(recons[0], np.ndarray):
            recons = [theta.cpu().numpy() for theta in recons]

        return recons

    @staticmethod
    def _MLEM_GPU_basic(A_matrix, y, numIteration):
        """
        This method implements the MLEM algorithm using PyTorch for GPU acceleration.
        Parameters:
            A_matrix: 4D numpy array (time, z, x, nScans)
            y: 2D numpy array (time, nScans)
            numIteration: number of iterations for the MLEM algorithm
        """
        #TODO: Only return the last theta if isSavingTheta is False
        A_matrix_torch = torch.tensor(A_matrix, dtype=torch.float32).cuda()  # shape: (T, Z, X, N)
        y_torch = torch.tensor(y, dtype=torch.float32).cuda()                # shape: (T, N)

        # Initialize variables
        T, Z, X, N = A_matrix.shape

        # flat
        A_flat = A_matrix_torch.permute(0, 3, 1, 2).reshape(T * N, Z * X)     # shape: (T * N, Z * X)
        y_flat = y_torch.reshape(-1)                                          # shape: (T * N, )

        # Step 1: start from a strickly positive image theta^(0)
        theta_0 = torch.ones((Z, X), dtype=torch.float32, device='cuda')      # shape: (Z, X)
        matrix_theta_torch = [theta_0]
        # matrix_theta_from_gpu = []

        # Compute normalization factor: A^T * 1
        normalization_factor = A_matrix_torch.sum(dim=(0, 3))                # shape: (Z, X)
        normalization_factor_flat = normalization_factor.reshape(-1)         # shape: (Z * X, )

        # EM iterative update
        for _ in trange(numIteration, desc=f"ML-EM Reshape Iteration (GPU {torch.cuda.current_device()})"):

            theta_p = matrix_theta_torch[-1]                                 # shape: (Z, X)

            # Step 2: Forward projection of current estimate : q = A * theta + b (acc with GPU)
            theta_p_flat = theta_p.reshape(-1)                               # shape: (Z * X, )
            q_flat = A_flat @ theta_p_flat                                   # shape: (T * N, )

            # Step 3: Current error estimate : compute ratio e = m / q
            e_flat = y_flat / (q_flat + torch.finfo(torch.float32).tiny)                                # shape: (T * N, )

            # Step 4: Backward projection of the error estimate : c = A.T * e (acc with GPU)
            c_flat = A_flat.T @ e_flat                                       # shape: (Z * X, )

            # Step 5: Multiplicative update of current estimate
            theta_p_plus_1_flat = (theta_p_flat / (normalization_factor_flat + torch.finfo(torch.float32).tiny)) * c_flat

            matrix_theta_torch.append(theta_p_plus_1_flat.reshape(Z, X))      # shape: (Z, X)
        
        return matrix_theta_torch  # Return the list of tensors
         
    @staticmethod
    def _MLEM_CPU_basic(A_matrix, y, numIteration):
        """
        This method implements the MLEM algorithm using basic numpy operations.
        Parameters:
            A_matrix: 4D numpy array (time, z, x, nScans)
            y: 2D numpy array (time, nScans)
            numIteration: number of iterations for the MLEM algorithm
        """
        #TODO: Only return the last theta if isSavingTheta is False

        # Initialize variables
        q_p = np.zeros((A_matrix.shape[0], A_matrix.shape[3]))  # shape : (t, i)
        c_p = np.zeros((A_matrix.shape[1], A_matrix.shape[2]))  # shape : (z, x)

        # Step 1: start from a strickly positive image theta^(0)
        theta_p_0 = np.ones((A_matrix.shape[1], A_matrix.shape[2]))  # initial theta^(0)
        matrix_theta = [theta_p_0]  # store theta 

        # Compute normalization factor: A^T * 1
        normalization_factor = np.sum(A_matrix, axis=(0, 3))  # shape: (z, x)

        # EM iterative update
        for _ in trange(numIteration, desc="ML-EM Iteration (CPU basic)"):

            theta_p = matrix_theta[-1]

            # Step 1: Forward projection of current estimate : q = A * theta + b
            for _t in range(A_matrix.shape[0]):
                for _n in range(A_matrix.shape[3]):
                    q_p[_t, _n] = np.sum(A_matrix[_t, :, :, _n] * theta_p)
            
            # Step 2: Current error estimate : compute ratio e = m / q
            e_p = y / (q_p + 1e-8)  # 避免除零
            
            # Step 3: Backward projection of the error estimate : c = A.T * e
            for _z in range(A_matrix.shape[1]):
                for _x in range(A_matrix.shape[2]):
                    c_p[_z, _x] = np.sum(A_matrix[:, _z, _x, :] * e_p)
            
            # Step 4: Multiplicative update of current estimate
            theta_p_plus_1 = theta_p / (normalization_factor + 1e-8) * c_p
            
            # Step 5: Store current theta
            matrix_theta.append(theta_p_plus_1)
        
        return matrix_theta  # Return the list of numpy arrays

    @staticmethod
    def _MLEM_CPU_multi(A_matrix, y, numIteration):
        """
        This method implements the MLEM algorithm using multi-threading with Numba.
        Parameters:
            A_matrix: 4D numpy array (time, z, x, nScans)
            y: 2D numpy array (time, nScans)
            numIteration: number of iterations for the MLEM algorithm
        """
        #TODO: Only return the last theta if isSavingTheta is False
        numba.set_num_threads(os.cpu_count())
        print(f"Number of threads : {numba.config.NUMBA_DEFAULT_NUM_THREADS}")
        q_p = np.zeros((A_matrix.shape[0], A_matrix.shape[3]))  # shape : (t, i)
        c_p = np.zeros((A_matrix.shape[1], A_matrix.shape[2]))  # shape : (z, x)

        # Step 1: start from a strickly positive image theta^(0)
        theta_p_0 = np.ones((A_matrix.shape[1], A_matrix.shape[2]))
        matrix_theta = [theta_p_0]

        # Compute normalization factor: A^T * 1
        normalization_factor = np.sum(A_matrix, axis=(0, 3))  # shape: (z, x)

        # EM iterative update
        for _ in trange(numIteration, desc="ML-EM Iteration (CPU Multithread)"):
            
            theta_p = matrix_theta[-1]

            # Step 1: Forward projection of current estimate : q = A * theta + b (acc with njit)
            IterativeRecon._forward_projection(A_matrix, theta_p, q_p)

            # Step 2: Current error estimate : compute ratio e = m / q
            e_p = y / (q_p + 1e-8)

            # Step 3: Backward projection of the error estimate : c = A.T * e (acc with njit)
            IterativeRecon._backward_projection(A_matrix, e_p, c_p)

            # Step 4: Multiplicative update of current estimate
            theta_p_plus_1 = theta_p / (normalization_factor + 1e-8) * c_p

            # Step 5: Store current theta
            matrix_theta.append(theta_p_plus_1)

    @staticmethod
    def _MLEM_CPU_opti(A_matrix, y, numIteration):
        """
        This method implements the MLEM algorithm using optimized numpy operations.
        Parameters:
            A_matrix: 4D numpy array (time, z, x, nScans)
            y: 2D numpy array (time, nScans)
            numIteration: number of iterations for the MLEM algorithm
        """
        #TODO: Only return the last theta if isSavingTheta is False
        # Initialize variables
        T, Z, X, N = A_matrix.shape

        A_flat = A_matrix.astype(np.float32).transpose(0, 3, 1, 2).reshape(T * N, Z * X)         # shape: (T * N, Z * X)
        y_flat = y.astype(np.float32).reshape(-1)                                                # shape: (T * N, )

        # Step 1: start from a strickly positive image theta^(0)
        theta_0 = np.ones((Z, X), dtype=np.float32)              # shape: (Z, X)
        matrix_theta = [theta_0]

        # Compute normalization factor: A^T * 1
        normalization_factor = np.sum(A_matrix, axis=(0, 3)).astype(np.float32)                  # shape: (Z, X)
        normalization_factor_flat = normalization_factor.reshape(-1) 

        # EM iterative update
        for p in trange(numIteration, desc="ML-EM Reshape Iteration"):
                
            theta_p = matrix_theta[-1]

            # Step 2: Forward projection of current estimate : q = A * theta + b (acc with njit)
            theta_p_flat = theta_p.reshape(-1)                                                    # shape: (Z * X, )
            q_flat = A_flat @ theta_p_flat                                                        # shape: (T * N)

            # Step 3: Current error estimate : compute ratio e = m / q
            e_flat = y_flat / (q_flat + np.finfo(np.float32).tiny)                                         # shape: (T * N, )
            # np.float32(1e-8)
            
            # Step 4: Backward projection of the error estimate : c = A.T * e (acc with njit)
            c_flat = A_flat.T @ e_flat                                                            # shape: (Z * X, )

            # Step 5: Multiplicative update of current estimate
            theta_p_plus_1_flat = theta_p_flat / (normalization_factor_flat + np.finfo(np.float32).tiny) * c_flat
            
            
            # Step 5: Store current theta
            matrix_theta.append(theta_p_plus_1_flat.reshape(Z, X))

    @staticmethod   
    def _MLEM_GPU_multi(A_matrix, y, numIteration):
        """
        This method implements the MLEM algorithm using PyTorch for GPU acceleration and multi-threading.
        Parameters:
            A_matrix: 4D numpy array (time, z, x, nScans)
            y: 2D numpy array (time, nScans)
            numIteration: number of iterations for the MLEM algorithm
        """
        #TODO: implement multi-threading with GPU
        #TODO: Only return the last theta if isSavingTheta is False
        pass

    @staticmethod
    @njit(parallel=True)
    def _forward_projection(A_matrix, theta_p, q_p):
        t_dim, z_dim, x_dim, i_dim = A_matrix.shape
        for _t in prange(t_dim):
            for _n in range(i_dim):
                total = 0.0
                for _z in range(z_dim):
                    for _x in range(x_dim):
                        total += A_matrix[_t, _z, _x, _n] * theta_p[_z, _x]
                q_p[_t, _n] = total

    @staticmethod
    @njit(parallel=True)
    def _backward_projection(A_matrix, e_p, c_p):
        t_dim, z_dim, x_dim, n_dim = A_matrix.shape
        for _z in prange(z_dim):
            for _x in range(x_dim):
                total = 0.0
                for _t in range(t_dim):
                    for _n in range(n_dim):
                        total += A_matrix[_t, _z, _x, _n] * e_p[_t, _n]
                c_p[_z, _x] = total

class AnalyticRecon(Recon):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.MSE = []
        self.SSIM = []
        self.I_recon = None
        self.I_ref = self.experiment.OpticImage.phantom

    def run(self, reconType):
        """
        This method is a placeholder for the analytic reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(reconType == ProcessType.CASToR):
            raise NotImplementedError("CASToR analytic reconstruction is not implemented yet.")
        elif(reconType == ProcessType.PYTHON):
            self._analyticReconPython()
        else:
            raise ValueError(f"Unknown analytic reconstruction type: {reconType}")
        self._getMSE()
        self._getSSIM()

    def _analyticReconPython(self, analyticType):
        """
        This method is a placeholder for the analytic reconstruction process in Python.
        It currently does not perform any operations but serves as a template for future implementations.
        
        Parameters:
            analyticType: The type of analytic reconstruction to perform (default is iFOURIER).
        """
        if analyticType == AnalyticType.iFOURIER:
            self._iFourierRecon()
        elif analyticType == AnalyticType.iRADON:
            self._iRadonRecon()
        else:
            raise ValueError(f"Unknown analytic type: {analyticType}")
    
    def _iFourierRecon(self, s_reconstructed):
        """
        Reconstruction d'image utilisant la transformation de Fourier inverse.

        :param s_reconstructed: Signal reconstruit dans le domaine fréquentiel.
        :return: Image reconstruite dans le domaine spatial.
        """
        # Appliquer la transformation de Fourier inverse
        image_reconstructed = np.fft.ifft2(s_reconstructed)

        # Prendre la partie réelle de l'image reconstruite
        self.I_recon = np.real(image_reconstructed)


    def _iRadonRecon(self):
        """
        Reconstruction d'image utilisant la méthode iRadon.

        :return: Image reconstruite.
        """
        # Initialisation de l'image reconstruite
        I_rec = np.zeros((len(self.experiment.OpticImage.x), len(self.experiment.OpticImage.z)), dtype=complex)

        # Transformation de Fourier du signal
        s_tilde = np.fft.fft(self.experiment.AOsignal, axis=0)

        # Extraction des angles et des fréquences spatiales
        theta = [acoustic_field.angle for acoustic_field in self.experiment.AcousticFields]
        f_s = [acoustic_field.f_s for acoustic_field in self.experiment.AcousticFields]

        # Calcul des coordonnées transformées et intégrales
        for i, th in enumerate(theta):
            x_prime = self.experiment.OpticImage.x[:, np.newaxis] * np.cos(th) - self.experiment.OpticImage.z[np.newaxis, :] * np.sin(th)
            z_prime = self.experiment.OpticImage.z[np.newaxis, :] * np.cos(th) + self.experiment.OpticImage.x[:, np.newaxis] * np.sin(th)

            # Première intégrale : partie réelle
            for j, fs in enumerate(f_s):
                integrand = s_tilde[i, j] * np.exp(2j * np.pi * (x_prime * fs + z_prime * fs))
                integral = trapz(integrand * fs, fs)
                I_rec += 2 * np.real(integral)

        # Deuxième intégrale : partie centrale
        for i, th in enumerate(theta):
            x_prime = self.experiment.OpticImage.x[:, np.newaxis] * np.cos(th) - self.experiment.OpticImage.z[np.newaxis, :] * np.sin(th)
            z_prime = self.experiment.OpticImage.z[np.newaxis, :] * np.cos(th) + self.experiment.OpticImage.x[:, np.newaxis] * np.sin(th)

            # Filtrer les fréquences spatiales pour ne garder que celles inférieures ou égales à f_s_max
            filtered_f_s = np.array(f_s)[np.array(f_s) <= self.f_s_max]
            integrand = s_tilde[i, np.array(f_s) == 0] * np.exp(2j * np.pi * z_prime * filtered_f_s)
            integral = trapz(integrand * filtered_f_s, filtered_f_s)
            I_rec += integral

        return I_rec

    def _getMSE(self):
        """
        Calcule l'erreur quadratique moyenne (MSE) entre l'image reconstruite et l'image de référence.

        :return: Valeur du MSE.
        """
        if self.I_recon is None:
            raise ValueError("L'image reconstruite n'est pas disponible. Veuillez exécuter la reconstruction avant de calculer le MSE.")
        self.MSE = np.mean((self.I_recon - self.I_ref) ** 2)

    def _getSSIM(self):
        """
        Calcule l'indice de similarité structurelle (SSIM) entre l'image reconstruite et l'image de référence.

        :return: Valeur du SSIM.
        """
        if self.I_recon is None:
            raise ValueError("L'image reconstruite n'est pas disponible. Veuillez exécuter la reconstruction avant de calculer le SSIM.")
        self.SSIM = ssim(self.I_recon, self.I_ref, data_range=self.I_ref.max() - self.I_ref.min())

class BayesianRecon(Recon):
    """
    This class implements the Bayesian reconstruction process.
    It currently does not perform any operations but serves as a template for future implementations.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theta_matrix = []

    def run(self, reconType):
        """
        This method is a placeholder for the Bayesian reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(reconType == ProcessType.CASToR):
            self._bayesianReconCASToR()
        elif(reconType == ProcessType.PYTHON):
            self._bayesianReconPython()
        else:
            raise ValueError(f"Unknown Bayesian reconstruction type: {reconType}")
        
    def _bayesianReconCASToR(self):
        pass

    def _bayesianReconPython(self):
        pass

    @staticmethod
    def compute_grad_hess_huber_sparse(theta_flat, index, values, delta=0.1):
        """
        Compute the gradient and Hessian of the Huber penalty function for sparse data.
        Parameters:
            theta_flat (torch.Tensor): Flattened parameter vector.
            index (torch.Tensor): Indices of the sparse matrix in COO format.
            values (torch.Tensor): Values of the sparse matrix in COO format.
            delta (float): Threshold for the Huber penalty.
        Returns:
            grad_U (torch.Tensor): Gradient of the penalty function.
            hess_U (torch.Tensor): Hessian of the penalty function.
            U_value (float): Value of the penalty function.
        """
        
        j_idx, k_idx = index
        diff = theta_flat[j_idx] - theta_flat[k_idx]
        abs_diff = torch.abs(diff)

        # Huber penalty (potential function) 
        psi_pair = torch.where(abs_diff > delta,
                            delta * abs_diff - 0.5 * delta ** 2,
                            0.5 * diff ** 2)
        psi_pair = values * psi_pair  

        # Huber gradient
        grad_pair = torch.where(abs_diff > delta,
                                delta * torch.sign(diff),
                                diff)
        grad_pair = values * grad_pair

        # Huber Hessian
        hess_pair = torch.where(abs_diff > delta,
                                torch.zeros_like(diff),
                                torch.ones_like(diff))
        hess_pair = values * hess_pair

        grad_U = scatter(grad_pair, j_idx, dim=0, dim_size=theta_flat.shape[0], reduce='sum')
        hess_U = scatter(hess_pair, j_idx, dim=0, dim_size=theta_flat.shape[0], reduce='sum')

        # Total penalty energy
        U_value = 0.5 * psi_pair.sum()  

        return grad_U, hess_U, U_value
    
    @staticmethod
    def build_adjacency_sparse(Z, X,corner,face,device):
        rows = []
        cols = []
        weights = []

        for z in range(Z):
            for x in range(X):
                j = z * X + x
                for dz in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dz == 0 and dx == 0:
                            continue
                        nz, nx = z + dz, x + dx
                        if 0 <= nz < Z and 0 <= nx < X:
                            k = nz * X + nx
                            weight = corner if abs(dz) + abs(dx) == 2 else face
                            rows.append(j)
                            cols.append(k)
                            weights.append(weight)
    
        index = torch.tensor([rows, cols], device=device)
        values = torch.tensor(weights, dtype=torch.float32, device=device)
        index, values = coalesce(index, values, m=Z*X, n=Z*X)
        return index, values  # COO 格式：用于稀疏邻接

    @staticmethod  
    def MAP_stop(A_matrix, y, device='cuda'):
        """
        Maximum A Posteriori (MAP) estimation for Bayesian reconstruction.
        This method computes the MAP estimate of the parameters given the data.
        """
        A_matrix_torch = torch.tensor(A_matrix, dtype=torch.float32).to(device)
        y_torch = torch.tensor(y, dtype=torch.float32).to(device)

        T, Z, X, N = A_matrix.shape
        J = Z * X

        A_flat = A_matrix_torch.permute(0, 3, 1, 2).reshape(T * N, Z * X)
        y_flat = y_torch.reshape(-1)

        theta_0 = torch.ones((Z, X), dtype=torch.float32, device=device)
        matrix_theta_torch = []
        matrix_theta_torch = [theta_0]
        matrix_theta_from_gpu_MAPEM = []
        matrix_theta_from_gpu_MAPEM = [theta_0.cpu().numpy()]

        normalization_factor = A_matrix_torch.sum(dim=(0, 3))                # (Z, X)
        normalization_factor_flat = normalization_factor.reshape(-1)         # (Z*X,)

        adj_index, adj_values = BayesianRecon.build_adjacency_sparse(Z, X)

        beta = 0.10
        delta = 0.10
        previous = -np.inf

        for p in trange(500000, desc="5.1 MAP-EM (Sparse Huber) + STOP condtion (penalized log-likelihood)"):
            theta_p = matrix_theta_torch[-1]
            theta_p_flat = theta_p.reshape(-1)

            q_flat = A_flat @ theta_p_flat
            e_flat = (y_flat - q_flat) / (q_flat + torch.finfo(torch.float32).tiny)
            c_flat = A_flat.T @ e_flat

            grad_U, hess_U, U_value = BayesianRecon.compute_grad_hess_huber_sparse(theta_p_flat, adj_index, adj_values, delta=delta)

            denom = normalization_factor_flat + theta_p_flat * beta * hess_U
            num = theta_p_flat * (c_flat - beta * grad_U)

            theta_p_plus_1_flat = theta_p_flat + num / (denom + torch.finfo(torch.float32).tiny)
            theta_p_plus_1_flat = torch.clamp(theta_p_plus_1_flat, min=0)

            theta_next = theta_p_plus_1_flat.reshape(Z, X)
            #matrix_theta_torch.append(theta_next) # save theta in GPU
            matrix_theta_torch[-1] = theta_next    # do not save theta in GPU

            if p % 1 == 0:
                matrix_theta_from_gpu_MAPEM.append(theta_next.cpu().numpy())

            # === compute penalized log-likelihood (without term ln(m_i !) inside) ===
            # log-likelihood (without term ln(m_i !) inside)
            # log_likelihood = (torch.where(q_flat > 0, y_flat * torch.log(q_flat), torch.zeros_like(q_flat)) - q_flat).sum()
            # log_likelihood = (y_flat * torch.log(q_flat) - q_flat).sum()
            log_likelihood = (y_flat * ( torch.log( q_flat + torch.finfo(torch.float32).tiny ) ) - (q_flat + torch.finfo(torch.float32).tiny)).sum()

            # penalized log-likelihood
            penalized_log_likelihood = log_likelihood - beta * U_value

            if p == 0 or (p+1) % 100 == 0:
                current = penalized_log_likelihood.item()

                if current<=previous:
                    nb_false_successive = nb_false_successive + 1

                else:
                    nb_false_successive = 0
                
                print(f"Iter {p+1}: lnL without term ln(m_i !) inside={log_likelihood.item():.8e}, Gibbs energy function U={U_value.item():.4e}, penalized lnL without term ln(m_i !) inside={penalized_log_likelihood.item():.8e}, p lnL (current {current:.8e} - previous {previous:.8e} > 0)={(current-previous>0)}, nb_false_successive={nb_false_successive}")
                
                #if nb_false_successive >= 25:
                    #break
            
                previous = penalized_log_likelihood.item()

class DeepLearningRecon(Recon):
    """
    This class implements the deep learning reconstruction process.
    It currently does not perform any operations but serves as a template for future implementations.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.model = None  # Placeholder for the deep learning model
        self.theta_matrix = []

    def run(self, reconType):
        """
        This method is a placeholder for the deep learning reconstruction process.
        It currently does not perform any operations but serves as a template for future implementations.
        """
        if(reconType == ProcessType.CASToR):
            self._deepLearningReconCASToR()
        elif(reconType == ProcessType.PYTHON):
            self._deepLearningReconPython()
        else:
            raise ValueError(f"Unknown deep learning reconstruction type: {reconType}")

    def _deepLearningReconCASToR(self):
        pass

    def _deepLearningReconPython(self):
        pass