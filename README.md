Catalog App
==================
Python app that allows an authenticated user to add, edit, and delete categories and category items that are stored in the app's database.


To Run
------

1. Ensure python is installed
2. Open command prompt and navigate to the script directory (Example: cd C:\Users\Public\CatalogApp)
3. Start the server by entering 'python catalog.py'
4. Access the app by navigating to http://localhost:5000
5. To stop the server use Ctrl+C


Description
-------------

This program will start a python (flask) webserver that provides an app where users can authenticate via Google and/or Facebook in order to modify the contents of the server database. Authenticated users are given the ability to add, edit, and delete categories and category items.

This app was created for my girlfriend's custom tutu business which is why the database pertains to tutus. However, none of the code (except some HTML) specifically references tutus meaning that the catalog can be relatively easily modified for another type of product.  



Future Updates
--------------
- Add full responsiveness
- Add flash messages for when users complete an action
- Ensure file uploading is safe (restrict file types)
