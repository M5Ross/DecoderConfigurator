
import os
import wx
import csv
import serial
from RRserial import SerialCom

extension = "CV file (*.cv)|*.cv|" \
            "Text file (*.txt)|*.txt|" \
            "All files (*.*)|*.*"


class RRfileManager:
    def __init__(self, parent, serial):
        self.parent = parent
        self.com = SerialCom(serial)
        self.cv = [0]*999
        self.val = [0]*999
        self.Set = 0
        self.ncv = 0
        self.color = [170, 170, 170]
        self.versions = []

    def Save(self, device, cv1):  # wxGlade: TerminalFrame.<event_handler>
        name = "My_" + str(device) + ("_" + str(cv1)) if cv1 else ""
        dlg = wx.FileDialog(
            None, message="Save file as ...", defaultDir=os.getcwd(),
            defaultFile=name, wildcard=extension, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        )

        dlg.SetFilterIndex(0)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.writeCSVfile(path)

        dlg.Destroy()

    def Open(self, device):
        dlg = wx.FileDialog(
            None, message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard=extension,
            style=wx.FD_OPEN |
                  wx.FD_CHANGE_DIR |
                  wx.FD_FILE_MUST_EXIST |
                  wx.FD_PREVIEW
        )

        if dlg.ShowModal() == wx.ID_OK:
            self.readCSVfile(dlg.GetPath(), device)

        dlg.Destroy()

    def writeCSVfile(self, path):
        with open(path, mode='w') as csv_file:
            fieldnames = ['CV_NUM', 'CV_VAL']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            cv_num = self.com.GetCVlist()
            if cv_num:
                self.cv = self.com.GetCV()
                self.val = self.com.GetVal()
                for n in range(cv_num):
                    writer.writerow({'CV_NUM': str(self.cv[n]), 'CV_VAL': str(self.val[n])})
                    #print("Write in file: cv %s = %s" % (self.cv[n], self.val[n]))

    def readCSVfile(self, path, dev):
        self.Set = 0
        with open(path, mode='r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            self.ncv = 0
            for row in csv_reader:
                self.cv[self.ncv] = int(row['CV_NUM'])
                self.val[self.ncv] = int(row['CV_VAL'])
                #print("Read form file: cv %s = %s" % (self.cv[self.ncv], self.val[self.ncv]))
                self.ncv += 1
            with wx.MessageDialog(None, 'Do you wont to write all CV?', 'Warning',
                                  wx.YES | wx.NO | wx.ICON_WARNING) as dlg:
                dlg.CenterOnScreen()
                result = dlg.ShowModal()
            if result == wx.ID_YES:
                try:
                    self.Set = self.com.SetCVlist(cv_list=self.cv[:self.ncv], val_list=self.val[:self.ncv],
                                                  row=self.ncv, val_max=999 if dev > 4 else 255)
                except ValueError as e:
                    with wx.MessageDialog(self.parent, str(e), "Error reading .cv file", wx.OK | wx.ICON_ERROR) as dlg:
                        dlg.CenterOnParent()
                        dlg.ShowModal()

    def readVersions(self, path, device):
        self.versions = []
        with open(path, mode='r') as conf_file:
            table = []
            for row in conf_file.readlines():
                line = row.replace('\r', '').replace('\n', '').split(',')
                print(row, line)
                # titles
                if 'DECODER' in line:
                    pass
                # color line
                elif 'Color' in line:
                    self.color = [int(line[1]), int(line[2]), int(line[3])]
                    print('Color =', self.color)
                # devices info
                else:
                    self.versions.append(row)
                    if int(line[1]) == device:
                        table.append([line[0], int(line[2]), int(line[3])])
            return table

    def GetCV(self):
        return self.com.GetCV()

    def GetVal(self):
        return self.com.GetVal()

    def GetSet(self):
        return self.Set

    def GetColor(self):
        return tuple(self.color)

    def SetColor(self, path, color):
        with open(path, mode='w') as conf_file:
            fieldnames = ['DECODER,ID,HW,SW\n', 'Color,%d,%d,%d\n' % (color[0], color[1], color[2])]
            conf_file.writelines(fieldnames)
            for row in self.versions:
                conf_file.writelines(row)


class TestPanel(wx.Panel):
    def __init__(self, parent, serial):
        wx.Panel.__init__(self, parent, -1)

        self.manager = RRfileManager(parent, serial)

        b = wx.Button(self, -1, "SAVE", (50, 50))
        self.Bind(wx.EVT_BUTTON, self.OnButton, b)

        b = wx.Button(self, -1, "OPEN", (50, 90))
        self.Bind(wx.EVT_BUTTON, self.OnButton2, b)

    def OnButton(self, evt):
        self.manager.Save("esempio", "x")

    def OnButton2(self, evt):
        self.manager.Open(0)


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
        frm = wx.Frame(None, -1, "Test Frame", size=(200, 200))
        frm.SetBackgroundColour(wx.YELLOW)
        TestPanel(frm, ser)
        frm.Show()
        app.MainLoop()
