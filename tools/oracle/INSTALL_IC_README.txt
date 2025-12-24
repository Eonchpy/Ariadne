install_ic.sh Script Usage Information
=======================================
1. In Finder, double click on all desired Instant Client .dmg packages to mount them

2. Open a terminal window and change directory to one of the packages, for example:
   $ cd /Volumes/instantclient-basic-macos.x64-19.16.0.0.0dbru

3. Run the install_ic.sh script:
   $ ./install_ic.sh
   This copies the contents of all currently mounted Instant Client .dmg packages to /User/$USER/Downloads/instantclient_19_16

4. In Finder, eject the mounted Instant Client packages
