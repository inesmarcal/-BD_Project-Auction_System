# BD_Project-Auction_System
- [x] Finished

## Description
This project was developed for Databases subject @University of Coimbra, Informatics Engineering <br>
Consists in develop a program that implements an Auction System using the framework Psycopg2 and other database elements

#### Main Languages:
![](https://img.shields.io/badge/Python-333333?style=flat&logo=python&logoColor=4F74DA) ![](https://img.shields.io/badge/PostgresSQL-333333?style=flat&logo=postgresql&logoColor=white)

## Technologies used:
1. Python
    - [Version 3.9](https://www.python.org/downloads/release/python-390/)
2. [Postman](https://www.postman.com/downloads/)
3. [PgAdmin](https://www.pgadmin.org/download/)
4. Libraries
    - [Flask](https://pypi.org/project/Flask/)
    - [Psycopg2](https://pypi.org/project/psycopg2/)

## To run this project:
After installing PgAdmin, Postman and all libraries:
1. Create a database with the configurations specified in the file "api_configurations.txt" that is in the folder "resources"
2. Download the src folder and create the tables using the script "cria_tabelas.sql"<br>
3. Before pass to Postman create an Admin User<br>
![image](https://i.imgur.com/jrRD7O3.png)
4. In Postman create some end-points (for more information see the Report)<br>
5. Create a folder called "logs" on same folder of the file "api.py"
6. Finally just run it
```shellscript
[your-disk]:[name-path]> python api.py
```

## Notes important to read:
   - To know how to use all the end-points see the Report, they are all described there
   - Some end-points need a token of authentication<br>

## Authors:
- [Inês Marçal](https://github.com/inesmarcal)
- [Duarte Meneses](https://github.com/DMeneses01)
- [Patricia  Costa](https://github.com/patii01)
