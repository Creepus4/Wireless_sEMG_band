import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import sys
import config
import numpy as np
    
def setup_gui():
    app = QtWidgets.QApplication(sys.argv)
    main_win = QtWidgets.QWidget()
    main_win.setWindowTitle('sEMG Real-time Monitor')
    
    main_h_layout = QtWidgets.QHBoxLayout(main_win)

    #graphs to the left
    graph_container = QtWidgets.QWidget()
    graph_layout = QtWidgets.QVBoxLayout(graph_container)
    view = pg.GraphicsLayoutWidget()
    graph_layout.addWidget(view)
    
    #buttons to the right
    control_panel = QtWidgets.QFrame()
    control_panel.setFixedWidth(200)
    control_panel.setStyleSheet("background-color: #2b2b2b; border-left: 1px solid #444;")
    control_v_layout = QtWidgets.QVBoxLayout(control_panel)
    control_v_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
    
    main_h_layout.addWidget(graph_container, stretch=5)
    main_h_layout.addWidget(control_panel, stretch=1)

    
    plots = []
    curves = []
     
    #-- ROW 0, RAW PLOTS --#
    
    for i in range(1, (config.N_CHANNELS + 1)):
        p = view.addPlot(title=f'Channel {i}, raw')
        p.setYRange(0, config.YRANGE_p1, padding=0)

        p.setLabel('left', 'Volt', units='V')
        p.setLabel('bottom', 'Time', units='s')
        plots.append(p)
        
        curves.append(p.plot(pen=pg.mkPen('y', width=1)))
    
    view.nextRow()
    
    #-- ROW 0, RMS PLOTS --#    
    for i in range(1, (config.N_CHANNELS + 1)):
        p = view.addPlot(title=f'Channel {i}, RMS')
        p.setYRange(0, config.YRANGE_p2, padding=0)
        p.setLabel('bottom', 'Time', units='s')
        p.setLabel('left', 'Volt', units='V')
        plots.append(p)
        
        curves.append(p.plot(pen=pg.mkPen('c', width=1)))
        
    view.nextRow()
        
    #CWT
    p_cwt = view.addPlot(title='CWT Channel 1',col = 2, row = 3, colspan = 1)
    cwt_plot = pg.ImageItem()
    p_cwt.addItem(cwt_plot)
    p_cwt.setLabel('bottom', 'Time', units='samples')
    p_cwt.setLabel('left', 'Frequency (Hz)')
    
    cmap_cwt = pg.colormap.get('inferno')
    cwt_plot.setLookupTable(cmap_cwt.getLookupTable())

    
    values_y = [10, 50, 100, 200, 500] #visible freqs on scalogram
    ticks=[]
    
    for i in values_y: #y axis on scalogram
        index = (np.log10(i) - np.log10(10)) / (np.log10(500) - np.log10(10)) * config.FREQ
        ticks.append((index, str(i)))
        
    ax_y = p_cwt.getAxis('left') 
    ax_y.setTicks([ticks])
    
    cwt_colorbar = pg.ColorBarItem(values=(config.min_level_cwt, config.max_level_cwt), colorMap = cmap_cwt ,label = 'Power (dB)')
    cwt_colorbar.setImageItem(cwt_plot)
    view.addItem(cwt_colorbar, row = 3, col=3)
    
    ## heatmap ##
    p_hm = view.addPlot(title='Heatmap (all channels)',row = 3, col = 0,  colspan=1)
    p_hm.setLabel('bottom', 'Time', units='s')
    p_hm.setLabel('left', 'Electrode')
    electrode_labels = ['Channel 1', 'Channel 2', 'Channel 3']
    yticks = [(i, label) for i, label in enumerate(electrode_labels)]
    p_hm.getAxis('left').setTicks([yticks])
    p_hm.setMouseEnabled(False, False)
    hm = pg.ImageItem()
    
    cmap_hm = pg.colormap.get('inferno')
    hm.setLookupTable(cmap_hm.getLookupTable())
    hm.setLevels([0, 1.0])
    hm_colorbar = pg.ColorBarItem(values=(config.min_level_hm, config.max_level_hm), colorMap = cmap_hm, label = 'Amplitude (V)')
    hm_colorbar.setImageItem(hm)
    view.addItem(hm_colorbar, row = 3, col=1)
    p_hm.addItem(hm)
    
    # Buttons #
    btn_start = QtWidgets.QPushButton('START')
    btn_start.setCheckable(True)  
    btn_start.setStyleSheet("background-color: #27ae60; color: white; height: 40px; font-weight: bold;margin-top: 50px;")
    control_v_layout.addWidget(btn_start)

    main_win.showMaximized()
    
    return curves, hm, cwt_plot, main_win, btn_start, plots

