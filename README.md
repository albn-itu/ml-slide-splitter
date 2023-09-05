# ML PDF splitter
This is a very simple python script to split the slide PDF files given in the Machine Learning course, that for some unknown reason has 2 slides per page. This crops them perfectly and places them on a page each.

## Usage
1. Clone the repo
2. Install the requirements: `pip install -r requirements.txt`
3. Run the script: `python split.py <input_file> <output_file>`
4. Enjoy your slides!

## Code quality
The code here is not meant to be pretty, just get the job done. There are many improvements to be made in terms of speed and readability, the `get_slide_location` method especially. This project took about ~3 hours to build, at least 1 of which consisted of getting the locations on the slide manually, then realising they change from lecture to lecture. My point here is that this is really quick code, and should not be used as an example or used to learn how to write Python, don't do that to yourself, read a real project.
