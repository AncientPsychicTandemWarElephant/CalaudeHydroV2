#!/usr/bin/env python3
"""
test_lag_demo.py - Demo to show lag reduction in comment textboxes
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import time
import sys

# Import our optimizations
from focused_textbox_fix import SmartTextBox

def create_demo():
    """Create a demo to show lag improvements"""
    
    fig = plt.figure(figsize=(12, 8))
    fig.suptitle('Comment TextBox Lag Improvement Demo', fontsize=16)
    
    # Create standard TextBox
    ax_standard = fig.add_axes([0.1, 0.7, 0.8, 0.05])
    tb_standard = TextBox(ax_standard, 'Standard (laggy):', 
                         initial='Type here - may have lag...')
    
    # Create optimized SmartTextBox
    ax_smart = fig.add_axes([0.1, 0.6, 0.8, 0.05])
    tb_smart = SmartTextBox(ax_smart, 'Optimized (fast):', 
                           initial='Type here - should be responsive!')
    
    # Performance tracking
    perf_data = {'standard': [], 'smart': []}
    last_update = {'standard': 0, 'smart': 0}
    
    # Create performance display
    ax_perf = fig.add_axes([0.1, 0.2, 0.8, 0.35])
    ax_perf.axis('off')
    perf_text = ax_perf.text(0, 1, '', va='top', fontsize=12, 
                            family='monospace')
    
    def update_performance(textbox_type):
        """Update performance display"""
        current_time = time.time()
        if textbox_type in last_update:
            delay = (current_time - last_update[textbox_type]) * 1000
            if delay > 0:  # Only track actual typing
                perf_data[textbox_type].append(delay)
            last_update[textbox_type] = current_time
        
        # Update display
        report = ['Performance Comparison:\n' + '='*40]
        
        for name, data in perf_data.items():
            if data:
                # Keep only last 20 measurements
                data = data[-20:]
                avg_delay = sum(data) / len(data)
                
                report.append(f'\n{name.capitalize()} TextBox:')
                report.append(f'  Average response: {avg_delay:.1f}ms')
                report.append(f'  Last response: {data[-1]:.1f}ms')
                
                # Performance rating
                if avg_delay < 20:
                    rating = "EXCELLENT ⭐⭐⭐"
                elif avg_delay < 50:
                    rating = "GOOD ⭐⭐"
                elif avg_delay < 100:
                    rating = "OK ⭐"
                else:
                    rating = "LAGGY ⚠"
                
                report.append(f'  Rating: {rating}')
        
        report.append('\n' + '='*40)
        report.append('\nTIP: Type the same text in both boxes to compare lag!')
        
        perf_text.set_text('\n'.join(report))
        fig.canvas.draw_idle()
    
    # Connect handlers
    def on_standard_change(text):
        last_update['standard'] = time.time()
        update_performance('standard')
    
    def on_smart_change(text):
        last_update['smart'] = time.time()
        update_performance('smart')
    
    tb_standard.on_text_change(on_standard_change)
    tb_smart.on_text_change(on_smart_change)
    
    # Add test button for rapid input
    ax_test = fig.add_axes([0.4, 0.05, 0.2, 0.05])
    btn_test = Button(ax_test, 'Fill with test text')
    
    def fill_test_text(event):
        """Fill both textboxes with test text rapidly"""
        test_text = "The quick brown fox jumps over the lazy dog. " * 3
        
        # Clear first
        tb_standard.set_val('')
        tb_smart.set_val('')
        
        # Type character by character
        for i, char in enumerate(test_text):
            tb_standard.set_val(test_text[:i+1])
            tb_smart.set_val(test_text[:i+1])
            plt.pause(0.01)  # Small pause between characters
    
    btn_test.on_clicked(fill_test_text)
    
    # Instructions
    ax_instructions = fig.add_axes([0.05, 0.05, 0.3, 0.1])
    ax_instructions.axis('off')
    ax_instructions.text(0, 0.5, 
                       'Instructions:\n'
                       '1. Type in both textboxes\n'
                       '2. Compare responsiveness\n'
                       '3. Click test button for rapid input',
                       va='center', fontsize=10)
    
    # Initial performance display
    update_performance('standard')
    
    plt.show()

if __name__ == '__main__':
    create_demo()