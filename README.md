# Octo.py | Austin Schick 15-112 Term Project

### [Project Video] (https://www.youtube.com/watch?v=87SCdgNYX68)

### Description

Octo.py is a "find the hidden object" type game with a twist: the objects hide themselves. Players are able to upload their own images to the game. Then by analyzing the image, the game generates camouflage patterns to overlay on octopi, and hides the octopi in the image for players to find. 

Octo.py is an experiment in biomimicry. The algorithm used to generate the in-game octopi's camouflage patterns is based on research about real life octopus camouflage techniques. One important element of the algorithm that came directly from this research is varying the granularity of the camouflage as the granularity of the background changes.

### Highlights
* Support for user uploaded images
* Image analysis (with a custom 3D histogram class)
* Biomimetic camouflage algorithm

To run the game go to source, and run main.py  
pygame and PIL are required libraries, and can be installed with pip  
Octo.py was designed for python 3.5.2  

### Disclaimer

Only tested on Mac OS X. Some features may not run on other operating systems.

### Directory Contents 

- README.md
- design
  - competetive_analysis.txt
  - project_proposal.txt
  - storyboard.pdf
  - updates1.txt
- source
  - Analysis.py
  - data
    - highscore.txt
    - images.txt
  - getFiles.py
  - ImageOpener.py
  - images
    - andes.jpg
    - atrium.jpg
    - beach.jpg
    - cutoutTitleImage.png
    - forest.jpg
    - greece.jpg
    - lavender.jpg
    - octopus_mask.jpg
    - rainbow.jpg
    - sunflowers.jpg
    - title.jpg
	- main.py
	- OctopusGenerator.py
  - Perlin.py
  - sounds
    - background.wav
    - error.wav
    - pop.wav
