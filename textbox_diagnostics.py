"""
textbox_diagnostics.py - Diagnostic tool for textbox performance
Helps identify sources of lag in comment textboxes
"""

import time
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox
import psutil
import traceback

class TextBoxDiagnostics:
    """Diagnostic tool for analyzing textbox performance"""
    
    def __init__(self):
        self.metrics = {
            'keypress_times': [],
            'draw_times': [],
            'update_times': [],
            'memory_usage': [],
            'event_queue_size': []
        }
        self.start_time = time.time()
        self.process = psutil.Process()
    
    def wrap_textbox(self, textbox):
        """Wrap a textbox with diagnostic monitoring"""
        
        # Store original methods - check for the correct attribute name
        if hasattr(textbox, '_keypress'):
            original_keypress = textbox._keypress
            attr_name = '_keypress'
        elif hasattr(textbox, '_on_keypress'):
            original_keypress = textbox._on_keypress
            attr_name = '_on_keypress'
        elif hasattr(textbox, 'on_keypress'):
            original_keypress = textbox.on_keypress
            attr_name = 'on_keypress'
        else:
            print(f"Warning: TextBox has no keypress handler attribute")
            return textbox
            
        original_set_val = textbox.set_val
        
        def monitored_keypress(event):
            start = time.time()
            try:
                original_keypress(event)
            finally:
                duration = time.time() - start
                self.metrics['keypress_times'].append(duration)
                
                # Check event queue
                if hasattr(textbox.ax.figure.canvas, '_event_queue'):
                    queue_size = len(textbox.ax.figure.canvas._event_queue)
                    self.metrics['event_queue_size'].append(queue_size)
        
        def monitored_set_val(val):
            start = time.time()
            try:
                original_set_val(val)
            finally:
                duration = time.time() - start
                self.metrics['update_times'].append(duration)
                
                # Monitor memory
                mem_info = self.process.memory_info()
                self.metrics['memory_usage'].append(mem_info.rss / 1024 / 1024)  # MB
        
        # Replace methods
        setattr(textbox, attr_name, monitored_keypress)
        textbox.set_val = monitored_set_val
        
        # Monitor canvas draws
        if hasattr(textbox.ax.figure.canvas, 'draw_idle'):
            original_draw = textbox.ax.figure.canvas.draw_idle
            
            def monitored_draw():
                start = time.time()
                try:
                    original_draw()
                finally:
                    duration = time.time() - start
                    self.metrics['draw_times'].append(duration)
            
            textbox.ax.figure.canvas.draw_idle = monitored_draw
        
        return textbox
    
    def generate_report(self):
        """Generate a performance report"""
        report = []
        report.append("=== TextBox Performance Report ===\n")
        
        # Analyze keypress times
        if self.metrics['keypress_times']:
            avg_keypress = sum(self.metrics['keypress_times']) / len(self.metrics['keypress_times'])
            max_keypress = max(self.metrics['keypress_times'])
            report.append(f"Keypress handling:")
            report.append(f"  Average: {avg_keypress*1000:.2f}ms")
            report.append(f"  Maximum: {max_keypress*1000:.2f}ms")
            report.append(f"  Total events: {len(self.metrics['keypress_times'])}\n")
        
        # Analyze draw times
        if self.metrics['draw_times']:
            avg_draw = sum(self.metrics['draw_times']) / len(self.metrics['draw_times'])
            max_draw = max(self.metrics['draw_times'])
            report.append(f"Canvas drawing:")
            report.append(f"  Average: {avg_draw*1000:.2f}ms")
            report.append(f"  Maximum: {max_draw*1000:.2f}ms")
            report.append(f"  Total draws: {len(self.metrics['draw_times'])}\n")
        
        # Analyze update times
        if self.metrics['update_times']:
            avg_update = sum(self.metrics['update_times']) / len(self.metrics['update_times'])
            max_update = max(self.metrics['update_times'])
            report.append(f"Value updates:")
            report.append(f"  Average: {avg_update*1000:.2f}ms")
            report.append(f"  Maximum: {max_update*1000:.2f}ms")
            report.append(f"  Total updates: {len(self.metrics['update_times'])}\n")
        
        # Memory usage
        if self.metrics['memory_usage']:
            avg_mem = sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
            max_mem = max(self.metrics['memory_usage'])
            report.append(f"Memory usage:")
            report.append(f"  Average: {avg_mem:.2f}MB")
            report.append(f"  Maximum: {max_mem:.2f}MB\n")
        
        # Event queue
        if self.metrics['event_queue_size']:
            avg_queue = sum(self.metrics['event_queue_size']) / len(self.metrics['event_queue_size'])
            max_queue = max(self.metrics['event_queue_size'])
            report.append(f"Event queue:")
            report.append(f"  Average size: {avg_queue:.2f}")
            report.append(f"  Maximum size: {max_queue}\n")
        
        # Performance issues
        issues = []
        if any(t > 0.05 for t in self.metrics['keypress_times']):
            issues.append("- Slow keypress handling (>50ms)")
        if any(t > 0.1 for t in self.metrics['draw_times']):
            issues.append("- Slow canvas drawing (>100ms)")
        if any(s > 10 for s in self.metrics['event_queue_size']):
            issues.append("- Event queue backup (>10 events)")
        
        if issues:
            report.append("Performance issues detected:")
            report.extend(issues)
        else:
            report.append("No significant performance issues detected.")
        
        return '\n'.join(report)
    
    def plot_metrics(self):
        """Plot performance metrics"""
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(10, 8))
        
        # Keypress times
        if self.metrics['keypress_times']:
            ax1.plot([t*1000 for t in self.metrics['keypress_times']])
            ax1.set_title('Keypress Handling Time')
            ax1.set_ylabel('Time (ms)')
            ax1.set_xlabel('Event #')
            ax1.axhline(y=50, color='r', linestyle='--', label='50ms threshold')
            ax1.legend()
        
        # Draw times
        if self.metrics['draw_times']:
            ax2.plot([t*1000 for t in self.metrics['draw_times']])
            ax2.set_title('Canvas Draw Time')
            ax2.set_ylabel('Time (ms)')
            ax2.set_xlabel('Draw #')
            ax2.axhline(y=100, color='r', linestyle='--', label='100ms threshold')
            ax2.legend()
        
        # Memory usage
        if self.metrics['memory_usage']:
            ax3.plot(self.metrics['memory_usage'])
            ax3.set_title('Memory Usage')
            ax3.set_ylabel('Memory (MB)')
            ax3.set_xlabel('Update #')
        
        # Event queue size
        if self.metrics['event_queue_size']:
            ax4.plot(self.metrics['event_queue_size'])
            ax4.set_title('Event Queue Size')
            ax4.set_ylabel('Queue Size')
            ax4.set_xlabel('Event #')
            ax4.axhline(y=10, color='r', linestyle='--', label='10 event threshold')
            ax4.legend()
        
        plt.tight_layout()
        return fig


def run_diagnostic_test():
    """Run a diagnostic test on textbox performance"""
    
    # Create test figure
    fig, ax = plt.subplots(figsize=(6, 2))
    
    # Create textbox
    textbox = TextBox(ax, 'Test:', initial='Type here to test performance...')
    
    # Create diagnostics
    diagnostics = TextBoxDiagnostics()
    diagnostics.wrap_textbox(textbox)
    
    # Add diagnostic display
    ax_report = fig.add_axes([0.1, 0.3, 0.8, 0.6])
    ax_report.axis('off')
    report_text = ax_report.text(0, 1, 'Type in the textbox to generate diagnostics...', 
                                va='top', fontsize=10)
    
    def update_diagnostics(text):
        """Update diagnostic display"""
        report = diagnostics.generate_report()
        report_text.set_text(report)
        fig.canvas.draw_idle()
    
    # Update diagnostics on text change
    textbox.on_text_change(update_diagnostics)
    
    # Show the diagnostic plots when window is closed
    def on_close(event):
        metrics_fig = diagnostics.plot_metrics()
        plt.show()
    
    fig.canvas.mpl_connect('close_event', on_close)
    
    plt.tight_layout()
    plt.show()


def diagnose_state_textboxes(state):
    """Diagnose textbox performance in the application state"""
    
    diagnostics = TextBoxDiagnostics()
    
    # Wrap comment textboxes
    if hasattr(state, 'comment_input'):
        diagnostics.wrap_textbox(state.comment_input)
        print("Monitoring comment_input textbox...")
    
    if hasattr(state, 'notes_input'):
        diagnostics.wrap_textbox(state.notes_input)
        print("Monitoring notes_input textbox...")
    
    # Add diagnostic command to log
    from utils import add_log_entry
    add_log_entry("Textbox diagnostics enabled - type 'show_textbox_diagnostics' in console")
    
    # Store diagnostics in state for later access
    state._textbox_diagnostics = diagnostics
    
    return diagnostics


if __name__ == '__main__':
    run_diagnostic_test()