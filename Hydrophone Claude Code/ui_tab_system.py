"""
ui_tab_system.py - Tab system for the modernized UI

This module provides the base classes and infrastructure for the tabbed interface.
It includes:
- Base tab class
- Tab manager
- Tab switching mechanism
- Common styling properties
"""

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Button
import logging
import numpy as np

# Import state directly
import state
from utils import add_log_entry

class TabBase:
    """Base class for all tabs in the application."""
    
    def __init__(self, fig, parent_ax):
        """
        Initialize a new tab.
        
        Args:
            fig: The main figure
            parent_ax: The parent axes where this tab will be rendered
        """
        self.fig = fig
        self.parent_ax = parent_ax
        self.visible = False
        self.components = {}  # Store all UI components created by this tab
        self.axes = {}  # Store all axes created by this tab
        
    def build(self):
        """
        Build the tab's UI components.
        This should be overridden by subclasses.
        """
        pass
        
    def show(self):
        """Show this tab (make it visible)."""
        for component_name, component in self.components.items():
            if hasattr(component, 'set_visible'):
                component.set_visible(True)
                
        for ax_name, ax in self.axes.items():
            ax.set_visible(True)
            
        self.visible = True
        self.on_show()
        
    def hide(self):
        """Hide this tab (make it invisible)."""
        for component_name, component in self.components.items():
            if hasattr(component, 'set_visible'):
                component.set_visible(False)
                
        for ax_name, ax in self.axes.items():
            ax.set_visible(False)
            
        self.visible = False
        self.on_hide()
        
    def on_show(self):
        """Called when the tab is shown. Override in subclasses for custom behavior."""
        pass
        
    def on_hide(self):
        """Called when the tab is hidden. Override in subclasses for custom behavior."""
        pass
        
    def update(self):
        """
        Update the tab's UI components.
        This should be called whenever the tab needs to refresh its display.
        """
        if self.visible:
            self.on_update()
            
    def on_update(self):
        """Called to update the tab. Override in subclasses for custom behavior."""
        pass
        
    def create_section(self, title, y_position, height=0.15):
        """
        Create a titled section within the tab.
        
        Args:
            title: The title of the section
            y_position: The y-position of the section (0-1, from bottom to top)
            height: The height of the section (0-1)
            
        Returns:
            The axes object for the section
        """
        # Create a nested axes for this section
        section_ax = plt.Axes(
            self.fig, 
            [0.01, y_position, 0.98, height], 
            frameon=True
        )
        self.fig.add_axes(section_ax)
        
        # Set up the section
        section_ax.set_title(title, fontsize=10, loc='left', pad=8)
        section_ax.set_facecolor('#2A2A2A')  # Dark gray background
        section_ax.set_xticks([])
        section_ax.set_yticks([])
        
        # Store the section
        section_name = f"section_{title.lower().replace(' ', '_')}"
        self.axes[section_name] = section_ax
        
        return section_ax
        
    def create_button(self, ax, label, callback, position, size, color='#444444', 
                     hover_color='#555555', text_color='white', fontsize=9):
        """
        Create a styled button.
        
        Args:
            ax: The axes where to place the button
            label: The button label
            callback: The function to call when button is clicked
            position: Tuple (x, y, width, height) for button position
            size: Tuple (width, height) for button size
            color: Button color
            hover_color: Button color when hovered
            text_color: Text color
            fontsize: Font size for button text
            
        Returns:
            The created button
        """
        button_ax = plt.Axes(self.fig, position)
        self.fig.add_axes(button_ax)
        
        button = Button(
            button_ax, label, 
            color=color, hovercolor=hover_color
        )
        button.label.set_fontsize(fontsize)
        button.label.set_color(text_color)
        
        # Connect callback
        button.on_clicked(callback)
        
        # Store the button
        button_name = f"button_{label.lower().replace(' ', '_')}"
        self.components[button_name] = button
        self.axes[button_name + "_ax"] = button_ax
        
        return button


class TabManager:
    """Manages the tabs and tab switching in the application."""
    
    def __init__(self, fig, grid):
        """
        Initialize the tab manager.
        
        Args:
            fig: The main figure
            grid: The GridSpec for the main layout
        """
        self.fig = fig
        self.grid = grid
        self.tabs = {}
        self.active_tab = None
        self.tab_buttons = {}
        
        # Create tab bar at the top of the right panel
        self.tab_bar_ax = fig.add_subplot(grid[0, 1])
        self.tab_bar_ax.set_facecolor('#1E1E1E')  # Dark background
        self.tab_bar_ax.set_xticks([])
        self.tab_bar_ax.set_yticks([])
        self.tab_bar_ax.set_title("Analysis Tools", fontsize=12, pad=10)
        
        # Create content area for tabs
        self.tab_content_ax = fig.add_subplot(grid[1:4, 1])
        self.tab_content_ax.set_facecolor('#1E1E1E')  # Dark background
        self.tab_content_ax.set_xticks([])
        self.tab_content_ax.set_yticks([])
        self.tab_content_ax.set_navigate(False)  # Disable navigation
        
        # Save to state for access from other modules
        state.tab_manager = self
        
    def add_tab(self, name, tab_class):
        """
        Add a new tab.
        
        Args:
            name: The name of the tab
            tab_class: The class of the tab (subclass of TabBase)
            
        Returns:
            The created tab
        """
        # Create tab instance
        tab = tab_class(self.fig, self.tab_content_ax)
        
        # Add to our dictionary
        self.tabs[name] = tab
        
        # Build tab UI
        tab.build()
        
        # Hide by default
        tab.hide()
        
        return tab
        
    def create_tab_buttons(self):
        """Create the tab selection buttons."""
        # Calculate button width
        button_count = len(self.tabs)
        if button_count == 0:
            return
            
        button_width = 1.0 / button_count
        
        # Create a button for each tab
        for i, (name, tab) in enumerate(self.tabs.items()):
            button_ax = plt.Axes(
                self.fig,
                [i * button_width, 0, button_width, 1],
                frameon=True
            )
            self.tab_bar_ax.figure.add_axes(button_ax)
            
            display_name = name.capitalize()
            
            button = Button(
                button_ax, display_name,
                color='#1E1E1E', hovercolor='#2A2A2A'
            )
            button.label.set_fontsize(9)
            button.label.set_color('white')
            
            # Store in our dictionary
            self.tab_buttons[name] = (button, button_ax)
            
            # Connect callback
            button.on_clicked(lambda event, tab_name=name: self.switch_to_tab(tab_name))
            
    def switch_to_tab(self, name):
        """
        Switch to the specified tab.
        
        Args:
            name: The name of the tab to switch to
        """
        if name not in self.tabs:
            add_log_entry(f"Tab '{name}' not found")
            return
            
        # Hide current tab if there is one
        if self.active_tab and self.active_tab in self.tabs:
            self.tabs[self.active_tab].hide()
            
            # Reset button color
            if self.active_tab in self.tab_buttons:
                button, button_ax = self.tab_buttons[self.active_tab]
                button.color = '#1E1E1E'
                button.hovercolor = '#2A2A2A'
                
        # Show new tab
        self.tabs[name].show()
        self.active_tab = name
        
        # Update button color to show it's active
        if name in self.tab_buttons:
            button, button_ax = self.tab_buttons[name]
            button.color = '#3A3A3A'
            button.hovercolor = '#444444'
            
        # Update plot
        self.fig.canvas.draw_idle()
        
        add_log_entry(f"Switched to {name} tab")
        
    def update_all_tabs(self):
        """Update all tabs."""
        for name, tab in self.tabs.items():
            tab.update()
            
    def update_active_tab(self):
        """Update only the active tab."""
        if self.active_tab and self.active_tab in self.tabs:
            self.tabs[self.active_tab].update()


# Modern color scheme
class UIColors:
    """Color scheme for the modernized UI."""
    
    # Background colors
    BACKGROUND_DARK = '#1E1E1E'
    BACKGROUND_MEDIUM = '#2A2A2A'
    BACKGROUND_LIGHT = '#3A3A3A'
    
    # Text colors
    TEXT_PRIMARY = '#FFFFFF'
    TEXT_SECONDARY = '#BBBBBB'
    TEXT_DISABLED = '#777777'
    
    # Accent colors
    ACCENT_BLUE = '#007ACC'
    ACCENT_GREEN = '#6A9955'
    ACCENT_RED = '#F14C4C'
    ACCENT_YELLOW = '#DCDCAA'
    ACCENT_ORANGE = '#CE9178'
    
    # Button colors
    BUTTON_DEFAULT = '#444444'
    BUTTON_HOVER = '#555555'
    BUTTON_ACTIVE = '#666666'
    BUTTON_DISABLED = '#333333'
    
    # Graph colors
    GRAPH_LINE = '#4EC9B0'
    GRAPH_GRID = '#444444'
    GRAPH_AXIS = '#888888'
    
    # Spectrogram colormap
    @staticmethod
    def get_modern_cmap():
        """Get a modern colormap for spectrograms."""
        # Create a colormap ranging from dark blue to bright yellow
        colors = [
            '#050831',  # Dark blue
            '#0E1167',  # Deep blue
            '#2A0F82',  # Purple blue
            '#4C0F84',  # Purple
            '#730F83',  # Magenta purple
            '#9E0F7E',  # Dark magenta
            '#C2114F',  # Dark pink
            '#D53F37',  # Red
            '#EC7D24',  # Orange
            '#F7B21D',  # Yellow orange
            '#FFDA30',  # Yellow
        ]
        
        return plt.cm.colors.LinearSegmentedColormap.from_list('modern', colors)


def apply_modern_style():
    """Apply modern style to matplotlib."""
    plt.style.use('dark_background')
    
    # Set global properties
    plt.rcParams['figure.facecolor'] = UIColors.BACKGROUND_DARK
    plt.rcParams['axes.facecolor'] = UIColors.BACKGROUND_MEDIUM
    plt.rcParams['axes.edgecolor'] = UIColors.GRAPH_AXIS
    plt.rcParams['axes.labelcolor'] = UIColors.TEXT_PRIMARY
    plt.rcParams['xtick.color'] = UIColors.TEXT_SECONDARY
    plt.rcParams['ytick.color'] = UIColors.TEXT_SECONDARY
    plt.rcParams['grid.color'] = UIColors.GRAPH_GRID
    plt.rcParams['text.color'] = UIColors.TEXT_PRIMARY
    
    # Font properties
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.sans-serif'] = ['Segoe UI', 'Arial', 'Helvetica', 'DejaVu Sans']
    
    # Line properties
    plt.rcParams['lines.linewidth'] = 1.5
    plt.rcParams['lines.solid_capstyle'] = 'round'
    
    # Default colormaps
    plt.rcParams['image.cmap'] = 'jet'  # Default colormap