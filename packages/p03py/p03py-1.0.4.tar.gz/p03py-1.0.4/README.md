# 📦 P03Py

Biblioteca Python para comunicação com balanças industriais via protocolo P03, com suporte à porta serial e TCP/IP.

---

## 📝 Descrição (PT-BR)

🚀 Conheça a **P03Py**, a primeira biblioteca Python dedicada à comunicação com balanças que utilizam o protocolo P03 (via serial ou TCP/IP).

Esta biblioteca foi desenvolvida para facilitar a integração com balanças industriais, utilizando leitura byte a byte com máquina de estados, validação de STX, CR e checksum, e extração de variáveis como peso bruto, líquido, tara e status da balança.

📺 Veja a demonstração da biblioteca no YouTube:  
https://youtu.be/kWqxdXJBAPY

🔧 Compatível com portas **COM (serial)** ou conexões **TCP/IP**

---

## 📝 Description (EN)

🚀 Meet **P03Py**, the first Python library dedicated to communication with weighing scales using the P03 protocol (via serial or TCP/IP).

This library is designed to simplify integration with industrial scales, using byte-by-byte reading, a state machine, validation of STX, CR and checksum, and extraction of variables like gross weight, net weight, tare, and scale status.

📺 Watch the library demo on YouTube:  
https://youtu.be/kWqxdXJBAPY

🔧 Compatible with **serial (COM) ports** and **TCP/IP connections**

---

## 📚 Funcionalidades | Features

- Comunicação via **porta serial (RS-232)** ou **TCP/IP**
- Máquina de estados para leitura segura
- Verificação de integridade (STX, CR, Checksum)
- Extração de dados: peso bruto, líquido, tara, status da balança
- Suporte a pacotes P03 reais usados na indústria

---

## 📦 Instalação | Installation

```bash
pip install p03py
```

---

## 📁 Exemplos disponíveis | Available Examples

- `diagnostico.py` — Testa a porta serial com diversas configurações para descobrir qual está sendo utilizada pela balança  
- `teste_leitura_serial.py` — Exemplo de leitura de dados da balança via **porta serial**  
- `teste_leitura_tcp.py` — Exemplo de leitura de dados da balança via **conexão TCP/IP**

- `diagnostico.py` — Tests the serial port with multiple settings to discover the correct configuration used by the scale  
- `teste_leitura_serial.py` — Sample test for reading scale data using **serial port**  
- `teste_leitura_tcp.py` — Sample test for reading scale data using **TCP/IP connection**

---
## 🧪 Running Examples

```bash
python -m p03py.Exemplos.diagnostico
python -m p03py.Exemplos.teste_leitura_serial
python -m p03py.Exemplos.teste_leitura_tcp
```
---

## 🔗 Project

- GitHub: [github.com/roneitop/p03py](https://github.com/roneitop/p03py)

---


## 📄 Licença | License

MIT © 2025 — Ronei Toporcov
