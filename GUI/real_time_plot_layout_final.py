import os
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtWidgets
import sys
import config
import numpy as np

### set up of real-time layout ###       
def setup_gui():
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
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
        if i == 1:
            placement = 'Extensor Carpi Radialis' #'left'
        elif i == 2:
            placement = 'Extensor Carpi Ulnaris' #'right'
        else:
            placement = ' Flexor Carpi Radialis' #'center'
        p = view.addPlot(title=f'Channel {i}, raw ({placement})')
        p.setYRange(0, config.YRANGE_p1, padding=0)
        p.setLabel('left', 'Volt', units='V')
        p.setLabel('bottom', 'Time', units='s')
        plots.append(p)
        
        curves.append(p.plot(pen=pg.mkPen('y', width=1)))
    
    view.nextRow()
    
    #-- ROW 1, RMS PLOTS --#    
    for i in range(1, (config.N_CHANNELS + 1)):
        if i == 1:
            placement = 'Extensor Carpi Radialis' #'left'
        elif i == 2:
            placement = 'Extensor Carpi Ulnaris' #'right'
        else:
            placement = ' Flexor Carpi Radialis' #'center'
        p = view.addPlot(title=f'Channel {i}, RMS ({placement})')
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
    cwt_plot.setImage(np.zeros((config.N, config.FREQ), dtype=np.float32))
    p_cwt.setLabel('bottom', 'Time', unit= 's')
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
    
    cwt_colorbar = pg.ColorBarItem(values=(config.min_level_cwt, config.max_level_cwt), colorMap = cmap_cwt ,label = 'Power')
    cwt_colorbar.setImageItem(cwt_plot)
    view.addItem(cwt_colorbar, row = 3, col=3)
    
    ## heatmap ##
    p_hm = view.addPlot(title='RMS Heatmap (all channels)',row = 3, col = 0,  colspan=1)
    p_hm.setYRange(0, 3, padding = 0)
    p_hm.setLabel('bottom', 'Time', units='s')
    p_hm.setLabel('left', 'Electrode')

    yticks = [(0,'Channel 1'), (1,'Channel 2'), (2,'Channel 3')]
    p_hm.getAxis('left').setTicks([yticks])
    p_hm.setMouseEnabled(False, False)
    
    cmap_hm = pg.colormap.get('inferno')
    
    hm = pg.ImageItem()
    hm.setImage(np.zeros((3,config.HM_HISTORY), dtype=np.float32))
    hm.setLookupTable(cmap_hm.getLookupTable())
    hm.setLevels([config.min_level_hm, config.max_level_hm])
    p_hm.addItem(hm)
    
    hm_colorbar = pg.ColorBarItem(values=(config.min_level_hm, config.max_level_hm), colorMap = cmap_hm, label = 'RMS Magnitude')
    hm_colorbar.setImageItem(hm)
    view.addItem(hm_colorbar, row = 3, col=1)
    
    
    # Buttons #
    btn_start = QtWidgets.QPushButton('START')
    btn_start.setCheckable(True)  
    btn_start.setStyleSheet("background-color: #27ae60; color: white; height: 40px; font-weight: bold;margin-top: 50px;")
    control_v_layout.addWidget(btn_start)
    
    # Classification text and button#
    label_title = QtWidgets.QLabel('SELECT VIEW')
    label_title.setStyleSheet('color: white; font-weight: bold; margin-bottom: 10px; margin-top: 50px;')
    label_title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    control_v_layout.addWidget(label_title)
    
    button_widget = QtWidgets.QWidget()
    button_layout = QtWidgets.QVBoxLayout(button_widget)
    button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft) 
    
    control_v_layout.addSpacing(20) 
    
    btn_all_plots = QtWidgets.QPushButton('Show All')
    btn_ch1_all = QtWidgets.QPushButton('Channel 1')
    btn_ch2_all = QtWidgets.QPushButton('Channel 2')
    btn_ch3_all = QtWidgets.QPushButton('Channel 3')

    view_group = QtWidgets.QButtonGroup(main_win)
    view_buttons = [btn_all_plots, btn_ch1_all, btn_ch2_all, btn_ch3_all]
    
    for btn in view_buttons:
        btn.setCheckable(True)
        view_group.addButton(btn)
        control_v_layout.addWidget(btn)
        
    control_v_layout.addStretch()    
    btn_all_plots.setChecked(True) #all plots as standard view
    
    
    btn_classify = QtWidgets.QPushButton('Activate Classification')
    btn_classify.setCheckable(True)
    btn_classify.setStyleSheet(""" 
        color: #f1c40f; 
        background-color: #000; 
        border: 2px solid #f1c40f; 
        border-radius: 5px; 
        margin-top: 10px;
        padding: 10px;
    """)
    control_v_layout.addWidget(btn_classify)
    
    value_label = QtWidgets.QLabel('---')
    value_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    value_label.setStyleSheet("""
        font-size: 18pt; 
        color: #f1c40f; 
        background-color: #000; 
        border: 2px solid #f1c40f; 
        border-radius: 5px; 
        margin-top: 10px;
        padding: 10px;
    """)
    
    control_v_layout.addWidget(value_label)
    

    main_win.showMaximized()
    
    def toggle_view(mode): #toggle between the views, scalogram is only visible when viewing a specific channel

        if mode == 0:
            p_cwt.setVisible(False)
            cwt_colorbar.setVisible(False)
            for i in range(config.N_CHANNELS):
                plots[i].setVisible(False) #raw
                plots[i+config.N_CHANNELS].setVisible(True) #rms
        
        else:
            target_ch = mode - 1
            for i in range(config.N_CHANNELS):
                is_active = (i == target_ch)
                plots[i].setVisible(is_active) #raw
                plots[i+config.N_CHANNELS].setVisible(is_active) #rms
                
            if target_ch == 0:
                    placement = 'Extensor Carpi Radialis' #'left'
            elif target_ch == 1:
                    placement = 'Extensor Carpi Ulnaris' #'right'
            else:
                    placement = 'Flexor Carpi Radialis' #'center'
                    
            p_cwt.setTitle(f'Channel {mode}, CWT ({placement})')
            p_cwt.setVisible(True)
            cwt_colorbar.setVisible(True)
        update_btn_colors(view_buttons)
            
    def toggle_classification_ui():
    
        is_active = btn_classify.isChecked()
        
        if is_active:
            btn_classify.setText('LDA: ON')
            btn_classify.setStyleSheet('height: 40px; background-color: #27ae60')  
            value_label.setText('Waiting...')     
        else:
            btn_classify.setText('Activate LDA')
            btn_classify.setStyleSheet(""" 
        color: #f1c40f; 
        background-color: #000; 
        border: 2px solid #f1c40f; 
        border-radius: 5px; 
        margin-top: 10px;
        padding: 10px;
    """)  
            value_label.setText('---')              
        


    btn_classify.clicked.connect(toggle_classification_ui)  
  
    update_btn_colors(view_buttons) 

    return app, curves, hm, cwt_plot, main_win, btn_start, plots, value_label, btn_classify, btn_all_plots, btn_ch1_all, btn_ch2_all ,btn_ch3_all, toggle_view, p_cwt, p_hm

### updates button colors ###           
def update_btn_colors(view_buttons):
    for btn in view_buttons:
        if btn.isChecked():
            btn.setStyleSheet("""
                height: 45px; 
                background-color: #3498DB; 
                color: white; 
                font-weight: bold; 
                text-align: center; 
                padding-left: 10px;
                border: 1px solid #34495E;
            """)
        else:
            btn.setStyleSheet("""
                height: 45px; 
                background-color: #D3D3D3; 
                color: black; 
                text-align: center; 
                padding-left: 10px;
                border: 1px solid #BDBDBD;
            """)
    
