#StreaLit App directory: cd "\Python_folder_location" 
#Run these in command prompt to test Strealit App:
    # 1) ipynb-py-convert CleanList.ipynb CleanList.py
    # 2) streamlit run CleanList.py   
#To end run in terminal, use "CTRL + C"



Public URL: 
	- run this first: npx localtunnel --port 8501
		(Temporary) By-Pass PowerShell Blocking: powershell -ExecutionPolicy Bypass -File your_script.ps1		               	 ------>(Permanent) By-Pass PowerShell Blocking: Set-ExecutionPolicy RemoteSigned 
	- then type this in Google Chrome or any webpage -->  https://big-islands-look.loca.lt
 
	Check Current Policy: Get-ExecutionPolicy
	You’ll likely see Restricted, which blocks all scripts.

	🧠 What Each Policy Means
	Policy		Description
	Restricted	No scripts allowed (default)
	RemoteSigned	Local scripts OK, downloaded ones need a signature
	Unrestricted	All scripts run, but with warnings
	Bypass		No restrictions, no warnings
	AllSigned	Only signed scripts allowed


Local URL: http://192.168.1.77:8501
Node.js version:
   - Local:        http://localhost:3000
   - Network:      http://192.168.1.77:3000

📱 Option 1: Local Network Access (Best for Development)
If you're running the app locally on your computer:

Run the app with network access Use this command in your terminal:

bash
streamlit run your_app.py --server.address=0.0.0.0 --server.port=8501
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

