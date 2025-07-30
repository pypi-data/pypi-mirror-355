# dfeqa

## Introduction

DfE-QA Python helper functions - covering a variety of checks primarily to report on the quality of data.

## Getting Started

`python -m pip install dfeqa`

or you can install with additional dependencies for analysis using Quarto with:

`python -m pip install dfeqa[user]`

## Using

### `dfeqa create`

Once `dfeqa` has been installed you can create new project files at the shell:

`dfeqa create data_quality my_dq_report.qmd`

Type `dfeqa create --help` for a list of templates.

You don't need to use the templates at all - you can just import the functions into your own scripts as follows

`from dfeqa import x [,y...]`

for example:

`from dfeqa import load_census, barchart as bc`

### `dfeqa addenv`

`dfeqa` v0.0.6 introduced `addenv` which will create a .env file in your working directory with some examples for connecting to SQL Server  or Databricks databases. You can define several connections and then define one of them using the `DEFAULT_CONN` variable (as shown in the template) as your default so you don't need to state it explicitly every time you use it. It's worth being explicit in your scripts though, so use the default when exploring data or developing scripts, but use explicit connection references when finalising your scripts.

### More details of the helper functions

You can find more information about the various helper functions and objects available to you at the [dfeqa wiki](https://github.com/quhack/dfeqa/wiki).

Some functions you may find helpful to get started:

*Data transformation and validation*
- year_group() - predict a pupil national curriculum year group from their date of birth
- valid_name_regex() - identify unlikely names (single character, odd characters like question marks, etc.)
- relaxed_valid_name_regex() - identify unlikely names (relaxed version used for school names)
- valid_upn() - validate UPNs, which allows for identifying invalid ones

*Summary functions*
- fd() - calculate frequency distributions from multiple variables and compare the results
- barchart()
- status_summary() - create a high-level summary suitable for mapping to organisational goals

*The Summary object*
- wide_fd() - create multiple frequency distibutions for comparison in wide format
- long_fd() - create multiple frequency distibutions for comparison in long format

*The Series object*
- minmax() - summarise the contents of a series including length of columns and characters used

*The DataFrame object*
- set_header() - convenience function to change the column headings in an easy-read format
- minmax() - summarise the contents of a dataframe including length of columns and characters used

*Database functions*
- list_tables() - list tables in a database
- get_table() - pull contents of a complete table from a database
- get_table_metadata() - pull the description of a table from a database including data types
- query() - query a database and put the result in a dataframe

## Contribute
You're very welcome to fork the repo or create a pull-request.
If you're working within DfE, get in touch, and I'll provide what guidance I can on developing new functions and updating the library.
