import sys
from PyQt4 import QtGui

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.pylab as plt
import numpy

import random

class Window(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QtGui.QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        self.setLayout(layout)
    def set_tfm(self, tfm):
        self.tfm = tfm
        
    def plot(self):
        ''' plot some random stuff '''

        # create an axis
        ax = self.figure.add_subplot(111)

        # discards the old graph
        ax.hold(False)
        
        
        data = self.tfm* self.tfm.T
        plt.imshow(data,  interpolation='nearest', cmap=plt.cm.ocean, aspect='auto')
        plt.colorbar()
        # refresh canvas
        self.canvas.draw()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    tfm = numpy.load("term_frequency.dat")
    main = Window()
    # pass the matrix to be plotted
    main.set_tfm(tfm)
    
    main.show()

    sys.exit(app.exec_())
