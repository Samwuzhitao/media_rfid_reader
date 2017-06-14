pyinstaller -F -w -i ./image/dtq.ico MEIDIREADER.py
del MEIDIREADER.spec
del *.pyc
rd /s /q build
copy dist/MEIDIREADER.exe ./MEIDIREADER.exe
