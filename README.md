Multi-Component Miedema Model Calculator
A desktop application with a graphical user interface (GUI) for calculating thermodynamic properties of multi-component alloys based on the Miedema model. This tool is designed for materials scientists, chemists, and engineers working on alloy design and analysis.

The application provides a user-friendly way to compute formation enthalpy, activity coefficients, and visualize how these properties change with composition and temperature.

![image](https://github.com/user-attachments/assets/5e7d377c-0add-479a-9748-72744e9f6c67)

![image](https://github.com/user-attachments/assets/6cb1d7a6-fcdd-4f74-83a8-64407a238b3a)
![image](https://github.com/user-attachments/assets/f9b6d65f-7dc8-411f-828d-64e072b9333c)
![image](https://github.com/user-attachments/assets/3cf42332-ac1e-4e09-a534-448815c13a70)


Key Features
Formation Enthalpy Calculation: Compute the enthalpy of formation for binary and multi-component alloys at a specific composition.
Activity & Activity Coefficient: Calculate the activity and activity coefficients of constituent elements in an alloy.
Composition Variation Analysis: Generate plots to visualize how thermodynamic properties (e.g., formation enthalpy, activity) vary across a range of compositions in binary or ternary systems.
Temperature Variation Analysis: Generate plots to visualize the effect of temperature on the activity of elements.
Modular & User-Friendly GUI: A clean, tab-based interface built with PyQt5 that separates different calculation modes for clarity.
Data Visualization: Integrated plotting functionality powered by Matplotlib to instantly visualize results.
Technology Stack
Python 3: The core programming language.
PyQt5: For the graphical user interface.
NumPy: For efficient numerical operations.
SciPy: For scientific calculations that may underpin the model.
Matplotlib: For generating high-quality 2D plots.
Getting Started
There are two ways to run this application: by using the pre-compiled executable or by running from the source code.

A) Running the Pre-compiled Executable (For End-Users)
This is the easiest way to get started.

Navigate to the Releases page of this repository.
Download the latest .exe file from the assets list.
Important Prerequisite: Before running, ensure you have the Microsoft Visual C++ Redistributable for Visual Studio 2015-2022 installed on your system. This is a common requirement for many applications built with Python. You can download it directly from Microsoft:
Latest Supported Visual C++ Redistributable Downloads (download the X64 version).
Double-click the downloaded .exe file to run the application.
B) Running from Source (For Developers)
This method is for developers who want to modify or inspect the code.

Clone the repository:

Bash

git clone https://github.com/your-username/your-repository.git
cd your-repository
Create and activate a virtual environment (recommended):

Bash

# For Windows
python -m venv venv
.\venv\Scripts\activate

# For macOS/Linux
python3 -m venv venv
source venv/bin/activate
Install the required dependencies:
Create a requirements.txt file in the project root with the following content:

PyQt5
numpy
scipy
matplotlib
Then, install them using pip:

Bash

pip install -r requirements.txt
Run the application:

Bash

python MiedemamodelApp_Pro.py
How to Build (Packaging)
This project uses PyInstaller to create a single-file executable. If you've made changes and want to create your own build:

Ensure PyInstaller is installed in your virtual environment:
Bash

pip install pyinstaller
Use the provided .spec file for a reliable build:
Bash

pyinstaller MiedemamodelApp_Pro.spec
The final executable will be located in the dist directory.
Contributing
Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

Fork the Project
Create your Feature Branch (git checkout -b feature/AmazingFeature)
Commit your Changes (git commit -m 'Add some AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request
License
Distributed under the MIT License. See LICENSE for more information.
