import setuptools 
  
with open("README.md", "r") as fh: 
    description = fh.read() 
  
setuptools.setup( 
    name="therm_inv_tools", 
    version="1.0.4", 
    author="Anthony R. Osborne", 
    author_email="anthony.r.osborne019@pm.me", 
    packages=["tools"], 
    description="A package containing all my tools for thermal inversions", 
    long_description=description, 
    long_description_content_type="text/markdown", 
    url="https://github.com/Anthony904175/therm_inv_tools.git", 
    license='MIT', 
    python_requires='>=3.8', 
    install_requires=[] 
) 
