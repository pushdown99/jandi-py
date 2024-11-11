## Run
~~~command
1) unzip jandi.zip
2) copy sample.env to .env
3) modify .env (i.e. email and password and so on)
4) run jandi.exe
~~~

## Installation
~~~console
git clone https://github.com/pushdown99/jandi-py
cd jandi-py
pip install -r requirements.txt
pyinstaller -F jandi.py
cd dist
~~~

## Files and Directories (git repositories)
name|Descriptioon
---|---
jandy.py|Python code
.env|Enviroment file for dotenv
sample.env|Sample file for .env
NanumBarunGothic.ttf|TTF embedding font for pdf document (Using FPDF2 Library)
build/|Compile and build working 
dist/|Distribution 
dist/jandi.exe|Execution file (*.exe)
output/|Document for topic and DM room
download/|Topic and DM room's attached file