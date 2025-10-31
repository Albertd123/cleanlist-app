\#StreaLit App directory: cd "OneDrive - Emory\\Entreprenuership\\CleanList\\Python" 

\#Run these in command prompt to test Strealit App:

&nbsp;   # 1) ipynb-py-convert CleanList.ipynb CleanList.py

&nbsp;   # 2) streamlit run CleanList.py   

\#To end run in terminal, use "CTRL + C"







**Public URL:** 

&nbsp;	- run this first: npx localtunnel --port 8501

&nbsp;		(Temporary) By-Pass PowerShell Blocking: powershell -ExecutionPolicy Bypass -File your\_script.ps1		               	 **------>**(Permanent) By-Pass PowerShell Blocking: Set-ExecutionPolicy RemoteSigned 

&nbsp;	- then type this in Google Chrome or any webpage --> **URL:**  *https://dull-gifts-wear.loca.lt   **Password:** 69.222.132.193*

&nbsp;

&nbsp;	Check Current Policy: Get-ExecutionPolicy

&nbsp;	You’ll likely see Restricted, which blocks all scripts.



&nbsp;	🧠 What Each Policy Means

&nbsp;	Policy		Description

&nbsp;	Restricted	No scripts allowed (default)

&nbsp;	RemoteSigned	Local scripts OK, downloaded ones need a signature

&nbsp;	Unrestricted	All scripts run, but with warnings

&nbsp;	Bypass		No restrictions, no warnings

&nbsp;	AllSigned	Only signed scripts allowed





**Local URL: *http://192.168.1.77:8501***



📱 Option 1: Local Network Access (Best for Development)

If you're running the app locally on your computer:



Run the app with network access Use this command in your terminal:



bash

streamlit run your\_app.py --server.address=0.0.0.0 --server.port=8501

Find your computer’s local IP address On Mac/Linux:



bash

ifconfig

On Windows:



bash

ipconfig

Look for something like 192.168.x.x.



Connect from your phone On the same Wi-Fi network, open your phone’s browser and go to:



Code

http://192.168.x.x:8501

Allow firewall access If prompted, allow Streamlit through your firewall so your phone can reach it.



🌐 Option 2: Deploy to the Web

If you want to test from anywhere:



Use Streamlit Community Cloud Upload your app to GitHub and deploy it at streamlit.io. You’ll get a public URL you can open on your phone.



Use platforms like Render, Heroku, or Hugging Face Spaces These also support Streamlit and give you mobile-accessible URLs.





