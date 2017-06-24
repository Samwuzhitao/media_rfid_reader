pyinstaller -F -w -i ./image/dtq.ico rfid_reader.py
del rfid_reader.spec
del *.pyc
rd /s /q build
