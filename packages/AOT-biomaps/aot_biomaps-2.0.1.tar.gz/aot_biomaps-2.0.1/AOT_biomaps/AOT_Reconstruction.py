import subprocess
import os
import numpy as np
from abc import ABC, abstractmethod
import enum
import AOT_biomaps
import numpy as np
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
    Algebraic = 'algebraic'
    """A reconstruction method using algebraic techniques."""
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
    \[
    p(u, v) = p(u - v)
    \]
    - Quadratic: \(p(u, v) = \\frac{1}{2} (u - v)^2\)
    - Geman-McClure: \(p(u, v, d) = \\frac{(u - v)^2}{d^2 + (u - v)^2}\)
    - Hebert-Leahy: \(p(u, v, m) = \log\left(1 + \\frac{(u - v)^2}{m^2}\\right)\)
    - Green's log-cosh: \(p(u, v, d) = \log(\cosh((u - v) / d))\)
    - Huber piecewise: \(p(u, v, d) = d \cdot |u - v| - \\frac{1}{2} d^2\) if \(|u - v| > d\), else \(0.5 \cdot (u - v)^2\)
    - Nuyts relative: \(p(u, v, g) = \\frac{(u - v)^2}{u + v + g \cdot |u - v|}\)
    """
    QUADRATIC = 'QUADRATIC'
    """
    Quadratic potential:
    \[
    p(u, v) = \\frac{1}{2} (u - v)^2
    \]

    Reference: Geman and Geman, IEEE Trans. Pattern Anal. Machine Intell., vol. PAMI-6, pp. 721-741, 1984.
    """

    GEMAN_MCCLURE = 'GEMAN_MCCLURE'
    """
    Geman-McClure potential:
    \[
    p(u, v, d) = \\frac{(u - v)^2}{d^2 + (u - v)^2}
    \]

    The parameter 'd' can be set using the 'deltaGMC' keyword.

    Reference: Geman and McClure, Proc. Amer. Statist. Assoc., 1985.
    """

    HEBERT_LEAHY = 'HEBERT_LEAHY'
    """
    Hebert-Leahy potential:
    \[
    p(u, v, m) = \log\left(1 + \\frac{(u - v)^2}{m^2}\\right)
    \]

    The parameter 'm' can be set using the 'muHL' keyword.

    Reference: Hebert and Leahy, IEEE Trans. Med. Imaging, vol. 8, pp. 194-202, 1989.
    """

    GREEN_LOGCOSH = 'GREEN_LOGCOSH'
    """
    Green's log-cosh potential:
    \[
    p(u, v, d) = \log(\cosh((u - v) / d))
    \]

    The parameter 'd' can be set using the 'deltaLogCosh' keyword.

    Reference: Green, IEEE Trans. Med. Imaging, vol. 9, pp. 84-93, 1990.
    """

    HUBER_PIECEWISE = 'HUBER_PIECE_WISE'
    """
    Huber piecewise potential:
    \[
    p(u, v, d) =
    \begin{cases}
    d \cdot |u - v| - \\frac{1}{2} d^2 & \text{if } |u - v| > d \\
    0.5 \cdot (u - v)^2 & \text{if } |u - v| \leq d
    \end{cases}
    \]

    The parameter 'd' can be set using the 'deltaHuber' keyword.

    Reference: e.g. Mumcuoglu et al, Phys. Med. Biol., vol. 41, pp. 1777-1807, 1996.
    """

    NUYTS_RELATIVE = 'NUYTS_RELATIVE'
    """
    Nuyts relative potential:
    \[
    p(u, v, g) = \\frac{(u - v)^2}{u + v + g \cdot |u - v|}
    \]

    The parameter 'g' can be set using the 'gammaRD' keyword.

    Reference: Nuyts et al, IEEE Trans. Nucl. Sci., vol. 49, pp. 56-60, 2002.
    """

class ProcessType(enum.Enum):
    CASToR = 'CASToR'
    PYTHON = 'PYTHON'

class Recon:
    def __init__(self, experiment, saveDir):
        self.reconOpticImage = None
        self.type = self.experiment.params.reconstruction['ReconType']
        self.experiment = experiment
        self.saveDir = saveDir

        if type(self.type) is not ReconType:
            raise TypeError(f"Recon type must be of type {ReconType}")
        if type(self.experiment) is not AOT_biomaps.AOT_experiment.Experiment:
            raise TypeError(f"Experiment must be of type {AOT_biomaps.AOT_experiment.Experiment}")

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

