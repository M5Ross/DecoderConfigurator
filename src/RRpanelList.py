
import serial
import wx
from RRserial import SerialCom
from time import sleep

CV_28_INV_DIR = 1
CV_28_SAVE_POS = 2
CV_28_EN_TASTER = 4
CV_28_PULSE = 8
CV_28_EN_USB_LN = 16
CV_28_EN_MULTI_ADR = 32


def serialerrormessage(parent=None, message=None, close=False):
    button = wx.CANCEL if not close else 0
    str_msg = (str(message) if message is not None else "Serial generic error") + ("\nOk" if close else "\nCancel")
    with wx.MessageDialog(parent, str_msg + " to exit...", "Serial Port Error", wx.OK | button | wx.ICON_ERROR) as dlg:
        dlg.CenterOnParent()
        if dlg.ShowModal() == wx.ID_CANCEL:
            close = True
    if close and parent is not None:
        parent.OnClose(None)


# multi address è disponibile solo da versioni software 4.1 in su
def checkMultiAdrAvailable(parent, com):
    try:
        cv = com.GetMultiAdrStart()
        return cv if com.OKcodeOK() else 0
    except serial.serialutil.SerialTimeoutException as e:
        serialerrormessage(parent, message=e, close=False)
    return 0


# single invert è disponibile solo da versioni software 4.1/2.1 in su
def checkSingleInvAvailable(parent, com):
    try:
        cv = com.GetSingleInvStart()
        return cv if com.OKcodeOK() else 0
    except serial.serialutil.SerialTimeoutException as e:
        serialerrormessage(parent, message=e, close=False)
    return 0


class CV1Panel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial):
        self.serial = serial
        self.parent = parent
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        #label_1 = wx.StaticText(self, -1, " CV1  ")
        #label_1.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        #sizer_1.Add(label_1, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        #line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        #sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        label_2 = wx.StaticText(self, -1, "Decoder address: ", style=wx.TE_CENTER)
        self.textind = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER, size=(50, -1))
        sizer_1.Add(label_2, 1, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_1.Add(self.textind, 1, wx.ALIGN_CENTRE_VERTICAL, 0)

        self.buttonsetind = wx.Button(self, -1, "SET", size=(40, -1))  # , size=wx.DefaultSize)
        self.buttongetind = wx.Button(self, -1, "GET", size=(40, -1))  # , size=wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, self.onSetInd, self.buttonsetind)
        self.Bind(wx.EVT_BUTTON, self.onGetInd, self.buttongetind)
        sizer_2.Add(self.buttongetind, 1, wx.ALIGN_CENTRE_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.buttonsetind, 1, wx.ALIGN_CENTRE_VERTICAL, 0)

        sizer_1.Add(sizer_2, 0, wx.EXPAND, 5)

        line = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.LEFT | wx.RIGHT, 5)

        self.buttonreset = wx.Button(self, -1, "MASTER RESET")
        self.Bind(wx.EVT_BUTTON, self.onReset, self.buttonreset)
        sizer_1.Add(self.buttonreset, 1, wx.ALIGN_CENTRE_VERTICAL, 0)

        line = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        label_3 = wx.StaticText(self, -1, " HW: ", style=wx.TE_CENTER, size=(40, -1))
        self.textHW = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER | wx.TE_READONLY, size=(35, -1))
        sizer_2.Add(label_3, 0, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_2.Add(self.textHW, 0, wx.ALIGN_CENTRE_VERTICAL, 0)

        label_4 = wx.StaticText(self, -1, " SW: ", style=wx.TE_CENTER, size=(40, -1))
        self.textSW = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER | wx.TE_READONLY, size=(35, -1))
        sizer_2.Add(label_4, 0, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_2.Add(self.textSW, 0, wx.ALIGN_CENTRE_VERTICAL, 0)

        sizer_1.Add(sizer_2, 0, wx.EXPAND, 5)

        line = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 5)

        #line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        #sizer_0.Add(line, 0, wx.GROW | wx.TOP | wx.BOTTOM, 1)

        #self.onGetAll(None)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

    def onSetInd(self, event):
        try:
            cv1e9 = int(self.textind.GetValue())
            if cv1e9 > 999 or cv1e9 < 1:
                raise ValueError
        except ValueError:
            with wx.MessageDialog(None, 'Decoder address must be a numeric value (1..999)',
                                  'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
        else:
            cv9 = int(cv1e9/256)
            cv1 = cv1e9 - cv9 * 256
            if event is None:
                self.com.writeCV(1, cv1)
                self.com.writeCV(9, cv9)
            else:
                try:
                    self.com.writeCV(1, cv1)
                    self.com.writeCV(9, cv9)
                except serial.serialutil.SerialTimeoutException as e:
                    serialerrormessage(self.parent, message=e, close=False)

    def onGetInd(self, event):
        if event is None:
            addr = self.com.readCV(1) + self.com.readCV(9) * 256
            self.textind.SetValue(str(addr))
            hw_version = self.com.GetHWversion()
            self.textHW.SetValue(str(float(hw_version)/10.0))
            sw_version = self.com.GetSWversion()
            self.textSW.SetValue(str(float(sw_version)/10.0))
        else:
            try:
                addr = self.com.readCV(1) + self.com.readCV(9) * 256
                self.textind.SetValue(str(addr))
                hw_version = self.com.GetHWversion()
                self.textHW.SetValue(str(float(hw_version)/10.0))
                sw_version = self.com.GetSWversion()
                self.textSW.SetValue(str(float(sw_version)/10.0))
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

    def GetCV1(self):
        return self.textind.GetValue()

    def onReset(self, event, type=None):
        ok = False
        with wx.MessageDialog(self, 'Reset all CV to factory default?', 'Warning',
                              wx.YES | wx.NO | wx.ICON_WARNING) as dlg:
            dlg.CenterOnScreen()
            result = dlg.ShowModal()
        if result == wx.ID_YES:
            if event is None:
                self.com.writeCV(120, 120)
                ok = True
            else:
                try:
                    self.com.writeCV(120, 120)
                except serial.serialutil.SerialTimeoutException as e:
                    serialerrormessage(self.parent, message=e, close=False)
                else:
                    ok = True
        if ok:
            if type is None:
                if self.parent is None:
                    with wx.MessageDialog(self, 'Need Refresh', 'Info', wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.CenterOnScreen()
                        dlg.ShowModal()
                else:
                    self.parent.OnReconnect(None)


class CV28Panel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, show_safe):
        self.serial = serial
        self.parent = parent
        self.show_safe = show_safe
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_0 = wx.BoxSizer(wx.VERTICAL)

        #line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        #sizer_0.Add(line, 0, wx.GROW | wx.TOP | wx.BOTTOM, 1)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        #label_1 = wx.StaticText(self, -1, " CV28")
        #label_1.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        #sizer_1.Add(label_1, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        #line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        #sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 4)

        label_1 = wx.StaticText(self, -1, "Config:")
        sizer_1.Add(label_1, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.cb1 = wx.CheckBox(self, -1, "Invert")  # , (65, 40), (150, 20), wx.NO_BORDER)
        self.cb2 = wx.CheckBox(self, -1, "Save")  # , (65, 60), (150, 20), wx.NO_BORDER)
        self.cb3 = wx.CheckBox(self, -1, "Taster")  # , (65, 60), (150, 20), wx.NO_BORDER)
        self.cb4 = wx.CheckBox(self, -1, "Pulse")  # , (65, 60), (150, 20), wx.NO_BORDER)
        self.cb5 = wx.CheckBox(self, -1, "LN-USB")  # , (65, 60), (150, 20), wx.NO_BORDER)
        self.cb6 = wx.CheckBox(self, -1, "MultiAdr")  # , (65, 60), (150, 20), wx.NO_BORDER)
        self.cb1.SetValue(False)
        self.cb2.SetValue(False)
        self.cb3.SetValue(False)
        self.cb4.SetValue(False)
        self.cb5.SetValue(False)
        self.cb6.SetValue(False)

        self.config = 0
        if self.cb1.GetValue() & CV_28_INV_DIR:
            self.config += CV_28_INV_DIR
        if self.cb2.GetValue() & CV_28_SAVE_POS:
            self.config += CV_28_SAVE_POS
        if self.cb3.GetValue() & CV_28_EN_TASTER:
            self.config += CV_28_EN_TASTER
        if self.cb4.GetValue() & CV_28_PULSE:
            self.config += CV_28_PULSE
        if self.cb5.GetValue() & CV_28_EN_USB_LN:
            self.config += CV_28_EN_USB_LN
        if self.cb6.GetValue() & CV_28_EN_MULTI_ADR:
            self.config += CV_28_EN_MULTI_ADR

        self.Bind(wx.EVT_CHECKBOX, self.checkBoxINV, self.cb1)
        self.Bind(wx.EVT_CHECKBOX, self.checkBoxSAVE, self.cb2)
        self.Bind(wx.EVT_CHECKBOX, self.checkBoxTASTER, self.cb3)
        self.Bind(wx.EVT_CHECKBOX, self.checkBoxPULSE, self.cb4)
        self.Bind(wx.EVT_CHECKBOX, self.checkBoxUSBLN, self.cb5)
        self.Bind(wx.EVT_CHECKBOX, self.checkBoxMULTIADR, self.cb6)
        sizer_1.Add(self.cb1, 0, wx.ALIGN_CENTRE | wx.LEFT, 5)
        sizer_1.Add(self.cb2, 0, wx.ALIGN_CENTRE | wx.ALL, 2)
        sizer_1.Add(self.cb3, 0, wx.ALIGN_CENTRE | wx.ALL, 2)
        sizer_1.Add(self.cb4, 0, wx.ALIGN_CENTRE | wx.ALL, 2)
        sizer_1.Add(self.cb5, 0, wx.ALIGN_CENTRE | wx.ALL, 2)
        sizer_1.Add(self.cb6, 0, wx.ALIGN_CENTRE | wx.RIGHT, 0)

        self.linesafe = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(self.linesafe, 0, wx.GROW | wx.RIGHT, 5)

        self.labelsafe = wx.StaticText(self, -1, "Safe time [ms]: ", style=wx.TE_CENTER)
        self.textsafe = wx.TextCtrl(self, -1, "", size=(50, -1), style=wx.TE_CENTER)
        sizer_1.Add(self.labelsafe, 0, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_1.Add(self.textsafe, 0, wx.ALIGN_CENTER, 0)
        if self.show_safe:
            self.linesafe.Show()
            self.labelsafe.Show()
            self.textsafe.Show()
        else:
            self.linesafe.Hide()
            self.labelsafe.Hide()
            self.textsafe.Show()

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.LEFT | wx.RIGHT, 5)

        self.buttonsetall = wx.Button(self, -1, "SET", size=(45, -1))
        self.buttongetall = wx.Button(self, -1, "GET", size=(45, -1))
        self.Bind(wx.EVT_BUTTON, self.onSetAll, self.buttonsetall)
        self.Bind(wx.EVT_BUTTON, self.onGetAll, self.buttongetall)
        sizer_1.Add(self.buttongetall, 1, wx.ALIGN_CENTRE, 0)
        sizer_1.Add(self.buttonsetall, 1, wx.ALIGN_CENTER, 0)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_0.Add(sizer_1, 0, wx.EXPAND, 0)

        self.SetSizer(sizer_0)
        sizer_0.Fit(self)
        self.Layout()

    def ShowSafe(self, show=True):
        self.linesafe.Show(show)
        self.textsafe.Show(show)
        self.labelsafe.Show(show)

    def checkBoxINV(self, event):
        if event.IsChecked():
            self.config += CV_28_INV_DIR
        else:
            self.config -= CV_28_INV_DIR
        #print(self.config)

    def checkBoxSAVE(self, event):
        if event.IsChecked():
            self.config += CV_28_SAVE_POS
        else:
            self.config -= CV_28_SAVE_POS
        #print(self.config)

    def checkBoxTASTER(self, event):
        if event.IsChecked():
            self.config += CV_28_EN_TASTER
        else:
            self.config -= CV_28_EN_TASTER
        #print(self.config)

    def checkBoxPULSE(self, event):
        if event.IsChecked():
            self.config += CV_28_PULSE
        else:
            self.config -= CV_28_PULSE
        #print(self.config)

    def checkBoxUSBLN(self, event):
        if event.IsChecked():
            self.config += CV_28_EN_USB_LN
        else:
            self.config -= CV_28_EN_USB_LN
        #print(self.config)

    def checkBoxMULTIADR(self, event):
        if event.IsChecked():
            self.config += CV_28_EN_MULTI_ADR
        else:
            self.config -= CV_28_EN_MULTI_ADR
        #print(self.config)

    def onSetAll(self, event):
        try:
            self.com.writeCV(28, self.config)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

        if self.textsafe.IsShown():
            try:
                cv27 = int(self.textsafe.GetValue())/10
                if cv27 > 255 or cv27 < 0:
                    raise ValueError
            except ValueError:
                with wx.MessageDialog(None, 'Safe time must be a numeric value (0..2550)',
                                      'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                    dlg.ShowModal()
            else:
                try:
                    self.com.writeCV(27, cv27)
                except serial.serialutil.SerialTimeoutException as e:
                    serialerrormessage(self.parent, message=e, close=False)

    def onGetAll(self, event):
        ok = False
        cv27 = -1
        if event is None:
            self.config = self.com.readCV(28)
            if self.textsafe.IsShown():
                cv27 = self.com.readCV(27)*10
            ok = True
        else:
            try:
                self.config = self.com.readCV(28)
                if self.textsafe.IsShown():
                    cv27 = self.com.readCV(27)*10
                ok = True
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

        if ok:
            if self.textsafe.IsShown():
                self.textsafe.SetValue(str(cv27))

            #print(self.config)
            if self.com.GetOKcode() == self.com.OKCODE_OK:
                if self.config & CV_28_INV_DIR:
                    self.cb1.SetValue(True)
                else:
                    self.cb1.SetValue(False)
                if self.config & CV_28_SAVE_POS:
                    self.cb2.SetValue(True)
                else:
                    self.cb2.SetValue(False)
                if self.config & CV_28_EN_TASTER:
                    self.cb3.SetValue(True)
                else:
                    self.cb3.SetValue(False)
                if self.config & CV_28_PULSE:
                    self.cb4.SetValue(True)
                else:
                    self.cb4.SetValue(False)
                if self.config & CV_28_EN_USB_LN:
                    self.cb5.SetValue(True)
                else:
                    self.cb5.SetValue(False)
                if self.config & CV_28_EN_MULTI_ADR:
                    self.cb6.SetValue(True)
                else:
                    self.cb6.SetValue(False)

    def SetMask(self, mask):
        if mask & CV_28_INV_DIR:
            self.cb1.Enable(True)
        else:
            self.cb1.Enable(False)
        if mask & CV_28_SAVE_POS:
            self.cb2.Enable(True)
        else:
            self.cb2.Enable(False)
        if mask & CV_28_EN_TASTER:
            self.cb3.Enable(True)
        else:
            self.cb3.Enable(False)
        if mask & CV_28_PULSE:
            self.cb4.Enable(True)
        else:
            self.cb4.Enable(False)
        if mask & CV_28_EN_USB_LN:
            self.cb5.Enable(True)
        else:
            self.cb5.Enable(False)
        if mask & CV_28_EN_MULTI_ADR and checkMultiAdrAvailable(self.parent, self.com):
            self.cb6.Enable(True)
        else:
            self.cb6.Enable(False)


class MovePanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, out):
        self.parent = parent
        self.serial = serial
        self.id = out
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_0 = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        #line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        #sizer_1.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 5)

        self.buttonmoveleft = wx.Button(self, -1, "OPEN")
        self.buttonmoveright = wx.Button(self, -1, "CLOSE")

        sizer_1.Add(self.buttonmoveleft, 1, wx.ALL | wx.EXPAND, 0)
        sizer_1.Add(self.buttonmoveright, 1, wx.ALL | wx.EXPAND, 0)

        #line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        #sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_0.Add(sizer_1, 0, wx.EXPAND, 0)

        self.Bind(wx.EVT_BUTTON, self.setleft, self.buttonmoveleft)
        self.Bind(wx.EVT_BUTTON, self.setright, self.buttonmoveright)

        self.SetSizer(sizer_0)
        sizer_0.Fit(self)
        self.Layout()

    def setleft(self, event):
        try:
            self.com.moveSX(self.id)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def setright(self, event):
        try:
            self.com.moveDX(self.id)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)


class ServoPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, out, slider_c_type="RELE"):
        self.parent = parent
        self.serial = serial
        self.id = out
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.multi_adr = 0
        self.single_inv = 0
        self.checkFunctionsAvailable()
        if slider_c_type == "INVERT":
            self.single_inv = 0

        self.SetBackgroundColour(bcolor)

        slider_dim = 150

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_0 = wx.BoxSizer(wx.HORIZONTAL)

        label_0 = wx.StaticText(self, -1, "Servo {}".format(self.id+1))
        label_0.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer_0.Add(label_0, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.sliderL = 60
        self.sliderR = 120
        if slider_c_type == "RELE":
            self.sliderC = 90
            slidec_min = 60
            slidec_max = 120
            slidec_freq = 5
        elif slider_c_type == "INVERT":
            self.sliderC = 0
            slidec_min = 0
            slidec_max = 1
            slidec_freq = 1
        else:
            self.sliderC = 90
            slidec_min = 60
            slidec_max = 120
            slidec_freq = 5
        self.sliderS = 5
        self.startval = self.sliderL
        self.slider_1 = wx.Slider(self, value=self.sliderL, minValue=1, maxValue=100, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_2 = wx.Slider(self, value=self.sliderR, minValue=70, maxValue=200, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_3 = wx.Slider(self, value=self.sliderC, minValue=slidec_min, maxValue=slidec_max, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_4 = wx.Slider(self, value=self.sliderS, minValue=1, maxValue=10, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_1.SetTickFreq(5)
        self.slider_2.SetTickFreq(5)
        self.slider_3.SetTickFreq(slidec_freq)
        self.slider_4.SetTickFreq(1)

        self.cb1 = wx.CheckBox(self, -1, " Invert")  # , (65, 60), (150, 20), wx.NO_BORDER)
        self.cb1.SetValue(False)
        self.Bind(wx.EVT_CHECKBOX, self.checkBox1, self.cb1)

        self.label_multi_adr = wx.StaticText(self, -1, "Multi adr: ", style=wx.TE_CENTER)
        self.text_multi_adr = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER, size=(50, -1))

        self.buttonstartleft = wx.Button(self, -1, "SET SX")
        self.buttonstartright = wx.Button(self, -1, "SET DX")
        self.buttonleft = wx.Button(self, -1, "SET")
        self.buttonright = wx.Button(self, -1, "SET")
        self.buttoncentre = wx.Button(self, -1, "SET")
        self.buttonspeed = wx.Button(self, -1, "SET")
        self.buttonsetall = wx.Button(self, -1, "SET ALL")
        self.buttongetall = wx.Button(self, -1, "GET ALL")
        self.buttonmoveleft = wx.Button(self, -1, "MOVE SX\n<<--")
        self.buttonmoveright = wx.Button(self, -1, "MOVE DX\n-->>")
        self.buttonmulti = wx.Button(self, -1, "SET")

        label_1 = wx.StaticText(self, -1, "Start value: ")
        self.textstartval = wx.TextCtrl(self, -1, str(self.startval), size=(30, -1), style=wx.TE_READONLY | wx.TE_CENTER)

        grid = wx.FlexGridSizer(2, 4, 0, 20)
        grid.Add(self.slider_1, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_2, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_3, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_4, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonleft, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonright, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttoncentre, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonspeed, 1, wx.ALIGN_CENTER, 0)
        sizer_1.Add(grid, 2, 0, 0)

        if self.sliderC:
            self.slider_3.Show()
            self.buttoncentre.Show()
        else:
            self.slider_3.Hide()
            self.buttoncentre.Hide()

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 5)

        grid = wx.FlexGridSizer(2, 2, 0, 10)
        grid.Add(self.label_multi_adr, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.text_multi_adr, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.cb1, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonmulti, 1, wx.ALIGN_CENTER, 0)
        sizer_1.Add(grid, 0, 0, 0)

        self.cb1.Enable(True if self.single_inv else False)
        self.label_multi_adr.Enable(True if self.multi_adr else False)
        self.text_multi_adr.Enable(True if self.multi_adr else False)
        self.buttonmulti.Enable(True if self.multi_adr else False)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 5)

        grid = wx.FlexGridSizer(2, 2, 0, 10)
        grid.Add(label_1, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.textstartval, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonstartleft, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonstartright, 1, wx.ALIGN_CENTER, 0)
        sizer_1.Add(grid, 0, 0, 0)

        sizer_0.Add(sizer_1, 2, wx.LEFT | wx.RIGHT, 10)

        line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.RIGHT, 5)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.buttongetall, 1, wx.ALIGN_CENTRE, 0)
        sizer_2.Add(self.buttonsetall, 1, wx.ALIGN_CENTER, 0)
        sizer_0.Add(sizer_2, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 5)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.buttonmoveleft, 1, wx.EXPAND, 0)
        sizer_3.Add(self.buttonmoveright, 1, wx.EXPAND, 0)
        sizer_0.Add(sizer_3, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.LEFT, 5)
        sizer_0.Add((22, 22))

        sizer.Add(sizer_0, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.TOP, 1)

        self.Bind(wx.EVT_SCROLL, self.onsliderL, self.slider_1)
        self.Bind(wx.EVT_SCROLL, self.onsliderR, self.slider_2)
        self.Bind(wx.EVT_SCROLL, self.onsliderC, self.slider_3)
        self.Bind(wx.EVT_SCROLL, self.onsliderS, self.slider_4)
        self.Bind(wx.EVT_BUTTON, self.onsetTL, self.buttonstartleft)
        self.Bind(wx.EVT_BUTTON, self.onsetTR, self.buttonstartright)
        self.Bind(wx.EVT_BUTTON, self.onsetL, self.buttonleft)
        self.Bind(wx.EVT_BUTTON, self.onsetR, self.buttonright)
        self.Bind(wx.EVT_BUTTON, self.onsetC, self.buttoncentre)
        self.Bind(wx.EVT_BUTTON, self.onsetS, self.buttonspeed)
        self.Bind(wx.EVT_BUTTON, self.onsetA, self.buttonsetall)
        self.Bind(wx.EVT_BUTTON, self.ongetA, self.buttongetall)
        self.Bind(wx.EVT_BUTTON, self.moveleft, self.buttonmoveleft)
        self.Bind(wx.EVT_BUTTON, self.moveright, self.buttonmoveright)
        self.Bind(wx.EVT_BUTTON, self.onsetMulti, self.buttonmulti)

        self.EnableAllButtons(True)

        #self.ongetA(None)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def checkFunctionsAvailable(self):
        self.multi_adr = checkMultiAdrAvailable(self.parent, self.com)
        self.single_inv = checkSingleInvAvailable(self.parent, self.com)

    def onsliderL(self, event):
        self.sliderL = event.GetPosition()
        self.buttonleft.Enable(True)
        self.buttonstartleft.Enable(True)

    def onsliderR(self, event):
        self.sliderR = event.GetPosition()
        self.buttonright.Enable(True)
        self.buttonstartright.Enable(True)

    def onsliderC(self, event):
        self.sliderC = event.GetPosition()
        self.buttoncentre.Enable(True)

    def onsliderS(self, event):
        self.sliderS = event.GetPosition()
        self.buttonspeed.Enable(True)

    def checkBox1(self, event):
        try:
            self.com.writeCV(self.single_inv + self.id, 1 if event.IsChecked() else 0)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def onsetMulti(self, event):
        try:
            adr = int(self.text_multi_adr.GetValue())
            if adr > 999 or adr < 1:
                raise ValueError
        except ValueError:
            with wx.MessageDialog(None, 'Address must be a numeric value (1..999)',
                                  'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
        else:
            adr_h = int(adr / 256)
            adr_l = adr - adr_h * 256
            if event is None:
                self.com.writeCV(self.multi_adr + self.id*2, adr_l)
                self.com.writeCV(self.multi_adr + self.id*2 + 1, adr_h)
            else:
                try:
                    self.com.writeCV(self.multi_adr + self.id*2, adr_l)
                    self.com.writeCV(self.multi_adr + self.id*2 + 1, adr_h)
                except serial.serialutil.SerialTimeoutException as e:
                    serialerrormessage(self.parent, message=e, close=False)

    def ongetMulti(self, event):
        if event is None:
            addr = self.com.readCV(self.multi_adr + self.id*2) + self.com.readCV(self.multi_adr + self.id*2 + 1) * 256
            self.text_multi_adr.SetValue(str(addr))
        else:
            try:
                addr = self.com.readCV(self.multi_adr + self.id*2) + self.com.readCV(self.multi_adr + self.id*2 + 1) * 256
                self.text_multi_adr.SetValue(str(addr))
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

    def onsetTR(self, event):
        try:
            self.onset(5, self.sliderR)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonstartright.Enable(False)
            self.buttonstartleft.Enable(True)

    def onsetTL(self, event):
        try:
            self.onset(5, self.sliderL)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonstartleft.Enable(False)
            self.buttonstartright.Enable(True)

    def onsetL(self, event):
        try:
            self.onset(1, self.sliderL)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonleft.Enable(False)

    def onsetR(self, event):
        try:
            self.onset(2, self.sliderR)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonright.Enable(False)

    def onsetC(self, event):
        try:
            self.onset(3, self.sliderC)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttoncentre.Enable(False)

    def onsetS(self, event):
        try:
            self.onset(4, self.sliderS)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonspeed.Enable(False)

    def onsetA(self, event):
        if event is None:
            self.EnableAllButtons(False)
            self.onset(6, -1)
        else:
            try:
                self.onset(6, -1)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)
            else:
                self.EnableAllButtons(False)

    def ongetA(self, event):
        if event is None:
            self.EnableAllButtons(False)
            self.onget(6)
        else:
            try:
                self.onget(6)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)
            else:
                self.EnableAllButtons(False)

    def EnableAllButtons(self, enable=True):
        self.buttonleft.Enable(enable)
        self.buttonright.Enable(enable)
        self.buttoncentre.Enable(enable)
        self.buttonspeed.Enable(enable)

    def onset(self, type, val):
        if type == 1:
            self.com.writeCV(32 + (self.id * 5), val)
            #print("set left %s" % val)
        elif type == 2:
            self.com.writeCV(33 + (self.id * 5), val)
            #print("set right %s" % val)
        elif type == 3:
            self.com.writeCV(30 + (self.id * 5), val)
            #print("set centre %s" % val)
        elif type == 4:
            self.com.writeCV(31 + (self.id * 5), val)
            #print("set speed %s" % val)
        elif type == 5:
            self.com.writeCV(34 + (self.id * 5), val)
            self.onget(type)
            #print("set speed %s" % val)
        else:
            if self.buttonleft.IsEnabled():
                self.com.writeCV(32 + (self.id * 5), self.sliderL)
            if self.buttonright.IsEnabled():
                self.com.writeCV(33 + (self.id * 5), self.sliderR)
            if self.buttoncentre.IsEnabled():
                self.com.writeCV(30 + (self.id * 5), self.sliderC)
            if self.buttonspeed.IsEnabled():
                self.com.writeCV(31 + (self.id * 5), self.sliderS)
            if self.cb1.IsEnabled():
                self.com.writeCV(self.single_inv + self.id, 1 if self.cb1.GetValue() else 0)
            if self.text_multi_adr.IsEnabled():
                self.onsetMulti(None)
            #print("set ALL")

    def onget(self, type):
        if type == 1:
            self.sliderL = self.com.readCV(32 + (self.id * 5))
            self.slider_1.SetValue(self.sliderL)
        elif type == 2:
            self.sliderR = self.com.readCV(33 + (self.id * 5))
            self.slider_2.SetValue(self.sliderR)
        elif type == 3:
            self.sliderC = self.com.readCV(30 + (self.id * 5))
            self.slider_3.SetValue(self.sliderC)
        elif type == 4:
            self.sliderS = self.com.readCV(31 + (self.id * 5))
            self.slider_4.SetValue(self.sliderS)
        elif type == 5:
            self.startval = self.com.readCV(34 + (self.id * 5))
            self.textstartval.SetValue(str(self.startval))
        else:
            self.sliderL = self.com.readCV(32 + (self.id * 5))
            self.sliderR = self.com.readCV(33 + (self.id * 5))
            self.sliderC = self.com.readCV(30 + (self.id * 5))
            self.sliderS = self.com.readCV(31 + (self.id * 5))
            self.startval = self.com.readCV(34 + (self.id * 5))
            self.slider_1.SetValue(self.sliderL)
            self.slider_2.SetValue(self.sliderR)
            self.slider_3.SetValue(self.sliderC)
            self.slider_4.SetValue(self.sliderS)
            self.textstartval.SetValue(str(self.startval))
            if self.startval == self.sliderL:
                self.buttonstartleft.Enable(False)
                self.buttonstartright.Enable(True)
            if self.startval == self.sliderR:
                self.buttonstartleft.Enable(True)
                self.buttonstartright.Enable(False)
            if self.cb1.IsEnabled():
                self.cb1.SetValue(True if self.com.readCV(self.single_inv + self.id) else False)
            if self.text_multi_adr.IsEnabled():
                self.ongetMulti(None)

    def moveleft(self, event):
        try:
            self.com.moveSX(self.id)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def moveright(self, event):
        try:
            self.com.moveDX(self.id)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def refreshSliderC(self, slider_c_type="RELE"):
        if slider_c_type == "RELE":
            slidec_min = 60
            slidec_max = 120
            slidec_freq = 5
        elif slider_c_type == "INVERT":
            slidec_min = 0
            slidec_max = 1
            slidec_freq = 1
        else:
            slidec_min = 60
            slidec_max = 120
            slidec_freq = 5

        self.slider_3.SetMin(slidec_min)
        self.slider_3.SetMax(slidec_max)
        self.slider_3.SetTickFreq(slidec_freq)

        self.cb1.Enable(True if self.single_inv else False)
        self.label_multi_adr.Enable(True if self.multi_adr else False)
        self.text_multi_adr.Enable(True if self.multi_adr else False)
        self.buttonmulti.Enable(True if self.multi_adr else False)

        if slidec_min:
            self.slider_3.Show()
            self.buttoncentre.Show()
        else:
            self.slider_3.Hide()
            self.buttoncentre.Hide()


class CoilPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, out):
        self.parent = parent
        self.serial = serial
        self.id = out
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        slider_dim = 180

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_0 = wx.BoxSizer(wx.HORIZONTAL)

        label_0 = wx.StaticText(self, -1, "Coil {}".format(self.id+1))
        label_0.SetFont(wx.Font(12, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer_0.Add(label_0, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.sliderT = 15
        self.startval = 0
        self.slider_1 = wx.Slider(self, value=self.sliderT, minValue=1, maxValue=50, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_1.SetTickFreq(10)
        self.buttonstartleft = wx.Button(self, -1, "SET SX")
        self.buttonstartright = wx.Button(self, -1, "SET DX")
        self.buttonGetTime = wx.Button(self, -1, "GET")
        self.buttonSetTime = wx.Button(self, -1, "SET")
        self.buttonmoveleft = wx.Button(self, -1, "MOVE SX\n<<--")
        self.buttonmoveright = wx.Button(self, -1, "MOVE DX\n-->>")

        label_1 = wx.StaticText(self, -1, "Start value: ")
        self.textstartval = wx.TextCtrl(self, -1, str(self.startval), size=(30, -1), style=wx.TE_READONLY | wx.TE_CENTER)

        grid = wx.FlexGridSizer(2, 1, 0, 20)
        grid.Add(self.slider_1, 1, wx.ALIGN_CENTER, 0)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.buttonGetTime, 1, wx.ALIGN_CENTER, 0)
        sizer_3.Add(self.buttonSetTime, 1, wx.ALIGN_CENTER, 0)
        grid.Add(sizer_3, 0, wx.ALIGN_CENTER, 0)
        sizer_1.Add(grid, 2, 0, 0)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 5)

        grid = wx.FlexGridSizer(2, 2, 0, 10)
        grid.Add(label_1, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.textstartval, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonstartleft, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.buttonstartright, 1, wx.ALIGN_CENTER, 0)
        sizer_1.Add(grid, 0, 0, 0)

        sizer_0.Add(sizer_1, 2, wx.LEFT | wx.RIGHT, 10)

        line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.RIGHT, 5)

        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_3.Add(self.buttonmoveleft, 1, wx.EXPAND, 0)
        sizer_3.Add(self.buttonmoveright, 1, wx.EXPAND, 0)
        sizer_0.Add(sizer_3, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.LEFT, 5)
        sizer_0.Add((22, 22))

        sizer.Add(sizer_0, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.TOP, 1)

        self.Bind(wx.EVT_SCROLL, self.onsliderT, self.slider_1)
        self.Bind(wx.EVT_BUTTON, self.onsetTL, self.buttonstartleft)
        self.Bind(wx.EVT_BUTTON, self.onsetTR, self.buttonstartright)
        self.Bind(wx.EVT_BUTTON, self.ongetT, self.buttonGetTime)
        self.Bind(wx.EVT_BUTTON, self.onsetT, self.buttonSetTime)
        self.Bind(wx.EVT_BUTTON, self.moveleft, self.buttonmoveleft)
        self.Bind(wx.EVT_BUTTON, self.moveright, self.buttonmoveright)

        self.EnableAllButtons(True)

        #self.ongetA(None)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def onsliderT(self, event):
        self.sliderT = event.GetPosition()
        self.buttonSetTime.Enable(True)
        self.buttonGetTime.Enable(True)

    def onsetTR(self, event):
        val = 0 if self.startval == 1 else 1
        try:
            self.onset(5, val)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonstartright.Enable(False)
            self.buttonstartleft.Enable(True)

    def onsetTL(self, event):
        val = 0 if self.startval == 1 else 1
        try:
            self.onset(5, val)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonstartleft.Enable(False)
            self.buttonstartright.Enable(True)

    def onsetT(self, event):
        try:
            self.onset(4, self.sliderT)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonSetTime.Enable(False)
            self.buttonGetTime.Enable(False)

    def ongetT(self, event):
        try:
            self.onget(4)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.buttonGetTime.Enable(False)
            self.buttonSetTime.Enable(False)

    def onsetA(self, event):
        if event is None:
            self.EnableAllButtons(False)
            self.onset(6, -1)
        else:
            try:
                self.onset(6, -1)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)
            else:
                self.EnableAllButtons(False)

    def ongetA(self, event):
        if event is None:
            self.EnableAllButtons(False)
            self.onget(6)
        else:
            try:
                self.onget(6)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)
            else:
                self.EnableAllButtons(False)

    def EnableAllButtons(self, enable=True):
        self.buttonGetTime.Enable(enable)
        self.buttonSetTime.Enable(enable)

    def onset(self, type, val):
        if type == 1:
            self.com.writeCV(32 + (self.id * 5), val)
            #self.onget(type)
            #print("set left %s" % val)
        elif type == 2:
            self.com.writeCV(33 + (self.id * 5), val)
            #self.onget(type)
            #print("set right %s" % val)
        elif type == 3:
            self.com.writeCV(30 + (self.id * 5), val)
            #self.onget(type)
            #print("set centre %s" % val)
        elif type == 4:
            self.com.writeCV(31 + (self.id * 5), val)
            #self.onget(type)
            #print("set speed %s" % val)
        elif type == 5:
            self.com.writeCV(34 + (self.id * 5), val)
            self.onget(type)
            #print("set speed %s" % val)
        else:
            #if self.buttonGetTime.IsEnabled():
            self.com.writeCV(34 + (self.id * 5), self.textstartval.GetValue())
            self.com.writeCV(31 + (self.id * 5), self.sliderT)
            #print("set ALL")

    def onget(self, type):
        if type == 1:
            self.sliderT = self.com.readCV(32 + (self.id * 5))
        elif type == 2:
            self.sliderR = self.com.readCV(33 + (self.id * 5))
            #self.slider_2.SetValue(self.sliderR)
        elif type == 3:
            self.sliderC = self.com.readCV(30 + (self.id * 5))
            #self.slider_3.SetValue(self.sliderC)
        elif type == 4:
            self.sliderT = self.com.readCV(31 + (self.id * 5))
            self.slider_1.SetValue(self.sliderT)
            #self.slider_4.SetValue(self.sliderS)
        elif type == 5:
            self.startval = self.com.readCV(34 + (self.id * 5))
            self.textstartval.SetValue(str(self.startval))
        else:
            #self.sliderL = self.com.readCV(32 + (self.id * 5))
            #self.sliderR = self.com.readCV(33 + (self.id * 5))
            #self.sliderC = self.com.readCV(30 + (self.id * 5))
            self.sliderT = self.com.readCV(31 + (self.id * 5))
            self.startval = self.com.readCV(34 + (self.id * 5))
            self.slider_1.SetValue(self.sliderT)
            #self.slider_2.SetValue(self.sliderR)
            #self.slider_3.SetValue(self.sliderC)
            #self.slider_4.SetValue(self.sliderS)
            self.textstartval.SetValue(str(self.startval))
            if self.startval == 1:
                self.buttonstartleft.Enable(False)
                self.buttonstartright.Enable(True)
            else:
                self.buttonstartleft.Enable(True)
                self.buttonstartright.Enable(False)

    def moveleft(self, event):
        try:
            self.com.moveSX(self.id)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def moveright(self, event):
        try:
            self.com.moveDX(self.id)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)


class CVdialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        serial = kwds['serial']
        color = kwds['bcolor']
        del kwds['serial']
        del kwds['bcolor']
        wx.Dialog.__init__(self, *args, **kwds)

        CVpanel(self, self, bcolor=color, serial=serial)

        self.Fit()
        self.Layout()


class CVpanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial):
        self.parent = parent
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(serial)

        self.n_cv = 0
        self.cv = []
        self.val = []

        self.SetBackgroundColour(bcolor)

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "CV List")
        label.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT | wx.TOP, 5)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.TOP | wx.BOTTOM, 5)

        self.updateImage()
        self.table = []

        print("n_cv =", self.n_cv, (self.n_cv / 10) + 1)

        grid = wx.FlexGridSizer(rows=10, cols=int(self.n_cv / 10) + 1, gap=wx.Size(1, 1))

        for n in range(self.n_cv):
            self.table.append(CVtable(self, self.cv[n], bcolor, self.val[n]))
            grid.Add(self.table[n], 0, wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT, 10)

        sizer.Add(grid)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.TOP | wx.BOTTOM, 5)

        self.buttonGet = wx.Button(self, -1, "GET ALL")
        self.buttonSet = wx.Button(self, -1, "SET ALL")
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.buttonSet)
        box.Add(self.buttonGet)
        sizer.Add(box, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.TOP | wx.BOTTOM, 5)

        self.Bind(wx.EVT_BUTTON, self.onget, self.buttonGet)
        self.Bind(wx.EVT_BUTTON, self.onset, self.buttonSet)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def onget(self, event):
        self.updateImage()
        for n in range(self.n_cv):
            self.table[n].SetCVval(self.val[n])

    def onset(self, event):
        val = [0]*self.n_cv
        ok = True
        for n in range(self.n_cv):
            try:
                val[n] = int(self.table[n].GetCVval())
                if val[n] > 255 or val[n] < 0:
                    raise ValueError
            except ValueError:
                with wx.MessageDialog(None, f'CV{self.cv[n]} must be a numeric value (0..255)', 'Value Error',
                                      wx.OK | wx.ICON_ERROR) as dlg:
                    dlg.ShowModal()
                    ok = False
                    break
        if ok:
            try:
                self.com.SetCVlist(self.cv, val, self.n_cv)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

    def updateImage(self):
        try:
            self.n_cv = self.com.GetCVlist()
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=True)
        else:
            self.cv = self.com.GetCV()
            self.val = self.com.GetVal()


class CVtable(wx.Panel):
    def __init__(self, parent, out, bcolor, defval):
        wx.Panel.__init__(self, parent)

        self.SetBackgroundColour(bcolor)

        sizer = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, -1, "CV {:03d} =".format(out))
        label.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.LEFT | wx.RIGHT, 1)
        self.textCVval = wx.TextCtrl(self, -1, str(defval), size=(40, -1), style=wx.TE_CENTER)
        sizer.Add(self.textCVval, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 1)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def GetCVval(self):
        return self.textCVval.GetValue()

    def SetCVval(self, val):
        self.textCVval.SetValue(str(val))


class LNCVPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, out):
        self.serial = serial
        self.parent = parent
        self.id = out
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_o = wx.BoxSizer(wx.VERTICAL)
        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        label_2 = wx.StaticText(self, -1, " LNCV {:02d} ".format(self.id+1), style=wx.TE_CENTER, size=(70, -1))
        label_2.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.textind = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER, size=(50, -1))
        sizer_1.Add(label_2, 1, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_1.Add(self.textind, 1, wx.ALIGN_CENTER, 0)

        self.buttonsetLNCV = wx.Button(self, -1, "SET", size=wx.DefaultSize)
        self.buttongetLNCV = wx.Button(self, -1, "GET", size=wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, self.onSetLNCV, self.buttonsetLNCV)
        self.Bind(wx.EVT_BUTTON, self.onGetLNCV, self.buttongetLNCV)
        sizer_2.Add(self.buttongetLNCV, 1, wx.ALIGN_CENTRE | wx.LEFT, 5)
        sizer_2.Add(self.buttonsetLNCV, 1, wx.ALIGN_CENTER, 0)

        sizer_1.Add(sizer_2, 0, wx.EXPAND, 5)

        sizer_1.Add((25, 25))

        # line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        # sizer_1.Add(line, 0, wx.GROW | wx.LEFT | wx.RIGHT, 5)

        # self.buttonreset = wx.Button(self, -1, "MASTER RESET")
        # self.Bind(wx.EVT_BUTTON, self.onReset, self.buttonreset)
        # sizer_1.Add(self.buttonreset, 1, wx.ALIGN_CENTRE, 0)

        # line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        # sizer_1.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_o.Add(sizer_1)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer_o.Add(line, 0, wx.GROW | wx.TOP | wx.BOTTOM, 1)

        #self.onGetAll(None)

        self.SetSizer(sizer_o)
        sizer_o.Fit(self)
        self.Layout()

    def onSetLNCV(self, event):
        try:
            lncv = int(self.textind.GetValue())
            if lncv > 999 or lncv < 0:
                raise ValueError
        except ValueError:
            with wx.MessageDialog(None, 'Value must be numeric (0..999)',
                                  'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
        else:
            if event is None:
                self.com.writeCV(self.id, lncv)
            else:
                try:
                    self.com.writeCV(self.id, lncv)
                except serial.serialutil.SerialTimeoutException as e:
                    serialerrormessage(self.parent, message=e, close=False)

    def onGetLNCV(self, event):
        if event is None:
            lncv = self.com.readCV(self.id)
            self.textind.SetValue(str(lncv))
        else:
            try:
                lncv = self.com.readCV(self.id)
                self.textind.SetValue(str(lncv))
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

    def GetLNCV(self):
        return self.textind.GetValue()


class LNCVResetPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial):
        self.serial = serial
        self.parent = parent
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        label_3 = wx.StaticText(self, -1, " HW: ", style=wx.TE_CENTER, size=(35, -1))
        self.textHW = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER | wx.TE_READONLY, size=(35, -1))
        sizer_2.Add(label_3, 0, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_2.Add(self.textHW, 0, wx.ALIGN_CENTRE_VERTICAL, 0)

        label_4 = wx.StaticText(self, -1, " SW: ", style=wx.TE_CENTER, size=(30, -1))
        self.textSW = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER | wx.TE_READONLY, size=(35, -1))
        sizer_2.Add(label_4, 0, wx.ALIGN_CENTRE_VERTICAL, 0)
        sizer_2.Add(self.textSW, 0, wx.ALIGN_CENTRE_VERTICAL, 0)

        sizer_1.Add(sizer_2, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        self.buttonreset = wx.Button(self, -1, "MASTER RESET", size=(155, -1))
        self.Bind(wx.EVT_BUTTON, self.onReset, self.buttonreset)
        sizer_1.Add(self.buttonreset, 1, wx.ALIGN_CENTRE_VERTICAL, 0)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

    def onGetInd(self, event):
        if event is None:
            hw_version = self.com.GetHWversion()
            self.textHW.SetValue(str(float(hw_version) / 10.0))
            sw_version = self.com.GetSWversion()
            self.textSW.SetValue(str(float(sw_version) / 10.0))
        else:
            try:
                hw_version = self.com.GetHWversion()
                self.textHW.SetValue(str(float(hw_version) / 10.0))
                sw_version = self.com.GetSWversion()
                self.textSW.SetValue(str(float(sw_version) / 10.0))
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

    def onReset(self, event, type=None):
        ok = False
        with wx.MessageDialog(self, 'Reset all LNCV to factory default?', 'Warning',
                              wx.YES | wx.NO | wx.ICON_WARNING) as dlg:
            dlg.CenterOnScreen()
            result = dlg.ShowModal()
        if result == wx.ID_YES:
            if event is None:
                self.com.writeCV(9, 0)
                ok = True
            else:
                try:
                    self.com.writeCV(9, 0)
                except serial.serialutil.SerialTimeoutException as e:
                    serialerrormessage(self.parent, message=e, close=False)
                else:
                    ok = True
        if ok:
            if type is None:
                if self.parent is None:
                    with wx.MessageDialog(self, 'Need Refresh', 'Info', wx.OK | wx.ICON_INFORMATION) as dlg:
                        dlg.CenterOnScreen()
                        dlg.ShowModal()
                else:
                    self.parent.OnReconnect(None)
                    self.parent.OnRefresh(None)


class PLSetPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial):
        self.serial = serial
        self.parent = parent
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)

        label_2 = wx.StaticText(self, -1, " Velocità barriere:   ", style=wx.TE_CENTER)
        self.texts = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER, size=(50, -1))
        sizer_1.Add(label_2, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer_1.Add(self.texts, 0, wx.ALIGN_CENTRE_VERTICAL, 5)

        label_2 = wx.StaticText(self, -1, "           Frequenza lampeggio led:   ", style=wx.TE_CENTER)
        self.textl = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER, size=(50, -1))
        sizer_1.Add(label_2, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer_1.Add(self.textl, 0, wx.ALIGN_CENTRE_VERTICAL, 5)

        label_2 = wx.StaticText(self, -1, "           Volume audio:   ", style=wx.TE_CENTER)
        self.textv = wx.TextCtrl(self, -1, "", style=wx.TE_CENTER, size=(50, -1))
        sizer_1.Add(label_2, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer_1.Add(self.textv, 0, wx.ALIGN_CENTRE_VERTICAL, 5)
        sizer_1.Add(20, -1)

        self.buttonsetind = wx.Button(self, -1, "SET ALL", size=(75, -1))  # , size=wx.DefaultSize)
        self.buttongetind = wx.Button(self, -1, "GET ALL", size=(75, -1))  # , size=wx.DefaultSize)
        self.Bind(wx.EVT_BUTTON, self.onSetInd, self.buttonsetind)
        self.Bind(wx.EVT_BUTTON, self.onGetInd, self.buttongetind)
        sizer_2.Add(self.buttongetind, 0, wx.ALIGN_CENTRE_VERTICAL | wx.LEFT, 5)
        sizer_2.Add(self.buttonsetind, 0, wx.ALIGN_CENTRE_VERTICAL, 0)

        #line = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
        #sizer_2.Add(line, 0, wx.GROW | wx.LEFT | wx.RIGHT, 2)

        sizer_1.Add(sizer_2, 0, wx.ALL, 2)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

    def onSetInd(self, event):
        ok = True
        cv32 = 0
        cv54 = 0
        cv56 = 0

        try:
            cv32 = int(self.texts.GetValue())
            if cv32 > 50 or cv32 < 10:
                raise ValueError
        except ValueError:
            ok = False
            with wx.MessageDialog(None, 'Servo speed must be a numeric value (10..50)',
                                  'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()

        try:
            cv54 = int(self.textl.GetValue())
            if cv54 > 255 or cv54 < 1:
                raise ValueError
        except ValueError:
            ok = False
            with wx.MessageDialog(None, 'Frequency must be a numeric value (1..255)',
                                  'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()

        try:
            cv56 = int(self.textv.GetValue())
            if cv56 > 30 or cv56 < 1:
                raise ValueError
        except ValueError:
            ok = False
            with wx.MessageDialog(None, 'Volume must be a numeric value (1..30)',
                                  'Value Error', wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()

        if ok:
            try:
                self.com.writeCV(32, cv32)
                self.com.writeCV(54, cv54)
                self.com.writeCV(56, cv56)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)

    def onGetInd(self, event):
        try:
            self.texts.SetValue(str(self.com.readCV(32)))
            self.textl.SetValue(str(self.com.readCV(54)))
            self.textv.SetValue(str(self.com.readCV(56)))
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)


class MultichoicePanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, cv, title, list):
        self.serial = serial
        self.parent = parent
        self.rb_select = 0
        self.cv = cv
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        sizer_0 = wx.BoxSizer(wx.VERTICAL)

        self.length = len(list)
        cols = self.length/4 + 1

        self.rb = wx.RadioBox(self, -1, title, wx.DefaultPosition, wx.DefaultSize, list, cols, wx.RA_SPECIFY_COLS)

        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)

        sizer_0.Add(self.rb, 0, wx.ALL, 5)

        self.SetSizer(sizer_0)
        sizer_0.Fit(self)
        self.Layout()

    def EvtRadioBox(self, event):
        self.rb_select = event.GetInt()
        try:
            self.com.writeCV(self.cv, self.rb_select)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def onGetChoice(self):
        try:
            sel = self.com.readCV(self.cv)
            if sel > self.length - 1:
                sel = 0
                self.rb.Enable(False)
            else:
                self.rb.Enable(True)
            self.SetSelection(sel)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)

    def GetSelection(self):
        return self.rb_select

    def SetSelection(self, val):
        self.rb.SetSelection(val)
        self.rb_select = val


class PLSliderPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial, out):
        self.parent = parent
        self.serial = serial
        self.id = out
        wx.Panel.__init__(self, mainparent)

        self.com = SerialCom(self.serial)

        self.SetBackgroundColour(bcolor)

        slider_dim = 100

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_0 = wx.BoxSizer(wx.HORIZONTAL)

        label_0 = wx.StaticText(self, -1, "Barriera {}".format(self.id+1))
        label_0.SetFont(wx.Font(8, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer_0.Add(label_0, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.LEFT, 5)

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)

        self.slider1 = 0
        self.slider2 = 0
        self.slider3 = 0
        self.slider4 = 0
        self.slider5 = 0

        self.slider_1 = wx.Slider(self, value=self.slider1, minValue=0, maxValue=255, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_2 = wx.Slider(self, value=self.slider2, minValue=0, maxValue=255, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_3 = wx.Slider(self, value=self.slider3, minValue=0, maxValue=255, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_4 = wx.Slider(self, value=self.slider4, minValue=0, maxValue=255, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_5 = wx.Slider(self, value=self.slider5, minValue=0, maxValue=255, size=(slider_dim, -1),
                                  style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
        self.slider_1.SetTickFreq(20)
        self.slider_2.SetTickFreq(20)
        self.slider_3.SetTickFreq(20)
        self.slider_4.SetTickFreq(20)
        self.slider_5.SetTickFreq(20)
        self.button_open = wx.Button(self, -1, "SET")
        self.button_close = wx.Button(self, -1, "SET")
        self.button_actual = wx.Button(self, -1, "SET")
        self.button_ctime = wx.Button(self, -1, "SET")
        self.button_otime = wx.Button(self, -1, "SET")
        self.buttonsetall = wx.Button(self, -1, "SET ALL")
        self.buttongetall = wx.Button(self, -1, "GET ALL")

        grid = wx.FlexGridSizer(2, 5, 0, 20)
        grid.Add(self.slider_1, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_2, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_3, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_4, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.slider_5, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.button_open, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.button_close, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.button_actual, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.button_ctime, 1, wx.ALIGN_CENTER, 0)
        grid.Add(self.button_otime, 1, wx.ALIGN_CENTER, 0)
        sizer_1.Add(grid, 2, 0, 0)

        line = wx.StaticLine(self, -1, size=(-1, 20), style=wx.LI_VERTICAL)
        sizer_1.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 0)

        sizer_0.Add(sizer_1, 2, wx.LEFT | wx.RIGHT, 0)

        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_2.Add(self.buttongetall, 1, wx.ALIGN_CENTRE, 0)
        sizer_2.Add(self.buttonsetall, 1, wx.ALIGN_CENTER, 0)
        sizer_0.Add(sizer_2, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(-1, 5), style=wx.LI_VERTICAL)
        sizer_0.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT, 2)
        sizer_0.Add((22, 22))

        sizer.Add(sizer_0, 0, wx.EXPAND, 0)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.TOP, 1)

        self.Bind(wx.EVT_SCROLL, self.onslider1, self.slider_1)
        self.Bind(wx.EVT_SCROLL, self.onslider2, self.slider_2)
        self.Bind(wx.EVT_SCROLL, self.onslider3, self.slider_3)
        self.Bind(wx.EVT_SCROLL, self.onslider4, self.slider_4)
        self.Bind(wx.EVT_SCROLL, self.onslider5, self.slider_5)
        self.Bind(wx.EVT_BUTTON, self.onset1, self.button_open)
        self.Bind(wx.EVT_BUTTON, self.onset2, self.button_close)
        self.Bind(wx.EVT_BUTTON, self.onset3, self.button_actual)
        self.Bind(wx.EVT_BUTTON, self.onset4, self.button_ctime)
        self.Bind(wx.EVT_BUTTON, self.onset5, self.button_otime)
        self.Bind(wx.EVT_BUTTON, self.onsetA, self.buttonsetall)
        self.Bind(wx.EVT_BUTTON, self.ongetA, self.buttongetall)

        self.EnableAllButtons(True)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def onslider1(self, event):
        self.slider1 = event.GetPosition()
        self.button_open.Enable(True)

    def onslider2(self, event):
        self.slider2 = event.GetPosition()
        self.button_close.Enable(True)

    def onslider3(self, event):
        self.slider3 = event.GetPosition()
        self.button_actual.Enable(True)

    def onslider4(self, event):
        self.slider4 = event.GetPosition()
        self.button_ctime.Enable(True)

    def onslider5(self, event):
        self.slider5 = event.GetPosition()
        self.button_otime.Enable(True)

    def onset1(self, event):
        try:
            self.onset(1, self.slider1)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.button_open.Enable(False)

    def onset2(self, event):
        try:
            self.onset(2, self.slider2)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.button_close.Enable(False)

    def onset3(self, event):
        try:
            self.onset(3, self.slider3)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.button_actual.Enable(False)

    def onset4(self, event):
        try:
            self.onset(4, self.slider4)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.button_ctime.Enable(False)

    def onset5(self, event):
        try:
            self.onset(5, self.slider5)
        except serial.serialutil.SerialTimeoutException as e:
            serialerrormessage(self.parent, message=e, close=False)
        else:
            self.button_otime.Enable(False)

    def onsetA(self, event):
        if event is None:
            self.EnableAllButtons(False)
            self.onset(6, -1)
        else:
            try:
                self.onset(6, -1)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)
            else:
                self.EnableAllButtons(False)

    def ongetA(self, event):
        if event is None:
            self.EnableAllButtons(False)
            self.onget(6)
        else:
            try:
                self.onget(6)
            except serial.serialutil.SerialTimeoutException as e:
                serialerrormessage(self.parent, message=e, close=False)
            else:
                self.EnableAllButtons(False)

    def EnableAllButtons(self, enable=True):
        self.button_close.Enable(enable)
        self.button_open.Enable(enable)
        self.button_actual.Enable(enable)
        self.button_ctime.Enable(enable)
        self.button_otime.Enable(enable)

    def onset(self, t, val):
        if t == 1:
            self.com.writeCV(33 + (self.id * 3), val)
        elif t == 2:
            self.com.writeCV(34 + (self.id * 3), val)
        elif t == 3:
            self.com.writeCV(35 + (self.id * 3), val)
        elif t == 4:
            self.com.writeCV(45 + self.id, val)
        elif t == 5:
            self.com.writeCV(49 + self.id, val)
        else:
            if self.button_open.IsEnabled():
                self.com.writeCV(33 + (self.id * 3), self.slider1)
            if self.button_close.IsEnabled():
                self.com.writeCV(34 + (self.id * 3), self.slider2)
            if self.button_actual.IsEnabled():
                self.com.writeCV(35 + (self.id * 3), self.slider3)
            if self.button_ctime.IsEnabled():
                self.com.writeCV(45 + self.id, self.slider4)
            if self.button_otime.IsEnabled():
                self.com.writeCV(49 + self.id, self.slider5)

    def onget(self, t):
        if t == 1:
            self.slider1 = self.com.readCV(33 + (self.id * 3))
            self.slider_1.SetValue(self.slider1)
        elif t == 2:
            self.slider2 = self.com.readCV(34 + (self.id * 3))
            self.slider_2.SetValue(self.slider2)
        elif t == 3:
            self.slider3 = self.com.readCV(35 + (self.id * 3))
            self.slider_3.SetValue(self.slider3)
        elif t == 4:
            self.slider4 = self.com.readCV(45 + self.id)
            self.slider_4.SetValue(self.slider4)
        elif t == 5:
            self.slider5 = self.com.readCV(49 + self.id)
            self.slider_5.SetValue(self.slider5)
        else:
            self.slider1 = self.com.readCV(33 + (self.id * 3))
            self.slider_1.SetValue(self.slider1)
            self.slider2 = self.com.readCV(34 + (self.id * 3))
            self.slider_2.SetValue(self.slider2)
            self.slider3 = self.com.readCV(35 + (self.id * 3))
            self.slider_3.SetValue(self.slider3)
            self.slider4 = self.com.readCV(45 + self.id)
            self.slider_4.SetValue(self.slider4)
            self.slider5 = self.com.readCV(49 + self.id)
            self.slider_5.SetValue(self.slider5)


class PLConfPanel(wx.Panel):
    def __init__(self, mainparent, parent, bcolor, serial):
        self.parent = parent
        self.serial = serial
        wx.Panel.__init__(self, mainparent)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_0 = wx.BoxSizer(wx.HORIZONTAL)

        control_list = ["manuale",
                        "sensori onboard",
                        "DCC"]
        barriere_list = ["nessuna barriera = 0 servo",
                         "barriera/semibarriere = 2 servo",
                         "semibarriere doppie = 4 servo"]
        luci_list = ["nessuna luce",
                     "singola fissa",
                     "doppia lampeggiante"]
        suono_list = ["disattivato",
                      "attivo solo in chiusura",
                      "attivo sempre"]
        audio_list = ["0000.mp3",
                      "0001.mp3",
                      "0002.mp3"]

        self.rb_controllo = MultichoicePanel(self, self, bcolor, serial, 30, "Controllo", control_list)
        self.rb_barriere = MultichoicePanel(self, self, bcolor, serial, 31, "Barriere", barriere_list)
        self.rb_luci = MultichoicePanel(self, self, bcolor, serial, 53, "Luci", luci_list)
        self.rb_suono = MultichoicePanel(self, self, bcolor, serial, 55, "Suono", suono_list)
        self.rb_audio = MultichoicePanel(self, self, bcolor, serial, 57, "File Audio", audio_list)

        sizer_0.Add(self.rb_controllo, 0, wx.ALL, 2)
        sizer_0.Add(self.rb_barriere, 0, wx.ALL, 2)
        sizer_0.Add(self.rb_luci, 0, wx.ALL, 2)
        sizer_0.Add(self.rb_suono, 0, wx.ALL, 2)
        sizer_0.Add(self.rb_audio, 0, wx.ALL, 2)

        sizer.Add(sizer_0, 0, wx.ALL, 0)

        self.SetBackgroundColour(bcolor)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.Layout()

    def onGetA(self):
        self.rb_controllo.onGetChoice()
        self.rb_barriere.onGetChoice()
        self.rb_luci.onGetChoice()
        self.rb_suono.onGetChoice()
        self.rb_audio.onGetChoice()

    def SetBackgroundColour(self, colour):
        self.rb_controllo.SetBackgroundColour(colour)
        self.rb_barriere.SetBackgroundColour(colour)
        self.rb_luci.SetBackgroundColour(colour)
        self.rb_suono.SetBackgroundColour(colour)
        self.rb_audio.SetBackgroundColour(colour)
        wx.Panel.SetBackgroundColour(self, colour)


if __name__ == '__main__':
    ser = serial.Serial()
    app = wx.App()
    try:
        ser.port = "COM7"
        ser.baudrate = 9600
        ser.timeout = 1
        ser.open()
        print(ser)
    except serial.SerialException as e:
        with wx.MessageDialog(None, str(e), "Serial Port Error", wx.OK | wx.ICON_ERROR) as dlg:
            dlg.ShowModal()
    else:
        sleep(5)
        frm = wx.Frame(None, -1, "Test Frame")
        frm.SetBackgroundColour(wx.YELLOW)
        frm.CenterOnScreen()

        #ServoPanel(frm, frm, bcolor=wx.YELLOW, serial=ser, out=0)
        #TestPanel(frm, frm, bcolor=wx.YELLOW, serial=ser, out=0)
        #CV28Panel(frm, frm, bcolor=wx.YELLOW, serial=ser)
        #CV1Panel(frm, frm, bcolor=wx.YELLOW, serial=ser)
        #CoilPanel(frm, frm, bcolor=wx.YELLOW, serial=ser, out=0)
        with CVdialog(frm, -1, "Test Dialog", bcolor=wx.YELLOW, serial=ser) as dlg:
            dlg.CenterOnScreen()
            dlg.ShowModal()
            dlg.Destroy()

        CVpanel(frm, frm, bcolor=wx.YELLOW, serial=ser)

        frm.Fit()
        frm.Show()
        frm.CenterOnScreen()
        app.MainLoop()
