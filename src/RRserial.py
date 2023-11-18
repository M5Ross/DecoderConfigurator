import serial


class SerialCom:
    def __init__(self, serial):
        self.OKCODE_DECODER_ID = 0
        self.OKCODE_HW_VERSION = 1
        self.OKCODE_SW_VERSION = 2
        self.OKCODE_WRITE_CV = 10
        self.OKCODE_READ_CV = 11
        self.OKCODE_MOVE_DX = 20
        self.OKCODE_MOVE_SX = 21
        self.OKCODE_OK = 98
        self.OKCODE_ERROR = 99

        self.serial = serial
        self.rawrx = None
        self.okcode = self.OKCODE_ERROR
        self.value = None
        self.num_cv = 0
        self.cv_list = [0]*999
        self.val_list = [0]*999

    def transaction(self, tx):
        print("TX: %s" % str(tx))
        # for x in range(8):
        #     try:
        #         self.serial.write(tx[x].encode())
        #     except serial.serialutil.SerialTimeoutException:
        #         raise serial.serialutil.SerialTimeoutException("Serial communication error")

        try:
            self.serial.write(tx.encode())
        except serial.serialutil.SerialTimeoutException:
            raise serial.serialutil.SerialTimeoutException("Serial communication error")

        self.rawrx = self.serial.read(size=8)
        try:
            rx = self.rawrx.decode('utf-8')
        except UnicodeDecodeError as e:
            print("RRserial error: ", e)
            self.rawrx = self.serial.read(self.serial.in_waiting)
            raise serial.serialutil.SerialTimeoutException("Serial communication error")

        k = 0
        for n in rx:
            try:
                int(n)
            except ValueError:
                k += 1
        if k > 0:
            print("Transazione corrotta: leggo", k, "byte per tornare al pari")
            self.serial.read(k)
            # provo un'altra volta
            return self.transaction(tx)

        print("RX: %s" % str(rx))

        try:
            self.okcode = int(self.rawrx[:2])
            # print("okcode = %s" % self.okcode)
        except ValueError:
            self.okcode = self.OKCODE_ERROR
        try:
            self.value = int(rx[3:])
            # print("val = %s" % self.value)
        except ValueError:
            self.value = 0
        return self.value

    def formatStr(self, value):
        string = ""
        if value < 100:
            string += "0"
        if value < 10:
            string += "0"
        string += str(value)
        return string

    def SetCVlist(self, cv_list, val_list, row, cv_max=999, val_max=999):
        ok = True
        for n in range(row):
            if cv_list[n] > cv_max or cv_list[n] < 0 or val_list[n] > val_max or val_list[n] < 0:
                ok = False
                raise ValueError(f"Row {n}: read CV{cv_list[n]} = {val_list[n]} bigger than {val_max} !!")
        if ok:
            for n in range(row):
                self.writeCV(cv_list[n], val_list[n])
                # print("Write: cv %s = %s" % (self.cv_list[n], self.val_list[n]))
            if self.OKcodeNOK():
                return 0
            return 1
        else:
            return -1

    def GetCVlist(self):
        self.num_cv = self.__write__("30")
        if self.OKcodeOK():
            self.cv_list = [0]*self.num_cv
            self.val_list = [0]*self.num_cv
            for n in range(self.num_cv):
                result = self.__write__("31")
                self.cv_list[n] = int(result/1000)
                self.val_list[n] = int(result-self.cv_list[n]*1000)
            return self.num_cv
        else:
            return 0

    def GetCV(self):
        return self.cv_list[:self.num_cv]

    def GetVal(self):
        return self.val_list[:self.num_cv]

    def GetOKcode(self):
        return self.okcode

    def OKcodeOK(self):
        return True if self.okcode == self.OKCODE_OK else False

    def OKcodeNOK(self):
        return False if self.okcode == self.OKCODE_OK else True

    def __write__(self, code="00", cv=0, value=0):
        return self.transaction(code + self.formatStr(cv) + self.formatStr(value))

    def GetDeviceID(self):
        values = []
        while True:
            try:
                self.FlushInputBuffer()
                val = self.__write__()
            except serial.serialutil.SerialTimeoutException:
                val = self.__write__()
            values.append(val)
            if len(values) > 2:
                if values[-1] == values[-2] == values[-3]:
                    break
        return values[-1]

    def GetHWversion(self):
        return self.__write__(code="01")

    def GetSWversion(self):
        return self.__write__(code="02")

    def writeCV(self, cv, value):
        return self.__write__(code="10", cv=cv, value=value)

    def readCV(self, cv):
        return self.__write__(code="11", cv=cv)

    def moveDX(self, output):
        return self.__write__(code="20", cv=output)

    def moveSX(self, output):
        return self.__write__(code="21", cv=output)

    def GetMultiAdrStart(self):
        return self.__write__(code="32")

    def GetSingleInvStart(self):
        return self.__write__(code="33")

    def FlushInputBuffer(self):
        return self.serial.read(self.serial.in_waiting)
