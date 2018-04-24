# Udacity nano degree item catalog project

This project is a RESTful web application using the Python framework Flask along with implementing third-party OAuth authentication.
The idea of the page is to allow authenticated users to display, create, edit and delete on the catalog website.
Non logged in users can only view the catalog.

### Prerequisites
1. Install Vagrant and VirtualBox


https://www.vagrantup.com/downloads.html


https://www.virtualbox.org/wiki/Downloads

2. Clone or download the fullstack-nanodegree-vm repository (https://github.com/udacity/fullstack-nanodegree-vm)

3. Launch the Vagrant VM by typing `vagrant up` in the directory fullstack/vagrant from the terminal

4. `cd` to `/vagrant` directory and run command `vagrant up` to install the VM.

5. Clone or download the catalog app and place it in the `/catalog` folder

6. You need to have a Google account to login

### Running the app

7. Run `vagrant ssh` to login to the virtual machine.

8. `cd` to `/vagrant/catalog/` and type `pyhton project.py` to run the app

9. Open http://localhost:8005 with your webbrowser to open the item catalog

10. Login using your Google account to create, edit or delete items

### Json endpoints

All items
http://localhost:8005/items/JSON


Specific item
http://localhost:8005/items/<id\>/JSON


(e.g. http://localhost:8005/items/1/JSON)

