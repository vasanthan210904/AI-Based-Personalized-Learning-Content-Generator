"""Honest, clearly-labelled offline demo content.

These packs are used only when no AI key is configured (or the live service is
unavailable) and demo fallback is allowed. Every record stores the mode so the
UI and PDFs can label this content accurately.
"""
from __future__ import annotations

import random


class DemoUnavailable(Exception):
    """No curated demo pack exists for the requested topic/quiz."""


DEMO_PACKS: dict[str, dict] = {
    "python basics": {
        "title": "Python Basics",
        "introduction": (
            "Python is a high-level, general-purpose programming language known for readable "
            "syntax and a huge ecosystem. Guido van Rossum created it in the late 1980s and "
            "released the first version in 1991. Today Python powers web backends, automation, "
            "data analysis and machine learning. A Python program is executed by an interpreter, "
            "which reads your code and carries out the instructions. Because indentation is part "
            "of the syntax, Python code looks close to structured English."
        ),
        "objectives": [
            "Explain what Python is and where it is used",
            "Declare variables and use the core data types",
            "Write and run a short Python program",
            "Read user input and display formatted output",
            "Recognise the role of indentation and comments",
        ],
        "concepts": [
            {
                "heading": "Running Python",
                "explanation": (
                    "You can run Python in two common ways. The interactive REPL lets you type "
                    "one statement at a time and immediately see the result. A script file with "
                    "a .py extension lets you store many statements and run them together with "
                    "`python hello.py`. During development, an error message points to the line "
                    "that failed and the type of error, which helps you debug."
                ),
            },
            {
                "heading": "Variables and data types",
                "explanation": (
                    "A variable is a name that refers to a value. Python is dynamically typed, "
                    "so the same name can later refer to a different type of value. The core "
                    "types are int (whole numbers), float (decimal numbers), str (text), bool "
                    "(True/False) and None (absence of a value). Use type(value) to inspect a "
                    "value and int(), float(), str() to convert between compatible types."
                ),
            },
            {
                "heading": "Indentation and blocks",
                "explanation": (
                    "Python uses indentation, usually four spaces, to define a block instead of "
                    "curly braces. A colon at the end of a statement such as if, for or def opens "
                    "a block, and every line in the block must share the same indentation. Mixing "
                    "tabs and spaces, or inconsistent indentation, raises an IndentationError."
                ),
            },
        ],
        "definitions": [
            {
                "term": "Interpreter",
                "definition": "A program that executes source code statement by statement, instead of producing a separate machine-code executable first.",
            },
            {
                "term": "Variable",
                "definition": "A name that refers to a value in memory; in Python a name can be rebound to values of different types.",
            },
            {
                "term": "Data type",
                "definition": "A category describing what kind of value is stored and which operations are valid, such as int, float, str and bool.",
            },
            {
                "term": "String",
                "definition": "An immutable sequence of characters written inside quotes and used to represent text.",
            },
            {
                "term": "Indentation",
                "definition": "Leading whitespace that groups statements into a block; it is part of Python's syntax.",
            },
        ],
        "key_terms": [
            "REPL",
            "expression",
            "assignment",
            "f-string",
            "comment",
            "type conversion",
            "syntax error",
        ],
        "steps": [
            "Install Python 3 and confirm it works by running `python --version` in a terminal.",
            "Open the interactive shell with `python` and try simple expressions such as `2 + 3`.",
            "Create a file called hello.py with a name variable and a print() statement.",
            "Run `python hello.py` from the same folder and read the output.",
            "Ask for input with input(), format the result with an f-string, and add a comment explaining the code.",
        ],
        "examples": [
            "A first program:\nname = \"Asha\"\nprint(f\"Hello, {name}!\")   # Hello, Asha!",
            "Area of a rectangle:\nlength = 8.5\nwidth = 4\narea = length * width\nprint(f\"Area: {area} square units\")",
            "Even or odd:\nnumber = int(input(\"Enter a number: \"))\nif number % 2 == 0:\n    print(\"Even\")\nelse:\n    print(\"Odd\")",
        ],
        "applications": [
            "Web backends built with Flask or Django",
            "Data analysis and visualisation with pandas and Matplotlib",
            "Automation scripts for files, downloads and spreadsheets",
            "Machine learning experiments with scikit-learn and PyTorch",
        ],
        "advantages": [
            "Readable syntax makes it beginner-friendly",
            "Very large standard library and third-party ecosystem",
            "Runs on Windows, macOS and Linux",
            "Rapid development for scripts and prototypes",
        ],
        "disadvantages": [
            "Slower than compiled languages such as C for CPU-heavy loops",
            "Dynamic typing can move some errors from compile time to run time",
        ],
        "important_points": [
            "Indentation is syntax, not decoration - a wrong indent changes the meaning of code.",
            "input() always returns a string, so convert it with int() or float() before arithmetic.",
            "Use == to compare values and = to assign a value.",
            "Indexing starts at 0; a string of length 6 has valid indices 0 to 5.",
            "Read error messages from the bottom up: the final line names the error type.",
            "Use a separate virtual environment for each project to avoid dependency conflicts.",
        ],
        "summary": (
            "Python is an interpreted, dynamically typed language designed for clarity. Variables "
            "name values of types such as int, float, str and bool. Indentation defines blocks, so "
            "layout matters. You can run code interactively or from .py files, read input with "
            "input(), and format output with f-strings. Mastering these basics prepares you for "
            "functions, collections, object-oriented programming and real projects."
        ),
        "revision_tips": [
            "Type every example yourself instead of copying it; predict the output first.",
            "Spend ten minutes in the REPL experimenting with int, float and str conversions.",
            "Write one tiny program each day, such as a unit converter or a tip calculator.",
            "When an error appears, read the last line first and locate the reported line number.",
        ],
        "faqs": [
            {
                "question": "Is Python compiled or interpreted?",
                "answer": "CPython first compiles source code into bytecode, then its virtual machine interprets that bytecode. From the learner's point of view, it behaves like an interpreted language.",
            },
            {
                "question": "Why does adding a number from input() fail?",
                "answer": "input() returns a string. Convert it with int() or float() before doing arithmetic, for example int(input(\"Age: \")).",
            },
            {
                "question": "Do I need semicolons at the end of lines?",
                "answer": "No. A newline ends a statement in Python. Semicolons are allowed but rarely used.",
            },
            {
                "question": "What is the difference between a list and a tuple?",
                "answer": "A list is mutable, so you can add or change items. A tuple is immutable, so its contents cannot be changed after creation.",
            },
        ],
        "quiz": [
            {
                "difficulty": "Easy",
                "question": "Which data type is used to store text in Python?",
                "options": ["str", "int", "float", "bool"],
                "correct_index": 0,
                "explanation": "str is Python's string type and stores sequences of characters. int stores whole numbers, float decimals and bool truth values.",
            },
            {
                "difficulty": "Easy",
                "question": "What does the print() function do?",
                "options": [
                    "Displays a value in the output",
                    "Reads input from the keyboard",
                    "Converts text to a number",
                    "Deletes a file",
                ],
                "correct_index": 0,
                "explanation": "print() writes its arguments to standard output. input() is used to read from the keyboard.",
            },
            {
                "difficulty": "Medium",
                "question": "What is the value of len(\"Python\")?",
                "options": ["6", "5", "7", "0"],
                "correct_index": 0,
                "explanation": "The string \"Python\" has six characters: P, y, t, h, o and n. len() counts them, so the result is 6.",
            },
            {
                "difficulty": "Medium",
                "question": "What is the result of int(\"25\") + 5?",
                "options": ["30", "\"255\"", "255", "TypeError"],
                "correct_index": 0,
                "explanation": "int(\"25\") converts the string to the number 25, then 25 + 5 evaluates to 30.",
            },
            {
                "difficulty": "Hard",
                "question": "Which statement about Python variables is correct?",
                "options": [
                    "A variable name can refer to values of different types over time",
                    "A variable's type must be declared before assignment",
                    "Variable names must start with a digit",
                    "A variable can never be reassigned",
                ],
                "correct_index": 0,
                "explanation": "Python is dynamically typed, so a name can be rebound to values of different types. Type declarations are not required, and names cannot begin with a digit.",
            },
            {
                "difficulty": "Hard",
                "question": "What error does inconsistent indentation typically raise?",
                "options": ["IndentationError", "TypeError", "NameError", "ValueError"],
                "correct_index": 0,
                "explanation": "Inconsistent leading whitespace breaks Python's block structure and raises IndentationError (or TabError).",
            },
        ],
    },
    "object-oriented programming": {
        "title": "Object-Oriented Programming",
        "introduction": (
            "Object-oriented programming (OOP) organises a program around objects. An object bundles "
            "data (attributes) together with the operations that act on that data (methods). A class "
            "is the blueprint used to create objects. Python supports OOP alongside procedural and "
            "functional styles. OOP helps teams model real-world entities, reuse code and keep large "
            "programs organised."
        ),
        "objectives": [
            "Differentiate between a class and an object",
            "Create classes, attributes and methods in Python",
            "Explain encapsulation, inheritance and polymorphism",
            "Use composition to model relationships between objects",
            "Identify when OOP is a good fit for a problem",
        ],
        "concepts": [
            {
                "heading": "Classes and objects",
                "explanation": (
                    "A class describes the attributes and methods its objects will have. An object "
                    "(instance) is a concrete value created from that class. In Python, __init__ "
                    "initialises a new instance, and self refers to the instance being operated on. "
                    "Each object gets its own attribute values while sharing the class's methods."
                ),
            },
            {
                "heading": "The four pillars",
                "explanation": (
                    "Encapsulation keeps state and behaviour together and hides internal details. "
                    "Inheritance lets a subclass reuse and extend a parent class. Polymorphism lets "
                    "different classes respond to the same method call in their own way. Abstraction "
                    "exposes a simple interface while hiding implementation complexity."
                ),
            },
            {
                "heading": "Inheritance versus composition",
                "explanation": (
                    "Inheritance expresses an is-a relationship: a Dog is an Animal. Composition "
                    "expresses a has-a relationship: a Car has an Engine. Prefer composition when "
                    "the relationship is not truly a subtype, because deep inheritance trees become "
                    "fragile and hard to change."
                ),
            },
        ],
        "definitions": [
            {"term": "Class", "definition": "A blueprint that defines the attributes and methods shared by its instances."},
            {"term": "Object", "definition": "An instance of a class that holds its own attribute values."},
            {"term": "Encapsulation", "definition": "Bundling data with the methods that operate on it and restricting direct access to internal state."},
            {"term": "Inheritance", "definition": "A mechanism where a subclass acquires and extends the attributes and methods of a parent class."},
            {"term": "Polymorphism", "definition": "The ability of different classes to provide their own implementation of the same method name."},
            {"term": "Abstraction", "definition": "Exposing only the essential interface of an object while hiding implementation details."},
        ],
        "key_terms": ["class", "instance", "self", "__init__", "method", "attribute", "super()", "override"],
        "steps": [
            "Identify the nouns in the problem - these are candidate classes.",
            "Define a class with __init__ to initialise its attributes.",
            "Add methods that operate on the object's own data via self.",
            "Create instances and call their methods to verify behaviour.",
            "Refactor shared behaviour into a parent class or a composed helper object.",
            "Keep each class focused on a single responsibility.",
        ],
        "examples": [
            "A bank account:\nclass BankAccount:\n    def __init__(self, owner, balance=0):\n        self.owner = owner\n        self.balance = balance\n\n    def deposit(self, amount):\n        if amount > 0:\n            self.balance += amount\n        return self.balance\n\naccount = BankAccount(\"Asha\", 500)\naccount.deposit(250)\nprint(account.balance)   # 750",
            "Inheritance:\nclass Animal:\n    def speak(self):\n        return \"...\"\n\nclass Dog(Animal):\n    def speak(self):\n        return \"Woof\"\n\nclass Cat(Animal):\n    def speak(self):\n        return \"Meow\"\n\nfor pet in (Dog(), Cat()):\n    print(pet.speak())",
            "Composition:\nclass Engine:\n    def start(self):\n        return \"engine started\"\n\nclass Car:\n    def __init__(self):\n        self.engine = Engine()\n\ncar = Car()\nprint(car.engine.start())",
        ],
        "applications": [
            "Backend models in web frameworks such as Django",
            "GUI widgets and game entities",
            "Simulation models in science and engineering",
            "Reusable libraries and plugin architectures",
        ],
        "advantages": [
            "Models complex domains in a readable way",
            "Reuse through inheritance and composition",
            "Encapsulation protects invariants and reduces coupling",
            "Polymorphism makes code extensible without editing callers",
        ],
        "disadvantages": [
            "Adds boilerplate and abstraction for very small scripts",
            "Deep or incorrect inheritance hierarchies make code harder to follow",
            "Design mistakes are costly once many classes depend on them",
        ],
        "important_points": [
            "A class is a blueprint; an object is a specific instance of it.",
            "__init__ initialises an object and self refers to that object.",
            "Use encapsulation to protect invariants such as a non-negative balance.",
            "Prefer is-a inheritance only when the subtype truly substitutes the parent.",
            "Dunder methods such as __str__ and __repr__ make objects easier to inspect.",
            "Composition often produces simpler designs than deep inheritance trees.",
        ],
        "summary": (
            "OOP groups state and behaviour into objects created from classes. The four pillars - "
            "encapsulation, inheritance, polymorphism and abstraction - help manage complexity. "
            "Python implements these ideas with classes, __init__, self, inheritance and method "
            "overriding. Good OOP design favours small, focused classes and composition over deep "
            "inheritance, while keeping interfaces clear for the rest of the program."
        ),
        "revision_tips": [
            "Write a small class from memory and explain every line of __init__.",
            "Practise converting a procedural script into classes with clear responsibilities.",
            "Draw a class diagram for a simple app such as a library or a shopping cart.",
            "Review the difference between inheritance and composition with one example each.",
        ],
        "faqs": [
            {"question": "What does self actually refer to?", "answer": "self is the specific instance whose method is being called. Python passes the instance automatically, so obj.method() calls method(obj)."},
            {"question": "Is inheritance always better than composition?", "answer": "No. Use inheritance for genuine is-a relationships. Composition is usually more flexible when one object simply uses another."},
            {"question": "What is the difference between a class attribute and an instance attribute?", "answer": "A class attribute is shared by all instances. An instance attribute is stored on one object and can differ between objects."},
        ],
        "quiz": [
            {
                "difficulty": "Easy",
                "question": "What is a class in object-oriented programming?",
                "options": ["A blueprint for creating objects", "A running program", "A built-in Python function", "A database table"],
                "correct_index": 0,
                "explanation": "A class defines the attributes and methods that its objects will have. Objects are instances created from that blueprint.",
            },
            {
                "difficulty": "Easy",
                "question": "Which keyword is used to define a class in Python?",
                "options": ["class", "def", "object", "new"],
                "correct_index": 0,
                "explanation": "Python uses the class keyword followed by the class name and a colon.",
            },
            {
                "difficulty": "Medium",
                "question": "Which OOP principle is demonstrated when Dog and Cat both implement their own speak() method?",
                "options": ["Polymorphism", "Encapsulation", "Abstraction", "Normalization"],
                "correct_index": 0,
                "explanation": "Polymorphism allows different classes to respond to the same method name with their own behaviour.",
            },
            {
                "difficulty": "Medium",
                "question": "What is composition best described as?",
                "options": ["A has-a relationship between objects", "An is-a relationship between classes", "A way to hide methods", "A database constraint"],
                "correct_index": 0,
                "explanation": "Composition builds an object from other objects, expressing a has-a relationship, such as a Car having an Engine.",
            },
            {
                "difficulty": "Hard",
                "question": "Why is deep inheritance often discouraged?",
                "options": [
                    "Changes in a parent can ripple unpredictably through subclasses",
                    "Python does not allow more than two classes",
                    "Subclasses cannot define methods",
                    "Inheritance always makes programs slower at runtime",
                ],
                "correct_index": 0,
                "explanation": "Deep hierarchies create tight coupling. A change in a base class can break many subclasses, making the design fragile.",
            },
            {
                "difficulty": "Hard",
                "question": "What does the __init__ method do?",
                "options": [
                    "Initialises a newly created instance",
                    "Deletes an instance",
                    "Compiles the class",
                    "Creates a new class at runtime",
                ],
                "correct_index": 0,
                "explanation": "__init__ is called after an object is created, letting the class set up its initial attributes.",
            },
        ],
    },
    "sql basics": {
        "title": "SQL Basics",
        "introduction": (
            "SQL (Structured Query Language) is the standard language for working with relational "
            "databases. Data is stored in tables made of rows and columns, and SQL lets you retrieve, "
            "filter, join and modify that data. Unlike procedural languages, SQL is declarative: you "
            "describe the result you want and the database engine decides how to compute it. A solid "
            "grasp of SELECT, WHERE, JOIN and basic data modification is the foundation for every "
            "database-driven application."
        ),
        "objectives": [
            "Explain tables, rows, columns and keys",
            "Write SELECT queries with filtering and sorting",
            "Combine tables using INNER JOIN",
            "Insert, update and delete rows safely",
            "Understand why parameterised queries prevent SQL injection",
        ],
        "concepts": [
            {
                "heading": "Tables, rows and keys",
                "explanation": (
                    "A table stores one kind of entity, such as students. Each row is a record and "
                    "each column is an attribute. A primary key uniquely identifies a row, while a "
                    "foreign key references a primary key in another table, creating a relationship "
                    "between them."
                ),
            },
            {
                "heading": "Reading data",
                "explanation": (
                    "SELECT chooses columns, FROM chooses the table, WHERE filters rows, ORDER BY "
                    "sorts results and LIMIT restricts the number of rows. Use IS NULL (not = NULL) "
                    "to test for missing values. Aggregates such as COUNT, AVG, MIN and MAX summarise "
                    "groups, often with GROUP BY."
                ),
            },
            {
                "heading": "Joins",
                "explanation": (
                    "A join combines rows from two tables using a related column. INNER JOIN returns "
                    "only matching rows. LEFT JOIN keeps every row from the left table and fills "
                    "missing matches with NULL. Always join on indexed keys and select only the "
                    "columns you need."
                ),
            },
        ],
        "definitions": [
            {"term": "Primary key", "definition": "A column or set of columns that uniquely identifies each row in a table."},
            {"term": "Foreign key", "definition": "A column that references a primary key in another table to enforce a relationship."},
            {"term": "Query", "definition": "A SQL statement that requests data or performs an operation on the database."},
            {"term": "NULL", "definition": "A marker for a missing or unknown value; it is not the same as zero or an empty string."},
            {"term": "Join", "definition": "An operation that combines rows from two or more tables based on a related column."},
            {"term": "Aggregate function", "definition": "A function such as COUNT, SUM or AVG that computes a single value from many rows."},
        ],
        "key_terms": ["SELECT", "WHERE", "ORDER BY", "JOIN", "GROUP BY", "INSERT", "UPDATE", "DELETE", "DDL", "DML"],
        "steps": [
            "Identify the table that holds the data you need.",
            "Write SELECT with the required columns; avoid SELECT * in application code.",
            "Add WHERE to filter rows and ORDER BY to sort them.",
            "Join related tables on their key columns.",
            "Test the query on a small dataset and inspect the result.",
            "Use INSERT, UPDATE or DELETE only inside a transaction and with a precise WHERE clause.",
        ],
        "examples": [
            "Students with marks above 80:\nSELECT name, marks\nFROM students\nWHERE marks > 80\nORDER BY marks DESC;",
            "Join students with their departments:\nSELECT s.name, d.department_name\nFROM students AS s\nJOIN departments AS d ON d.id = s.department_id;",
            "Average marks by department:\nSELECT department_id, AVG(marks) AS average_marks\nFROM students\nGROUP BY department_id\nHAVING AVG(marks) > 70;",
        ],
        "applications": [
            "Student information and result management systems",
            "E-commerce order and inventory databases",
            "Reporting and analytics dashboards",
            "Backing storage for web and mobile applications",
        ],
        "advantages": [
            "Declarative language with a standard syntax across databases",
            "Efficient querying of structured data with indexes",
            "Strong integrity through keys and constraints",
            "Transactions keep multi-step changes consistent",
        ],
        "disadvantages": [
            "Schemas can be rigid when requirements change rapidly",
            "Poorly written joins and missing indexes cause slow queries",
            "Large-scale distribution is harder than with some NoSQL systems",
        ],
        "important_points": [
            "SQL is declarative: describe the result, not the algorithm.",
            "Use IS NULL and IS NOT NULL; = NULL never matches.",
            "A WHERE clause on DELETE or UPDATE is essential - without it every row is affected.",
            "Parameterised queries separate SQL code from user data and prevent injection.",
            "INNER JOIN drops unmatched rows; LEFT JOIN keeps left-side rows.",
            "Indexes speed up reads but add write and storage overhead.",
        ],
        "summary": (
            "Relational databases store related data in tables, linked by primary and foreign keys. "
            "SELECT with WHERE, ORDER BY, GROUP BY and JOIN covers most read operations. INSERT, "
            "UPDATE and DELETE modify data and should always be scoped carefully. Writing clear, "
            "parameterised queries and indexing the right columns keeps applications correct and fast."
        ),
        "revision_tips": [
            "Practise writing queries by hand before running them, then compare the results.",
            "Create a two-table sample database and test INNER versus LEFT joins.",
            "Memorise the logical order: FROM, WHERE, GROUP BY, HAVING, SELECT, ORDER BY.",
            "Keep a list of common mistakes such as = NULL and missing WHERE clauses.",
        ],
        "faqs": [
            {"question": "What is the difference between WHERE and HAVING?", "answer": "WHERE filters rows before grouping. HAVING filters groups after aggregation, so it is used with conditions on aggregate values."},
            {"question": "Why does = NULL return no rows?", "answer": "NULL represents an unknown value, so equality with it is unknown. Use IS NULL or IS NOT NULL instead."},
            {"question": "What is a primary key?", "answer": "A column or combination of columns that uniquely identifies each row. Primary keys cannot contain duplicate values or NULLs."},
        ],
        "quiz": [
            {
                "difficulty": "Easy",
                "question": "Which SQL statement retrieves data from a table?",
                "options": ["SELECT", "INSERT", "UPDATE", "DELETE"],
                "correct_index": 0,
                "explanation": "SELECT reads data. INSERT adds rows, UPDATE modifies rows and DELETE removes rows.",
            },
            {
                "difficulty": "Easy",
                "question": "Which clause filters rows in a query?",
                "options": ["WHERE", "ORDER BY", "GROUP BY", "LIMIT"],
                "correct_index": 0,
                "explanation": "WHERE filters individual rows. ORDER BY sorts, GROUP BY aggregates and LIMIT restricts row count.",
            },
            {
                "difficulty": "Medium",
                "question": "Which join returns only rows that match in both tables?",
                "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"],
                "correct_index": 0,
                "explanation": "INNER JOIN keeps only matching rows. LEFT and RIGHT joins keep unmatched rows from one side; CROSS JOIN produces a Cartesian product.",
            },
            {
                "difficulty": "Medium",
                "question": "How should you test that a column has no value?",
                "options": ["column IS NULL", "column = NULL", "column == NULL", "column LIKE NULL"],
                "correct_index": 0,
                "explanation": "NULL is an unknown value, so equality tests do not work. Use IS NULL.",
            },
            {
                "difficulty": "Hard",
                "question": "What is the main security benefit of parameterised queries?",
                "options": [
                    "User input is treated as data, not executable SQL",
                    "They automatically encrypt the database",
                    "They make every query run in constant time",
                    "They remove the need for primary keys",
                ],
                "correct_index": 0,
                "explanation": "Parameters are bound separately from the SQL text, so input cannot change the query structure. This prevents SQL injection.",
            },
            {
                "difficulty": "Hard",
                "question": "Which clause filters groups after aggregation?",
                "options": ["HAVING", "WHERE", "FROM", "ORDER BY"],
                "correct_index": 0,
                "explanation": "HAVING is evaluated after GROUP BY and can filter on aggregate results such as AVG(marks) > 70.",
            },
        ],
    },
    "normalization": {
        "title": "Database Normalization",
        "introduction": (
            "Normalization is the process of organising a relational schema to reduce redundancy and "
            "prevent update anomalies. Edgar Codd introduced the normal forms in the 1970s. Instead of "
            "storing the same fact in many rows, normalization stores each fact once and links tables "
            "with keys. The first three normal forms - 1NF, 2NF and 3NF - solve most practical design "
            "problems. Over-normalization can hurt performance, so real systems sometimes denormalize "
            "deliberately."
        ),
        "objectives": [
            "Explain redundancy and the three classic anomalies",
            "Test a table for first normal form (1NF)",
            "Remove partial dependencies to reach 2NF",
            "Remove transitive dependencies to reach 3NF",
            "Decide when denormalization is justified",
        ],
        "concepts": [
            {
                "heading": "Why normalize?",
                "explanation": (
                    "Redundant data causes three anomalies. An insert anomaly makes it impossible to "
                    "record a fact without unrelated data. An update anomaly leaves copies of the same "
                    "fact inconsistent after a partial update. A delete anomaly removes unrelated facts "
                    "along with the deleted row. Normalization removes these risks by decomposing tables."
                ),
            },
            {
                "heading": "1NF and 2NF",
                "explanation": (
                    "A table is in 1NF when every cell holds a single atomic value and each row is unique. "
                    "A table is in 2NF when it is in 1NF and every non-key attribute depends on the whole "
                    "composite key, not just part of it. Partial dependencies are removed by splitting "
                    "the table into smaller tables keyed by the relevant portion."
                ),
            },
            {
                "heading": "3NF and beyond",
                "explanation": (
                    "A table is in 3NF when it is in 2NF and no non-key attribute depends on another "
                    "non-key attribute (no transitive dependency). For example, a student table should "
                    "not store both department_id and department_name. BCNF is a stricter form that "
                    "handles certain overlapping candidate keys; it is less commonly needed in coursework."
                ),
            },
        ],
        "definitions": [
            {"term": "Functional dependency", "definition": "A relationship where the value of one attribute determines the value of another, written X -> Y."},
            {"term": "Candidate key", "definition": "A minimal set of attributes that uniquely identifies each row."},
            {"term": "Partial dependency", "definition": "A non-key attribute that depends on only part of a composite primary key, violating 2NF."},
            {"term": "Transitive dependency", "definition": "A non-key attribute that depends on another non-key attribute, violating 3NF."},
            {"term": "Denormalization", "definition": "Deliberately reintroducing redundancy to improve read performance, usually after normalization."},
            {"term": "Anomaly", "definition": "A data inconsistency or operational problem caused by a poorly designed schema."},
        ],
        "key_terms": ["1NF", "2NF", "3NF", "BCNF", "functional dependency", "candidate key", "partial dependency", "transitive dependency", "denormalization"],
        "steps": [
            "List every attribute and write down all functional dependencies.",
            "Identify a candidate key for the relation.",
            "Check 1NF: ensure each cell is atomic and no repeating groups exist.",
            "Check 2NF: remove attributes that depend on only part of a composite key.",
            "Check 3NF: remove attributes that depend on other non-key attributes.",
            "Verify the decomposed tables join back to the original without losing information.",
        ],
        "examples": [
            "Unnormalized order data: (order_id, customer_name, customer_address, product_name, price, quantity). Storing customer and product data on every order repeats facts and risks inconsistencies.",
            "3NF decomposition: customers(customer_id, name, address), products(product_id, name, price), orders(order_id, customer_id, order_date), order_items(order_id, product_id, quantity).",
            "A violation: student_id -> department_id and department_id -> department_name. Since department_name depends on a non-key attribute, move departments into their own table.",
        ],
        "applications": [
            "Designing OLTP schemas for business applications",
            "Reducing storage and update errors in student databases",
            "Preparing clean schemas before adding indexes",
            "Supporting reliable reporting through consistent source data",
        ],
        "advantages": [
            "Removes duplicate data and update anomalies",
            "Keeps each fact stored in exactly one place",
            "Makes schemas easier to understand and maintain",
            "Improves data integrity through keys and constraints",
        ],
        "disadvantages": [
            "More tables mean more joins and sometimes slower reads",
            "Aggressive normalization can make reports complex",
            "Denormalization may be needed for high-performance analytics",
        ],
        "important_points": [
            "1NF is about atomic values; 2NF is about the whole key; 3NF is about nothing but the key.",
            "Functional dependencies drive every normalization decision.",
            "An update anomaly is the classic symptom of redundant data.",
            "Always verify that decomposition is lossless before adopting it.",
            "OLTP systems usually normalize, while data warehouses may denormalize.",
            "Normalization is a design activity, not a one-time cleanup script.",
        ],
        "summary": (
            "Normalization organizes relations so each fact appears once. 1NF removes repeating groups "
            "and non-atomic values. 2NF removes partial dependencies on a composite key. 3NF removes "
            "transitive dependencies through non-key attributes. The result is a set of linked tables "
            "that avoid insert, update and delete anomalies. Denormalize only with a measured reason."
        ),
        "revision_tips": [
            "Practise identifying candidate keys before checking normal forms.",
            "Write out functional dependencies for every practice relation.",
            "Create one worked example for each anomaly so you can recognize them quickly.",
            "Remember the shorthand: every attribute must depend on the key, the whole key, and nothing but the key.",
        ],
        "faqs": [
            {"question": "What is the difference between 2NF and 3NF?", "answer": "2NF removes partial dependencies on part of a composite key. 3NF removes transitive dependencies where a non-key attribute depends on another non-key attribute."},
            {"question": "Does normalization always improve performance?", "answer": "No. It improves integrity and reduces redundancy, but more tables can mean more joins. Performance-critical reporting may justify limited denormalization."},
            {"question": "What is a lossless decomposition?", "answer": "A split of a table where joining the resulting tables recreates exactly the original rows, with no data loss or spurious rows."},
        ],
        "quiz": [
            {
                "difficulty": "Easy",
                "question": "What is the main goal of normalization?",
                "options": ["Reduce redundancy and anomalies", "Encrypt database tables", "Increase the number of columns", "Remove all foreign keys"],
                "correct_index": 0,
                "explanation": "Normalization organizes data to reduce redundant storage and avoid insert, update and delete anomalies.",
            },
            {
                "difficulty": "Easy",
                "question": "A table with repeating groups violates which normal form?",
                "options": ["1NF", "2NF", "3NF", "BCNF"],
                "correct_index": 0,
                "explanation": "1NF requires atomic values and no repeating groups.",
            },
            {
                "difficulty": "Medium",
                "question": "A non-key column that depends on only part of a composite primary key violates:",
                "options": ["2NF", "1NF", "3NF", "BCNF"],
                "correct_index": 0,
                "explanation": "Partial dependencies violate 2NF. The attribute must depend on the entire composite key.",
            },
            {
                "difficulty": "Medium",
                "question": "Which anomaly occurs when the same fact is stored in several rows and only one copy is updated?",
                "options": ["Update anomaly", "Insert anomaly", "Delete anomaly", "Join anomaly"],
                "correct_index": 0,
                "explanation": "An update anomaly leaves copies inconsistent when redundant data is partially updated.",
            },
            {
                "difficulty": "Hard",
                "question": "A table has student_id -> department_id and department_id -> department_name. Which dependency must be removed for 3NF?",
                "options": ["Transitive dependency", "Partial dependency", "Multivalued dependency", "Join dependency"],
                "correct_index": 0,
                "explanation": "department_name depends on a non-key attribute (department_id), which is a transitive dependency. Move it to a departments table.",
            },
            {
                "difficulty": "Hard",
                "question": "When is denormalization most justified?",
                "options": [
                    "When measured read performance outweighs redundancy costs",
                    "Always, because it saves storage",
                    "Before identifying candidate keys",
                    "When the schema has no primary keys",
                ],
                "correct_index": 0,
                "explanation": "Denormalization is a deliberate trade-off: redundant data can speed reads but increases update risk and storage.",
            },
        ],
    },
    "process management": {
        "title": "Process Management",
        "introduction": (
            "A process is a program in execution. The operating system creates processes, allocates "
            "them CPU time and memory, isolates them from one another and reclaims their resources "
            "when they finish. Process management covers the process lifecycle, the process control "
            "block (PCB), context switching, scheduling and inter-process communication. These ideas "
            "explain why a computer can run a browser, a music player and a compiler at the same time "
            "without them corrupting each other's memory."
        ),
        "objectives": [
            "Define a process and distinguish it from a program",
            "Describe the process states and valid transitions",
            "Explain the role of the process control block",
            "Understand context switching and its cost",
            "Compare basic scheduling goals and IPC mechanisms",
        ],
        "concepts": [
            {
                "heading": "Process states",
                "explanation": (
                    "A process moves through new, ready, running, waiting and terminated states. A ready "
                    "process could run but is waiting for the CPU. A running process holds the CPU. It "
                    "enters waiting when it requests I/O or an event. When the event completes it returns "
                    "to ready. Only the scheduler moves a process from ready to running."
                ),
            },
            {
                "heading": "The process control block",
                "explanation": (
                    "The OS stores per-process metadata in a process control block (PCB). The PCB contains "
                    "the process id, state, program counter, CPU registers, memory limits, open file "
                    "descriptors and scheduling information. During a context switch, the OS saves the "
                    "current process's register state in its PCB and restores the next process's state."
                ),
            },
            {
                "heading": "Scheduling and IPC",
                "explanation": (
                    "The scheduler chooses which ready process runs next. Fairness, throughput, latency "
                    "and CPU utilisation often conflict, so policies such as round-robin or priority "
                    "scheduling make different trade-offs. Processes communicate through shared memory "
                    "or message passing; the OS must synchronise access to avoid race conditions and "
                    "deadlocks."
                ),
            },
        ],
        "definitions": [
            {"term": "Process", "definition": "A program in execution, including its code, data, stack, registers and OS metadata."},
            {"term": "Process control block", "definition": "The kernel data structure that stores the state and resources of a process."},
            {"term": "Context switch", "definition": "Saving the state of one process and restoring the state of another so it can run."},
            {"term": "Thread", "definition": "An execution path within a process that shares the process's memory and resources."},
            {"term": "Inter-process communication", "definition": "Mechanisms such as pipes, shared memory and message queues that let processes exchange data."},
            {"term": "PID", "definition": "A unique numeric identifier assigned by the operating system to a process."},
        ],
        "key_terms": ["PCB", "context switch", "ready queue", "scheduler", "fork", "zombie process", "IPC", "race condition"],
        "steps": [
            "A program is loaded into memory and a PCB is created (new state).",
            "The process enters the ready queue and waits for the CPU.",
            "The scheduler dispatches it; it runs until it blocks, finishes or is preempted.",
            "On an I/O request it moves to the waiting state; on completion it returns to ready.",
            "On termination the OS releases memory, files and other resources, then removes the PCB.",
        ],
        "examples": [
            "Opening a browser often starts several processes: one for the UI, one per tab or renderer, plus network and GPU processes. Crash isolation is a major reason for this design.",
            "A shell runs `python script.py` by creating a child process with fork() and loading the interpreter with exec(), while the shell waits or continues.",
            "A web server may fork worker processes so one slow request cannot block all other clients.",
        ],
        "applications": [
            "Operating system kernels and schedulers",
            "Containers and virtual machines",
            "Web servers and background job systems",
            "Debugging and monitoring tools",
        ],
        "advantages": [
            "Isolation prevents one faulty program from corrupting another",
            "Concurrent execution improves CPU and I/O utilisation",
            "Per-process accounting supports fair resource allocation",
        ],
        "disadvantages": [
            "Creating processes and context switching add overhead",
            "Synchronisation between processes introduces complexity",
            "Bugs such as deadlocks and race conditions are hard to reproduce",
        ],
        "important_points": [
            "A program is passive code; a process is that code in execution.",
            "The PCB is the kernel's record of a process and its resources.",
            "A context switch saves and restores CPU state and costs time.",
            "Only one process per CPU core executes at any instant; concurrency is interleaving or parallelism.",
            "A zombie process has finished but its exit status has not been reaped by its parent.",
            "Threads share memory, which makes communication cheap but requires synchronisation.",
        ],
        "summary": (
            "The OS represents running programs as processes and tracks them with PCBs. Processes move "
            "between ready, running, waiting and terminated states under scheduler control. Context "
            "switching enables multitasking at a cost. Isolation makes systems robust, while IPC and "
            "synchronisation let processes cooperate. These mechanisms underpin every modern operating "
            "system and server."
        ),
        "revision_tips": [
            "Draw the five-state process diagram and label every transition with its trigger.",
            "List five fields stored in a PCB from memory.",
            "Explain context switching to a friend in under a minute.",
            "Compare process and thread creation with one concrete example each.",
        ],
        "faqs": [
            {"question": "What is the difference between a process and a program?", "answer": "A program is a passive file of instructions. A process is an active execution of that program with its own state and resources."},
            {"question": "What is a zombie process?", "answer": "A process that has terminated but whose parent has not yet read its exit status. The kernel keeps a minimal entry until it is reaped."},
            {"question": "Why are context switches expensive?", "answer": "They save and restore registers and memory mappings, invalidate caches and TLB entries, and give the scheduler less time for useful work."},
        ],
        "quiz": [
            {
                "difficulty": "Easy",
                "question": "A program in execution is called a:",
                "options": ["Process", "File", "Thread", "Package"],
                "correct_index": 0,
                "explanation": "A process is a program in execution, with its own state, memory and resources.",
            },
            {
                "difficulty": "Easy",
                "question": "Which state is a process in while waiting for disk I/O?",
                "options": ["Waiting", "Ready", "Running", "Terminated"],
                "correct_index": 0,
                "explanation": "A process that is blocked on I/O is in the waiting (blocked) state until the event completes.",
            },
            {
                "difficulty": "Medium",
                "question": "What does the process control block store?",
                "options": ["Process state and CPU context", "Only the source code", "Only the user's files", "The compiler settings"],
                "correct_index": 0,
                "explanation": "The PCB stores the pid, state, registers, program counter, memory information and other scheduling data.",
            },
            {
                "difficulty": "Medium",
                "question": "What happens during a context switch?",
                "options": [
                    "The current process state is saved and another is restored",
                    "The process is deleted from memory",
                    "The CPU frequency is doubled",
                    "The file system is reformatted",
                ],
                "correct_index": 0,
                "explanation": "The kernel saves the running process's state and restores the state of the next scheduled process.",
            },
            {
                "difficulty": "Hard",
                "question": "Why can a deadlock occur between two processes?",
                "options": [
                    "Each holds a resource and waits for one held by the other",
                    "Both processes have the same priority",
                    "Both processes use the same compiler",
                    "The CPU has more than one core",
                ],
                "correct_index": 0,
                "explanation": "Circular waiting, combined with mutual exclusion and no preemption, lets each process hold one resource while waiting for another.",
            },
            {
                "difficulty": "Hard",
                "question": "Which statement about threads is correct?",
                "options": [
                    "Threads in a process share memory but have separate execution stacks",
                    "Threads always have separate address spaces",
                    "Threads cannot run concurrently",
                    "Threads are the same as processes",
                ],
                "correct_index": 0,
                "explanation": "Threads share the process address space and open resources, but each has its own stack and register context.",
            },
        ],
    },
    "machine learning basics": {
        "title": "Machine Learning Basics",
        "introduction": (
            "Machine learning (ML) builds systems that improve at a task by learning patterns from "
            "data rather than following hand-written rules. A model is trained on examples, evaluated "
            "on unseen data and then used to make predictions. The three main paradigms are supervised "
            "learning, unsupervised learning and reinforcement learning. ML powers spam filters, "
            "recommendation systems, fraud detection, speech recognition and much more."
        ),
        "objectives": [
            "Explain what machine learning is and when to use it",
            "Distinguish features, labels and target variables",
            "Compare supervised, unsupervised and reinforcement learning",
            "Describe training, validation and testing",
            "Recognise overfitting and how to reduce it",
        ],
        "concepts": [
            {
                "heading": "Learning from data",
                "explanation": (
                    "A dataset is organised into rows (examples) and columns (features). In supervised "
                    "learning, each training row also has a label - the answer we want to predict. The "
                    "algorithm adjusts its parameters to reduce the difference between its predictions "
                    "and the labels. The learned mapping can then predict labels for new examples."
                ),
            },
            {
                "heading": "Training, validation and testing",
                "explanation": (
                    "Data is usually split into training, validation and test sets. The model learns on "
                    "training data, hyperparameters are tuned on validation data, and the test set is "
                    "used only once for a final estimate of performance. Evaluating on training data "
                    "overstates quality because the model has already seen those answers."
                ),
            },
            {
                "heading": "Overfitting and underfitting",
                "explanation": (
                    "Overfitting means memorising training noise, so performance is excellent on training "
                    "data but poor on new data. Underfitting means the model is too simple to capture the "
                    "pattern. More data, regularisation, simpler models and cross-validation help control "
                    "overfitting; richer features and more capacity help underfitting."
                ),
            },
        ],
        "definitions": [
            {"term": "Model", "definition": "A mathematical structure whose parameters are learned from data to make predictions."},
            {"term": "Feature", "definition": "An input variable used by the model, such as age, price or a pixel value."},
            {"term": "Label", "definition": "The target answer associated with a training example in supervised learning."},
            {"term": "Training", "definition": "The process of adjusting model parameters to minimise error on training data."},
            {"term": "Overfitting", "definition": "Fitting noise in the training data so closely that generalisation to new data suffers."},
            {"term": "Inference", "definition": "Using a trained model to produce predictions on new examples."},
            {"term": "Hyperparameter", "definition": "A setting chosen before training, such as learning rate or tree depth, rather than learned from data."},
        ],
        "key_terms": ["supervised learning", "unsupervised learning", "reinforcement learning", "training set", "test set", "feature", "label", "overfitting", "regularisation", "accuracy"],
        "steps": [
            "Define the problem and the decision the model should support.",
            "Collect and clean representative data; handle missing values and leakage.",
            "Choose features and a suitable model family.",
            "Split data into training, validation and test sets.",
            "Train the model and tune hyperparameters on validation data.",
            "Evaluate on the test set using metrics that match the problem, then deploy and monitor.",
        ],
        "examples": [
            "Spam filtering: features are word frequencies and sender signals; the label is spam or not spam. A classifier learns from thousands of labelled emails.",
            "House price prediction: features include area, location and number of rooms; the label is the sale price. Linear regression is a common baseline.",
            "Customer segmentation: no labels are given, so clustering groups customers with similar buying behaviour.",
        ],
        "applications": [
            "Recommendation systems for products and media",
            "Fraud and anomaly detection in finance",
            "Medical image analysis and diagnosis support",
            "Speech recognition and natural language processing",
        ],
        "advantages": [
            "Can capture complex patterns that rules cannot express",
            "Improves with more and better data",
            "Automates prediction and decision support at scale",
        ],
        "disadvantages": [
            "Requires representative, high-quality data",
            "Models can be opaque and hard to explain",
            "Performance can degrade when real-world data drifts",
            "Bias in data can produce unfair or harmful predictions",
        ],
        "important_points": [
            "The test set must remain unseen during training and tuning.",
            "Overfitting shows as high training accuracy and low validation accuracy.",
            "More features are not always better - irrelevant features add noise.",
            "Choose metrics that match the cost of errors, not accuracy by default.",
            "Data leakage can make results look excellent and fail in production.",
            "A simple baseline model is the best starting point for comparison.",
        ],
        "summary": (
            "Machine learning learns patterns from data to make predictions or decisions. Supervised "
            "learning uses labelled examples, unsupervised learning finds structure without labels, "
            "and reinforcement learning learns from rewards. Honest evaluation requires separate "
            "training, validation and test sets. Managing overfitting, leakage and bias is as important "
            "as choosing a powerful algorithm."
        ),
        "revision_tips": [
            "Explain the difference between a feature, a label and a hyperparameter in one sentence each.",
            "Sketch the train/validation/test workflow from memory.",
            "Describe one concrete overfitting example and three ways to reduce it.",
            "Practise choosing a metric for a scenario such as fraud detection, where false negatives are costly.",
        ],
        "faqs": [
            {"question": "What is the difference between AI and machine learning?", "answer": "AI is the broad goal of building intelligent systems. Machine learning is one approach to AI in which models learn patterns from data."},
            {"question": "Why is accuracy a poor metric for imbalanced data?", "answer": "If 99% of cases are negative, predicting negative every time gives 99% accuracy while catching none of the important positive cases. Use precision, recall or F1 instead."},
            {"question": "What is data leakage?", "answer": "Information from outside the training data - often from the target or the test set - accidentally influences training, producing inflated results that do not generalize."},
        ],
        "quiz": [
            {
                "difficulty": "Easy",
                "question": "In supervised learning, what is a label?",
                "options": ["The target answer for an example", "An input feature", "A model hyperparameter", "A type of database"],
                "correct_index": 0,
                "explanation": "The label is the known target value the model learns to predict. Features are the inputs.",
            },
            {
                "difficulty": "Easy",
                "question": "Which paradigm learns from labelled examples?",
                "options": ["Supervised learning", "Unsupervised learning", "Reinforcement learning", "Rule-based search"],
                "correct_index": 0,
                "explanation": "Supervised learning trains on input-label pairs. Unsupervised learning works without labels, and reinforcement learning uses rewards.",
            },
            {
                "difficulty": "Medium",
                "question": "Why do we keep a separate test set?",
                "options": [
                    "To estimate performance on unseen data",
                    "To increase the training data",
                    "To tune hyperparameters",
                    "To label the data automatically",
                ],
                "correct_index": 0,
                "explanation": "The test set simulates new data and is used only for a final, unbiased performance estimate. Hyperparameters are tuned on validation data.",
            },
            {
                "difficulty": "Medium",
                "question": "High training accuracy with low validation accuracy usually indicates:",
                "options": ["Overfitting", "Underfitting", "Data leakage", "Perfect generalisation"],
                "correct_index": 0,
                "explanation": "The model has memorised training data instead of learning general patterns, so validation performance lags.",
            },
            {
                "difficulty": "Hard",
                "question": "Which action most directly helps reduce overfitting?",
                "options": [
                    "Adding regularisation and more training data",
                    "Adding more features from the test set",
                    "Training for more epochs without validation",
                    "Removing the validation split",
                ],
                "correct_index": 0,
                "explanation": "Regularisation constrains model complexity, and more representative data helps it learn general patterns. Using test data would leak information.",
            },
            {
                "difficulty": "Hard",
                "question": "Which metric is most appropriate when missing a fraudulent transaction is very costly?",
                "options": ["Recall for the fraud class", "Overall accuracy", "Training loss", "Model size"],
                "correct_index": 0,
                "explanation": "High recall means catching most fraud cases. Accuracy can look high while missing rare positives, and training loss does not measure deployment performance.",
            },
        ],
    },
}


DEMO_TOPICS = [pack["title"] for pack in DEMO_PACKS.values()]

_LEVEL_NOTES = {
    "Beginner": "This sample is pitched at beginner level: focus on the definitions and examples first, then reread the detailed explanation.",
    "Intermediate": "This sample is pitched at intermediate level: connect each concept to the examples and try the revision questions.",
    "Advanced": "This sample is pitched at advanced level: use the summary as a map, then dig into the trade-offs and edge cases.",
}


def _generic_content(subject_name: str, topic_name: str) -> dict:
    """An honest study framework for topics without a curated demo pack."""
    return {
        "title": topic_name,
        "introduction": (
            f"This is an offline demo study framework for '{topic_name}' in {subject_name}. "
            "It shows how LearnForge organises personalized learning material, but it does not "
            "contain a full factual explanation because this topic has no curated demo pack. "
            "Configure an AI key to generate complete notes, definitions and examples for this topic."
        ),
        "learning_objectives": [
            f"Describe what {topic_name} covers and why it matters in {subject_name}",
            f"Identify the core terminology needed to discuss {topic_name}",
            f"Explain at least three key ideas about {topic_name} in your own words",
            "Connect the topic to one real-world or exam-style application",
        ],
        "basic_concepts": [
            {
                "heading": "Map the topic before memorising",
                "explanation": (
                    "Skim your textbook or class notes and write the main headings for this topic. "
                    "Group them into three to five themes. This gives you a mental map and prevents "
                    "isolated fact memorisation."
                ),
            },
            {
                "heading": "Build precise definitions",
                "explanation": (
                    "For every new term, write a one-sentence definition and one example. Test yourself "
                    "by covering the definition and explaining it aloud. The AI mode fills this section "
                    "with course-accurate definitions automatically."
                ),
            },
            {
                "heading": "Practise retrieval, not rereading",
                "explanation": (
                    "After reading a section, close the book and write down what you remember. Compare "
                    "with the source, then repeat the missed points. This active recall step is what "
                    "turns recognition into recall."
                ),
            },
        ],
        "detailed_explanation": (
            "A strong study sequence for this topic is: preview the structure, read for understanding, "
            "summarise from memory, then apply the idea to a question. Because this is an offline demo "
            "framework, specific facts are intentionally left out rather than guessed. Use the steps, "
            "objectives and study prompts below as a scaffold, and add an AI key to receive a complete "
            "explanation tailored to your level and learning style."
        ),
        "important_definitions": [],
        "key_terms": [],
        "step_by_step": [
            "Preview the topic and list its main headings.",
            "Define each unfamiliar term in your own words.",
            "Read the material in short sections and summarise each from memory.",
            "Work through at least two examples or solved problems.",
            "Write five exam-style questions and answer them without notes.",
        ],
        "real_world_examples": [
            f"Find one case in your textbook where {topic_name} is applied, and explain the inputs and outcome.",
            "Look for a news article, product or system that depends on this topic and note the connection.",
        ],
        "practical_applications": [
            "Use the topic to solve a past exam question under timed conditions.",
            "Explain the topic to a classmate in under five minutes.",
            "Build a one-page revision sheet with definitions, a diagram and two examples.",
        ],
        "advantages": [],
        "disadvantages": [],
        "important_points": [
            "Start with the official syllabus wording for this topic.",
            "Prefer precise definitions over vague paraphrases.",
            "Test recall before adding more reading.",
            "Use examples to check understanding, not just to illustrate.",
            "Review the topic again after 24 hours and after one week.",
        ],
        "summary": (
            f"This demo framework gives you a structured way to begin studying {topic_name}. It is "
            "not a substitute for course material or live AI-generated notes. Use the objectives to "
            "guide your reading, then verify facts against your textbook before an exam."
        ),
        "revision_tips": [
            "Create a one-page summary from memory and compare it with the source.",
            "Turn each objective into a question and answer it aloud.",
            "Schedule a short review after 24 hours and a longer one after a week.",
            "Explain the topic to someone else; gaps in your explanation reveal gaps in understanding.",
        ],
        "faqs": [
            {
                "question": "Why is this demo content shorter than expected?",
                "answer": "This topic has no curated offline demo pack. LearnForge only shows facts it can source reliably. Add an AI API key to generate complete notes for this topic.",
            },
            {
                "question": "How do I get the full personalized version?",
                "answer": "Set AI_API_KEY and AI_PROVIDER in your .env file and restart the app. Live AI then generates notes tailored to your level, style and language.",
            },
        ],
        "quiz": [],
    }


def _normalise_topic(topic_name: str) -> str:
    return " ".join((topic_name or "").lower().replace("-", " ").split())


def get_demo_pack(topic_name: str) -> dict | None:
    return DEMO_PACKS.get(_normalise_topic(topic_name))


# Curated packs use compact key names; the stored schema uses the same keys
# as live AI output so the viewer, PDF and API all share one contract.
_PACK_ALIASES = {
    "objectives": "learning_objectives",
    "concepts": "basic_concepts",
    "definitions": "important_definitions",
    "steps": "step_by_step",
    "examples": "real_world_examples",
    "applications": "practical_applications",
}


def _apply_pack_aliases(content: dict) -> None:
    for source, target in _PACK_ALIASES.items():
        if source in content and not content.get(target):
            content[target] = content.pop(source)
    if not content.get("detailed_explanation") and content.get("basic_concepts"):
        paragraphs = []
        for concept in content["basic_concepts"]:
            if not isinstance(concept, dict):
                continue
            heading = (concept.get("heading") or "").strip()
            explanation = (concept.get("explanation") or "").strip()
            if not explanation:
                continue
            paragraphs.append(f"{heading}: {explanation}" if heading else explanation)
        if paragraphs:
            content["detailed_explanation"] = "\n\n".join(paragraphs)


def build_demo_content(
    *,
    subject_name: str,
    topic_name: str,
    level: str,
    content_type: str,
    language: str,
    style: str,
) -> tuple[dict, str]:
    import copy

    pack = get_demo_pack(topic_name)
    notes: list[str] = []
    if pack:
        content = copy.deepcopy(pack)
        content.pop("quiz", None)
        _apply_pack_aliases(content)
        content["title"] = topic_name
        notes.append(
            "Demo mode: this is sample educational content from the offline demo library, "
            "not generated by a live AI model."
        )
    else:
        content = _generic_content(subject_name, topic_name)
        notes.append(
            "Demo mode: no curated offline pack exists for this topic, so a study framework is shown. "
            "It is not AI-generated."
        )

    level_note = _LEVEL_NOTES.get(level, _LEVEL_NOTES["Beginner"])
    content["introduction"] = f"{content['introduction']} {level_note}"
    content["learning_objectives"] = list(content.get("learning_objectives", []))
    if content_type in {"Short Notes", "Quick Revision Notes"}:
        content["introduction"] = content["introduction"].replace(
            level_note, f"{level_note} Keep this revision-focused sample compact."
        )
    elif content_type in {"Important Questions", "Exam Preparation Notes"}:
        content["important_points"] = list(content.get("important_points", [])) + [
            "Turn each FAQ into a practice question and answer it without looking.",
        ]

    if language != "English":
        notes.append(
            f"Offline demo content is available in English only. Configure an AI key to generate this material in {language}."
        )

    if not pack:
        notes.append(
            "For a complete, factual explanation with definitions and examples, connect a live AI provider."
        )

    return content, " ".join(notes)


def _build_generic_quiz(topic_name: str, difficulty: str, count: int) -> tuple[list[dict], str]:
    """Generates structured educational multiple-choice questions for any topic without curated bank."""
    diff_label = difficulty.title()
    template_bank = [
        {
            "question": f"What is the foundational concept behind {topic_name}?",
            "options": [
                f"A systematic framework designed to analyze and implement {topic_name} principles efficiently.",
                f"A legacy utility that has been entirely deprecated in modern computer science.",
                f"A hardware-only logic gate configuration with no software abstraction.",
                f"An unstructured data store that operates without algorithms or conventions."
            ],
            "correct_index": 0,
            "explanation": f"In academic study, {topic_name} provides a structured model and standardized methodology for problem-solving."
        },
        {
            "question": f"When applying {topic_name} in practical problem-solving, which consideration is most critical?",
            "options": [
                "Ignoring edge cases and error handling to reduce preliminary overhead.",
                f"Ensuring correct implementation, boundary validation, and adherence to {topic_name} best practices.",
                "Maximizing hardcoded parameters to eliminate modularity.",
                "Disabling algorithmic consistency across execution environments."
            ],
            "correct_index": 1,
            "explanation": f"Effective application of {topic_name} requires rigorous adherence to boundary validation, modularity, and operational constraints."
        },
        {
            "question": f"Which of the following best describes the key advantage of utilizing {topic_name}?",
            "options": [
                "It eliminates the requirement for system memory and computational power.",
                "It bypasses all procedural compilation and execution checks entirely.",
                f"It enhances maintainability, scalability, and predictable system behavior for {topic_name}.",
                "It restricts system architecture to a single-threaded sequential environment."
            ],
            "correct_index": 2,
            "explanation": f"The primary engineering advantage of {topic_name} is improved maintainability, modularity, and reproducible behavior."
        },
        {
            "question": f"What is a standard troubleshooting or debugging practice when an anomaly occurs in {topic_name}?",
            "options": [
                "Deleting all test assertions and ignoring runtime execution logs.",
                "Assuming compiler failure and rewriting the entire underlying operating system.",
                "Restarting hardware repeatedly without checking data flow or logic states.",
                f"Isolating inputs, analyzing execution traces, and verifying core {topic_name} assumptions."
            ],
            "correct_index": 3,
            "explanation": f"Systematic debugging in {topic_name} begins with input isolation, step-by-step trace inspection, and validation of initial assumptions."
        },
        {
            "question": f"In modern system design, how does {topic_name} interact with related architectural components?",
            "options": [
                f"Through well-defined interfaces and modular data flow contracts tailored to {topic_name}.",
                "By directly overwriting shared memory sectors without synchronization primitives.",
                "By establishing unconstrained cyclical dependencies across all system layers.",
                "By refusing integration with any external service or analytical framework."
            ],
            "correct_index": 0,
            "explanation": f"{topic_name} integrates cleanly into larger systems via well-defined interface contracts and clean boundary separation."
        },
        {
            "question": f"What trade-off is commonly evaluated when optimizing {topic_name} for high performance?",
            "options": [
                "Balancing computational time complexity, resource consumption, and implementation complexity.",
                "Sacrificing algorithmic correctness solely to minimize source code line count.",
                "Replacing all persistent storage with volatile temporary variables.",
                "Eliminating user access controls to boost instruction throughput."
            ],
            "correct_index": 0,
            "explanation": f"Optimization around {topic_name} involves balancing space vs. time efficiency, resource utilization, and code clarity."
        },
        {
            "question": f"Which metric or indicator is typically evaluated to assess the efficiency of {topic_name}?",
            "options": [
                "The physical weight of the storage disk containing the source code files.",
                "Execution latency, memory footprint, and algorithmic complexity under varying workloads.",
                "The arbitrary number of blank lines separating function declarations.",
                "The alphabetical ordering of identifier variable names."
            ],
            "correct_index": 1,
            "explanation": f"Performance assessment of {topic_name} focuses on throughput, latency, memory utilization, and scalability under load."
        },
        {
            "question": f"What role does documentation and formal specification play in {topic_name}?",
            "options": [
                "Documentation is counterproductive and should be prohibited in production environments.",
                "Specifications are only intended for sales presentations and have no engineering value.",
                f"It guarantees consistent understanding, proper usage patterns, and reliable collaboration around {topic_name}.",
                "It serves only to artificially inflate repository file size."
            ],
            "correct_index": 2,
            "explanation": f"Accurate documentation and technical specifications ensure consistent implementation and operational safety for {topic_name}."
        }
    ]
    
    rng = random.Random(f"{topic_name}|{difficulty}|{count}")
    chosen = list(template_bank)
    rng.shuffle(chosen)
    chosen = chosen[:max(1, min(count, len(chosen)))]
    
    questions = [
        {
            "question": q["question"],
            "options": list(q["options"]),
            "correct_index": int(q["correct_index"]),
            "explanation": q["explanation"],
        }
        for q in chosen
    ]
    
    note = (
        f"Demo mode: {len(questions)} educational sample questions for '{topic_name}' ({diff_label} level). "
        "Generated from the offline academic curriculum bank."
    )
    return questions, note


def get_demo_quiz(topic_name: str, difficulty: str, count: int) -> tuple[list[dict], str]:
    pack = get_demo_pack(topic_name)
    if not pack or not pack.get("quiz"):
        return _build_generic_quiz(topic_name, difficulty, count)

    rng = random.Random(f"{topic_name}|{difficulty}|{count}")
    preferred = [q for q in pack["quiz"] if q["difficulty"] == difficulty]
    others = [q for q in pack["quiz"] if q["difficulty"] != difficulty]
    rng.shuffle(preferred)
    rng.shuffle(others)
    chosen = (preferred + others)[: max(1, min(count, len(pack["quiz"])))]
    questions = [
        {
            "question": q["question"],
            "options": list(q["options"]),
            "correct_index": int(q["correct_index"]),
            "explanation": q["explanation"],
        }
        for q in chosen
    ]
    note = (
        f"Demo mode: {len(questions)} sample questions from the offline {pack['title']} quiz bank. "
        "Not generated by a live AI model."
    )
    if len(questions) < count:
        note += f" The demo bank supports up to {len(questions)} questions for this topic."
    return questions, note


def get_demo_topic_guide(topic_name: str, level: str, hours_per_day: float) -> dict:
    pack = get_demo_pack(topic_name)
    if pack:
        objectives = list(pack.get("objectives", []))[:4]
        key_points = list(pack.get("important_points", []))
        activities = [
            "Read the key concepts and write a short summary from memory.",
            "Work through the real-world examples without looking at the answers.",
            "Answer the practice questions, then check your reasoning.",
            "Review yesterday's material for 15 minutes before starting new content.",
        ]
        practice = list(pack.get("faqs", []))[:3]
        practice_questions = [item["question"] for item in practice] or [
            f"Explain {topic_name} in your own words.",
            f"List three key facts about {topic_name}.",
            f"Give one real-world example of {topic_name}.",
        ]
        if key_points:
            objectives.append(f"Recall: {key_points[0]}")
    else:
        objectives = [
            f"Define {topic_name} and list its main components",
            f"Summarise the three most important ideas in {topic_name}",
            "Work through two examples or exam questions",
        ]
        activities = [
            "Preview the chapter headings and write a one-page mind map.",
            "Read the core sections and summarise each from memory.",
            "Solve two practice questions and check your reasoning.",
            "Do a five-minute retrieval review at the end of the session.",
        ]
        practice_questions = [
            f"Explain {topic_name} in one paragraph without notes.",
            f"List three exam-worthy facts about {topic_name}.",
            f"Describe one application of {topic_name}.",
        ]
    return {
        "topic": topic_name,
        "objectives": objectives[:4],
        "activities": activities,
        "practice_questions": practice_questions[:4],
        "revision_minutes": max(10, round(hours_per_day * 60 * 0.2)),
    }
