#!/usr/bin/env python3
"""
test_lag_improvements.py - Test the textbox lag improvements
"""

import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import time
import sys

# Import our optimization modules
from focused_textbox_fix import SmartTextBox, MinimalTextBox
from textbox_diagnostics import TextBoxDiagnostics

def test_textbox_implementations():
    """Test different textbox implementations side by side"""
    
    fig = plt.figure(figsize=(10, 8))
    fig.suptitle('TextBox Lag Improvement Test', fontsize=14)
    
    # Create axes for different implementations
    ax_standard = fig.add_axes([0.1, 0.7, 0.8, 0.05])
    ax_smart = fig.add_axes([0.1, 0.6, 0.8, 0.05])
    ax_minimal = fig.add_axes([0.1, 0.5, 0.8, 0.05])
    
    # Create diagnostics display
    ax_diag = fig.add_axes([0.1, 0.1, 0.8, 0.35])
    ax_diag.axis('off')
    
    # Create textboxes
    tb_standard = TextBox(ax_standard, 'Standard:', initial='Type here...')
    tb_smart = SmartTextBox(ax_smart, 'Smart:', initial='Type here...')
    tb_minimal = MinimalTextBox(ax_minimal, 'Minimal:', initial='Type here...')
    
    # Create diagnostics
    diagnostics = TextBoxDiagnostics()
    try:
        diagnostics.wrap_textbox(tb_standard)
        diagnostics.wrap_textbox(tb_smart)
    except AttributeError as e:
        print(f"Warning: Could not wrap textboxes for diagnostics: {e}")
        print("Continuing without diagnostics...")
    
    # Performance tracking
    perf_data = {
        'standard': {'times': [], 'chars': 0},
        'smart': {'times': [], 'chars': 0},
        'minimal': {'times': [], 'chars': 0}
    }
    
    # Create performance display
    perf_text = ax_diag.text(0, 1, 'Performance Metrics:\n', 
                            va='top', fontsize=10, family='monospace')
    
    def update_performance(name, start_time):
        """Update performance metrics"""
        duration = (time.time() - start_time) * 1000  # Convert to ms
        perf_data[name]['times'].append(duration)
        perf_data[name]['chars'] += 1
        
        # Calculate averages
        report = ['Performance Metrics:\n' + '='*50]
        
        for impl_name, data in perf_data.items():
            if data['times']:
                avg_time = sum(data['times']) / len(data['times'])
                max_time = max(data['times'])
                min_time = min(data['times'])
                
                report.append(f'\n{impl_name.capitalize()} TextBox:')
                report.append(f'  Characters typed: {data["chars"]}')
                report.append(f'  Average response: {avg_time:.2f}ms')
                report.append(f'  Min/Max response: {min_time:.2f}ms / {max_time:.2f}ms')
                
                # Performance rating
                if avg_time < 10:
                    rating = "EXCELLENT"
                elif avg_time < 30:
                    rating = "GOOD"
                elif avg_time < 50:
                    rating = "ACCEPTABLE"
                else:
                    rating = "POOR"
                
                report.append(f'  Performance: {rating}')
        
        # Add diagnostic summary
        report.append('\n' + '='*50)
        report.append(diagnostics.generate_report())
        
        perf_text.set_text('\n'.join(report))
        fig.canvas.draw_idle()
    
    # Track performance for each textbox
    def track_standard(text):
        start = time.time()
        update_performance('standard', start)
    
    def track_smart(text):
        start = time.time()
        update_performance('smart', start)
    
    def track_minimal(text):
        start = time.time()
        update_performance('minimal', start)
    
    tb_standard.on_text_change(track_standard)
    tb_smart.on_text_change(track_smart)
    tb_minimal.on_text_change(track_minimal)
    
    # Add clear button
    ax_clear = fig.add_axes([0.4, 0.02, 0.2, 0.05])
    btn_clear = Button(ax_clear, 'Clear Stats')
    
    def clear_stats(event):
        for data in perf_data.values():
            data['times'].clear()
            data['chars'] = 0
        perf_text.set_text('Performance Metrics:\n')
        diagnostics.metrics = {k: [] for k in diagnostics.metrics}
        fig.canvas.draw_idle()
    
    btn_clear.on_clicked(clear_stats)
    
    # Instructions
    fig.text(0.5, 0.95, 'Type in each textbox to test responsiveness', 
             ha='center', fontsize=12)
    fig.text(0.5, 0.92, 'The Smart and Minimal implementations should show less lag', 
             ha='center', fontsize=10, style='italic')
    
    plt.show()
    
    # Show diagnostic plots after closing
    if diagnostics.metrics['keypress_times']:
        diagnostics.plot_metrics()
        plt.show()


def test_in_application():
    """Test the optimizations in the actual application context"""
    
    # Import the main application components
    try:
        import state
        from ui_components import create_comment_section
        from visualization import setup_main_spectrogram
        
        # Create a minimal test environment
        fig = plt.figure(figsize=(12, 8))
        state.fig = fig
        
        # Create basic axes
        state.ax_spec = fig.add_axes([0.1, 0.3, 0.8, 0.6])
        state.ax_spec.set_title("Test Spectrogram")
        
        # Initialize state variables
        state.comments = []
        state.selected_comment_id = None
        state.comments_visible = True
        
        # Create comment section
        create_comment_section()
        
        # Add diagnostics
        from textbox_diagnostics import diagnose_state_textboxes
        diagnostics = diagnose_state_textboxes(state)
        
        # Add diagnostic display
        ax_diag = fig.add_axes([0.1, 0.02, 0.8, 0.25])
        ax_diag.axis('off')
        diag_text = ax_diag.text(0, 1, 'Textbox Diagnostics:\n', 
                                va='top', fontsize=9, family='monospace')
        
        def update_diagnostics():
            """Update diagnostic display"""
            diag_text.set_text(diagnostics.generate_report())
            fig.canvas.draw_idle()
        
        # Update diagnostics periodically
        timer = fig.canvas.new_timer(interval=1000)  # Update every second
        timer.add_callback(update_diagnostics)
        timer.start()
        
        plt.show()
        
    except Exception as e:
        print(f"Error testing in application context: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--app':
        print("Testing in application context...")
        test_in_application()
    else:
        print("Testing textbox implementations...")
        test_textbox_implementations()