import matplotlib
matplotlib.use('QtAgg')  # Set interactive backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from multiprocessing import Process, Queue
import numpy as np
import time

def visualizer_process(queue, x_range, y_range):
    """Process function to run matplotlib visualization."""
    targets = {}

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(x_range)
    ax.set_ylim(y_range)
    ax.set_xlabel('X Position (mm)')
    ax.set_ylabel('Y Position (mm)')
    ax.set_title('Target Position Tracking')
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')

    scatter = ax.scatter([], [], c='blue', s=100, alpha=0.6, edgecolors='black')
    annotations = {}

    def animate(frame):
        nonlocal targets, annotations

        # Process all queued updates
        while not queue.empty():
            try:
                targets = queue.get_nowait()
            except:
                break

        if not targets:
            scatter.set_offsets(np.empty((0, 2)))
            for ann in annotations.values():
                ann.remove()
            annotations.clear()
            return scatter,

        # Extract positions and IDs
        tids = list(targets.keys())
        positions = list(targets.values())
        xs = [pos[0] for pos in positions]
        ys = [pos[1] for pos in positions]

        # Update scatter plot
        scatter.set_offsets(list(zip(xs, ys)))

        # Update annotations
        for ann in annotations.values():
            ann.remove()
        annotations.clear()

        for tid, x, y in zip(tids, xs, ys):
            ann = ax.annotate(f"T{tid}", (x, y),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, color='red')
            annotations[tid] = ann

        return scatter,

    anim = animation.FuncAnimation(
        fig,
        animate,
        interval=100,
        blit=False,
        cache_frame_data=False
    )

    plt.show(block=True)

SCALE = (1.0 / 800.0) * 14.0
X_OFFSET = 400

class TargetVisualizer:
    """Real-time visualizer for target positions using multiprocessing."""

    def __init__(self, x_range=(0, 14), y_range=(0, 14)):
        self.x_range = x_range
        self.y_range = y_range
        self.queue = Queue()
        self.process = None

    def update_targets(self, target_list):
        """Update target positions from decoded location_track_data.

        Args:
            target_list: List of tuples (tid, x, y, z, velocity, snr, classifier, posture, active)
        """
        # Build target dict and send to visualization process
        targets = {}
        for target in target_list:
            tid, x, y = target[0], target[1], target[2]
            targets[tid] = ((x + X_OFFSET) * SCALE, y * SCALE)

        # Non-blocking send to queue
        try:
            self.queue.put_nowait(targets)
        except:
            # Queue full, skip this update
            pass

    def start(self):
        """Start the visualizer in a separate process."""
        self.process = Process(
            target=visualizer_process,
            args=(self.queue, self.x_range, self.y_range),
            daemon=True
        )
        self.process.start()
        return self.process

    def stop(self):
        """Stop the visualization process."""
        if self.process and self.process.is_alive():
            self.process.terminate()
            self.process.join(timeout=1)
