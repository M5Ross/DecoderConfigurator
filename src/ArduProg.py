
import os
import wx
import sys
from subprocess import call
import serial.tools.list_ports

extension = "Hex file (*.hex)|*.hex|" \
            "Exe file (*.exe)|*.exe|" \
            "Conf file (*.conf)|*.conf|" \
            "All files (*.*)|*.*"


def resource_path(relative_path, meipass=False):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if meipass:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    else:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    return os.path.join(base_path, relative_path)


class UpgradeFrame(wx.Frame):
    def __init__(self, *args, **kw):
        self.micro = kw['micro']
        self.show = kw['show']
        self.uploadType = kw['uploadtype']
        self.avrdudedir = kw['avrdudedir']

        del kw['show']
        del kw['micro']
        del kw['uploadtype']
        del kw['avrdudedir']
        # del kw['parent']
        self.minsize = 200
        self.boxprosize = 100
        self.batdirectory = ""
        self.batfilename = "__uploader.bat"
        self.microlist = ["atmega328p", "atmega32u4"]
        self.arrow = ""
        self.default = self.setDefault()
        self.pathHex = self.setPathHex()
        self.commonProcess = ""
        self.leoprocess1 = "set port="
        self.leoprocess2 = "\nmode %port%: BAUD=1200 parity=N data=8 stop=1\nping 127.0.0.1 -n 2 > nul\n" \
                           "for /f \"tokens=1* delims==\" %%I in ('wmic path win32_pnpentity get caption" \
                           "  /format:list ^| find \"Arduino Leonardo bootloader\"') do (call :setCOM \"%%~J\")\n" \
                           "goto :EOF\n:setCOM <WMIC_output_line>\nsetlocal\nset \"str=%~1\"\n" \
                           "set \"num=%str:*(COM=%\"\nset \"num=%num:)=%\"\nset port=COM%num%\necho %port%\n" \
                           "goto :flash\n:flash\n"
        # self.commonProcess = "C:\\Users\\Jaco\\AppData\\Local\\Arduino15\\packages\\arduino\\tools\\avrdude\\" \
        #                     "6.3.0-arduino9/bin/avrdude -CC:\\Users\\Jaco\\AppData\\Local\\Arduino15\\packages\\" \
        #                     "arduino\\tools\\avrdude\\6.3.0-arduino9/etc/avrdude.conf -v -patmega328p -c"
        self.serialprocess1uno = "arduino "
        self.serialprocess1leo = "avr109 "
        self.serialspeeduno = " -b115200"
        self.serialspeedleo = " -b57600"
        self.serialprocess2 = " -D -Uflash:w:"
        self.programprocess1 = "stk500v1"
        self.programprocess2uno = ""
        self.programprocess2leo = ""
        # self.programprocess2 = " -b19200 -e -Ulock:w:0x3F:m -Uefuse:w:0xFD:m -Uhfuse:w:0xDE:m -Ulfuse:w:0xFF:m" \
        #                       "\n" \
        #                       "C:\\Users\\Jaco\\AppData\\Local\\Arduino15\\packages\\arduino\\tools\\avrdude\\" \
        #                       "6.3.0-arduino9/bin/avrdude -CC:\\Users\\Jaco\\AppData\\Local\\Arduino15\\packages\\" \
        #                       "arduino\\tools\\avrdude\\6.3.0-arduino9/etc/avrdude.conf " \
        #                       "-v -patmega328p -cstk500v1"
        self.programprocess3 = " -b19200 -Uflash:w:"
        self.previousConsol = ""
        self.dirHex = ""
        self.nameHex = ""
        self.serial = serial.Serial()
        self.ports = []
        self.com_port = ""
        self.comx = ""

        self.color = kw['bcolor']
        del kw['bcolor']

        # ensure the parent's __init__ is called
        super(UpgradeFrame, self).__init__(*args, **kw)

        icon = wx.Icon(resource_path("icon.ico", True))
        self.SetIcon(icon)
        if self.avrdudedir is None:
            self.avrdudedir = os.path.dirname(resource_path("avrdude.txt"))
        self.avrdudefile = ConfFile(self.avrdudedir + "\\avrdude.txt")
        # self.avrdudefile = HiddenFile("C:\\avrdude.txt")
        self.avrdude = self.avrdudefile.readlines()

        self.SetBackgroundColour(self.color)

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "Simple HEX Uploader")
        label.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # -----------------------------------------------------------
        # crea box per "open .hex"
        box = wx.BoxSizer(wx.HORIZONTAL)

        # crea il bottone, ci attacca l'evento e lo posiziona
        self.btnOpenHex = wx.Button(self, -1, "Open .hex")
        self.Bind(wx.EVT_BUTTON, self.openHex, self.btnOpenHex)
        box.Add(self.btnOpenHex, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # crea la text bar per la path
        self.textPathHex = wx.TextCtrl(self, -1, self.default, size=(self.minsize, -1), style=wx.TE_READONLY)
        box.Add(self.textPathHex, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        # aggiunge il box al sizer per l'allineamneto verticale
        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        self.box = wx.BoxSizer(wx.HORIZONTAL)
        self.radiobox = wx.BoxSizer(wx.VERTICAL)

        self.rbm = wx.RadioBox(self, -1, "Processor", wx.DefaultPosition, wx.DefaultSize,
                               self.microlist, 2, wx.RA_SPECIFY_COLS)
        self.rbm.SetSelection(self.micro)
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBoxM, self.rbm)
        # self.rb.SetBackgroundColour(wx.BLUE)
        # self.rb.SetToolTip(wx.ToolTip("This is a ToolTip!"))
        # self.rb.SetLabel("wx.RadioBox")
        self.radiobox.Add(self.rbm, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.rb = wx.RadioBox(self, -1, "Upload Type", wx.DefaultPosition, wx.DefaultSize,
                              ['Programmer', 'Serial'], 2, wx.RA_SPECIFY_COLS)
        self.rb.SetSelection(self.uploadType)
        self.Bind(wx.EVT_RADIOBOX, self.EvtRadioBox, self.rb)
        # self.rb.SetBackgroundColour(wx.BLUE)
        # self.rb.SetToolTip(wx.ToolTip("This is a ToolTip!"))
        # self.rb.SetLabel("wx.RadioBox")
        self.radiobox.Add(self.rb, 1, wx.ALIGN_CENTRE | wx.ALL, 5)
        self.box.Add(self.radiobox, 1, wx.GROW | wx.ALL, 0)

        self.choicebox = wx.BoxSizer(wx.VERTICAL)

        self.label = wx.StaticText(self, -1, "Select Port:")
        self.choicebox.Add(self.label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.choice_port = wx.Choice(self, -1, choices=[], size=(190, -1))
        self.getportlist()
        self.Bind(wx.EVT_CHOICE, self.EvtChoicePort, self.choice_port)
        self.choicebox.Add(self.choice_port, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        self.box.Add(self.choicebox, 1, wx.GROW | wx.ALL, 0)

        sizer.Add(self.box, 0, wx.GROW | wx.ALL, 5)

        # aggiunge separatore linea
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.RIGHT | wx.LEFT | wx.TOP, 5)

        # -----------------------------------------------------------
        # crea box per per lo standard output di processo
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.textProcess = wx.TextCtrl(self, -1, "", size=(self.minsize+50, self.boxprosize),
                                       style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.textProcess.SetBackgroundColour(wx.BLACK)
        self.updateConsol()
        box.Add(self.textProcess, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        if not self.show:
            self.rbm.Hide()
            self.rb.Hide()
            self.label.Hide()
            self.choice_port.Hide()
            self.textProcess.Hide()

        btnsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.btnUpload = wx.Button(self, wx.ID_OK, "Upload")
        self.Bind(wx.EVT_BUTTON, self.uploadFile, self.btnUpload)
        self.btnUpload.SetDefault()
        self.btnUpload.Enable(True)
        btnsizer.Add(self.btnUpload)

        # self.btnClear = wx.Button(self, wx.ID_CANCEL, "Clear")
        # self.Bind(wx.EVT_BUTTON, self.clearAll, self.btnClear)
        # self.btnClear.Enable(False)
        # btnsizer.Add(self.btnClear, 0, wx.LEFT | wx.RIGHT, 5)

        btnsizer.Add((10, -1))

        self.btnConf = wx.Button(self, wx.ID_EDIT, "Settings")
        self.Bind(wx.EVT_BUTTON, self.OnEdit, self.btnConf)
        self.btnConf.Enable(True)
        btnsizer.Add(self.btnConf)

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(btnsizer, 0, wx.ALL, 10)

        sizer.Add(box, 0, wx.ALIGN_CENTRE, 10)

        self.Bind(wx.EVT_CLOSE, self.OnExit)

        self.CreateStatusBar()
        self.SetStatusText("By M.Ross")
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.CenterOnScreen()
        self.Show()

    def OnExit(self, event):
        """Close the frame, terminating the application."""
        self.Destroy()

    def OnEdit(self, event):
        dlg = AvrdudePathDialog(self, -1, "Avrdude configuration", self.avrdudefile, self.color)
        dlg.CenterOnScreen()
        result = dlg.ShowModal()
        if result == wx.ID_OK:
            self.avrdudefile.write(type=True)
            self.avrdude = self.avrdudefile.readlines()

        dlg.Destroy()
        #self.getportlist()
        self.updateConsol()

    def EvtRadioBox(self, event):
        self.uploadType = event.GetInt()
        #self.getportlist()
        self.updateConsol()

    def EvtRadioBoxM(self, event):
        self.micro = event.GetInt()
        #self.getportlist()
        self.updateConsol()

    def EvtChoicePort(self, event):
        port = event.GetString()[:5]
        if port[-1] == " ":
            port = port[:-1]
        self.com_port = " -P" + port
        self.updateConsol()

    def getportlist(self):
        # fill in ports and select current setting
        preferred_index = 0
        self.choice_port.Clear()

        i = 0
        for n, (portname, desc, hwid) in enumerate(sorted(serial.tools.list_ports.comports())):
            i += 1
            self.choice_port.Append(u'{}'.format(desc))
            self.ports.append(portname)
            if self.serial.name == portname:
                preferred_index = n
        self.choice_port.SetSelection(preferred_index)

        if i > 0:
            self.comx = self.ports[preferred_index]
            self.com_port = " -P" + self.comx
        else:
            self.com_port = ""

    def openHex(self, event):
        path = self.avrdudedir + "\\HEX"
        if not os.path.exists(self.avrdudedir + "\\HEX"):
            path = os.getcwd()

        dlg = wx.FileDialog(self,
                            message="Choose a file...",
                            defaultDir=path,  # os.getcwd(),
                            defaultFile="",
                            wildcard=extension,
                            style=wx.FD_OPEN |
                                  wx.FD_CHANGE_DIR |
                                  wx.FD_FILE_MUST_EXIST |
                                  wx.FD_PREVIEW)

        dlg.SetFilterIndex(0)

        if dlg.ShowModal() == wx.ID_OK:
            self.dirHex = dlg.GetDirectory()
            self.nameHex = dlg.GetFilename()
            path = os.path.join(self.dirHex, self.nameHex)
            self.textPathHex.SetValue(self.nameHex)
            self.pathHex = path
            self.updateConsol()

        #self.getportlist()
        dlg.Destroy()

    def commandLine(self):
        lockend = ""

        try:
            txt1 = self.avrdude[0][:-5]
        except IndexError or TypeError:
            txt1 = ""
        try:
            txt2 = self.avrdude[1][:-1]
        except IndexError or TypeError:
            txt2 = ""

        self.commonProcess = "\"" + txt1 + "\" -C\"" + txt2 + "\" -v -p" + self.microlist[self.micro] + " -c"
        self.programprocess2uno = " -b19200 -e -Ulock:w:0x3F:m -Uefuse:w:0xFD:m -Uhfuse:w:0xDE:m -Ulfuse:w:0xFF:m" \
                               "\n\"" + txt1 + "\" -C\"" + txt2 + "\" -v -p" + self.microlist[self.micro] + \
                               " -cstk500v1"
        self.programprocess2leo = " -b19200 -e -Ulock:w:0x3F:m -Uefuse:w:0xcb:m -Uhfuse:w:0xd8:m -Ulfuse:w:0xff:m" \
                                  "\n\"" + txt1 + "\" -C\"" + txt2 + "\" -v -p" + self.microlist[self.micro] + \
                                  " -cstk500v1"

        preprocess = ""
        if self.uploadType == 0:
            # Programmer
            lockend = " -Ulock:w:0x0F:m"
            if self.micro == 0:
                # UNO
                process = self.programprocess1 + self.com_port + \
                          self.programprocess2uno + self.com_port + \
                          self.programprocess3
            else:
                # LEO
                process = self.programprocess1 + self.com_port + \
                          self.programprocess2leo + self.com_port + \
                          self.programprocess3
        else:
            # Serial
            if self.micro == 0:
                # UNO
                process = self.serialprocess1uno + self.com_port + self.serialspeeduno + self.serialprocess2
            else:
                # LEO
                preprocess = self.leoprocess1 + self.comx + self.leoprocess2
                process = self.serialprocess1leo + "-P%port%" + self.serialspeedleo + self.serialprocess2
        return preprocess + self.commonProcess + process + "\"" + self.pathHex + "\":i" + lockend

    def extUploadInit(self):
        pass

    def extUploadFinish(self):
        pass

    def setDefault(self):
        return ""

    def setPathHex(self):
        return ""

    def uploadFile(self, event):
        if self.pathHex == "" or self.comx == "":
            self.updateConsol("ERROR: no file .hex selected", wx.RED)
            if not self.show:
                with wx.MessageDialog(self, 'No .EXE file selected', 'Error', wx.OK | wx.ICON_EXCLAMATION) as dlg:
                    dlg.CenterOnScreen()
                    dlg.ShowModal()
        else:
            self.extUploadInit()
            self.btnUpload.Enable(False)
            self.btnOpenHex.Enable(False)
            self.rb.Enable(False)
            self.rbm.Enable(False)
            self.choice_port.Enable(False)

            if os.path.exists(self.batfilename):
                os.remove(self.batfilename)

            file = open(self.batfilename, "w")
            #file.write("color 06\ncls\n" + self.commandLine())
            file.write(self.commandLine())
            file.close()

            call(self.batfilename)

            # cancella .bat
            if os.path.exists(self.batfilename):
                os.remove(self.batfilename)

            # self.btnClear.Enable(True)

            self.updateConsol("\n\n  !!.:DONE:.!!", wx.GREEN, False)
            self.extUploadFinish()

    # def clearAll(self, event):
    #     self.btnClear.Enable(False)
    #     self.btnOpenHex.Enable(True)
    #     self.textPathHex.SetValue("")
    #     self.pathHex = ""
    #     self.rb.Enable(True)
    #     self.rbm.Enable(True)
    #     self.rb.SetSelection(self.uploadType)
    #     self.rbm.SetSelection(self.micro)
    #     self.choice_port.Enable(True)
    #
    #     self.getportlist()
    #     self.updateConsol()
    #
    #     self.btnUpload.Enable(True)

    def updateConsol(self, string="", color=wx.WHITE, errase=True):
        self.textProcess.SetForegroundColour(color)
        if errase:
            self.previousConsol = ""
        if string == "":
            self.previousConsol += self.arrow + self.commandLine()
        else:
            self.previousConsol += string
        self.textProcess.SetValue(self.previousConsol)


class AvrdudePathDialog(wx.Dialog):
    def __init__(self, parent, id, title, hiddenfile, bcolor, size=wx.DefaultSize, pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE, name='dialog'):

        self.hiddenfile = hiddenfile
        color = bcolor
        del hiddenfile
        del bcolor

        wx.Dialog.__init__(self)
        self.Create(parent, id, title, pos, size, style, name)

        self.minsize = 700
        self.path = ""

        path = self.hiddenfile.readlines()
        try:
            self.pathexe = path[0]
        except IndexError:
            self.pathexe = ""
        try:
            self.pathconf = path[1]
        except IndexError:
            self.pathconf = ""

        icon = wx.Icon(resource_path("icon.ico", True))
        self.SetIcon(icon)

        self.SetBackgroundColour(color)

        sizer = wx.BoxSizer(wx.VERTICAL)

        label = wx.StaticText(self, -1, "Avrdude Paths")
        label.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # crea box per "open .exe"
        box = wx.BoxSizer(wx.HORIZONTAL)

        # crea il bottone, ci attacca l'evento e lo posiziona
        self.btnOpenExe = wx.Button(self, -1, "Open .exe  ")
        self.Bind(wx.EVT_BUTTON, self.OnExe, self.btnOpenExe)
        box.Add(self.btnOpenExe, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # crea la text bar per la path
        self.textPathExe = wx.TextCtrl(self, -1, self.pathexe, size=(self.minsize, -1), style=wx.TE_READONLY)
        box.Add(self.textPathExe, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        # aggiunge il box al sizer per l'allineamneto verticale
        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        # crea box per "open .conf"
        box = wx.BoxSizer(wx.HORIZONTAL)

        # crea il bottone, ci attacca l'evento e lo posiziona
        self.btnOpenConf = wx.Button(self, -1, "Open .conf")
        self.Bind(wx.EVT_BUTTON, self.OnConf, self.btnOpenConf)
        box.Add(self.btnOpenConf, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # crea la text bar per la path
        self.textPathConf = wx.TextCtrl(self, -1, self.pathconf, size=(self.minsize, -1), style=wx.TE_READONLY)
        box.Add(self.textPathConf, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        # aggiunge il box al sizer per l'allineamneto verticale
        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.RIGHT | wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btnOk = wx.Button(self, wx.ID_OK)
        btnOk.SetDefault()
        btnsizer.AddButton(btnOk)

        btnC = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btnC)

        btnsizer.Realize()

        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(btnsizer, 1, wx.ALL, 10)

        sizer.Add(box, 1, wx.ALIGN_CENTRE, 20)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def OnExe(self, event):
        self.open(1)
        if self.path != "" and self.path is not None:
            self.pathexe = self.path
            self.textPathExe.SetValue(self.path)
            self.hiddenfile.write(list=[self.pathexe, self.pathconf])

    def OnConf(self, event):
        self.open(2)
        if self.path != "" and self.path is not None:
            self.pathconf = self.path
            self.textPathConf.SetValue(self.path)
            self.hiddenfile.write(list=[self.pathexe, self.pathconf])

    def open(self, filetype):
        dlg = wx.FileDialog(self,
                            message="Choose Avrdude file...",
                            defaultDir=os.getcwd(),
                            defaultFile="",
                            wildcard=extension,
                            style=wx.FD_OPEN |
                                  wx.FD_CHANGE_DIR |
                                  wx.FD_FILE_MUST_EXIST |
                                  wx.FD_PREVIEW)

        dlg.SetFilterIndex(filetype)

        if dlg.ShowModal() == wx.ID_OK:
            dir = dlg.GetDirectory()
            name = dlg.GetFilename()
            self.path = os.path.join(dir, name)

        dlg.Destroy()


class ConfFile:
    def __init__(self, filename):
        self.filemane = filename
        self.tempexe = ""
        self.tempconf = ""

    def readlines(self):
        try:
            return open(self.filemane, "r").readlines()
        except FileNotFoundError:
            return ""

    def read(self):
        try:
            return open(self.filemane, "r").read()
        except FileNotFoundError:
            return ""

    def write(self, list="", type=False):
        if type is True:
            if self.tempexe != "" or self.tempconf != "":
                file = open(self.filemane, "w")
                file.write(self.tempexe)
                file.write(self.tempconf)
                file.close()
        else:
            self.tempexe = list[0]
            self.tempconf = list[1]
            try:
                if self.tempexe[-1] != "\n":
                    self.tempexe += "\n"
            except IndexError:
                pass
            try:
                if self.tempconf[-1] != "\n":
                    self.tempconf += "\n"
            except IndexError:
                pass


if __name__ == '__main__':
    app = wx.App()
    frm = UpgradeFrame(None, title=" HexUploader ", micro=0, show=True, uploadtype=0, avrdudedir=None, bcolor=wx.YELLOW)
    # frm.Show()
    app.MainLoop()
