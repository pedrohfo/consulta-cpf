import requests
import unicodedata
from lxml.html import fromstring
import sys
from PyQt5.QtWidgets import *
from PyQt5 import QtCore

URL_GET = "https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublica.asp"
URL_POST = "https://servicos.receita.fazenda.gov.br/Servicos/CPF/ConsultaSituacao/ConsultaPublicaExibir.asp"

class LineEdit(QLineEdit):
  def __init__(self):
    super().__init__()
    self.installEventFilter(self)
  
  def eventFilter(self, source, event):
    if source == self and event.type() == QtCore.QEvent.MouseButtonPress:
        self.setFocus(QtCore.Qt.MouseFocusReason)
        self.setCursorPosition(0)
        return True
    return super().eventFilter(source, event)

def validate_cpf(cpf):
    
  cpf = ''.join(filter(str.isdigit, cpf))

  if len(cpf) != 11:
    return False

  if cpf == cpf[0] * len(cpf):
    return False
  
  def calculate_digit(cpf, digit_position):
    weights = list(range(digit_position, 1, -1))
    sum_digits = sum(int(digit) * weight for digit, weight in zip(cpf, weights))
    remainder = sum_digits % 11
    return 0 if remainder < 2 else 11 - remainder

  first_digit = calculate_digit(cpf[:9], 10)
  if int(cpf[9]) != first_digit:
    return False

  second_digit = calculate_digit(cpf[:10], 11)
  if int(cpf[10]) != second_digit:
    return False

  return True

def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn')

def compare_names(string1, string2):

  names1 = strip_accents(string1).casefold().split()
  names2 = strip_accents(string2).casefold().split()

  if names2[0] not in names1:
    return False

  i = 0
  for name in names1:
    try:
      j = names2.index(name)
    except ValueError:
      return False

    if j < i:
      return False
    i = j + 1

  return True

def search_action():

  s = requests.Session()
  get = s.get(URL_GET)

  name1 = name.text()
  cpf1 = cpf.text()
  birthday1 = birthday.text()
  hcaptcha1 = hcaptcha.text()

  if not validate_cpf(cpf1):
    cpf_error = QMessageBox()
    cpf_error.setWindowTitle("Erro")
    cpf_error.setText("CPF inválido!")
    cpf_error.exec()

  else:
    payload = {
      'idCheckedReCaptcha': 'false',
      'txtCPF': cpf1,
      'txtDataNascimento': birthday1,
      'h-captcha-response': hcaptcha1,
      'Enviar': 'Consultar'
    }

    response = s.post(URL_POST, data=payload)

    tree = fromstring(response.text)

    try:
      hcaptcha_msg = tree.xpath('//*[@id="idMensagemErro"]/span/text()')[0]
    except:
      hcaptcha_msg = ''

    if hcaptcha_msg.find("O Anti-Robô não foi preenchido corretamente.") != -1:
      hcaptcha_error = QMessageBox()
      hcaptcha_error.setWindowTitle("Erro")
      hcaptcha_error.setText("Erro no hCaptcha!")
      hcaptcha_error.exec()

    try:
      # date_msg = tree.xpath('//*[@id="content-core"]/div/div/div[1]/span/h4/b/text()')[0]
      date_msg = tree.xpath('//*[@id="F_Consultar"]/div/div/div[1]/span/h4/b/text()[1]')[0]
    except:
      date_msg = ''

    if date_msg.find("Data de nascimento informada") != -1:
      date_error = QMessageBox()
      date_error.setWindowTitle("Erro")
      date_error.setText("Data de nascimento divergente!")
      date_error.exec()
    
    else:
      try:
          result_name = tree.xpath('//*[@id="mainComp"]/div[2]/p/span[2]/b/text()')[0]
      except:
          result_name = "not found"

      try:
        result_status = tree.xpath('//*[@id="mainComp"]/div[2]/p/span[4]/b/text()')[0]
      except:
        result_status = ''

      try:
        in_date = tree.xpath('//*[@id="mainComp"]/div[2]/p/span[5]/b/text()')[0]
      except:
        in_date = ''
      
      if result_name == "not found" and hcaptcha == '':
        name_error = QMessageBox()
        name_error.setWindowTitle("Erro")
        name_error.setText("Pessoa não encontrada/registrada!")
        name_error.exec()      
      
      else:
        comparison = compare_names(name1, result_name)
        name_found = QMessageBox()
        name_found.setWindowTitle("Pessoa Encontrada!")
        if comparison:
          name_found.setText("Nome pesquisado: " + name1 + "\nNome registrado: " + result_name + "\n\nSituação Cadastral: " + result_status + "\nData da Inscrição: " + in_date + "\n\nNOMES COMPATÍVEIS!")
          name_found.exec()
        else:
          name_found.setText("Nome pesquisado: " + name1 + "\nNome registrado: " + result_name + "\n\nSituação Cadastral: " + result_status + "\nData da Inscrição: " + in_date + "\n\nNOMES INCOMPATÍVEIS!")
          name_found.exec()

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("Consulta Pessoa (Receita Federal)")
window.setFixedSize(1000, 250)

layout = QFormLayout()

name = QLineEdit(window)
layout.addRow("Nome: ", name)

cpf = LineEdit()
cpf.setMaxLength(11)
cpf.setInputMask("000.000.000-00")
layout.addRow("CPF: ", cpf)

birthday = QDateEdit(window)
layout.addRow("Data de nascimento: ", birthday)

hcaptcha = QLineEdit(window)
layout.addRow("hCaptcha: ", hcaptcha)

button = QPushButton(window)
button.setText("Pesquisar")
button.setGeometry(450, 190, 100, 40)
button.clicked.connect(search_action)

window.setLayout(layout)
window.show()
app.exec()