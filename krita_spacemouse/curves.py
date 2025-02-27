from PyQt5.QtCore import QPointF, Qt
import pyqtgraph as pg
import numpy as np

def cubic_bezier(t, p0, p1, p2, p3):
    """Calculate point on a cubic Bezier curve."""
    t2 = t * t
    t3 = t2 * t
    mt = 1 - t
    mt2 = mt * mt
    mt3 = mt2 * mt
    return mt3 * p0 + 3 * mt2 * t * p1 + 3 * mt * t2 * p2 + t3 * p3

class BezierCurveEditor(pg.GraphicsLayoutWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot = self.addPlot()
        self.plot.setRange(xRange=[0, 1], yRange=[0, 1])
        self.plot.setLabel("left", "Output Value")
        self.plot.setLabel("bottom", "Input Value")
        self.plot.setAspectLocked(True)
        self.plot.showGrid(x=True, y=True)

        self.control_points = [
            QPointF(0.0, 0.0),
            QPointF(0.25, 0.25),
            QPointF(0.75, 0.75),
            QPointF(1.0, 1.0)
        ]

        self.curve = self.plot.plot(pen='b')
        self.control_lines = self.plot.plot(pen='g', style=Qt.DashLine)
        self.control_points_items = [
            self.plot.plot([p.x()], [p.y()], pen=None, symbol='o', symbolPen='r', symbolSize=10)
            for p in self.control_points
        ]

        self.update_curve()
        self.plot.scene().sigMouseMoved.connect(self.on_mouse_moved)
        self.plot.scene().sigMouseClicked.connect(self.on_mouse_clicked)
        self.dragging = None

    def update_curve(self):
        t = np.linspace(0, 1, 100)
        x = [cubic_bezier(ti, self.control_points[0].x(), self.control_points[1].x(),
                          self.control_points[2].x(), self.control_points[3].x()) for ti in t]
        y = [cubic_bezier(ti, self.control_points[0].y(), self.control_points[1].y(),
                          self.control_points[2].y(), self.control_points[3].y()) for ti in t]
        self.curve.setData(x, y)
        self.control_lines.setData(
            [p.x() for p in self.control_points],
            [p.y() for p in self.control_points]
        )
        for i, item in enumerate(self.control_points_items):
            item.setData([self.control_points[i].x()], [self.control_points[i].y()])
        self.plot.getViewBox().update()  # Fixed: Use getViewBox() instead of plotItem.vb
        self.plot.replot()  # Force full replot

    def on_mouse_moved(self, pos):
        if self.dragging is not None and self.dragging in [1, 2]:
            scene_pos = self.plot.vb.mapSceneToView(pos)
            x, y = max(0, min(1, scene_pos.x())), max(0, min(1, scene_pos.y()))
            if self.dragging == 1:
                x = min(x, self.control_points[2].x())
            elif self.dragging == 2:
                x = max(x, self.control_points[1].x())
            self.control_points[self.dragging] = QPointF(x, y)
            self.update_curve()
            if hasattr(self, 'parent_widget'):
                self.parent_widget.save_current_settings()

    def on_mouse_clicked(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.plot.vb.mapSceneToView(event.scenePos())
            x, y = pos.x(), pos.y()
            for i, p in enumerate(self.control_points):
                if i in [1, 2] and abs(p.x() - x) < 0.05 and abs(p.y() - y) < 0.05:
                    self.dragging = i
                    return
        elif event.button() == Qt.RightButton:
            self.dragging = None

    def get_curve_value(self, input_val):
        t = max(0, min(1, input_val))
        return cubic_bezier(t, self.control_points[0].y(), self.control_points[1].y(),
                            self.control_points[2].y(), self.control_points[3].y())
