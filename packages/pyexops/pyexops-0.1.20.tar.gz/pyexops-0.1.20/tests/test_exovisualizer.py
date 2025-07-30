# pyexops/tests/test_exovisualizer.py

import pytest
import numpy as np
import matplotlib.pyplot as plt
from pyexops import ExoVisualizer, Star, Planet, TransitSimulator

# Fixture for the visualizer
@pytest.fixture
def visualizer():
    return ExoVisualizer()

# Fixture for basic simulation data
@pytest.fixture
def basic_sim_data():
    times = np.linspace(0, 10, 100)
    fluxes = 1.0 - 0.01 * np.sin(times) # Simple sinusoidal flux for testing
    return times, fluxes

@pytest.fixture
def basic_simulator_instance():
    # A minimal simulator instance required by plot_interactive_frames
    star = Star(radius=10.0, base_flux=100.0)
    planet = Planet(radius=0.1, period=1.0, semimajor_axis=2.0, inclination=90.0, epoch_transit=0.5)
    return TransitSimulator(
        star=star, planets=[planet],
        image_resolution=(20, 20), star_center_pixel=(10, 10),
        background_flux_per_pixel=1.0, read_noise_std=1.0,
        target_aperture_radius_pixels=3.0,
        background_aperture_inner_radius_pixels=5.0,
        background_aperture_outer_radius_pixels=8.0
    )

# Test cases for plot_light_curve
def test_plot_light_curve_basic(visualizer, basic_sim_data):
    times, fluxes = basic_sim_data
    
    # Test that it runs without error (no explicit checks on plot content)
    visualizer.plot_light_curve(times, fluxes, "Test Light Curve")
    assert plt.gcf().axes # Check if a figure and axes were created
    plt.close('all') # Close the plot to prevent it from blocking tests

def test_plot_light_curve_show_false(visualizer, basic_sim_data):
    times, fluxes = basic_sim_data
    
    # Test with show=False
    visualizer.plot_light_curve(times, fluxes, "Test No Show", show=False)
    assert plt.gcf().axes # Still creates figure/axes
    # We can't directly assert plt.show() was NOT called, but this is standard practice.
    # A subsequent plt.show() should display it.
    plt.close('all')

def test_plot_light_curve_custom_color(visualizer, basic_sim_data):
    times, fluxes = basic_sim_data
    
    visualizer.plot_light_curve(times, fluxes, "Test Custom Color", color='red')
    ax = plt.gca()
    # Check if the line color is approximately red (RGBA value)
    assert ax.lines[0].get_color() == 'red'
    plt.close('all')

def test_plot_light_curve_with_label(visualizer, basic_sim_data):
    times, fluxes = basic_sim_data
    
    visualizer.plot_light_curve(times, fluxes, "Test With Label", label="My Data")
    ax = plt.gca()
    # Check if a legend is present and the label is set
    assert ax.get_legend() is not None
    assert ax.get_legend().get_texts()[0].get_text() == "My Data"
    plt.close('all')

# Test cases for plot_interactive_frames
def test_plot_interactive_frames_basic(visualizer, basic_simulator_instance):
    times_for_viz = np.arange(0.0, 1.0, 0.2) # A few frames
    
    # Test that it runs without error. 
    # Mocking ipywidgets interaction is complex, so focus on initial setup.
    try:
        visualizer.plot_interactive_frames(basic_simulator_instance, times_for_viz)
        # We can't easily assert the widget is displayed or functional,
        # but if no error is raised, the setup part is likely ok.
    except Exception as e:
        pytest.fail(f"plot_interactive_frames raised an unexpected exception: {e}")
    finally:
        plt.close('all') # Ensure any created plots are closed