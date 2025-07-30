"""
EEG Head Map Widget - 10-20 System Quality Visualization
Shows electrode positions on a circular head representation with real-time quality indicators.

Author: Michele Romani
"""

import math
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QPen, QBrush, QFont, QColor, QLinearGradient
from brainflow.board_shim import BoardShim


class EEGHeadMapWidget(QWidget):
    """
    Widget that displays EEG electrodes on a circular head map with quality indicators.
    Based on the international 10-20 system positioning.
    """

    electrode_clicked = pyqtSignal(str)  # Emits electrode name when clicked

    def __init__(self, board_id, eeg_channels=None):
        super().__init__()

        self.board_id = board_id
        self.eeg_channels = eeg_channels or BoardShim.get_eeg_channels(board_id)
        self.channel_names = BoardShim.get_eeg_names(board_id)

        # Head map properties
        self.head_radius = 120
        self.electrode_radius = 12
        self.center_x = 150
        self.center_y = 150

        # Quality data storage
        self.quality_data = {}
        self.amplitude_data = {}

        # Animation properties
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(100)  # Update every 100ms
        self.animation_step = 0

        # UI Setup
        self.setupUI()
        self.setup_electrode_positions()

        # Initialize quality data
        for i, channel in enumerate(self.eeg_channels):
            channel_name = self.channel_names[i] if i < len(self.channel_names) else f"Ch{channel}"
            self.quality_data[channel_name] = {'quality': 'good', 'amplitude': 0.0, 'active': True}

    def setupUI(self):
        """Setup the widget UI"""
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Title
        title = QLabel("EEG Electrode Quality Map")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                background-color: #3a3a3a;
                border-radius: 8px;
                border: 2px solid #555;
            }
        """)
        title.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(title)

        # Legend
        self.create_legend(layout)

        # Set widget properties
        self.setMinimumSize(320, 450)
        self.setMaximumSize(400, 500)
        self.setStyleSheet("background-color: #2b2b2b;")

        self.setLayout(layout)

    def create_legend(self, layout):
        """Create quality legend"""
        legend_widget = QWidget()
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(5)

        legend_title = QLabel("Signal Quality")
        legend_title.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        legend_layout.addWidget(legend_title)

        # Quality indicators
        quality_items = [
            ("Excellent", "#4CAF50", "● Strong, clean signal"),
            ("Good", "#8BC34A", "● Acceptable signal quality"),
            ("Fair", "#FF9800", "▲ Moderate noise/artifacts"),
            ("Poor", "#FF5722", "✖ High noise/poor contact"),
            ("No Signal", "#666666", "○ No data/disconnected")
        ]

        for quality, color, description in quality_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(8)

            # Color indicator
            color_label = QLabel("●")
            color_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
            color_label.setFixedWidth(20)

            # Description
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #bbb; font-size: 10px;")

            item_layout.addWidget(color_label)
            item_layout.addWidget(desc_label)
            item_layout.addStretch()

            item_widget = QWidget()
            item_widget.setLayout(item_layout)
            legend_layout.addWidget(item_widget)

        legend_widget.setLayout(legend_layout)
        legend_widget.setStyleSheet("""
            QWidget {
                background-color: #3a3a3a;
                border-radius: 8px;
                border: 2px solid #555;
                padding: 8px;
            }
        """)

        layout.addWidget(legend_widget)

    def setup_electrode_positions(self):
        """Setup electrode positions based on 10-20 system"""
        # Standard 10-20 system positions (simplified circular layout)
        # Positions are in degrees from top (0°) going clockwise

        self.electrode_positions = {}

        # Common electrode positions for different systems
        standard_positions = {
            # Frontal electrodes
            'Fp1': (-45, 0.85), 'Fp2': (45, 0.85),
            'F7': (-90, 0.6), 'F3': (-45, 0.5), 'Fz': (0, 0.5), 'F4': (45, 0.5), 'F8': (90, 0.6),

            # Central electrodes
            'T7': (-135, 0.0), 'C3': (-45, 0.0), 'Cz': (0, 0.0), 'C4': (45, 0.0), 'T8': (135, 0.0),

            # Parietal electrodes
            'P7': (-135, -0.6), 'P3': (-45, -0.5), 'Pz': (0, -0.5), 'P4': (45, -0.5), 'P8': (135, -0.6),

            # Occipital electrodes
            'O1': (-45, -0.85), 'O2': (45, -0.85), 'Oz': (0, -0.85),

            # Additional electrodes
            'FC1': (-22.5, 0.25), 'FC2': (22.5, 0.25), 'CP1': (-22.5, -0.25), 'CP2': (22.5, -0.25),
            'T3': (-110, 0.0), 'T4': (110, 0.0), 'T5': (-110, -0.3), 'T6': (110, -0.3),

            # Extended 10-10 system
            'AF3': (-30, 0.7), 'AF4': (30, 0.7), 'FC5': (-67.5, 0.25), 'FC6': (67.5, 0.25),
            'CP5': (-67.5, -0.25), 'CP6': (67.5, -0.25), 'PO3': (-30, -0.7), 'PO4': (30, -0.7),
        }

        # Map available channels to positions
        for i, channel in enumerate(self.eeg_channels):
            channel_name = self.channel_names[i] if i < len(self.channel_names) else f"Ch{channel}"

            if channel_name in standard_positions:
                angle, radius_ratio = standard_positions[channel_name]
                self.electrode_positions[channel_name] = self.polar_to_cartesian(angle, radius_ratio)
            else:
                # If electrode not in standard positions, distribute evenly around the head
                angle = (i * 360 / len(self.eeg_channels)) - 90  # Start from top
                radius_ratio = 0.8  # Default radius
                self.electrode_positions[channel_name] = self.polar_to_cartesian(angle, radius_ratio)

    def polar_to_cartesian(self, angle_degrees, radius_ratio):
        """Convert polar coordinates to cartesian for electrode positioning"""
        angle_rad = math.radians(angle_degrees)
        radius = self.head_radius * radius_ratio

        x = self.center_x + radius * math.cos(angle_rad)
        y = self.center_y - radius * math.sin(angle_rad)  # Negative because Y increases downward

        return (x, y)

    def paintEvent(self, event):
        """Custom paint event for drawing the head map"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw head outline
        self.draw_head_outline(painter)

        # Draw nose and ears
        self.draw_head_features(painter)

        # Draw electrodes
        self.draw_electrodes(painter)

        # Draw connections (optional)
        if hasattr(self, 'show_connections') and self.show_connections:
            self.draw_electrode_connections(painter)

    def draw_head_outline(self, painter):
        """Draw the circular head outline"""
        # Head circle with gradient
        gradient = QLinearGradient(self.center_x - self.head_radius, self.center_y - self.head_radius,
                                   self.center_x + self.head_radius, self.center_y + self.head_radius)
        gradient.setColorAt(0, QColor(80, 80, 80, 100))
        gradient.setColorAt(1, QColor(40, 40, 40, 100))

        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(200, 200, 200), 3))
        painter.drawEllipse(self.center_x - self.head_radius, self.center_y - self.head_radius,
                            self.head_radius * 2, self.head_radius * 2)

        # Inner circle for reference
        painter.setBrush(QBrush(QColor(0, 0, 0, 0)))  # Transparent
        painter.setPen(QPen(QColor(100, 100, 100, 100), 1, QtCore.Qt.DashLine))
        inner_radius = self.head_radius * 0.6
        painter.drawEllipse(self.center_x - inner_radius, self.center_y - inner_radius,
                            inner_radius * 2, inner_radius * 2)

    def draw_head_features(self, painter):
        """Draw nose and ear indicators"""
        painter.setBrush(QBrush(QColor(150, 150, 150)))
        painter.setPen(QPen(QColor(200, 200, 200), 2))

        # Nose (triangle at top)
        nose_points = [
            QtCore.QPoint(self.center_x, self.center_y - self.head_radius - 15),
            QtCore.QPoint(self.center_x - 8, self.center_y - self.head_radius + 5),
            QtCore.QPoint(self.center_x + 8, self.center_y - self.head_radius + 5)
        ]
        painter.drawPolygon(nose_points)

        # Ears (small rectangles on sides)
        ear_width, ear_height = 15, 25
        # Left ear
        painter.drawRoundedRect(self.center_x - self.head_radius - ear_width,
                                self.center_y - ear_height // 2,
                                ear_width, ear_height, 3, 3)
        # Right ear
        painter.drawRoundedRect(self.center_x + self.head_radius,
                                self.center_y - ear_height // 2,
                                ear_width, ear_height, 3, 3)

    def draw_electrodes(self, painter):
        """Draw electrode positions with quality indicators"""
        painter.setFont(QFont('Arial', 8, QFont.Bold))

        for channel_name, (x, y) in self.electrode_positions.items():
            if channel_name in self.quality_data:
                quality_info = self.quality_data[channel_name]
                quality = quality_info['quality']
                amplitude = quality_info['amplitude']
                active = quality_info['active']

                # Determine color based on quality
                if not active:
                    color = QColor(100, 100, 100)  # Gray for inactive
                    symbol = '○'
                elif quality == 'excellent':
                    color = QColor(76, 175, 80)  # Green
                    symbol = '●'
                elif quality == 'good':
                    color = QColor(139, 195, 74)  # Light green
                    symbol = '●'
                elif quality == 'fair':
                    color = QColor(255, 152, 0)  # Orange
                    symbol = '▲'
                elif quality == 'poor':
                    color = QColor(255, 87, 34)  # Red-orange
                    symbol = '✖'
                else:  # No signal
                    color = QColor(102, 102, 102)  # Dark gray
                    symbol = '○'

                # Add pulsing effect for active electrodes
                if active and quality in ['excellent', 'good']:
                    pulse_factor = 1 + 0.2 * math.sin(self.animation_step * 0.3)
                    radius = self.electrode_radius * pulse_factor
                else:
                    radius = self.electrode_radius

                # Draw electrode circle
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawEllipse(x - radius, y - radius, radius * 2, radius * 2)

                # Draw quality symbol
                painter.setPen(QPen(QColor(255, 255, 255)))
                symbol_rect = QtCore.QRect(x - 6, y - 6, 12, 12)
                painter.drawText(symbol_rect, QtCore.Qt.AlignCenter, symbol)

                # Draw channel label
                painter.setPen(QPen(QColor(255, 255, 255)))
                label_rect = QtCore.QRect(x - 15, y + radius + 2, 30, 15)
                painter.drawText(label_rect, QtCore.Qt.AlignCenter, channel_name)

                # Draw amplitude if significant
                if amplitude > 10:  # Only show if amplitude > 10μV
                    painter.setPen(QPen(QColor(200, 200, 200)))
                    painter.setFont(QFont('Arial', 7))
                    amp_text = f"{amplitude:.0f}μV"
                    amp_rect = QtCore.QRect(x - 20, y + radius + 15, 40, 12)
                    painter.drawText(amp_rect, QtCore.Qt.AlignCenter, amp_text)
                    painter.setFont(QFont('Arial', 8, QFont.Bold))

    def draw_electrode_connections(self, painter):
        """Draw connections between related electrodes (optional feature)"""
        painter.setPen(QPen(QColor(100, 100, 100, 50), 1, QtCore.Qt.DashLine))

        # Example connections (can be customized)
        connections = [
            ('Fp1', 'F3'), ('F3', 'C3'), ('C3', 'P3'), ('P3', 'O1'),
            ('Fp2', 'F4'), ('F4', 'C4'), ('C4', 'P4'), ('P4', 'O2'),
            ('F7', 'T7'), ('T7', 'P7'), ('F8', 'T8'), ('T8', 'P8'),
        ]

        for ch1, ch2 in connections:
            if ch1 in self.electrode_positions and ch2 in self.electrode_positions:
                x1, y1 = self.electrode_positions[ch1]
                x2, y2 = self.electrode_positions[ch2]
                painter.drawLine(x1, y1, x2, y2)

    def update_quality_data(self, channel_qualities):
        """Update quality data for all channels"""
        for i, (quality_score, amplitude) in enumerate(channel_qualities):
            if i < len(self.channel_names):
                channel_name = self.channel_names[i]

                # Convert quality score to quality level
                if quality_score >= 0.8:
                    quality = 'excellent'
                elif quality_score >= 0.6:
                    quality = 'good'
                elif quality_score >= 0.4:
                    quality = 'fair'
                elif quality_score >= 0.2:
                    quality = 'poor'
                else:
                    quality = 'no_signal'

                self.quality_data[channel_name] = {
                    'quality': quality,
                    'amplitude': amplitude,
                    'active': True
                }

        self.update()  # Trigger repaint

    def update_single_channel_quality(self, channel_name, quality, amplitude):
        """Update quality for a single channel"""
        if channel_name in self.quality_data:
            self.quality_data[channel_name].update({
                'quality': quality,
                'amplitude': amplitude,
                'active': True
            })
            self.update()

    def set_channel_active(self, channel_name, active=True):
        """Set channel active/inactive status"""
        if channel_name in self.quality_data:
            self.quality_data[channel_name]['active'] = active
            self.update()

    def update_animation(self):
        """Update animation step for pulsing effects"""
        self.animation_step += 1
        if self.animation_step % 10 == 0:  # Update every 10 steps (1 second)
            self.update()

    def mousePressEvent(self, event):
        """Handle mouse clicks on electrodes"""
        click_x, click_y = event.x(), event.y()

        for channel_name, (x, y) in self.electrode_positions.items():
            distance = math.sqrt((click_x - x) ** 2 + (click_y - y) ** 2)
            if distance <= self.electrode_radius * 1.5:  # Allow some tolerance
                self.electrode_clicked.emit(channel_name)
                break

    def get_quality_summary(self):
        """Get summary of overall quality status"""
        if not self.quality_data:
            return "No data"

        quality_counts = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0, 'no_signal': 0}
        active_channels = 0

        for channel_data in self.quality_data.values():
            if channel_data['active']:
                active_channels += 1
                quality_counts[channel_data['quality']] += 1

        if active_channels == 0:
            return "No active channels"

        # Return the most common quality level
        max_quality = max(quality_counts, key=quality_counts.get)
        return f"Overall: {max_quality.title()} ({active_channels} channels)"


# ===================== DEMO APPLICATION =====================

class EEGHeadMapDemo(QtWidgets.QMainWindow):
    """Demo application for the EEG Head Map Widget"""

    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setup_demo_timer()

    def setupUI(self):
        self.setWindowTitle("EEG Head Map Demo")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QHBoxLayout()

        # Create head map widget
        self.head_map = EEGHeadMapWidget(board_id=0)  # Synthetic board
        self.head_map.electrode_clicked.connect(self.on_electrode_clicked)

        # Create control panel
        control_panel = self.create_control_panel()

        layout.addWidget(self.head_map)
        layout.addWidget(control_panel, 1)

        central_widget.setLayout(layout)

        # Set dark theme
        self.setStyleSheet("background-color: #2b2b2b; color: white;")

    def create_control_panel(self):
        """Create control panel for demo"""
        panel = QtWidgets.QWidget()
        layout = QVBoxLayout()

        # Title
        title = QLabel("Head Map Demo Controls")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Quality summary
        self.quality_summary = QLabel("Overall: Good (8 channels)")
        self.quality_summary.setStyleSheet("color: #4CAF50; font-weight: bold; padding: 5px;")
        layout.addWidget(self.quality_summary)

        # Demo buttons
        simulate_btn = QtWidgets.QPushButton("Simulate Quality Changes")
        simulate_btn.clicked.connect(self.simulate_quality_changes)
        layout.addWidget(simulate_btn)

        reset_btn = QtWidgets.QPushButton("Reset All Good")
        reset_btn.clicked.connect(self.reset_all_good)
        layout.addWidget(reset_btn)

        # Selected electrode info
        self.electrode_info = QLabel("Click an electrode for details")
        self.electrode_info.setStyleSheet("color: #bbb; padding: 10px; border: 1px solid #555;")
        layout.addWidget(self.electrode_info)

        layout.addStretch()
        panel.setLayout(layout)

        return panel

    def setup_demo_timer(self):
        """Setup timer for demo quality updates"""
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.update_demo_data)
        self.demo_timer.start(2000)  # Update every 2 seconds

    def update_demo_data(self):
        """Update demo data with random quality changes"""
        import random

        # Simulate quality data for available channels
        channel_qualities = []
        for i in range(len(self.head_map.channel_names)):
            quality_score = random.uniform(0.3, 1.0)
            amplitude = random.uniform(10, 100)
            channel_qualities.append((quality_score, amplitude))

        self.head_map.update_quality_data(channel_qualities)

        # Update summary
        summary = self.head_map.get_quality_summary()
        self.quality_summary.setText(summary)

    def simulate_quality_changes(self):
        """Simulate various quality scenarios"""
        import random

        scenarios = ['all_good', 'mixed', 'poor_contacts', 'no_signal']
        scenario = random.choice(scenarios)

        if scenario == 'all_good':
            qualities = [(random.uniform(0.8, 1.0), random.uniform(20, 60))
                         for _ in self.head_map.channel_names]
        elif scenario == 'mixed':
            qualities = [(random.uniform(0.2, 1.0), random.uniform(10, 80))
                         for _ in self.head_map.channel_names]
        elif scenario == 'poor_contacts':
            qualities = [(random.uniform(0.0, 0.3), random.uniform(5, 30))
                         for _ in self.head_map.channel_names]
        else:  # no_signal
            qualities = [(0.0, 0.0) for _ in self.head_map.channel_names]

        self.head_map.update_quality_data(qualities)
        self.quality_summary.setText(self.head_map.get_quality_summary())

    def reset_all_good(self):
        """Reset all channels to good quality"""
        qualities = [(0.9, 40.0) for _ in self.head_map.channel_names]
        self.head_map.update_quality_data(qualities)
        self.quality_summary.setText(self.head_map.get_quality_summary())

    def on_electrode_clicked(self, channel_name):
        """Handle electrode click"""
        if channel_name in self.head_map.quality_data:
            data = self.head_map.quality_data[channel_name]
            info_text = f"""
Electrode: {channel_name}
Quality: {data['quality'].title()}
Amplitude: {data['amplitude']:.1f} μV
Status: {'Active' if data['active'] else 'Inactive'}
            """.strip()
            self.electrode_info.setText(info_text)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    demo = EEGHeadMapDemo()
    demo.show()

    sys.exit(app.exec_())