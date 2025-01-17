# Custom Mouse Path

This is a program that adds custom paths to your mouse.

##### **How does it do it?**

By making an application full screen, not visible in the taskbar, invisible and making the mouse move through it, this software allows you to display HTML files on the screen (don't worry you get stuck and the mouse can't move through the window click on it and it will close itself)


##### trails html structure

each trail realy has just the style (css) code and the script (js) code.

the only thing that you need to know is the functions:

* mouseMove
  inputs are the x and y

  it adds a div at the x and y with the css style and makes it disapeare after a short delay
* mouseClick

  inputs are the x and y

  it's the same as mouseMove but called for a mouse click

the python script


##### **How do I use it**

1. Install python: I'm using 3.12.6 but you can use any version that is compatible with pyside6
2. Install dependesis:

* pyside6
  *accident
  *globus

3. Run the application: The only thing you really need is the main.py and trails folder from this project everything else (like custom_trails) is created automatically
4. Enjoy: Are custom trails still a work in progress, the existing trails are finished

Tip:

If you have ideas for trail ideas, custom trail features Or anything else please send them, I'd be happy to add them if I can.
