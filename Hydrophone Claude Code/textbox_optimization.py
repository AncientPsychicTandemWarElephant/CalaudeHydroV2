"""
textbox_optimization.py - Consolidated TextBox optimization module
Combines all optimization strategies for better TextBox performance
"""

import time
import threading
from matplotlib.widgets import TextBox

class TextBoxOptimizer:
    """Unified TextBox optimization with multiple strategies"""
    
    @staticmethod
    def disable_blitting(textbox):
        """Disable blitting which can cause lag"""
        if hasattr(textbox, '_use_blit'):
            textbox._use_blit = False
        if hasattr(textbox, 'useblit'):
            textbox.useblit = False
            
        # Also disable animation
        if hasattr(textbox, '_animated'):
            textbox._animated = False
            
    @staticmethod
    def optimize_drawing(textbox):
        """Use draw_idle instead of draw for better performance"""
        if hasattr(textbox, 'set_val'):
            original_set_val = textbox.set_val
            
            def optimized_set_val(val):
                original_set_val(val)
                if hasattr(textbox.ax.figure.canvas, 'draw_idle'):
                    textbox.ax.figure.canvas.draw_idle()
            
            textbox.set_val = optimized_set_val
    
    @staticmethod
    def add_keystroke_debouncing(textbox, delay=0.05):
        """Add debouncing to reduce update frequency"""
        if hasattr(textbox, '_on_keypress'):
            original_keypress = textbox._on_keypress
            last_update = [0]
            
            def debounced_keypress(event):
                current_time = time.time()
                
                # Always process the keypress
                original_keypress(event)
                
                # But limit canvas updates
                if current_time - last_update[0] > delay:
                    last_update[0] = current_time
                    if hasattr(textbox.ax.figure.canvas, 'draw_idle'):
                        textbox.ax.figure.canvas.draw_idle()
            
            textbox._on_keypress = debounced_keypress
    
    @staticmethod
    def add_event_optimization(textbox, update_delay=0.1):
        """Event-based optimization with batched updates"""
        class EventOptimizer:
            def __init__(self, tb, delay):
                self.textbox = tb
                self.update_delay = delay
                self.pending_update = False
                self.update_timer = None
                self.last_text = ""
                
                # Replace the original key press handler
                self._original_on_key = tb._on_keypress
                tb._on_keypress = self._optimized_on_keypress
            
            def _optimized_on_keypress(self, event):
                # Process the key immediately
                self._original_on_key(event)
                
                # Schedule a canvas update if not already pending
                if not self.pending_update:
                    self.pending_update = True
                    
                    if self.update_timer is not None:
                        self.update_timer.cancel()
                    
                    self.update_timer = threading.Timer(self.update_delay, self._perform_update)
                    self.update_timer.start()
            
            def _perform_update(self):
                self.pending_update = False
                
                current_text = self.textbox.text
                if current_text != self.last_text:
                    self.last_text = current_text
                    
                    if hasattr(self.textbox.ax.figure.canvas, 'draw_idle'):
                        self.textbox.ax.figure.canvas.draw_idle()
        
        return EventOptimizer(textbox, update_delay)
    
    @classmethod
    def apply_all_optimizations(cls, textbox, use_event_optimizer=False):
        """Apply all optimizations to a TextBox"""
        cls.disable_blitting(textbox)
        cls.optimize_drawing(textbox)
        cls.add_keystroke_debouncing(textbox)
        
        if use_event_optimizer:
            cls.add_event_optimization(textbox)
        
        # Set focus optimization flags
        textbox._optimize_focus = True
        
        # Ensure keyboard capture
        if hasattr(textbox, 'capturekeyboard'):
            textbox.capturekeyboard = True
        
        return textbox


def optimize_textbox(textbox, full_optimization=True):
    """Single function to optimize a TextBox widget"""
    return TextBoxOptimizer.apply_all_optimizations(textbox, use_event_optimizer=full_optimization)


def optimize_comment_textboxes(state):
    """Optimize all comment-related TextBox widgets in the application"""
    # Add text caching
    if not hasattr(state, '_text_cache'):
        state._text_cache = {}
    
    # Optimize comment input
    if hasattr(state, 'comment_input'):
        optimize_textbox(state.comment_input)
    
    # Optimize notes input
    if hasattr(state, 'notes_input'):
        optimize_textbox(state.notes_input)
    
    # Set figure-wide optimization flags
    if hasattr(state, 'fig') and state.fig:
        # Reduce the number of figure updates
        if hasattr(state.fig.canvas, 'supports_blit'):
            state.fig.canvas.supports_blit = False
    
    return state