import serial
import os
import sys
import wx
import wx.adv
from wx.lib.wordwrap import wordwrap
import wx.lib.scrolledpanel as scrolled
import RRpanelList
import RRdeviceSettings
import RRserialConfig
import RRfile
import RRserial
import ArduProg
from time import sleep

SOFTWARE_VERSION = "1.8"

ID_UPGRADE = 0
ID_REFRESH = 1
ID_OPEN = 2
ID_SAVE = 3
ID_FILESET = 4
ID_PORTSET = 5
ID_CVSET = 6
ID_RECON = 7
ID_COLOR = 8
ID_ABOUT = 9
ID_EXIT = 10
ID_UPDATE = 11


def resource_path(relative_path, meipass=False):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if meipass:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)


def main_name():
    temp = os.getcwd()
    basename = os.path.basename(__file__)
    os.chdir(os.path.join(getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))))
    for root, dirs, files in os.walk("."):
        for name in files:
            if name[-8:] == "manifest":  # name.exe.manifest
                os.chdir(temp)
                return name[:-13]
    os.chdir(temp)
    return basename[:-3] if basename[-2:] == "py" else ""


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.serial = serial.Serial()
        self.newserial = self.serial
        self.serial.timeout = 1  # make sure that the alive event can be checked from time to time
        self.serialok = False
        self.reconnect = False
        self.first = True
        self.panels = 1
        self.devtype = 0
        self.cv28mask = 0
        self.maxLNCV = 10
        self.upgrade_path = ""
        self.upgrade_file = ""
        self.version_file = None
        self.color = (170, 170, 170)  # (0, 100, 250)  # wx.YELLOW

        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        self.SetBackgroundColour(self.color)

        self.dirfile = os.path.dirname(resource_path("icon.ico"))

        icon = wx.Icon(resource_path("icon.ico", True))
        self.SetIcon(icon)

        self.dev = RRdeviceSettings.Device()
        self.devsel = None

        self.filemanager = RRfile.RRfileManager(self, self.serial)

        self.com = RRserial.SerialCom(self.serial)

        # Menu Bar
        self.frame_terminal_menubar = wx.MenuBar()
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(ID_UPDATE, "&Check for Update", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(ID_UPGRADE, "&Upgrade...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_REFRESH, "&Refresh...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_OPEN, "&Open .cv file", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(ID_SAVE, "&Save .cv file", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_EXIT, "&Exit", "", wx.ITEM_NORMAL)
        self.frame_terminal_menubar.Append(wxglade_tmp_menu, "&File")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(ID_FILESET, "&Device Settings", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(ID_PORTSET, "&Port Settings", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_CVSET, "&Direct CV Set", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(ID_RECON, "&Reconnect...", "", wx.ITEM_NORMAL)
        self.frame_terminal_menubar.Append(wxglade_tmp_menu, "&Settings")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(ID_COLOR, "&Color...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.Append(ID_ABOUT, "&About", "", wx.ITEM_NORMAL)
        self.frame_terminal_menubar.Append(wxglade_tmp_menu, "&Help")
        self.SetMenuBar(self.frame_terminal_menubar)
        # Menu Bar end

        self.Bind(wx.EVT_MENU, self.OnUpdate, id=ID_UPDATE)
        self.Bind(wx.EVT_MENU, self.OnUpgrade, id=ID_UPGRADE)
        self.Bind(wx.EVT_MENU, self.OnRefresh, id=ID_REFRESH)
        self.Bind(wx.EVT_MENU, self.OnOpen, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnExit, id=ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnDeviceSettings, id=ID_FILESET)
        self.Bind(wx.EVT_MENU, self.OnPortSettings, id=ID_PORTSET)
        self.Bind(wx.EVT_MENU, self.OnCVSettings, id=ID_CVSET)
        self.Bind(wx.EVT_MENU, self.OnReconnect, id=ID_RECON)
        self.Bind(wx.EVT_MENU, self.OnColor, id=ID_COLOR)
        self.Bind(wx.EVT_MENU, self.OnAbout, id=ID_ABOUT)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # costruisco il frame
        self.OnPortSettings(None)
        if self.serialok:
            sleep(1.2)
            self.OnDeviceSettings(None)
            if self.devsel is not None:
                self.serial.flush()
                tim = self.serial.timeout
                if self.devsel > self.dev.Device_AccDec_8Servo_LN_USB and self.serial.timeout < 5.0:
                    self.serial.timeout = 5.0
                self.__set_properties()
                self.__do_layout()
                self.__check_version()
                self.serial.timeout = tim
                self.first = False
            else:
                self.OnClose(None)
        else:
            self.OnClose(None)

    def __set_properties(self):
        self.__device_type()

        self.sizer_4 = wx.BoxSizer(wx.VERTICAL)

        self.scrollpanel = scrolled.ScrolledPanel(self, 1, style=wx.TAB_TRAVERSAL | wx.SUNKEN_BORDER)
        self.scrollpanel.SetAutoLayout(1)
        self.scrollpanel.SetupScrolling()

        self.panel = wx.Panel(self.scrollpanel)
        self.panel.SetBackgroundColour(self.color)

        self.sizer_0 = wx.BoxSizer(wx.VERTICAL)

        self.line_1 = wx.StaticLine(self.scrollpanel, -1, style=wx.LI_HORIZONTAL)
        self.sizer_0.Add(self.line_1, 0, wx.GROW | wx.TOP, 1)

        self.panel_CV1_RESET_1 = RRpanelList.CV1Panel(self.scrollpanel, self, bcolor=self.color, serial=self.serial)
        self.panel_CV1_RESET_2 = RRpanelList.CV1Panel(self.scrollpanel, self, bcolor=self.color, serial=self.serial)
        self.panel_CV28_1 = RRpanelList.CV28Panel(self.scrollpanel, self, bcolor=self.color,
                                                  serial=self.serial, show_safe=self.devtype)
        self.panel_CV28_2 = RRpanelList.CV28Panel(self.scrollpanel, self, bcolor=self.color,
                                                  serial=self.serial, show_safe=self.devtype)
        self.panel_LNCV_RESET = RRpanelList.LNCVResetPanel(self.scrollpanel, self, bcolor=self.color,
                                                           serial=self.serial)
        self.panel_PLMove = RRpanelList.MovePanel(self.scrollpanel, self, bcolor=self.color, serial=self.serial, out=0)

        self.sizer_2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer_2.Add(self.panel_CV1_RESET_1)
        self.line__2 = wx.StaticLine(self.scrollpanel, -1, style=wx.LI_HORIZONTAL)
        self.sizer_2.Add(self.line__2, 0, wx.GROW | wx.TOP | wx.BOTTOM, 1)
        self.sizer_2.Add(self.panel_CV28_1)
        self.sizer_2.Add(self.panel_LNCV_RESET, 0, wx.CENTRE)
        self.sizer_0.Add(self.sizer_2)

        self.sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_3.Add(self.panel_CV1_RESET_2)
        self.sizer_3.Add(self.panel_CV28_2)
        self.sizer_3.Add(self.panel_PLMove, 0, wx.LEFT | wx.RIGHT, 5)
        self.sizer_0.Add(self.sizer_3)

        self.line_2 = wx.StaticLine(self.scrollpanel, -1, style=wx.LI_HORIZONTAL)
        self.sizer_0.Add(self.line_2, 0, wx.EXPAND | wx.BOTTOM, 1)

        self.panel_PLSet = RRpanelList.PLSetPanel(self.scrollpanel, self, self.color, self.serial)
        self.sizer_0.Add(self.panel_PLSet, 0, wx.ALL, 0)

        self.line_3 = wx.StaticLine(self.scrollpanel, -1, style=wx.LI_HORIZONTAL)
        self.sizer_0.Add(self.line_3, 0, wx.EXPAND | wx.BOTTOM, 1)

        self.panel_PLConf = RRpanelList.PLConfPanel(self.scrollpanel, self, self.color, self.serial)
        self.sizer_0.Add(self.panel_PLConf, 0, wx.ALL, 0)

        self.line__3 = wx.StaticLine(self.scrollpanel, -1, style=wx.LI_HORIZONTAL)
        self.sizer_0.Add(self.line__3, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 1)

        self.sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.label_1 = wx.StaticText(self.panel, -1, "                              Left position")
        self.label_2 = wx.StaticText(self.panel, -1, "                      Right position")
        self.label_3 = wx.StaticText(self.panel, -1, "")
        self.label_4 = wx.StaticText(self.panel, -1, "                          Speed")
        self.label_5 = wx.StaticText(self.panel, -1, "                              Options "
                                                     "                       Start Position")
        self.label_6 = wx.StaticText(self.panel, -1, "                                                Move")
        self.label_7 = wx.StaticText(self.panel, -1, "                      Posizione Aperto"
                                                     "         Posizione Chiuso"
                                                     "        Posizione Attuale"
                                                     "         Ritardo Chiusura"
                                                     "         Ritardo Apertura")
        font = wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.label_1.SetFont(font)
        self.label_2.SetFont(font)
        self.label_3.SetFont(font)
        self.label_4.SetFont(font)
        self.label_5.SetFont(font)
        self.label_6.SetFont(font)
        font = wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        self.label_7.SetFont(font)
        self.sizer_1.Add(self.label_1, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.label_2, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.label_3, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.label_4, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.label_5, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.label_6, 0, wx.ALIGN_CENTER, 0)
        self.sizer_1.Add(self.label_7, 0, wx.ALIGN_CENTER, 0)
        self.panel.SetSizer(self.sizer_1)
        self.sizer_0.Add(self.panel, 0, 0, 5)

        self.line_4 = wx.StaticLine(self.scrollpanel, -1, style=wx.LI_HORIZONTAL)
        self.sizer_0.Add(self.line_4, 0, wx.EXPAND | wx.TOP, 1)

        self.panel_Servo = []
        self.panel_Coil = []
        self.panel_LNCV = []
        self.panel_PL = []

        scroll = self.GetScrollType()

        for x in range(8):
            self.panel_Servo.append(RRpanelList.ServoPanel(self.scrollpanel, self, bcolor=self.color,
                                                           serial=self.serial, out=x, slider_c_type=scroll))
            self.sizer_0.Add(self.panel_Servo[x])
            self.panel_Coil.append(RRpanelList.CoilPanel(self.scrollpanel, self, bcolor=self.color,
                                                         serial=self.serial, out=x))
            self.sizer_0.Add(self.panel_Coil[x])

        for x in range(self.maxLNCV):
            self.panel_LNCV.append(RRpanelList.LNCVPanel(self.scrollpanel, self, bcolor=self.color,
                                                         serial=self.serial, out=x))
            self.sizer_0.Add(self.panel_LNCV[x])

        for x in range(4):
            self.panel_PL.append(RRpanelList.PLSliderPanel(self.scrollpanel, self, bcolor=self.color,
                                                           serial=self.serial, out=x))
            self.sizer_0.Add(self.panel_PL[x])

        self.sizer_0.Add((22, 22))
        self.scrollpanel.SetSizer(self.sizer_0)
        self.sizer_4.Add(self.scrollpanel, -1, wx.EXPAND)

    def __do_layout(self):
        # self.Show(False)
        self.__device_type()

        if self.devsel == self.dev.Device_AccDec_8Servo_LN_USB:
            # self.label_3.SetLabel("              Invert position")
            self.label_3.SetLabel("")
        else:
            self.label_3.SetLabel("                  Center position")

        if self.devtype == self.dev.Type_Coils:
            self.line_1.Show()
            self.line_2.Show()
            self.line_3.Hide()
            self.line_4.Show()
            self.label_1.Hide()
            self.label_2.Hide()
            self.label_3.Hide()
            self.label_4.Hide()
            self.label_5.Hide()
            self.label_6.Hide()
            self.label_7.Hide()
            self.panel_CV1_RESET_1.Show()
            self.panel_CV1_RESET_2.Hide()
            self.panel_CV28_1.Show()
            self.panel_CV28_1.ShowSafe(True)
            self.panel_CV28_2.Hide()
            self.panel_CV28_2.ShowSafe(False)
            self.panel_PLMove.Hide()
            self.panel_LNCV_RESET.Hide()
            self.panel_PLConf.Hide()
            self.panel_PLSet.Hide()
            self.line__2.Show()
            self.line__3.Hide()
        elif self.devtype == self.dev.Type_Servos:
            self.line_1.Show()
            self.line_2.Show()
            self.line_3.Hide()
            self.line_4.Show()
            self.label_1.Show()
            self.label_2.Show()
            self.label_3.Show()
            self.label_4.Show()
            self.label_5.Show()
            self.label_6.Show()
            self.label_7.Hide()
            self.panel_CV1_RESET_1.Hide()
            self.panel_CV1_RESET_2.Show()
            self.panel_CV28_1.Hide()
            self.panel_CV28_1.ShowSafe(False)
            self.panel_CV28_2.Show()
            self.panel_CV28_2.ShowSafe(False)
            self.panel_PLMove.Hide()
            self.panel_LNCV_RESET.Hide()
            self.panel_PLConf.Hide()
            self.panel_PLSet.Hide()
            self.line__2.Hide()
            self.line__3.Hide()
        elif self.devtype == self.dev.Type_Loconet:
            self.line_1.Hide()
            self.line_2.Hide()
            self.line_3.Hide()
            self.line_4.Show()
            self.label_1.Hide()
            self.label_2.Hide()
            self.label_3.Hide()
            self.label_4.Hide()
            self.label_5.Hide()
            self.label_6.Hide()
            self.label_7.Hide()
            self.panel_CV1_RESET_1.Hide()
            self.panel_CV1_RESET_2.Hide()
            self.panel_CV28_1.Hide()
            self.panel_CV28_1.ShowSafe(False)
            self.panel_CV28_2.Hide()
            self.panel_CV28_2.ShowSafe(False)
            self.panel_PLMove.Hide()
            self.panel_LNCV_RESET.Show()
            self.panel_PLConf.Hide()
            self.panel_PLSet.Hide()
            self.line__2.Hide()
            self.line__3.Hide()
            for x in range(8):
                self.panel_Servo[x].Hide()
                self.panel_Coil[x].Hide()
                if x < 4:
                    self.panel_PL[x].Hide()
        elif self.devtype == self.dev.Type_PL_sound:
            self.line_1.Show()
            self.line_2.Show()
            self.line_3.Show()
            self.line_4.Show()
            self.label_1.Hide()
            self.label_2.Hide()
            self.label_3.Hide()
            self.label_4.Hide()
            self.label_5.Hide()
            self.label_6.Hide()
            self.label_7.Show()
            self.panel_CV1_RESET_1.Hide()
            self.panel_CV1_RESET_2.Show()
            self.panel_CV28_1.Hide()
            self.panel_CV28_1.ShowSafe(False)
            self.panel_CV28_2.Hide()
            self.panel_CV28_2.ShowSafe(False)
            self.panel_PLMove.Show()
            self.panel_LNCV_RESET.Hide()
            self.panel_PLConf.Show()
            self.panel_PLSet.Show()
            self.line__2.Show()
            self.line__3.Show()

        ok = None
        if self.devtype == self.dev.Type_Loconet:
            try:
                self.panel_LNCV_RESET.onGetInd(None)
            except serial.serialutil.SerialTimeoutException as e:
                ok = e

            for x in range(self.maxLNCV):
                if x + 1 > self.panels:
                    self.panel_LNCV[x].Hide()
                else:
                    self.panel_LNCV[x].Show()
                    try:
                        self.panel_LNCV[x].onGetLNCV(None)
                    except serial.serialutil.SerialTimeoutException as e:
                        ok = e
        else:
            try:
                self.panel_CV28_1.onGetAll(None)
                self.panel_CV28_1.SetMask(self.cv28mask)
            except serial.serialutil.SerialTimeoutException as e:
                ok = e
            try:
                self.panel_CV28_2.onGetAll(None)
                self.panel_CV28_2.SetMask(self.cv28mask)
            except serial.serialutil.SerialTimeoutException as e:
                ok = e
            try:
                self.panel_CV1_RESET_1.onGetInd(None)
            except serial.serialutil.SerialTimeoutException as e:
                ok = e
            try:
                self.panel_CV1_RESET_2.onGetInd(None)
            except serial.serialutil.SerialTimeoutException as e:
                ok = e

            if self.panel_PLConf.IsShown():
                try:
                    self.panel_PLConf.onGetA()
                    self.panel_PLSet.onGetInd(None)
                except serial.serialutil.SerialTimeoutException as e:
                    ok = e

            for x in range(8):
                self.panel_Servo[x].checkFunctionsAvailable()
                self.panel_Servo[x].refreshSliderC(self.GetScrollType())

                if x + 1 > self.panels:
                    self.panel_Servo[x].Hide()
                    self.panel_Coil[x].Hide()
                else:
                    if self.devtype == self.dev.Type_Coils:
                        self.panel_Servo[x].Hide()
                        self.panel_Coil[x].Show()
                        if x < 4:
                            self.panel_PL[x].Hide()
                        try:
                            self.panel_Coil[x].ongetA(None)
                        except serial.serialutil.SerialTimeoutException as e:
                            ok = e
                    elif self.devtype == self.dev.Type_Servos:
                        self.panel_Coil[x].Hide()
                        self.panel_Servo[x].Show()
                        if x < 4:
                            self.panel_PL[x].Hide()
                        try:
                            self.panel_Servo[x].ongetA(None)
                        except serial.serialutil.SerialTimeoutException as e:
                            ok = e
                    elif self.devtype == self.dev.Type_PL_sound:
                        self.panel_Coil[x].Hide()
                        self.panel_Servo[x].Hide()
                        self.panel_PL[x].Show()
                        try:
                            self.panel_PL[x].ongetA(None)
                        except serial.serialutil.SerialTimeoutException as e:
                            ok = e

            for x in range(self.maxLNCV):
                self.panel_LNCV[x].Hide()

        self.scrollpanel.SetupScrolling(scroll_x=True, scroll_y=True, rate_x=5, rate_y=5)
        self.SetSizer(self.sizer_4)
        self.sizer_0.Fit(self)
        self.Layout()
        self.CenterOnScreen()
        # self.Show(True)

        if ok is None:
            if self.reconnect:
                self.reconnect = False
                with wx.MessageDialog(self, 'Done', 'Info', wx.OK | wx.ICON_INFORMATION) as dlg:
                    dlg.CenterOnScreen()
                    dlg.ShowModal()
        else:
            with wx.MessageDialog(None, str(ok) + "\nPress OK to exit...",
                                  "Serial Port Error", wx.OK | wx.ICON_ERROR)as dlg:
                dlg.CenterOnParent()
                dlg.ShowModal()
            self.OnClose(None)

    def __device_type(self):
        self.devsel = self.dev.GetDevice()
        if self.devsel == self.dev.Device_AccDec_4Coil_4Relais:
            self.panels = 4
            self.devtype = self.dev.Type_Coils
            self.cv28mask = RRpanelList.CV_28_INV_DIR | \
                            RRpanelList.CV_28_SAVE_POS | \
                            RRpanelList.CV_28_PULSE | \
                            RRpanelList.CV_28_EN_TASTER | \
                            RRpanelList.CV_28_EN_MULTI_ADR
        elif self.devsel == self.dev.Device_AccDec_4Servos_4Relais:
            self.panels = 4
            self.devtype = self.dev.Type_Servos
            self.cv28mask = RRpanelList.CV_28_INV_DIR | \
                            RRpanelList.CV_28_SAVE_POS | \
                            RRpanelList.CV_28_EN_TASTER | \
                            RRpanelList.CV_28_EN_MULTI_ADR
        elif self.devsel == self.dev.Device_AccDec_8Coil:
            self.panels = 8
            self.devtype = self.dev.Type_Coils
            self.cv28mask = RRpanelList.CV_28_INV_DIR | \
                            RRpanelList.CV_28_SAVE_POS | \
                            RRpanelList.CV_28_PULSE | \
                            RRpanelList.CV_28_EN_MULTI_ADR
        elif self.devsel == self.dev.Device_AccDec_8Servos_8Relais:
            self.panels = 8
            self.devtype = self.dev.Type_Servos
            self.cv28mask = RRpanelList.CV_28_INV_DIR | \
                            RRpanelList.CV_28_SAVE_POS | \
                            RRpanelList.CV_28_EN_MULTI_ADR
        elif self.devsel == self.dev.Device_AccDec_8Servo_LN_USB:
            self.panels = 8
            self.devtype = self.dev.Type_Servos
            self.cv28mask = RRpanelList.CV_28_INV_DIR | \
                            RRpanelList.CV_28_SAVE_POS | \
                            RRpanelList.CV_28_EN_USB_LN | \
                            RRpanelList.CV_28_EN_MULTI_ADR | \
                            RRpanelList.CV_28_EN_DCC_LN
        elif self.devsel == self.dev.Device_LoconetFeedback8Led:
            self.panels = self.maxLNCV
            self.devtype = self.dev.Type_Loconet
            self.cv28mask = 0
        elif self.devsel == self.dev.Device_LoconetRailcomFeedback4Led:
            self.panels = self.maxLNCV
            self.devtype = self.dev.Type_Loconet
            self.cv28mask = 0
        elif self.devsel == self.dev.Device_AccDec_PL_Sound:
            self.panels = 4
            self.devtype = self.dev.Type_PL_sound
            self.cv28mask = 0

    def __check_version(self):
        ok = False
        self.version_hw = self.com.GetHWversion()
        self.version_sw = self.com.GetSWversion()
        print("HW_VERSION =", self.version_hw)
        print("SW_VERSION =", self.version_sw)

        hex_dir = self.dirfile + "\\HEX\\"
        self.version_file = hex_dir + "\\versions.conf"

        if os.path.exists(self.version_file):
            version_table = self.filemanager.readVersions(self.version_file, self.devsel)

            if self.first:
                self.color = self.filemanager.GetColor()
                self.SetColor(self.color)

            for i in range(len(version_table)):
                if version_table[i][1] == self.version_hw:
                    print("HW_VERSION find")
                    if version_table[i][2] > self.version_sw:
                        print("SW_VERSION is old")
                        self.upgrade_path = hex_dir + version_table[i][0]
                        self.upgrade_file = version_table[i][0]
                        print("upgrade path:", self.upgrade_path)
                        print("upgrade file:", self.upgrade_file)

                        if os.path.exists(self.upgrade_path):
                            ok = True
                            with wx.MessageDialog(self, "New software version available!\n\nDo you wont to install it?"
                                                        + "\n\nActual: " + str(self.version_sw / 10) + "    Newone: " +
                                                        str((version_table[i][2]) / 10.0),
                                                  "New sw available", wx.YES | wx.NO | wx.ICON_INFORMATION) as dlg:
                                dlg.CenterOnParent()
                                if dlg.ShowModal() == wx.ID_YES:
                                    self.OnUpgrade(None)
                    else:
                        print("SW_VERSION is up to date, no upgrade required")
                break
        return ok

    def GetScrollType(self):
        if self.devsel == self.dev.Device_AccDec_8Servo_LN_USB:
            return "INVERT"
        else:
            return "RELE"

    def OnExit(self, event):
        """Menu point Exit"""
        self.serial.close()
        self.Close()

    def OnClose(self, event):
        """Called on application shutdown."""
        self.serial.close()  # cleanup
        self.Destroy()  # close windows, exit app

    def OnUpdate(self, event):
        if not self.__check_version():
            with wx.MessageDialog(self, 'Your decoder is up to date!', ' ',
                                  wx.OK | wx.ICON_INFORMATION) as dlg:
                dlg.CenterOnScreen()
                dlg.ShowModal()

    def OnUpgrade(self, event):
        if self.devsel < self.dev.Device_LoconetFeedback8Led or \
           self.devsel > self.dev.Device_LoconetRailcomFeedback4Led:
            conf_ = self.panel_CV1_RESET_1
        else:
            conf_ = self.panel_LNCV_RESET

        if event:
            self.upgrade_file = ""
            self.upgrade_path = ""

        upgrade = MyUpgrader(parent=self, conf=conf_, title=" Uploader ",
                             micro=1 if self.dev.GetDevice() == 4 else 0, uploadtype=1,
                             show=False, avrdudedir=self.dirfile, serial=self.serial, bcolor=self.color,
                             default=self.upgrade_file, pathHex=self.upgrade_path)

        if event is None:
            upgrade.uploadFile(None)

    def OnRefresh(self, event):
        self.__do_layout()

    def OnOpen(self, event):
        self.filemanager.Open(self.devsel)
        if self.filemanager.GetSet():
            self.__do_layout()

    def OnSave(self, event):
        if self.panel_CV1_RESET_1.IsShown():
            val = self.panel_CV1_RESET_1.GetCV1()
        elif self.panel_CV1_RESET_2.IsShown():
            val = self.panel_CV1_RESET_2.GetCV1()
        elif self.panel_LNCV[0].IsShown():
            val = self.panel_LNCV[0].GetLNCV()
        else:
            val = ""

        self.filemanager.Save(self.dev.GetName(), val)

    def OnPortSettings(self, event):
        self.serialok = False
        with RRserialConfig.SerialConfigDialog(
                self,
                -1,
                "",
                show=RRserialConfig.SHOW_ALL,
                serial=self.newserial) as dialog_serial_cfg:
            dialog_serial_cfg.CenterOnScreen()
            result = dialog_serial_cfg.ShowModal()
        # open port if not called on startup, open it on startup and OK too
        if result == wx.ID_OK:
            self.serial.close()
            self.serial = self.newserial
            try:
                self.serial.open()
            except serial.SerialException as e:
                with wx.MessageDialog(self, str(e), "Serial Port Error", wx.OK | wx.ICON_ERROR)as dlg:
                    dlg.CenterOnParent()
                    dlg.ShowModal()
                self.OnPortSettings(None)
            else:
                self.serialok = True
                if not self.first:
                    for x in range(8):
                        self.panel_Servo[x].EnableAllButtons(True)
                        self.panel_Coil[x].EnableAllButtons(True)

    def OnDeviceSettings(self, event):
        with RRdeviceSettings.DeviceSettingsDialog(self, -1, "", serial=self.serial, device=self.dev) as dialog:
            dialog.CenterOnScreen()
            result = dialog.ShowModal()
        if result == wx.ID_OK:
            devsel = self.dev.GetDevice()
            if devsel != self.devsel:
                self.devsel = devsel
                if not self.first:
                    self.__do_layout()

    def OnCVSettings(self, event):
        with RRpanelList.CVdialog(self, -1, "CV Settings", bcolor=self.color, serial=self.serial) as dialog:
            dialog.CenterOnScreen()
            dialog.ShowModal()
        self.__do_layout()

    def OnReconnect(self, event, onlyopen=False):
        if not onlyopen:
            self.serial.close()
            sleep(0.5)
        try:
            if self.devsel == self.dev.Device_AccDec_8Servo_LN_USB or self.devsel == self.dev.Device_AccDec_PL_Sound:
                sleep(2.0)
            self.serial.open()
        except serial.SerialException as e:
            with wx.MessageDialog(self, str(e), "Serial Port Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.CenterOnParent()
                dlg.ShowModal()
            self.OnPortSettings(None)
        else:
            tim = self.serial.timeout
            self.serial.timeout = 10
            sleep(3)
            self.dev.SetDevice(self.com.GetDeviceID())
            self.reconnect = True
            self.__do_layout()
            self.serial.timeout = tim

    def OnColor(self, event):
        dlg = wx.ColourDialog(self)
        dlg.CenterOnParent()

        # Ensure the full colour dialog is displayed,
        # not the abbreviated version.
        dlg.GetColourData().SetChooseFull(True)

        if dlg.ShowModal() == wx.ID_OK:
            # ... then do something with it. The actual colour data will be
            # returned as a three-tuple (r, g, b) in this particular case.
            self.color = dlg.GetColourData().GetColour().Get()
            self.SetColor(self.color)

            if os.path.exists(self.version_file):
                self.filemanager.SetColor(self.version_file, self.color)

        dlg.Destroy()

    def SetColor(self, color):
        self.SetBackgroundColour(color)
        self.scrollpanel.SetBackgroundColour(color)
        self.panel.SetBackgroundColour(color)
        self.panel_CV1_RESET_1.SetBackgroundColour(color)
        self.panel_CV1_RESET_2.SetBackgroundColour(color)
        self.panel_CV28_1.SetBackgroundColour(color)
        self.panel_CV28_2.SetBackgroundColour(color)
        self.panel_PLMove.SetBackgroundColour(color)
        self.panel_LNCV_RESET.SetBackgroundColour(color)
        self.panel_PLConf.SetBackgroundColour(color)
        self.panel_PLSet.SetBackgroundColour(color)

        for x in range(8):
            self.panel_Servo[x].SetBackgroundColour(color)
            self.panel_Servo[x].Refresh()
            self.panel_Coil[x].SetBackgroundColour(color)
            self.panel_Coil[x].Refresh()
            if x < 4:
                self.panel_PL[x].SetBackgroundColour(color)
                self.panel_PL[x].Refresh()
        for x in range(self.maxLNCV):
            self.panel_LNCV[x].SetBackgroundColour(color)
            self.panel_LNCV[x].Refresh()

        self.Refresh()

    def OnAbout(self, event):
        # First we create and fill the info object
        info = wx.adv.AboutDialogInfo()
        info.Name = "DecoderConfigurator\n"
        info.Version = SOFTWARE_VERSION
        info.Copyright = "(c) 2019-2023 M.Ross"

        info.Description = wordwrap(
            "\nA simple tool for configure ad upgrade software "
            "of my electronic board series for model railroading",
            300, wx.ClientDC(self))
        # info.WebSite = ("http://en.wikipedia.org/wiki/Hello_world", "Hello World home page")
        info.Developers = [" M.Ross "]

        # info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        # Then we call wx.AboutBox giving it that info object
        wx.adv.AboutBox(info)


class MyUpgrader(ArduProg.UpgradeFrame):
    def __init__(self, *args, **kw):
        self.conf = kw['conf']
        self._serial_in_use = kw['serial']
        self.parent = kw['parent']
        self.default_file = kw['default']
        self.default_path = kw['pathHex']
        del kw['conf']
        del kw['serial']
        del kw['default']
        del kw['pathHex']
        super(MyUpgrader, self).__init__(*args, **kw)

    def setDefault(self):
        return self.default_file

    def setPathHex(self):
        return self.default_path

    def extUploadInit(self):
        self.conf.onReset(None, -1)
        self._serial_in_use.close()

    def extUploadFinish(self):
        # self._serial_in_use.open()
        self.parent.OnReconnect(None, True)
        self.OnExit(None)


class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        frame = MainFrame(None, -1, main_name())
        self.SetTopWindow(frame)
        frame.CenterOnScreen()
        frame.Show(True)
        return 1


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
