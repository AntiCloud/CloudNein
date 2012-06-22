Cloud Nein - Version 1080.1
==================================

We are pleased to present Cloud Nein, a private server implementation for the CrowdRE application.  While this implementation may not promote as great synergy as the official CrowdRE cloud environment, we hope that users will not mind the fact that there is no ability to have a converged cloud strategy with nearly infinite elasticity, flexibility and capacity using this application.  (Those of you playing buzzword bingo should now have a line and can move on to the next presentation).

The authors of Cloud Nein do appreciate the time and effort that some of the best at CrowdStrike have put into the CrowdRE application.  In an effort to extend the usefulness of this application, and based on popular demand, we have created a simple server which can facilitate CrowdRE usage, without the need for internet connectivity, let alone the "Cloud".  Some of the CrowdStrike folks hinted that they were working on a private server implementation, and we encourage them to use and extend our server for that purpose going forward.

Onto the useful stuff:

SETUP AND INSTALLATION
==================================

1) If you haven't already, install CrowdRE.  A zip containing the application is provided, so that you don't need to register on the Crowd.RE website (more on this later).  Follow the instructions included with it to install the IDA plugin.

2) Add a new registry key to point CrowdRE to the Cloud Nein server which you will be running.  To do this, open regedit, and navigate to:
HKEY_CURRENT_USER\Software\CrowdStrike\CrowdRE\cloud
and add in a new string value named "root-url".  Set the value of it to match the URL to your server.  If you're running Cloud Nein on the same machine, for example, your value should be: http://localhost:8080

3) Make sure you have all the Python libraries and junk that you need installed to make Cloud Nein work.  Beyond the Python install and libraries that come with IDA, the only other library that should be needed is "Twisted".  You can get it, and all the garbage that goes with it from the following links:

http://twistedmatrix.com/Releases/Twisted/12.1/Twisted-12.1.0.win32-py2.7.msi
http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11.win32-py2.7.exe#md5=57e1e64f6b7c7f1d2eddfc9746bbaf20
http://pypi.python.org/packages/2.7/z/zope.interface/zope.interface-4.0.1-py2.7-win32.egg#md5=1e3a463d11aa98e9452bfaff01ab70f2
"Eggs" can be installed using the command something like this: easy_install zope.interface-4.0.1-py2.7-win32.egg

4) Add some users to Cloud Nein.  This needs to be done before you can upload and download anything from the server.  The crowdre_adduser.py script is used to add users to the database, and should be run with the following options:
<database filename> <name> <email> <authtoken>

Where <database filename> is the name of the sqllite database file you want your Cloud Nein instance to use, <name> and <email> say whatever you want Cloud Nein to list for that user, and <authtoken> is the value that you would like Cloud Nein to authenticate that user against.  Run this script multiple times to add users one by one.  When you first start CrowdRE, or when your token doesn't match, you will be prompted to enter your authtoken.  This can be used to add some measure of security to your Cloud Nein server (more on that later).

5) Run Cloud Nein!  The script crowdre_main.py starts the Cloud Nein server instance.  It takes the following parameters:
<database filename>

The filename should match the one you just added users to in step 4.

6) Run CrowdRE (Ctrl-F2 in IDA if you fail at reading docs), and see if everything works!


FUNCTIONALITY AND IMPORTANT NOTES
==================================

This release of Cloud Nein implements all of the basic CrowdRE functionality, and nothing more.  There's a few things that seem broken or silly, but that's just how CrowdRE does it.  The only major thing which Cloud Nein probably does not implement correctly is "fuzzy matching".  The CrowdStrike guys finally posted their presentation, so we'll probably go over it sometime soon and improve the server side Cloud Nein fuzzy matching, but we didn't want to delay this thing forever!

Google Accounts - Sharing your infos:
To sign up for CrowdStrike's CloudRE service, you need to authenticate with a google account.  This isn't too awesome because now they have your name and email.  But it's a little bit worse even, as your name (as listed on your google account) goes into their database, and then shows up under the "Author" field for anything you check in.  Pretty easy to fake and all that, but also a pretty easy way to harvest names of researchers (both for CrowdStrike as well as anyone using CloudRE).  Do a fuzzy match against a simple function, and watch the matches, and author names roll in!

Security - We has none:
Cloud Nein has not been implemented as an enterprise ready production application.  If it was, there would be more security vulnerabilities present.  But in all seriousness, we didn't add any sort of security features to this thing, so only use it with people you trust.  If you'd like to update the code to have some proper security, go for it.


FINAL COMMENTS
==================================

Thanks to everyone who helped in the development of Cloud Nein, and more so to everyone who gave us the motivation to do it.  Cloud's suck, but buzzwords even more so.

This application will not be maintained, unless we have the time, need, or desire to make further updates.  Feel free to branch new versions and extend this application as you see fit.  If anything particularly great is created, we'll point a link to it so others can make use of it too.