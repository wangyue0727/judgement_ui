# judgement_ui

This is a package for online assessment interface. This version supports:

* Sentence level binary judgement;
* Multiple assessors per query;
* Document level data import (TREC format), while the system will split the document into sentence;

After pull from this repository, do the followings:

1. Modify the www/ir_eval/ir_eval/settings.py, line 72-74, for the username and password of the database.
2. Modify the import/db-import.py for the username and password of the database
3. Modify the schemas of the database if necessary in www/ir_eval/ir_eval/models.py
4. Read the example data in the import/data folder

Some useful codes:

* db-import.py in import folder:

Import the data into the system, it requires the original data in import/data folder

* views.py in www/ir_eval/ir_eval folder: 

Defines the logic level between the database and the frontend


