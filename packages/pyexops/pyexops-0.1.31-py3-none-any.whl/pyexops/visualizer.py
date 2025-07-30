# pyexops/src/pyexops/exovisualizer.py

import numpy as np
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display
from mpl_toolkits.axes_grid1 import make_axes_locatable

# Type hinting for classes from other modules
from .simulator import TransitSimulator 

class ExoVisualizer:
    """
    A class dedicated to visualizing simulation results from pyExopS,
    including light curves and interactive image frames.
    """
    def __init__(self):
        """
        Initializes the ExoVisualizer. No specific simulator instance is
        required at initialization, as visualization methods take data as input.
        """
        pass

    def plot_light_curve(self, times: np.ndarray, fluxes: np.ndarray, 
                         title: str = "Simulated Light Curve",
                         show: bool = True, 
                         color: str = None,
                         label: str = None):
        """
        Plots a light curve.
        :param times: Array of time points.
        :param fluxes: Array of normalized flux values.
        :param title: Title of the plot.
        :param show: If True, calls plt.show() after plotting. Useful for subplots (set to False).
        :param color: Optional color for the plot line.
        :param label: Optional label for the plot line (used in legend).
        """
        if not plt.gcf().axes: 
            plt.figure(figsize=(12, 6))
            ax = plt.gca() 
        else:
            ax = plt.gca() 

        ax.plot(times, fluxes, marker='.', linestyle='-', markersize=2, linewidth=0.7, color=color, label=label) 
        ax.set_xlabel("Time (arbitrary units, e.g., days)")
        ax.set_ylabel("Normalized Flux")
        ax.set_title(title)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Only call legend if a label was provided
        if label: # <<< CORREÇÃO AQUI
            ax.legend() 

        if show: 
            plt.tight_layout() 
            plt.show()

    def plot_radial_velocity_curve(self, times: np.ndarray, rvs: np.ndarray,
                                   title: str = "Simulated Radial Velocity Curve",
                                   show: bool = True,
                                   color: str = None,
                                   label: str = None):
        """
        Plots a radial velocity curve.
        :param times: Array of time points.
        :param rvs: Array of radial velocity values (e.g., in m/s).
        :param title: Title of the plot.
        :param show: If True, calls plt.show() after plotting. Useful for subplots (set to False).
        :param color: Optional color for the plot line.
        :param label: Optional label for the plot line (used in legend).
        """
        if not plt.gcf().axes: 
            plt.figure(figsize=(12, 6))
            ax = plt.gca() 
        else:
            ax = plt.gca() 

        ax.plot(times, rvs, marker='.', linestyle='-', markersize=2, linewidth=0.7, color=color, label=label) 
        ax.set_xlabel("Time (days)")
        ax.set_ylabel("Radial Velocity (m/s)")
        ax.set_title(title)
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Only call legend if a label was provided
        if label: # <<< CORREÇÃO AQUI
            ax.legend() 

        if show: 
            plt.tight_layout() 
            plt.show()

    def plot_interactive_frames(self, simulator_instance: TransitSimulator, 
                                times_for_viz: np.ndarray, 
                                add_noise: bool = True, 
                                inject_systematics: bool = False):
        """
        Generates and displays an interactive slider to browse through simulated image frames.
        :param simulator_instance: The TransitSimulator instance to get image data from.
        :param times_for_viz: Array of specific time points for which to generate images.
        :param add_noise: Whether to add Poisson and Gaussian noise to each image.
        :param inject_systematics: Whether to inject synthetic systematic trends (usually False for clear viz).
        """
        # Collect images for the visualization time range using the simulator's method
        images_viz, target_masks_viz, background_masks_viz, star_center_viz = \
            simulator_instance.get_simulation_images_for_visualization(
                times_for_viz, add_noise=add_noise, inject_systematics=inject_systematics
            )
        
        if not images_viz:
            print("No images collected for visualization. Check 'times_for_viz' or simulator setup.")
            return

        print(f"Collected {len(images_viz)} image frames for interactive visualization.")

        # Determine global min/max for consistent colorbar scaling across all frames
        global_vmin = np.min(images_viz)
        global_vmax = np.max(images_viz)
        
        # Function to plot a single frame, to be used by the interactive widget
        def _plot_single_frame(frame_idx):
            fig, ax = plt.subplots(figsize=(8, 8)) 
            ax.set_aspect('equal') # Ensure square pixels
            
            current_image = images_viz[frame_idx]
            current_target_mask = target_masks_viz[frame_idx]
            current_background_mask = background_masks_viz[frame_idx]

            im = ax.imshow(current_image, cmap='viridis', origin='lower',
                            vmin=global_vmin, vmax=global_vmax) 

            # Plot apertures and star center
            Y_coords, X_coords = np.indices(current_image.shape)
            ax.scatter(X_coords[current_target_mask], Y_coords[current_target_mask],\
                       color='red', s=5, alpha=1.0, label='Target Pixels')
            ax.scatter(X_coords[current_background_mask], Y_coords[current_background_mask],\
                       color='blue', s=5, alpha=1.0, label='Background Pixels')
            ax.scatter(star_center_viz[0], star_center_viz[1],\
                       marker='+', color='white', s=100, label='Star Center')

            ax.set_title(f'Frame at Time = {times_for_viz[frame_idx]:.3f} days (Frame {frame_idx+1}/{len(images_viz)})')
            ax.set_xlabel('X Pixel')
            ax.set_ylabel('Y Pixel')
            ax.legend(loc='upper right')

            # Make colorbar proportional to the image
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.1)
            fig.colorbar(im, cax=cax, label='Flux (arbitrary units)')

            plt.show()

        # Create the interactive slider widget
        frame_slider = widgets.IntSlider(
            min=0,
            max=len(images_viz) - 1,
            step=1,
            description='Frame Index:',
            continuous_update=True,
            orientation='horizontal'
        )

        # Display the interactive widget
        interactive_plot = widgets.interactive(_plot_single_frame, frame_idx=frame_slider)
        display(interactive_plot)
        
        print("Interactive visualization loaded. Move the slider to browse frames.")
