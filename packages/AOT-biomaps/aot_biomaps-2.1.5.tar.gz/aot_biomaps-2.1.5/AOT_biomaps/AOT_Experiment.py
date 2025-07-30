
from .Settings import *
from .AOT_Optic import *
from .AOT_Acoustic import *
import os
import ast
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import matplotlib as mpl
from datetime import datetime
from tqdm import trange
from enum import Enum
from .config import config

class Experiment():
    def __init__(self, params):
        self.params = params
        self.OpticImage = AOT_biomaps.AOT_Optic.Phantom(params=params)
        self.AOsignal = None
        self.AcousticFields = None

        if type(params) != AOT_biomaps.Settings.Params:
            raise TypeError("params must be an instance of the Params class")
        
class Focus(Experiment):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
       
class Tomography(Experiment):

    def __init__(self, acousticType = AOT_biomaps.AOT_Acoustic.WaveType.StructuredWave ,fieldParamPath=None, fieldDataPath = None, formatSave = AOT_biomaps.AOT_Acoustic.FormatSave.HDR_IMG, **kwargs):
        super().__init__(**kwargs)

        if fieldParamPath is None:
            raise ValueError("fieldParamPath must be provided for Tomography experiment")
        if type(acousticType).__name__ != "WaveType":
            raise TypeError("acousticType must be an instance of the WaveType class")
        self.TypeAcoustic = acousticType
        self.FormatSave = formatSave
        self.fieldDataPath = fieldDataPath
        self.AcousticFields = self._generate_system_matrix(fieldDataPath, fieldParamPath)
        self.OpticImage = AOT_biomaps.AOT_Optic.Phantom(params=self.params)
        self.AOsignal = self._generate_AO_signal()

        if type(self.params)!= AOT_biomaps.Settings.Params:
            raise TypeError("params must be an instance of the Params class")
        
    def _generate_system_matrix(self, fieldDataPath, fieldParamPath):
        """
        Generate the system matrix for the structured wave.

        Args:
            fieldDataPath: Path to save the generated fields.
            fieldParamPath: Path to the field parameters file.
            params: Parameters object containing simulation settings.

        Returns:
            systemMatrix: A numpy array of the generated fields.
        """
        if self.TypeAcoustic.value == AOT_biomaps.AOT_Acoustic.WaveType.StructuredWave.value:
            return self._generate_system_matrixSTRUCT(fieldDataPath, fieldParamPath)
        else:
            raise ValueError("Unsupported wave type.")
        
    def _generate_system_matrixSTRUCT(self, fieldDataPath, fieldParamPath):
        if not os.path.exists(fieldParamPath):
            raise FileNotFoundError(f"Field parameter file {fieldParamPath} not found.")
        if not fieldDataPath is None:
            os.makedirs(fieldDataPath, exist_ok=True)
        listAcousticFields = []
        patternList = []
        with open(fieldParamPath, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if not line:
                    continue  # skip empty lines

                try:
                    # Sécurise l'évaluation en supprimant accès à builtins
                    parsed = eval(line, {"__builtins__": None})

                    if isinstance(parsed, tuple) and len(parsed) == 2:
                        coords, angles = parsed
                        for angle in angles:
                            patternList.append([*coords, angle])
                    else:
                        raise ValueError("Ligne inattendue (pas un tuple de deux éléments)")

                except Exception as e:
                    print(f"Erreur de parsing sur la ligne : {line}\n{e}")

        if config.get_process() == 'gpu':
            print("Using GPU for computation.")
        else:
            print("Using CPU for computation.")
        progress_bar = trange(1,len(patternList), desc="Generating system matrix")

        for i in progress_bar:
            pattern = patternList[i]
            if len(pattern) != 5:
                raise ValueError(f"Invalid pattern format: {pattern}. Expected 5 values.")
            # Initialisation de l'objet AcousticField
            AcousticField = AOT_biomaps.AOT_Acoustic.StructuredWave(
                angle_deg=pattern[4],
                space_0=pattern[0],
                space_1=pattern[1],
                move_head_0_2tail=pattern[2],
                move_tail_1_2head=pattern[3],
                params=self.params
            )

            if fieldDataPath is None:
                pathField = None
            else:
                pathField = os.path.join(fieldDataPath, os.path.basename(AcousticField.getName_field() + self.FormatSave.value))

            if not pathField is None and os.path.exists(pathField):
                    progress_bar.set_postfix_str(f"Loading field - {AcousticField.getName_field()}")
                    AcousticField.load_field(fieldDataPath,  self.FormatSave)
            
            elif pathField is None or not os.path.exists(pathField):
                progress_bar.set_postfix_str(f"Generating field - {AcousticField.getName_field()}")
                AcousticField.generate_field()

                progress_bar.set_postfix_str(f"Calculating squared envelope of the field - {AcousticField.getName_field()}")
                AcousticField.calculate_envelope_squared()

                progress_bar.set_postfix_str(f"Saving system matrix - {AcousticField.getName_field()}")
            
            if not pathField is None and not os.path.exists(pathField):
                os.makedirs(os.path.dirname(pathField), exist_ok=True) 
                AcousticField.save_field(fieldDataPath)

            listAcousticFields.append(AcousticField)
            # Réinitialiser le texte de la barre de progression pour l'itération suivante
            progress_bar.set_postfix_str("")
   
        return listAcousticFields
    
    def _generate_AO_signal(self):
        if self.AcousticFields is None:
            raise ValueError("AcousticFields is not initialized. Please generate the system matrix first.")
        # for field in self.AcousticFields:
        #     print(field)
        #check if all AcousticFields.field have the same shape
        if not all(field.enveloppe.shape == self.AcousticFields[0].enveloppe.shape for field in self.AcousticFields):
            minShape = min([field.enveloppe.shape[0] for field in self.AcousticFields])
            self.cutAcousticFields(minShape*self.params['fs_aq'])
        else:
            shape_field = self.AcousticFields[0].enveloppe.shape

        AOsignal = np.zeros((shape_field[0], len(self.AcousticFields)), dtype=np.float32)

        for i in trange(len(self.AcousticFields), desc="Generating AO Signal"):
            for t in range(self.AcousticFields[i].enveloppe.shape[0]):
                interaction = self.OpticImage.phantom * self.AcousticFields[i].enveloppe[t, :, :]
                AOsignal[t,i] = np.sum(interaction)
        
        return AOsignal
    

    def cutAcousticFields(self,max_t,min_t=0,saveFields=False):
      
        min_sample = int(np.floor(min_t * float(self.params.acoustic['f_AQ'])))
        max_sample = int(np.floor(max_t * float(self.params.acoustic['f_AQ'])))

        print(f"Cutting fields from {min_sample} to {max_sample} samples.")
        if min_sample < 0 or max_sample < 0:
            raise ValueError("min_sample and max_sample must be non-negative integers.")
        if min_sample >= max_sample:
            raise ValueError("min_sample must be less than max_sample.")
        
        if not self.AcousticFields:
            raise ValueError("AcousticFields is empty. Cannot cut fields.")
        
        for i in trange(len(self.AcousticFields), desc="Cutting Acoustic Fields"):
            field = self.AcousticFields[i]
            if field.field.shape[0] < max_sample:
                raise ValueError(f"Field {field.getName_field()} has an invalid shape: {field.enveloppe.shape}. Expected shape to be at least ({max_sample},).")
            self.AcousticFields[i].enveloppe = field.enveloppe[min_sample:max_sample, :, :]
            self.AcousticFields[i].field = field.field[min_sample:max_sample, :, :]

        self.AOsignal = self._generate_AO_signal()

        if saveFields:
            self._saveSMatrixForCastor(self.fieldDataPath)


    def _saveSMatrixForCastor(self, save_directory):
        for i in trange(len(self.AcousticFields), desc="Saving Acoustic Fields"):
            field = self.AcousticFields[i]
            field.save_field(save_directory,formatSave = self.FormatSave)

    def _saveAOsignalForCastor(self,save_directory):
        """
        Sauvegarde le signal AO au format .cdf et .cdh (comme dans le script MATLAB)
        
        :param AOsignal: np.ndarray de taille (times, angles) 
        :param save_directory: chemin de sauvegarde
        :param set_id: identifiant du set
        :param n_experiment: identifiant de l'expérience
        :param param: dictionnaire contenant les paramètres nécessaires (comme fs_aq, Nt, angles, etc.)
        """

        # Noms des fichiers de sortie
        cdf_location = os.path.join(save_directory, "AOSignals.cdf")
        cdh_location = os.path.join(save_directory, "AOSignals.cdh")
        info_location = os.path.join(save_directory, "info.txt")

        # Calcul des angles (en degrés) si nécessaire

        nScan = self.AOsignal.shape[1]  # Nombre de scans ou d'événements

        # **1. Sauvegarde du fichier .cdf**
        with open(cdf_location, "wb") as fileID:
            for j in range(self.AOsignal.shape[1]):
                active_list = self.AcousticFields[j].pattern.activeList
                angle = self.AcousticFields[j].angle
                # Écrire les identifiants hexadécimaux
                active_list_str = ''.join(map(str, active_list)) 

                nb_padded_zeros = (4 - len(active_list_str) % 4) % 4  # Calcul du nombre de 0 nécessaires
                active_list_str += '0' * nb_padded_zeros  # Ajout des zéros à la fin de la chaîne

                # Regrouper par paquets de 4 bits et convertir chaque paquet en hexadécimal
                active_list_hex = ''.join([hex(int(active_list_str[i:i+4], 2))[2:] for i in range(0, len(active_list_str), 4)])
                for i in range(0, len(active_list_hex), 2):  # Chaque 2 caractères hex représentent 1 octet
                    byte_value = int(active_list_hex[i:i + 2], 16)  # Convertit l'hexadécimal en entier
                    fileID.write(byte_value.to_bytes(1, byteorder='big'))  # Écriture en big endian
            
                fileID.write(np.int8(angle).tobytes())
                
                # Écrire le signal AO correspondant (times x 1) en single (float32)
                fileID.write(self.AOsignal[:, j].astype(np.float32).tobytes())

    # **2. Sauvegarde du fichier .cdh**
        header_content = (
            f"Data filename: AOSignals.cdf\n"
            f"Number of events: {nScan}\n"
            f"Number of acquisitions per event: {self.AOsignal.shape[1]}\n"
            f"Start time (s): 0\n"
            f"Duration (s): 1\n"
            f"Acquisition frequency (Hz): {1/self.AcousticFields[0].kgrid.dt}\n"
            f"Data mode: histogram\n"
            f"Data type: AOT\n"
            f"Number of US transducers: {self.params['num_elements']}"
        )
        with open(cdh_location, "w") as fileID:
            fileID.write(header_content)

        with open(info_location, "w") as fileID:
            for field in self.AcousticFields:
                fileID.write(field.getName_field() + "\n")

        print(f"Fichiers .cdf, .cdh et info.txt sauvegardés dans {save_directory}")

    def load_AOSignal(self,cdh_file):
        # Lire les métadonnées depuis le fichier .cdh
        with open(cdh_file, "r") as file:
            cdh_content = file.readlines()

        # Extraire les dimensions des données à partir des métadonnées
        n_events = int([line.split(":")[1].strip() for line in cdh_content if "Number of events" in line][0])
        n_acquisitions = int([line.split(":")[1].strip() for line in cdh_content if "Number of acquisitions per event" in line][0])

        # Initialiser la matrice pour stocker les données
        AOsignal_matrix = np.zeros((n_events, n_acquisitions), dtype=np.float32)

        # Lire les données binaires depuis le fichier .cdf
        with open(cdh_file.replace(".cdh", ".cdf"), "rb") as file:
            for event in range(n_events):
                # Lire et ignorer la chaîne hexadécimale (active_list)
                num_elements = int([line.split(":")[1].strip() for line in cdh_content if "Number of US transducers" in line][0])
                hex_length = (num_elements + 3) // 4  # Nombre de caractères hex nécessaires
                file.read(hex_length // 2)  # Ignorer la chaîne hexadécimale
                
                # Lire l'angle (int8)
                angle = int.from_bytes(file.read(1), byteorder='big', signed=True)
                
                # Lire le signal AO correspondant (float32)
                signal = np.frombuffer(file.read(n_acquisitions * 4), dtype=np.float32)  # 4 octets par float32
                
                # Stocker le signal dans la matrice
                AOsignal_matrix[event, :] = signal

        self.AOsignal = AOsignal_matrix

    def plot_animations_A_matrix(self, wave_name=None, desired_duration_ms = 5000, save_dir=None):
            """
            Plot synchronized animations of A_matrix slices for selected angles.

            Args:
                A_matrix: 4D numpy array (time, z, x, angles)
                z: array of z-axis positions
                x: array of x-axis positions
                angles_to_plot: list of angles to visualize
                wave_name: optional name for labeling the subplots (e.g., "wave1")
                step: time step between frames (default every 10 frames)
                save_dir: directory to save the animation gif; if None, animation will not be saved

            Returns:
                ani: Matplotlib FuncAnimation object
            """

            # Set the maximum embedded animation size to 100 MB
            mpl.rcParams['animation.embed_limit'] = 100

            if save_dir is not None:
                os.makedirs(save_dir, exist_ok=True)

            num_plots = len(self.AcousticFields)

            # Automatically adjust layout
            if num_plots <= 5:
                nrows, ncols = 1, num_plots
            else:
                ncols = 5
                nrows = (num_plots + ncols - 1) // ncols

            # Create figure and subplots 
            fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 5.3 * nrows))
            if isinstance(axes, plt.Axes):
                axes = np.array([axes])
            axes = axes.flatten()

            ims = []

            # Set main title 
            fig.suptitle(f"System Matrix Animation {wave_name}",
                        fontsize=12, y=0.98)

            # Ensure start_idx_in_A_matrix exists
            if not hasattr(self, 'start_idx_in_A_matrix'):
                raise AttributeError("StructuredWave must have attribute 'start_idx_in_A_matrix' to locate A_matrix slices.")

            for idx in range(num_plots):
                ax = axes[idx]

                im = ax.imshow(self.AcousticFields[0, :, :, idx],
                            # extent=(x[0]*1000, x[-1]*1000, z[-1]*1000, z[0]*1000), vmax =  0.2*np.max(A_matrix[:,:,:,global_index]),
                            extent=(self.params['Xrange'][0], self.params['Xrange'][1], self.params['Zrange'][1],self.params['Zrange'][0]), vmax =  1,
                            aspect='equal', cmap='jet', animated=True)
                ax.set_xlabel("x (mm)", fontsize=8)
                ax.set_ylabel("z (mm)", fontsize=8)
                ims.append((im, ax, idx))

            # Remove unused axes if any
            for j in range(num_plots, len(axes)):
                fig.delaxes(axes[j])

            # Adjust layout to leave space for main title
            plt.tight_layout(rect=[0, 0, 1, 0.95])

            # Unified update function for all subplots
            def update(frame):
                artists = []
                for im, ax, idx in ims:
                    im.set_array(self.AcousticFields[frame, :, :,idx ])
                    fig.suptitle(f"System Matrix Animation {wave_name} t = {frame * 25e-6 * 1000:.2f} ms", fontsize=10)
                    artists.append(im)
                return artists

            interval = desired_duration_ms / self.AcousticFields.shape[0]
            # Create animation
            ani = animation.FuncAnimation(
                fig, update,
                frames=range(0, self.AcousticFields.shape[0]),
                interval=interval, blit=True
            )

            # Save animation if needed
            if save_dir is not None:
                now = datetime.now()
                date_str = now.strftime("%Y_%d_%m_%y")
                save_filename = f"AcousticField_{wave_name}_{date_str}.gif"
                save_path = os.path.join(save_dir, save_filename)
                ani.save(save_path, writer='pillow', fps=20)
                print(f"Saved: {save_path}")

            plt.close(fig)

            return ani

    def plot_animated_y_A_LAMBDA(self, fileOfAcousticField,  save_dir=None, desired_duration_ms = 5000):

        mpl.rcParams['animation.embed_limit'] = 100

        pattern_str = AOT_biomaps.AOT_Acoustic.StructuredWave.getPattern(fileOfAcousticField)
        angle = AOT_biomaps.AOT_Acoustic.StructuredWave.getAngle(fileOfAcousticField)

        fieldToPlot = None

        for field in self.AcousticFields:
            if field.get_path() == fileOfAcousticField:
                break
            fieldToPlot = field
            idx = self.AcousticFields.index(field)
        else:
            raise ValueError(f"Field {fileOfAcousticField} not found in AcousticFields.")
        
        if wave_name is None:
            wave_name = f"Pattern structure {pattern_str}"

        fig, axs = plt.subplots(1, 2, figsize=(6 * 2, 5.3 * 1))

        if isinstance(axs, plt.Axes):
            axs = np.array([axs])
        
        fig.suptitle(f"AO Signal Animation {wave_name} | Angle {angle}°", fontsize=12, y=0.98)

        # Left: LAMBDA at bottom
        axs[0].imshow(self.OpticImage.T, cmap='hot', alpha=1, origin='upper',
                                        extent=(self.params['Xrange'][0], self.params['Xrange'][1], self.params['Zrange'][1], self.params['Zrange'][0]),
                                        aspect='equal')

        # Acoustic field drawn on top of LAMBDA
        im_field = axs[0].imshow(fieldToPlot[0, :, :, idx], cmap='jet', origin='upper',
                                extent=(self.params['Xrange'][0], self.params['Xrange'][1], self.params['Zrange'][1], self.params['Zrange'][0]),
                                vmax =  1, vmin = 0.01, alpha=0.8,
                                aspect='equal')

        axs[0].set_title(f"{wave_name} | Angle {angle}° | t = 0.00 ms", fontsize=10)
        axs[0].set_xlabel("x (mm)", fontsize=8)
        axs[0].set_ylabel("z (mm)", fontsize=8)

        # Center: AO signal y
        time_axis = np.arange(self.AOsignal.shape[0]) * 25e-6 * 1000  # in ms
        line_y, = axs[1].plot(time_axis, self.AOsignal[:, idx])
        # vertical_line = axs[1].axvline(x=time_axis[0], color='r', linestyle='--')
        vertical_line, = axs[1].plot([time_axis[0], time_axis[0]], [0, self.AOsignal[0, idx]], 'r--')
        axs[1].set_xlabel("Time (ms)", fontsize=8)
        axs[1].set_ylabel("Value", fontsize=8)
        axs[1].set_title(f"{wave_name} | Angle {angle}° | t = 0.00 ms", fontsize=10)

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        def update(frame):
            current_time_ms = frame * 25e-6 * 1000

            # Apply masking to suppress background
            frame_data = fieldToPlot[frame, :, :, idx]
            masked_data = np.where(frame_data > 0.02, frame_data, np.nan)
            im_field.set_data(masked_data)

            axs[0].set_title(f"{wave_name} | Angle {angle}° | t = {current_time_ms:.2f} ms", fontsize=10)

            # Copy partial y signal
            y_vals = self.AOsignal[:, idx]
            y_copy = np.full_like(y_vals, np.nan)
            y_copy[:frame + 1] = y_vals[:frame + 1]
            line_y.set_data(time_axis, y_copy)

            # Red vertical line
            vertical_line.set_data([time_axis[frame], time_axis[frame]], [0, y_vals[frame]])

            axs[1].set_title(f"{wave_name} | Angle {angle}° | t = {current_time_ms:.2f} ms", fontsize=10)

            return [im_field, vertical_line, line_y]

        interval = desired_duration_ms / fieldToPlot.shape[0]

        # Create the animation
        ani = animation.FuncAnimation(
            fig, update,
            frames=range(0, self.AcousticFields.shape[0]),
            interval=interval, blit=True
        )
        
        if save_dir is not None:
            now = datetime.now()
            date_str = now.strftime("%Y_%d_%m_%y")
            os.makedirs(save_dir, exist_ok=True)
            save_filename = f"A_y_LAMBDA_overlay_{pattern_str}_{angle}_{date_str}.gif"
            save_path = os.path.join(save_dir, save_filename)
            ani.save(save_path, writer='pillow', fps=20)
            print(f"Saved: {save_path}")

        plt.close(fig)

        return ani

    def plot_AO_signal_y(self, save_dir=None, wave_name=None):
        """
        Plot AO signals y(t) for selected angles.

        Args:
            y: 2D numpy array (time, angles)
            angles_to_plot: list of angles to visualize
            save_dir: directory to save the figure; if None, only display
            wave_name: optional name for labeling; default uses pattern structure
        """

        # Time axis in milliseconds
        time_axis = np.arange(self.AOsignal.shape[0]) * 25e-6 * 1000

        # Set up layout
        num_plots = self.AOsignal.shape[1]

        if num_plots <= 5:
                nrows, ncols = 1, num_plots
        else:
            ncols = 5
            nrows = (num_plots + ncols - 1) // ncols

        fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 5.3 * nrows))
        if isinstance(axes, plt.Axes):
            axes = np.array([axes])
        axes = axes.flatten()

        # Set main title
        fig.suptitle(f"AO Signal Plot {wave_name}", fontsize=12, y=0.98)


        for idx in range(num_plots):
            ax = axes[idx]
            ax.plot(time_axis, self.AOsignal[:,idx])
            ax.set_xlabel("Time (ms)", fontsize=8)
            ax.set_ylabel("Value", fontsize=8)

        # Remove unused axes
        for j in range(num_plots, len(axes)):
            fig.delaxes(axes[j])

        plt.tight_layout(rect=[0, 0, 1, 0.95])

        # Save if needed
        if save_dir is not None:
            now = datetime.now()    
            date_str = now.strftime("%Y_%d_%m_%y")
            os.makedirs(save_dir, exist_ok=True)
            save_filename = f"Static_y_Plot{wave_name}_{date_str}.png"
            save_path = os.path.join(save_dir, save_filename)
            plt.savefig(save_path, dpi=200)
            print(f"Saved: {save_path}")

        plt.show()
        plt.close(fig)

