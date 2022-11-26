
import wx
import serial
from RRserial import SerialCom


class Device:
    def __init__(self, device=None):
        self.device_selected = device                           # HW ID     # MICRO
        self.list_of_device = ["AccDec_4Coil_4Relais",          # 0         # atmega328p
                               "AccDec_4Servos_4Relais",        # 1         # atmega328p
                               "AccDec_8Coil",                  # 2         # atmega328p
                               "AccDec_8Servos_8Relais",        # 3         # atmega328p
                               "AccDec_8Servo_LN_USB",          # 4         # atmega32u4
                               "LoconetFeedback8Led",           # 5         # atmega328p
                               "LoconetRailcomFeedback4Led",    # 6         # atmega328p
                               "AccDec_PL_Sound"                # 7         # atmega328p
                               ]

        self.Device_AccDec_4Coil_4Relais = 0
        self.Device_AccDec_4Servos_4Relais = 1
        self.Device_AccDec_8Coil = 2
        self.Device_AccDec_8Servos_8Relais = 3
        self.Device_AccDec_8Servo_LN_USB = 4
        self.Device_LoconetFeedback8Led = 5
        self.Device_LoconetRailcomFeedback4Led = 6
        self.Device_AccDec_PL_Sound = 7

        self.Type_Coils = 0
        self.Type_Servos = 1
        self.Type_Loconet = 2
        self.Type_PL_sound = 3

    def SetDevice(self, newdevice):
        self.device_selected = newdevice

    def GetDevice(self):
        return self.device_selected

    def GetName(self):
        return self.list_of_device[self.device_selected] if self.device_selected is not None else ""

    def append(self, newdevice):
        self.list_of_device.append(newdevice)

    def GetList(self):
        return self.list_of_device


class DeviceSettingsDialog(wx.Dialog):
    """Simple dialog with common terminal settings like echo, newline mode."""

    def __init__(self, *args, **kwds):
        self.serial = kwds['serial']
        self.dev = kwds['device']
        del kwds['serial']
        del kwds['device']
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        self.com = SerialCom(self.serial)

        self.panel_device = wx.Panel(self, -1)
        self.label_1 = wx.StaticText(self.panel_device, -1, "   Select device:      ")
        self.button_device = wx.Button(self.panel_device, wx.ID_EDIT, "Auto Search", size=(100, 30))
        self.choice_device = wx.Choice(self.panel_device, -1, choices=self.dev.GetList())
        self.sizer_device_staticbox = wx.StaticBox(self.panel_device, -1, "")
        self.button_ok = wx.Button(self, wx.ID_OK, "")
        self.button_cancel = wx.Button(self, wx.ID_CANCEL, "")

        self.__set_properties()
        self.__do_layout()
        self.__attach_events()

    def __set_properties(self):
        self.SetTitle("Device Selection")
        device = self.dev.GetDevice() if self.dev.GetDevice() is not None else -1
        self.choice_device.SetSelection(device)
        self.button_ok.SetDefault()

    def __do_layout(self):
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)

        self.sizer_device_staticbox.Lower()
        sizer_device = wx.StaticBoxSizer(self.sizer_device_staticbox, wx.VERTICAL)
        grid_sizer_2 = wx.FlexGridSizer(1, 2, 0, 0)
        grid_sizer_2.Add(self.label_1, 2, wx.ALIGN_CENTRE_VERTICAL | wx.ALIGN_CENTRE_HORIZONTAL, 0)
        grid_sizer_2.Add(self.button_device, 2, wx.ALIGN_RIGHT, 2)
        sizer_device.Add(grid_sizer_2, 2, wx.EXPAND, 0)
        sizer_device.Add((5, 5))
        sizer_device.Add(self.choice_device, 0, wx.EXPAND, 0)
        self.panel_device.SetSizer(sizer_device)
        sizer_2.Add(self.panel_device, 0, wx.EXPAND, 0)

        sizer_3.Add(self.button_ok, 0, wx.ALL, 5)
        sizer_3.Add(self.button_cancel, 0, wx.ALL, 5)
        sizer_2.Add(sizer_3, 0, wx.ALIGN_CENTRE, 20)
        self.SetSizer(sizer_2)
        sizer_2.Fit(self)
        self.Layout()

    def __attach_events(self):
        self.Bind(wx.EVT_CHOICE, self.EvtChoice, self.choice_device)
        self.Bind(wx.EVT_BUTTON, self.OnSearch, self.button_device)
        self.Bind(wx.EVT_BUTTON, self.OnOK, self.button_ok)
        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.button_cancel)

    def EvtChoice(self, events):
        dis = events.GetSelection()
        self.dev.SetDevice(dis)
        # print("device N°%s = %s" % (dis, self.dev.GetName()))

    def OnSearch(self, events):
        ok = True
        tim = self.serial.timeout
        try:
            self.serial.timeout = 10
        except serial.serialutil.SerialException:
            pass
        try:
            val = self.com.GetDeviceID()
            try:
                self.serial.timeout = tim
            except serial.serialutil.SerialException:
                pass
        except serial.serialutil.SerialTimeoutException:
            val = -1
        if self.com.GetOKcode() == self.com.OKCODE_OK and val > -1:
            self.choice_device.SetSelection(val)
            self.dev.SetDevice(val)
        else:
            ok = False
        if not ok:
            dlg = wx.MessageDialog(self, 'Device not found!', 'Warning', wx.OK | wx.ICON_INFORMATION)
            dlg.CenterOnParent()
            dlg.ShowModal()
            dlg.Destroy()

    def OnOK(self, events):
        """Update data wil new values and close dialog."""
        if self.dev.GetDevice() is None:
            dlg = wx.MessageDialog(self, 'No device selected!', 'Error', wx.OK | wx.ICON_ERROR)
            dlg.CenterOnParent()
            dlg.ShowModal()
            dlg.Destroy()
        else:
            self.EndModal(wx.ID_OK)

    def OnCancel(self, events):
        """Do not update data but close dialog."""
        self.EndModal(wx.ID_CANCEL)


class MyApp(wx.App):
    """Test code"""
    def OnInit(self):
        wx.InitAllImageHandlers()

        ser = serial.Serial()
        try:
            ser.port = "COM7"
            ser.baudrate = 9600
            ser.timeout = 1
            ser.open()
            print(ser)
        except serial.SerialException as e:
            with wx.MessageDialog(None, str(e), "Serial Port Error", wx.OK | wx.ICON_ERROR) as dlg:
                dlg.ShowModal()
                return 0
        else:
            dev = Device()
            while True:
                dev.SetDevice(None)
                dialog_device_settings = DeviceSettingsDialog(None, -1, "", serial=ser, status=True, device=dev)
                self.SetTopWindow(dialog_device_settings)
                result = dialog_device_settings.ShowModal()
                print(dev.GetName() if not dev.GetName() == "" else "No Selection")
                if result != wx.ID_OK:
                    ser.close()
                    break
        return 0


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
