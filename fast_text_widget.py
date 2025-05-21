"""
fast_text_widget.py - Ultra-fast text widget implementation
Minimal redrawing for maximum responsiveness
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import AxesWidget
from matplotlib.text import Text
import matplotlib.patches as patches

class FastTextWidget(AxesWidget):
    """Fast text input widget with minimal redrawing"""
    
    def __init__(self, ax, label='', initial='', color='.95', 
                 text_color='black', cursor_color='black'):
        super().__init__(ax)
        
        self.label = label
        self.text = initial
        self.color = color
        self.text_color = text_color
        self.cursor_color = cursor_color
        self.cursor_position = len(initial)
        
        # Setup the visual elements
        self.ax.set_facecolor(color)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        
        # Create text element
        self.text_obj = Text(0.02, 0.5, self.text, 
                            transform=self.ax.transAxes,
                            verticalalignment='center',
                            fontsize=10,
                            color=self.text_color)
        self.ax.add_artist(self.text_obj)
        
        # Create cursor
        self.cursor = self.ax.axvline(x=0.02, ymin=0.2, ymax=0.8,
                                     color=self.cursor_color, 
                                     linewidth=1,
                                     visible=False)
        
        # Track focus
        self.has_focus = False
        
        # Connect events
        self.connect_event('button_press_event', self._on_click)
        self.connect_event('key_press_event', self._on_key_press)
        self.connect_event('figure_leave_event', self._on_leave)
        
        # Callbacks
        self.callbacks = []
        
        # Disable all blitting and animation
        self._use_blit = False
        self._animated = False
        
    def _on_click(self, event):
        """Handle mouse clicks"""
        if event.inaxes == self.ax:
            self.has_focus = True
            self.cursor.set_visible(True)
            self._update_cursor()
        else:
            self.has_focus = False
            self.cursor.set_visible(False)
        self.ax.figure.canvas.draw_idle()
    
    def _on_leave(self, event):
        """Handle mouse leaving the figure"""
        self.has_focus = False
        self.cursor.set_visible(False)
        self.ax.figure.canvas.draw_idle()
    
    def _on_key_press(self, event):
        """Handle key presses"""
        if not self.has_focus:
            return
            
        if event.key == 'backspace':
            if self.cursor_position > 0:
                self.text = (self.text[:self.cursor_position-1] + 
                           self.text[self.cursor_position:])
                self.cursor_position -= 1
                self._update_display()
                
        elif event.key == 'delete':
            if self.cursor_position < len(self.text):
                self.text = (self.text[:self.cursor_position] + 
                           self.text[self.cursor_position+1:])
                self._update_display()
                
        elif event.key == 'left':
            if self.cursor_position > 0:
                self.cursor_position -= 1
                self._update_cursor()
                
        elif event.key == 'right':
            if self.cursor_position < len(self.text):
                self.cursor_position += 1
                self._update_cursor()
                
        elif event.key == 'home':
            self.cursor_position = 0
            self._update_cursor()
            
        elif event.key == 'end':
            self.cursor_position = len(self.text)
            self._update_cursor()
            
        elif event.key == 'enter' or event.key == 'return':
            self._on_submit()
            
        elif event.key and len(event.key) == 1:
            # Regular character
            self.text = (self.text[:self.cursor_position] + 
                       event.key + 
                       self.text[self.cursor_position:])
            self.cursor_position += 1
            self._update_display()
    
    def _update_display(self):
        """Update the text display"""
        self.text_obj.set_text(self.text)
        self._update_cursor()
        
        # Trigger callbacks
        for callback in self.callbacks:
            callback(self.text)
        
        # Only redraw the specific axis, not the whole figure
        self.ax.draw_artist(self.text_obj)
        self.ax.draw_artist(self.cursor)
        self.ax.figure.canvas.blit(self.ax.bbox)
    
    def _update_cursor(self):
        """Update cursor position"""
        if not self.has_focus:
            return
            
        # Calculate cursor x position based on text
        text_width = self.text_obj.get_window_extent().width
        fig_width = self.ax.figure.get_window_extent().width
        ax_width = self.ax.get_window_extent().width
        
        # Simple approximation - would need font metrics for accuracy
        if self.text:
            char_width = text_width / len(self.text)
            cursor_x = 0.02 + (self.cursor_position * char_width) / ax_width
        else:
            cursor_x = 0.02
            
        cursor_x = min(cursor_x, 0.98)  # Keep within bounds
        
        self.cursor.set_xdata([cursor_x, cursor_x])
        
        # Only update the cursor
        self.ax.draw_artist(self.cursor)
        self.ax.figure.canvas.blit(self.ax.bbox)
    
    def _on_submit(self):
        """Handle submit (enter key)"""
        for callback in self.callbacks:
            callback(self.text)
    
    def on_text_change(self, func):
        """Register a callback for text changes"""
        self.callbacks.append(func)
    
    def set_val(self, val):
        """Set the text value"""
        self.text = str(val)
        self.cursor_position = len(self.text)
        self._update_display()
    
    def get_text(self):
        """Get the current text"""
        return self.text


def create_fast_text_widget(ax, label='', initial='', **kwargs):
    """Create a fast text widget"""
    return FastTextWidget(ax, label=label, initial=initial, **kwargs)