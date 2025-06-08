# DOI Finder

This project provides a command-line tool for finding DOIs (Digital Object Identifiers) from academic citations using the CrossRef API interface habanero: https://github.com/sckott/habanero.git. The main functionality is encapsulated in the `DOIFinder` class, which can parse citations, search for DOIs, and save results in both CSV and Excel formats.

This script was designed so that the user could simply copy and paste all of the references from a given paper and get the DOIs/links to these papers automatically. With minimal processing (make sure you only have one reference per line in your input text file), this script will take in a list of references and return both the raw DOIs as well as links to the papers in a csv. Additionally (and importantly) if you keep adding references to the csv file by copying/adding new references from other papers, the script automatically detects duplicate DOIs and will inform you that while there may be, for example, 20-30 references in the list you provided, a few had already been added to your csv file by a previous run, so they were not added this time.

If you manually add a single citation/DOI to the csv/excel sheet or otherwise suspect that duplicate DOIs are still in the sheet, you can use the -c flag to "clean" your csv of duplicate DOIs.

Also, feel free to edit the resultant excel file to keep track of which papers you have read, downloaded, exhausted the citations of, etc. The script is made to not entirely overwrite your excel/csv file each time you add/purge citations, but rather just keeps a running list. That way if you add additional columns to track your reading progress, this script will not affect them.

### Files ###

- `src/doi_finder.py`: Contains the main functionality for finding DOIs from citations.
- `requirements.txt`: Lists the required Python packages for the project.
- `README.md`: Documentation for the project.

### Requirements ### 

To run this project, you need to install the following Python packages:

- requests
- pandas
- openpyxl
- habanero

as well as some other more standard packages which can be found at the top of doi_finder.py. Install those packages as necessary 

You can install these packages using a standard package manager:

pip/pip3/conda/mamba install -r requirements.txt

### Usage ###

To find DOIs for a list of citations and add them to a csv file, run the following command in your terminal in the src folder:

python3 doi_finder.py -i path/to/citation/file -o path/to/output/csv/file

To check an existing csv file for duplicate DOIs (for example, if you manually have added citations)

python3 doi_finder.py -c path/to/csv/file

It is not necessary to use the -c flag when adding new citations to an existing csv file. If a new citation has a DOI which matches an existing entry in your csv file, it will not be added, and you will be notified. 

### Command-Line Flags ###

- `-i`: Specify the input file containing citations (one citation per line).
- `-o`: Specify the output file path for the results in CSV format (default is `dois.csv`).
- `-c`: (Optional) Check the output CSV for duplicate DOIs and remove them.

### Input Format ###

The input file should contain one citation per line, for example:

```
Abate, A. R., and D. J. Durian, 2007, Phys. Rev. E 76, 021306.
Abou, B., and F. Gallet, 2004, Phys. Rev. Lett. 93, 160603.
```

Each line will be read and then directly searched for in the CrossRef API using the habanero CrossRef API client: https://github.com/sckott/habanero.
 
### Output ###
 
The output will be saved in the specified CSV file, containing the following columns:

- `citation`: The original citation text.
- `doi`: The found DOI (if any).
- `doi_url`: The DOI URL (if a DOI was found).

If a DOI is not found, then the doi column will have "Not Found" in it. You must manually enter a DOI for this citation. 

## License

Copyright (C) 2025 Lucas Trojanowski under MIT license
