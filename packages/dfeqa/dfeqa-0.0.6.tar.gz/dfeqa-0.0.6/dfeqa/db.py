import os
import re
import warnings
from enum import Enum

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.sql import quoted_name

from dfeqa.datastructures import DataFrame

engines = {}
inspectors = {}

class Constants(Enum):
    DEFAULT_CONN = 'DEFAULT_CONN'

def get_default_conn():
    load_dotenv()
    return os.environ.get(Constants.DEFAULT_CONN.value)

def query(query,conn=None):
    if conn is None:
        conn = get_default_conn()
    else:
        load_dotenv()
        conn = os.environ[conn] if conn in os.environ else conn
    return DataFrame(pd.read_sql(query, conn))

def get_table(tablename, conn=None, schema = "dbo"):
    """
        tablename:
        conn: connection string or engine of db
        schema: defaults to dbo
        (returns): dataframe containing target table
    """
    if conn is None:
        conn = get_default_conn()
    else:
        load_dotenv()
        conn = os.environ[conn] if conn in os.environ else conn
    return DataFrame(pd.read_sql_table(tablename, schema = schema, con = conn))

def list_tables(conn = None, schema = None):
    """
        conn: connection string or engine to database
        schema: (optional) schema to filter results by
        (returns): list of table names in target db"""
    if conn is None:
        conn = get_default_conn()
    else:
        load_dotenv()
        conn = os.environ[conn] if conn in os.environ else conn
    eng = create_engine(conn, echo=False, future=True)
    i = inspect(eng)
    list_of_tablenames = []
    schemanames = i.get_schema_names()
    if schema is not None:
        schemanames = [schema] if schema in schemanames else None
    for s in schemanames:
        for t in i.get_table_names(schema=s):
            list_of_tablenames.append((s,t))
    return list_of_tablenames

def list_views(conn = None, schema = None):
    """
        conn: connection string or engine to database
        schema: (optional) schema to filter results by
        (returns): list of view names in target db"""
    if conn is None:
        conn = get_default_conn()
    else:
        load_dotenv()
        conn = os.environ[conn] if conn in os.environ else conn
    eng = create_engine(conn, echo=False, future=True)
    i = inspect(eng)
    list_of_viewnames = []
    schemanames = i.get_schema_names()
    if schema is not None:
        schemanames = [schema] if schema in schemanames else None
    for s in schemanames:
        for v in i.get_view_names(schema=s):
            list_of_viewnames.append((s,v))
    return list_of_viewnames

def load_census(year, term=None, NCYear=None, columns=None, conn='DEFAULT_CONN'):
    """to load a census dataset from PDR
    pass the year to load data from
    optionally pass the term in that year (or don't to get all terms)
    and also optionally, pass the year group NCYear,
    or a list of year groups, or don't specify to get all year groups
    and an optional list of columns to reduce the size of the query
    and resulting dataframe"""

    warnings.warn("""load_census() is deprecated and will be removed in a future release.
    It's a convenience function for DfE users, but it doesn't add functionality not available
    in get_table() or query().""", DeprecationWarning, stacklevel=2)

    load_dotenv()
    db_conn = os.environ[conn] if conn in os.environ else conn

    # check what is in ncyear - list or string?
    ncyear_list = list()
    if isinstance(NCYear, str):
        ncyear_list.append(NCYear)
    elif isinstance(NCYear, list):
        ncyear_list = NCYear
    # build sql query
    query = "select "
    if columns:
        assert isinstance(columns, (str, list))
        if isinstance(columns, str):
            query += columns
        elif isinstance(columns, list):
            query += ", ".join(columns)
    else:
        query += "*"
    query += """ from {tablename}
    where AcademicYear = {acadyr}""".format(tablename = 'tier0.CensusSeasonSSA_MasterView',
        acadyr = year)
    if term:
        query += " and CensusTerm = '{term}'".format(term = term)
    if NCYear:
        query += " and NCYearActual IN ({ncyear})""".format(ncyear = "'" + "','".join(ncyear_list) + "'")
    # query the db
    return DataFrame(pd.read_sql(query, db_conn))

class table_meta():
    def __init__(self, tablename, conn = Constants.DEFAULT_CONN.value):
        self._tablename = None
        self._schema = None
        self._columns = None
        self._constraints = None
        self._foreign_keys = None
        self._indexes = None
        self._pk_constr = None
        self._uniq_constr = None
        self._table_comment = None
        load_dotenv()
        conn = os.environ.get(conn) if conn in os.environ else conn
        if not engines.get(conn):
            engines[conn] = create_engine(conn, echo=False, future=True)
        if not inspectors.get(conn):
            inspectors[conn] = inspect(engines[conn])
        self._insp = inspectors[conn]

        schema_tablename = self._process_tablename(tablename)
        self._schema = schema_tablename[0]
        self._tablename = schema_tablename[1]
        self._columns = self._get_columns()
        self._constraints = self._get_constraints()
        self._foreign_keys = self._get_foreign_keys()
        self._indexes = self._get_indexes()
        self._pk_constr = self._get_pk_constr()
        self._uniq_constr = self._get_uniq_constr()
        self._table_comment = self._get_table_comment()

    def as_dict(self):
        return {
            'schema': self._schema,
            'tablename': self._tablename,
            'columns': self._columns,
            'constraints': self._constraints,
            'foreign_keys': self._foreign_keys,
            'indexes': self._indexes,
            'pk_constr': self._pk_constr,
            'uniq_constr': self._uniq_constr,
            'table_comment': self._table_comment
            }

    @property
    def schema(self):
        return self._schema

    @property
    def tablename(self):
        return self._tablename

    def _process_tablename(self,tn):
        tablename_list = re.sub(r"\[|\]","",tn).split(".")
        if len(tablename_list) == 1:
            tn = quoted_name(tablename_list[0], None)
            sc = quoted_name('dbo', None)
        elif len(tablename_list) == 2:
            tn = quoted_name(tablename_list[1], None)
            sc = quoted_name(tablename_list[0], None)
        else:
            raise RuntimeError("tablename not in a valid format")
        table_exists = self._insp.has_table(table_name = tn, schema = sc)
        if not table_exists:
            raise KeyError ("Table doesn't exist")
        return (sc,tn)

    @property
    def columns(self):
        return self._columns

    def _get_columns(self):
        try:
            cols = self._insp.get_columns(table_name = self._tablename, schema = self._schema)
        except NotImplementedError:
            cols = None
        else:
            for index, col in enumerate(cols):
                col['order'] = index
        return cols

    @property
    def constraints(self):
        return self._constraints

    def _get_constraints(self):
        try:
            constr = self._insp.get_check_constraints(table_name = self._tablename, schema = self._schema)
        except NotImplementedError:
            constr = None
        return constr

    @property
    def foreign_keys(self):
        return self._foreign_keys

    def _get_foreign_keys(self):
        try:
            fks = self._insp.get_foreign_keys(table_name = self._tablename, schema = self._schema)
        except NotImplementedError:
            fks = None
        return fks

    @property
    def indexes(self):
        return self._indexes

    def _get_indexes(self):
        try:
            indx = self._insp.get_indexes(table_name = self._tablename, schema = self._schema)
            indxs=[]
            for _x in indx:
                indxs.extend([_x['name'], _x])
        except NotImplementedError:
            indxs = None
        return indxs

    @property
    def pk_constr(self):
        return self._pk_constr

    def _get_pk_constr(self):
        try:
            pk_constr = self._insp.get_pk_constraint(table_name = self._tablename, schema = self._schema)
        except NotImplementedError:
            pk_constr = None
        return pk_constr

    @property
    def uniq_constr(self):
        return self._uniq_constr

    def _get_uniq_constr(self):
        try:
            uniq_constr = self._insp.get_unique_constraints(table_name = self._tablename, schema = self._schema)
        except NotImplementedError:
            uniq_constr = None
        return uniq_constr

    @property
    def table_comment(self):
        return self._table_comment

    def _get_table_comment(self):
        try:
            tab_comment = self._insp.get_table_comment(table_name = self._tablename, schema = self._schema)['text']
        except NotImplementedError:
            tab_comment = None
        return tab_comment

def get_table_metadata(tablename, conn = Constants.DEFAULT_CONN.value):
    """
    function to get the metadata for a given SQL table
    """
    return table_meta(tablename = tablename, conn = conn).as_dict()
