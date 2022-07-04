Auto add onts for gpon ZTE C320:
========================
## English:

#### Requirements:
* ipaddress and telnetlib libraries installed.
* gpon ZTE C320, SMXA board version V2.1.0
* tested with Python 3.7.4, Windows 7
* in the executable file **ZTE_c320_AutoCfgOnu.py** you need to specify the name of your **line profile** and the name of **remote profile**, where the last character is the number of **pon port**. 
For example for my **pon port 1**, the profile is **Internet_pon1**, and for the **pon port 5** remote profile is **Internet_pon5**. It is also necessary to specify the name of the option 82 format profile and the control subnet where the gpon is located.

#### Description:

At the time of writing this script GPON vendor ZTE model C320 with the software version for SMXA board 2.1.0 had no function of auto-add onts, such as on gpon bdcom.
As a solution, this crutch script for auto-register onu was written. This is not the final version and may contain some errors.

<sub>PS: I apologize for possible grammatical errors and comments in the code in Russian. I will be glad if you point out the errors, I will try to understand and correct them. <sub>

## Русский:

#### Требования:

* установленные библиотеки **telnetlib** и **ipaddress**
* gpon ZTE C320, версия платы SMXA V2.1.0
* протестировано на версии Python 3.7.4 ос - Windows 7
* в исполняемом файле **ZTE_c320_AutoCfgOnu** вам нужно указать название вашего **line профайла** и название **remote профайла**, где последний символ номер **pon порта**. 
Например у меня для **pon порта 1**, профайл - **Internet_pon1**, а для профайла **pon порта 5** remote профайл - **Internet_pon5**. Также необходимо указать название профайла формата опции 82 и подсеть управления в которой находится gpon.

#### Описание:

На момент написания данного скрипта GPON вендора ZTE модели C320 с версией ПО для SMXA платы 2.1.0 не имел функции автодобавления onu как например на gpon bdcom.
В качестве решения был написан данный костыльный скрипт для авторегистрации ону. Это не окончательный вариант написанный на скорую руку, может содержать ошибки.
