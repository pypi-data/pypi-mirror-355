import logging
import sys
import typing

from PyQt5 import QtWidgets, QtCore, QtGui
from brainflow import BoardShim, BrainFlowInputParams, BoardIds
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

from connect import retrieve_unicorn_devices


class Graph(QtWidgets.QMainWindow):

    def __init__(self, board_shim, *args, **kwargs):
        super(Graph, self).__init__(*args, **kwargs)
        self.board_id = board_shim.get_board_id()
        self.board_shim = board_shim
        self.exg_channels = BoardShim.get_exg_channels(self.board_id)
        self.sampling_rate = BoardShim.get_sampling_rate(self.board_id)
        self.update_speed_ms = 250
        self.window_size = 4
        self.num_points = self.window_size * self.sampling_rate

        self.app = QtGui.QGuiApplication([])
        self.win = pg.GraphicsLayoutWidget(title='BrainFlow Plot', size=(800, 600))

        self._init_timeseries()

        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(self.update_speed_ms)

    def _init_timeseries(self):
        self.plots = list()
        self.curves = list()
        for i in range(len(self.exg_channels)):
            p = self.win.addPlot(row=i, col=0)
            p.showAxis('left', False)
            p.setMenuEnabled('left', False)
            p.showAxis('bottom', False)
            p.setMenuEnabled('bottom', False)
            if i == 0:
                p.setTitle('TimeSeries Plot')
            self.plots.append(p)
            curve = p.plot()
            self.curves.append(curve)

    def update(self):
        data = self.board_shim.get_current_board_data(self.num_points)
        avg_bands = [0, 0, 0, 0, 0]
        for count, channel in enumerate(self.exg_channels):
            # plot timeseries
            self.curves[count].setData(data[channel].tolist())

        self.app.processEvents()


def main():
    BoardShim.enable_dev_board_logger()
    # use synthetic board for demo
    params = BrainFlowInputParams()
    print(retrieve_unicorn_devices()[0][1])
    params.serial_number = retrieve_unicorn_devices()[0][1]
    try:
        board_shim = BoardShim(BoardIds.SYNTHETIC_BOARD.value, params)
        board_shim.prepare_session()
        board_shim.start_stream(450000)
        data = board_shim.get_board_data()
        app = QtWidgets.QApplication(sys.argv)
        w = Graph(board_shim)
        w.show()
        sys.exit(app.exec_())
    except BaseException as e:
        logging.warning('Exception', exc_info=True)
    finally:
        logging.info('End')
        if board_shim.is_prepared():
            logging.info('Releasing session')
            board_shim.release_session()


if __name__ == '__main__':
    main()
