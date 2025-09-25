import socket
import threading
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QLineEdit, QStackedWidget, QVBoxLayout, QSpinBox
from PyQt6.QtCore import QThread, pyqtSignal
import sys
import ipaddress

app = QApplication(sys.argv)
mainWindow = QWidget()

stack = QStackedWidget()

menuWindow = QWidget()
findPortWindow = QWidget()
checkPortWindow = QWidget()

stack.addWidget(menuWindow)
stack.addWidget(findPortWindow)
stack.addWidget(checkPortWindow)

findPortsButton = QPushButton(menuWindow)
findPortsButton.setText("Açık portları tespit et")
findPortsButton.adjustSize()
findPortsButton.move(0, 30)
findPortsButton.clicked.connect(lambda: stack.setCurrentIndex(1))

checkPortButton = QPushButton(menuWindow)
checkPortButton.setText("Manuel port sorgula")
checkPortButton.adjustSize()
checkPortButton.move(120, 30)
checkPortButton.clicked.connect(lambda: stack.setCurrentIndex(2))

backToMenuButtonA = QPushButton(findPortWindow)
backToMenuButtonA.setText("Geri Dön")
backToMenuButtonA.move(0, 60)
backToMenuButtonA.adjustSize()
backToMenuButtonA.clicked.connect(lambda: stack.setCurrentIndex(0))

backToMenuButtonB = QPushButton(checkPortWindow)
backToMenuButtonB.setText("Geri Dön")
backToMenuButtonB.move(0, 90)
backToMenuButtonB.adjustSize()
backToMenuButtonB.clicked.connect(lambda: stack.setCurrentIndex(0))

findPortsLine = QLineEdit(findPortWindow)
findPortsLine.setPlaceholderText("Lütfen bir IP adresi giriniz...")
findPortsLine.resize(160, 20)

findPortLabel = QLabel(findPortWindow)
findPortLabel.move(190, 0)

findPort = QPushButton(findPortWindow)
findPort.setText("Taramayı başlat")
findPort.adjustSize()
findPort.move(0, 30)

# adresin geçerli olma durumu denetleniyor ve buna göre bir bool sinyal yayılıyor.
class qthr(QThread):
    signal = pyqtSignal(bool)
    def run(self):
        try:
            ipaddress.ip_address(socket.gethostbyname(findPortsLine.text()))
            self.signal.emit(True)
        except:
            self.signal.emit(False)
threadA = qthr()

# girilen adresin aktif portları taranıyor ve aktif portlar liste olarak sinyal yayılıyor.
class qthrB(QThread):
    signal = pyqtSignal(list)
    def run(self):
        aktifPortlar = []
        threads = []
        lock = threading.Lock()

        def checkPort(port):
            for i in range(port - 100, port):
                if i > 65535 or i < 1:
                    continue
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((findPortsLine.text(), i))
                sock.close()
                if result == 0:
                    with lock:
                        aktifPortlar.append(i)
        # 65.5xx'li bütün portların taranması için 65602 yapıldı.
        for i in range(1, 65602, 100):
            if i == 1:
                continue
            t = threading.Thread(target=checkPort, args=(i, ))
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()
        
        strPorts = []
        for prt in sorted(aktifPortlar):
            strPorts.append(str(prt))

        self.signal.emit(strPorts)

threadB = qthrB()

# sinyal olarak gönderilen aktif portların listesi (varsa) arayüze yazdırılıyor.
def threadBSignal(signal):
    findPort.setEnabled(True)
    backToMenuButtonA.setEnabled(True)
    findPortsLine.setReadOnly(False)

    if len(signal) == 0:
        findPortLabel.setText("Aktif port bulunamadı.")
        findPortLabel.adjustSize()
    else:
        text = "-".join(signal)
        findPortLabel.setText(f"Aktif port(lar): {text}")
        findPortLabel.adjustSize()

threadB.signal.connect(threadBSignal)

# butona basıldığında threadA çalıştırılıyor, girilen adresin uygunluğu ve diğer faktörler denetleniyor. Uygunluk durumunda threadB çalıştırılıyor.
def findingPorts():
    def threadASignal(sign):
        if not sign:
            findPortLabel.setText("Hata!")
            findPortLabel.adjustSize()
            findPortsLine.setReadOnly(False)
            findPort.setEnabled(True)
            backToMenuButtonA.setEnabled(True)
        else:
            findPortLabel.setText("Lütfen bekleyin. Bu işlem birkaç dakika sürebilir.")
            findPortLabel.adjustSize()
            findPort.setDisabled(True)
            backToMenuButtonA.setDisabled(True)
            threadB.start()

    if not findPortsLine.text() == "":
        threadA.signal.connect(threadASignal)
        threadA.start()
        findPortsLine.setReadOnly(True)
        findPort.setDisabled(True)
        backToMenuButtonA.setDisabled(True)
    else:
        findPortLabel.setText("Lütfen bir adres girin.")
        findPortLabel.adjustSize()

findPort.clicked.connect(findingPorts)

checkPortLineIP = QLineEdit(checkPortWindow)
checkPortLineIP.setPlaceholderText("Lütfen bir IP adresi giriniz...")
checkPortLineIP.resize(160, 20)

checkPortSpin = QSpinBox(checkPortWindow)
checkPortSpin.move(37, 30)
checkPortSpin.setRange(1, 65535)

checkPortLabel = QLabel(checkPortWindow)
checkPortLabel.move(190, 0)

checkPortSpinLabel = QLabel(checkPortWindow)
checkPortSpinLabel.move(0, 33)
checkPortSpinLabel.setText("<h3>Port:</h3>")

checkPort = QPushButton(checkPortWindow)
checkPort.setText("Kontrol et")
checkPort.adjustSize()
checkPort.move(0, 60)

# verilen portun verilen adresde aktifliği denetleniyor ve buna göre bir bool sinyal yayılıyor.
class qthrC(QThread):
    signal = pyqtSignal(bool)
    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((checkPortLineIP.text(), checkPortSpin.value()))
        sock.close()
        if result == 0:
            self.signal.emit(True)
        else:
            self.signal.emit(False)
threadC = qthrC()

# yayınlanan bool sinyale bağlı olarak portun aktifliği ile ilgili bilgi arayüze yazdırılıyor.
def threadCSignal(signal):
    if signal:
        checkPortLabel.setText(f"{checkPortSpin.value()} portu {checkPortLineIP.text()} adresinde aktif!")
        checkPortLabel.adjustSize()
        checkPortLineIP.setReadOnly(False)
        checkPortSpin.setReadOnly(False)
        backToMenuButtonB.setEnabled(True)
        checkPort.setEnabled(True)
    else:
        checkPortLabel.setText(f"{checkPortSpin.value()} portu {checkPortLineIP.text()} adresinde aktif değil!")
        checkPortLabel.adjustSize()
        checkPortLineIP.setReadOnly(False)
        checkPortSpin.setReadOnly(False)
        backToMenuButtonB.setEnabled(True)
        checkPort.setEnabled(True)

threadC.signal.connect(threadCSignal)

# girilen adresin geçerliliği denetleniyor ve buna bağlı olarak bir bool sinya yayılıyor.
class qthrD(QThread):
    signal = pyqtSignal(bool)
    def run(self):
        try:
            ipaddress.ip_address(socket.gethostbyname(checkPortLineIP.text()))
            self.signal.emit(True)
        except:
            self.signal.emit(False)
threadD = qthrD()

# adres geçerliyse ve başka hata yoksa threadC ile portun aktifliği denetlenmeye başlıyor.
def threadDSignal(signal):
    if not signal:
        checkPortLabel.setText("Hata!")
        checkPortLabel.adjustSize()
        checkPort.setEnabled(True)
        backToMenuButtonB.setEnabled(True)
        checkPortLineIP.setReadOnly(False)
        checkPortSpin.setReadOnly(False)
    else:
        checkPortLabel.setText("Lütfen bekleyin.")
        checkPortLabel.adjustSize()
        checkPort.setDisabled(True)
        backToMenuButtonB.setDisabled(True)
        threadC.start()

# butona basıldığında threadD çalıştırılıp adresin geçerliliği denetleniyor.
def checkingPort():
    if not checkPortLineIP.text() == "":
        threadD.signal.connect(threadDSignal)
        threadD.start()
        checkPort.setDisabled(True)
        backToMenuButtonB.setDisabled(True)
        checkPortLineIP.setReadOnly(True)
        checkPortSpin.setReadOnly(True)
    else:
        checkPortLabel.setText("Lütfen bir adres girin.")
        checkPortLabel.adjustSize()

checkPort.clicked.connect(checkingPort)

layout = QVBoxLayout()
layout.addWidget(stack)

mainWindow.setWindowTitle("Port Sorgulama")
mainWindow.resize(700, 150)
mainWindow.setLayout(layout)
mainWindow.show()
app.exec()