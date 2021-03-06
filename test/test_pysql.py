#! /usr/bin/env/python
# -*- coding: utf-8 -*-
# cython: language_level=3, always_allow_keywords=True

## Copyright 2014-2019 by LivingLogic AG, Bayreuth/Germany
## Copyright 2014-2019 by Walter Dörwald
##
## All Rights Reserved
##
## See ll/xist/__init__.py for the license


import io, os, tempfile

import cx_Oracle

import pytest

from ll import orasql, pysql


dbname = os.environ.get("LL_ORASQL_TEST_CONNECT") # Need a connectstring as environment var


commands = """
create table pysql_test_table(
	odtt_id integer
);

-- @@@

create or replace procedure pysql_test_procedure(
	p_odtt_id in out integer
)
as
begin
	if p_odtt_id is null then
		p_odtt_id := 1;
	end if;
	insert into pysql_test_table (odtt_id) values (p_odtt_id);
	p_odtt_id := p_odtt_id + 100;
end;
/

-- @@@

{
	"type": "sql",
	"sql":
		"create sequence pysql_test_sequence"
		"	minvalue 10"
		"	maxvalue 9999999999999999999999999999"
		"	start with 30"
		"	increment by 10"
		"	cache 20",
	"comment": "Create the sequence pysql_test_sequence",
}

{
	"type": "procedure",
	"name": "pysql_test_procedure",
	"args": {
		"p_odtt_id": var("odtt_1"),
	},
	"comment": "Call pysql_test_procedure",
}

{
	"type": "procedure",
	"name": "pysql_test_procedure",
	"args": {
		"p_odtt_id": var("odtt_1"),
	},
	"comment": "Call pysql_test_procedure",
}

{
	"type": "resetsequence",
	"sequence": "pysql_test_sequence",
	"table": "pysql_test_table",
	"field": "odtt_id"
}

{
	"type": "sql",
	"sql": "begin :filename_file := 'gurk_file.txt'; end;",
	"args": {
		"filename_file": var("filename_file", str),
	}
}

{
	"type": "sql",
	"sql": "begin :filename_scp := 'gurk_scp.txt'; end;",
	"args": {
		"filename_scp": var("filename_scp", str),
	}
}

{
	"type": "file",
	"name": "{filename_file}",
	"content": b"gurk_file",
	"mode": 0o644,
}

{
	"type": "scp",
	"name": "{filename_scp}",
	"content": b"gurk_scp",
}
"""


def execute_commands(commands, tmpdir):
	with tempfile.NamedTemporaryFile(delete=False) as f:
		tempname = f.name
		f.write(commands.encode("utf-8"))

	try:
		pysql.main([dbname, tempname, "-vfull", "--scpdirectory", tmpdir, "--filedirectory", tmpdir])
	finally:
		os.remove(tempname)


def cleanup():
	with orasql.connect(dbname) as db:
		c = db.cursor()
		try:
			c.execute("drop table pysql_test_table")
		except cx_Oracle.DatabaseError:
			pass
		try:
			c.execute("drop sequence pysql_test_sequence")
		except cx_Oracle.DatabaseError:
			pass


@pytest.mark.db
def test_pysql(tmpdir):
	cleanup()

	execute_commands(commands, f"{tmpdir}/")

	with orasql.connect(dbname) as db:
		c = db.cursor()
		c.execute("select odtt_id from pysql_test_table order by odtt_id")
		data = [int(r.odtt_id) for r in c]
		assert data == [1, 101]
		c.execute("select pysql_test_sequence.nextval as nv from dual")
		data = c.fetchone().nv
		assert data == 111

	f = tmpdir.join("gurk_file.txt")
	assert f.read() == "gurk_file"
	stat = os.stat(str(f))
	assert stat.st_mode & 0o777 == 0o644

	f2 = tmpdir.join("gurk_scp.txt")
	assert f2.read() == "gurk_scp"

	cleanup()
