@echo off
type db_tables.sql > db.sql
echo. >> db.sql
type proc_train_2stations2.sql >> db.sql
echo. >> db.sql
type query_train_id.sql >> db.sql
echo. >> db.sql
type db_insert_data.sql >> db.sql