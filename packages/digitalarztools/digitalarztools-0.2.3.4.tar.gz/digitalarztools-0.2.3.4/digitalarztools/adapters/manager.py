import traceback
from contextlib import contextmanager
from typing import Union, List, Any, Generator, Optional
from urllib import parse

import pandas as pd
import geopandas as gpd
from dotenv import load_dotenv
from pydantic import BaseModel
from shapely import wkb, wkt
from sqlalchemy import Engine, create_engine, Select, text, MetaData, Table, Column, Integer, String, inspect, func, \
    select, QueuePool
from sqlalchemy.exc import SQLAlchemyError, NoSuchTableError
from sqlalchemy.orm import sessionmaker, Session, joinedload, DeclarativeMeta
from geoalchemy2 import WKBElement

load_dotenv()
import logging

logging.disable(logging.WARNING)


class DBString(BaseModel):
    """
    Represents database connection string parameters.
    """
    host: str
    user: str
    password: str
    name: str
    port: str


"""
Usage: 
   DATABASES = {
        "cache_db": {
            "engine": "sqlite",
            "file_path": os.path.join(BASE_DIR, "dch_cache.sqlite")
        },
        "default": {
            "engine": "postgresql+pg8000",
            "host": os.environ.get("DB_HOST") if not IS_LOCAL else localhost,
            "name": os.environ.get("DCH_DB"),
            "port": os.environ.get("DB_PORT"),
            "user": os.environ.get("DB_USER"),
            "password": os.environ.get("DB_PASSWORD")
        },
    }
    config = DBParams( DATABASES['default']['engine'], DATABASES['default'])
    engine = DBManager.create_sql_alchemy_engine(config)
    manager = DBManager(engine)
    with manager.managed_session() as session:
        result = session.execute(text("SELECT * FROM dafastmap_dch.public.dch_map_info"))
        rows = result.fetchall()  # Fetch all rows
         print(len(rows))  # Count of rows
"""


class DBParams:
    """
    Encapsulates database connection parameters and engine type.
    """
    engine_name: str  # postgresql, sqlite
    con_str: DBString  # either provide file_path or DBString

    def __init__(self, engine_name: str, con_str: Union[dict, DBString]):
        """
        Initialize DBParams.

        :param engine_name: Database engine type (e.g., 'postgresql', 'sqlite').
        :param con_str: Connection string parameters, either a file path for SQLite
                        or a DBString object/dictionary for other databases.
        """
        self.engine_name = engine_name

        if engine_name == "sqlite":
            self.con_str = con_str.get("file_path") if isinstance(con_str, dict) else con_str
        else:
            self.con_str = DBString(**con_str) if isinstance(con_str, dict) else con_str
            # self.con_str = DBString(**con_str) if isinstance(con_str, dict) else con_str

    def __eq__(self, other):
        """
        Compare two DBString objects for equality based on their attributes.
        """
        if not isinstance(other, DBString):
            return False
        return (self.con_str.user == other.con_str.user and
                self.con_str.password == other.con_str.password and
                self.con_str.host == other.con_str.host and
                self.con_str.port == other.con_str.port and
                self.con_str.name == other.con_str.name)


class DBManager:
    """
    Manages database connections and provides methods for interacting with the database.
    """

    engine: Engine = None
    db_name: str = None

    def __init__(self, db_info: Union[DBParams, Engine]):
        """
        Initialize DBManager.

        :param db_info: Either DBParams to create a new engine or an existing Engine.
        """
        if isinstance(db_info, Engine):
            self.engine = db_info
        else:
            self.create_sql_alchemy_engine(db_info)
        self.db_name = self.engine.url.database
        if self.engine is None:
            raise Exception("Failed to create SQL Alchemy engine")

    def get_engine(self) -> Engine:
        """
        Return the SQLAlchemy Engine associated with this manager.
        """
        return self.engine

    def get_session(self) -> Session:
        """
        Create and return a new SQLAlchemy session from the session factory.
        """
        session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)()
        self.terminate_idle_connections(1, session)
        return session

    @contextmanager
    def managed_session(self, session: Optional[Session] = None) -> Generator[Session, None, None]:
        """
        Smart session manager:
        - If session is passed, yields it without managing (no commit/rollback/close).
        - If session is None, manages the session (commit, rollback, close).
        """
        if session is not None:
            yield session
        else:
            new_session = self.get_session()
            try:
                yield new_session
                new_session.commit()
            except Exception as e:
                new_session.rollback()
                print(f"Session rolled back due to an exception: {e}")
                raise
            finally:
                new_session.close()

    def create_sql_alchemy_engine(self, config: DBParams):
        """
        Create a SQLAlchemy engine with connection pooling and timeout settings.

        This method now reuses an existing engine if one has already been created.
        """
        # if DBManager.engine is not None and DBManager.engine.url.database == config.con_str.name:
        #     return DBManager.engine
        try:
            if config.engine_name in ["sqlite"]:
                db_string = f'{config.engine_name}:///{config.con_str}'
            else:
                params = config.con_str
                db_string = f'{config.engine_name}://{params.user}:{parse.quote(params.password)}@{params.host}:{params.port}/{params.name}'

            self.engine = create_engine(  # Store the engine at the class level
                db_string,
                echo=False,  # Set to False in production
                poolclass=QueuePool,
                pool_size=10,  # Number of connections to keep open inside the pool
                max_overflow=5,  # Allow 10 extra connections if pool is full
                pool_timeout=30,  # Wait time before raising an error if pool is full
                pool_recycle=1200,  # Recycle connections every 30 minutes (to prevent stale connections)
                pool_pre_ping=True,  # Check connections before use
                # connect_args={'connect_timeout': 100}
            )
            # return self.engine
        except Exception as e:
            traceback.print_exc()
            # return None
        # else:
        #     return DBManager.engine  # Return the existing engine

    @staticmethod
    def create_postgres_engine(db_str: Union[DBString, dict]) -> Engine:
        """
        Create a PostgreSQL engine.
        """
        if isinstance(db_str, dict):
            db_str = DBString(**db_str)
        params = DBParams(engine_name='postgresql+psycopg2', con_str=db_str)
        return DBManager(params).get_engine()

    def exists(self, stmt: Select):
        """
        Check if a row exists based on the given SELECT statement.
        """
        with self.managed_session() as session:
            return session.execute(stmt).first() is not None

    def get_sqlalchemy_table(self, table_name, schema_name='public') -> Table:
        """
        Get a SQLAlchemy Table object, correctly handling schema-qualified names like 'public.table_name'.
        """
        try:
            # Handle schema-qualified table names
            if '.' in table_name:
                parts = table_name.split('.')
                schema_name = parts[0]
                table_name = parts[1]

            metadata = MetaData()

            try:
                tbl = Table(
                    table_name,
                    metadata,
                    autoload_with=self.engine,
                    schema=schema_name
                )
            except NoSuchTableError:
                # optionally log here
                return None
            return tbl
        except Exception:
            traceback.print_exc()
            return None

    def execute_query_as_one(self, query: Union[str, Select], session: Optional[Session] = None) -> Any:
        """
        Execute a query and return a single row.
        """
        try:
            with self.managed_session(session=session) as session:
                if isinstance(query, str):
                    query_obj = text(query)
                    row = session.execute(query_obj).mappings().first()
                    result = dict(row) if row else None
                else:
                    query_obj = query.options(joinedload('*'))
                    obj = session.execute(query_obj).scalars().first()
                    result = {k: v for k, v in obj.__dict__.items() if not k.startswith('_')} if obj else None
                return result
        except SQLAlchemyError as e:
            print(f"Error executing query: {e}")
            traceback.print_exc()
            return None

    def execute_stmt_as_df(
            self,
            stmt: Union[str, Select, Table],
            session: Optional[Session] = None,
            model: Optional[DeclarativeMeta] = None,
            enum_columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Execute a SQLAlchemy statement and return the results as a pandas DataFrame.

        Parameters:
        -----------
        stmt : Union[str, Select, Table]
            The SQL query to execute. Can be a raw SQL string, a SQLAlchemy Select object, or a Table.
        session : Optional[Session]
            SQLAlchemy Session object. If not provided, a managed session will be created.
        model : Optional[DeclarativeMeta]
            The ORM model class associated with the query.
            Purpose:
                - If provided, we introspect the model to detect nullable integer columns.
                - This allows us to automatically convert these columns to pandas 'Int64' dtype
                  (nullable integer type) instead of defaulting to float64 when NULL values exist.
                - This avoids common serialization issues (e.g. NaN values) when returning DataFrames as JSON.
        enum_columns : Optional[List[str]]
            List of column names which are Enum fields in the model like ChoiceType
                accessibility_type = Column(ChoiceType(AccessibilityType.choices()), nullable=True)
                class AccessibilityType(APIEnum):
                    File = 'File'
                    DB = 'Database'
                    D_DB = 'Django Database Key'
                    URL = 'url'

                class APIEnum(Enum):
                    @classmethod
                    def choices(cls):
                        return [(key.name, key.value) for key in cls]
            Purpose:
                - SQLAlchemy often returns enum values as Enum instances.
                - This parameter allows us to automatically extract `.value` from Enum fields,
                  so that DataFrame columns contain plain values (e.g., string or int) instead of Enum objects.

        Returns:
        --------
        pd.DataFrame
            Query results as a pandas DataFrame, with appropriate type conversions applied.
        """
        try:
            with self.managed_session(session) as session:
                # Execute the provided statement according to its type
                if isinstance(stmt, Select):
                    rs = session.execute(stmt)
                elif isinstance(stmt, Table):
                    stmt = select(stmt)
                    rs = session.execute(stmt)
                else:  # raw SQL string
                    rs = session.execute(text(stmt))

                # Convert result set to pandas DataFrame
                df = pd.DataFrame(rs.fetchall())
                if not df.empty:
                    df.columns = rs.keys()

                    # Handle Enum columns if specified
                    if enum_columns:
                        for col in enum_columns:
                            if col in df.columns:
                                df[col] = df[col].apply(
                                    lambda x: [v.value if hasattr(v, 'value') else v for v in x] if isinstance(x, list)
                                    else x.value if hasattr(x, 'value') else x
                                )

                    # Introspect model to handle nullable integer columns
                    if model:
                        for col in model.__table__.columns:
                            if isinstance(col.type, Integer) and col.nullable:
                                if col.name in df.columns:
                                    df[col.name] = df[col.name].astype("Int64")

                return df

        except SQLAlchemyError as e:
            print(f"Error executing statement: {e}")
            return pd.DataFrame()

    def get_query_data(self, query: Union[Table, Select, str], external_session=None) -> Any:
        """
        Execute a query and return the results as a list of dictionaries.
        """
        try:
            with self.managed_session(external_session) as session:
                if isinstance(query, Table):
                    qs = session.query(query)
                    return qs.all()
                elif isinstance(query, Select):
                    rs = session.execute(query)
                    return rs.fetchall()
                else:
                    rs = session.execute(text(query))
                    return rs.fetchall()
        except SQLAlchemyError as e:
            print(f"Error executing query: {e}")
            return []

    def execute_dml(self, stmt, session: Optional[Session] = None):
        """
        Execute a DML statement (INSERT, UPDATE, DELETE).
        """
        try:
            with self.managed_session(session) as session:
                if isinstance(stmt, str):
                    stmt = text(stmt)
                session.execute(stmt)
                session.commit()
                return True
        except SQLAlchemyError:
            traceback.print_exc()
            return False

    def execute_ddl(self, stmt):
        """
        Execute a DDL statement (CREATE, ALTER, DROP).
        """
        try:
            with self.managed_session() as session:
                if isinstance(stmt, str):
                    stmt = text(stmt)
                session.execute(stmt)
                session.commit()
                print("DDL performed successfully")
                return True
        except Exception as e:
            traceback.print_exc()
            return False

    def table_to_df(self, tbl: Union[Table, str, Select]):
        """
        Convert a table or SELECT statement results to a Pandas DataFrame.
        """
        if isinstance(tbl, str):
            tbl = self.get_sqlalchemy_table(tbl)
        data = self.get_query_data(tbl)
        return pd.DataFrame(data)

    def get_tables(self):
        """
        Get all tables in the database.
        """
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        return list(metadata.tables.values())

    def get_tables_names(self):
        """
        Get names of all tables in the database.
        """
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        return list(metadata.tables.keys())

    @staticmethod
    def get_table_column_names(table: Table) -> list:
        """
        Get column names of a table.
        """
        if table is not None:
            return [col.name for col in inspect(table).columns]

    @staticmethod
    def get_table_column_types(table: Table) -> list:
        """
        Get column types of a table.
        """
        if table is not None:
            return [col.type for col in inspect(table).columns]

    def inspect_related_models(self, table_name: str, schema: str = "public", visited=None):
        """
        Recursively inspects and prints models for a table and its foreign key dependencies.
        """
        if visited is None:
            visited = set()

        # Normalize input in case "public.table" is passed as table_name
        if "." in table_name:
            parts = table_name.split(".")
            schema = parts[0]
            table_name = parts[1]

        key = f"{schema}.{table_name}".lower()
        if key in visited:
            return

        visited.add(key)

        tbl = self.get_sqlalchemy_table(table_name=table_name, schema_name=schema)
        if tbl is None:
            return

        # Recursively inspect referenced tables (foreign key dependencies)
        for column in tbl.columns:
            for fk in column.foreign_keys:
                ref_table = fk.column.table.name
                ref_schema = fk.column.table.schema or schema  # If missing, assume current
                self.inspect_related_models(ref_table, ref_schema, visited)

        # After all dependencies, print the model
        print("# --------------------------------------------")
        self.inspect_table(table_name=table_name, schema=schema, visited=visited)

    def inspect_table(self, table_name: str, schema: str = 'public', visited=None):
        """
        Inspects a table and prints a SQLAlchemy model class definition.
        Assumes SQLAlchemy is imported as 'db'.
        """
        self.inspect_related_models(table_name, schema, visited)
        parts = table_name.split(".")
        schema_name = parts[0] if len(parts) > 1 else schema
        actual_table_name = parts[-1]

        tbl = self.get_sqlalchemy_table(actual_table_name, schema_name)
        if tbl is None:
            print(f"Table '{schema_name}.{actual_table_name}' not found.")
            return

        class_name = actual_table_name.title().replace("_", "")
        print(f"class {class_name}(DBBase):")
        print(f'    __tablename__ = "{actual_table_name}"')
        if schema_name != "public":
            print(f'    __table_args__ = {{"schema": "{schema_name}"}}')
        print("")

        for column in tbl.columns:
            col_args = []

            # Column type
            col_type = f"db.{str(column.type).split('(')[0].strip().replace(' ', '_')}"
            col_args.append(col_type)

            # ForeignKey
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    ref_table = fk.column.table.name
                    ref_column = fk.column.name
                    col_args.append(f"db.ForeignKey('{ref_table}.{ref_column}')")
                    break  # Assume one FK per column

            # Primary Key
            if column.primary_key:
                col_args.append("primary_key=True")

            # Nullable
            if not column.nullable:
                col_args.append("nullable=False")

            # Unique
            if column.unique:
                col_args.append("unique=True")

            # Default value
            if column.default is not None:
                try:
                    default_val = column.default.arg if hasattr(column.default, "arg") else column.default
                    col_args.append(f"default={repr(default_val)}")
                except Exception:
                    pass

            # Server default (from DB, like now())
            if column.server_default is not None:
                try:
                    col_args.append(f"server_default=db.text({repr(str(column.server_default.arg))})")
                except Exception:
                    pass

            # Comment as inline comment
            if column.comment:
                print(f"    # {column.name}: {column.comment}")

            # Final Column() line
            col_line = f"    {column.name} = db.Column({', '.join(col_args)})"
            print(col_line)

        # ✅ Correctly placed after column definitions
        relationships_printed = set()
        for column in tbl.columns:
            for fk in column.foreign_keys:
                ref_table = fk.column.table.name
                rel_name = ref_table.lower()
                if rel_name not in relationships_printed:
                    print(f"    {rel_name} = relationship('{ref_table.title().replace('_', '')}')")
                    relationships_printed.add(rel_name)

        print("")

    def is_table(self, table_name):
        """
        Check if a table exists.
        """
        inspector = inspect(self.engine)
        return table_name in inspector.get_table_names()

    def con_2_dict(self):
        """
        Convert connection parameters to a dictionary.
        """
        engine = self.get_engine()
        return {
            'engine': engine.url.drivername,
            'host': engine.url.host,
            'port': engine.url.port,
            "user": engine.url.username,
            "password": engine.url.password,
            "db_name": engine.url.database
        }

    def execute_query_as_dict(self, query: Union[str, Select]) -> List[dict]:
        """
        Execute a query and return the results as a list of dictionaries.
        """
        df = self.execute_stmt_as_df(query)
        return df.to_dict(orient='records')

    def get_missing_dates(self, table_name: str, date_col_name: str, start_date: str, end_date: str,
                          id_col_name: str = None, id_col_value: str = None) -> pd.DataFrame:
        """
        Find missing dates in a date column within a specified range.

        :param table_name: Name of the table.
        :param date_col_name: Name of the date column.
        :param start_date: Start date in YYYY-MM-DD format.
        :param end_date: End date in YYYY-MM-DD format.
        :param id_col_name: Optional ID column name for filtering.
        :param id_col_value: Optional ID column value for filtering.
        :return: DataFrame containing the missing dates.
        """
        try:
            id_con = f"{id_col_name} = '{id_col_value}' AND " if id_col_name is not None else ""
            query = (f"WITH date_series AS ( "
                     f"SELECT generate_series('{start_date}'::date, '{end_date}'::date,'1 day'::interval) AS date),"
                     f"filtered_basin_data AS( SELECT {date_col_name} FROM {table_name} WHERE {id_con} "
                     f"{date_col_name} BETWEEN '{start_date}' AND '{end_date}')")
            query += (f"SELECT ds.date as dates FROM date_series ds LEFT JOIN filtered_basin_data fbd "
                      f"ON ds.date = fbd.{date_col_name} WHERE fbd.{date_col_name} IS NULL ORDER BY ds.date")
            df = self.execute_stmt_as_df(query)
            return df
        except:
            return pd.DataFrame()

    async def monitor_pg_connections(self, idle_cutoff_minutes: int = 3, terminate_idle: bool = True):
        """
        Asynchronously monitor and optionally clean up idle PostgreSQL connections for this DBManager instance.
        """
        if "sqlite" in self.engine.url.drivername:
            return  # Skip non-PostgreSQL databases

        try:
            with self.managed_session() as session:
                print(f"\n📡 Monitoring DB: {self.db_name}")

                count_rs = session.execute(text("SELECT COUNT(*) FROM pg_stat_activity")).scalar()
                print(f"🧮 Active connections: {count_rs}")

            if terminate_idle:
                terminated = self.terminate_idle_connections(self.db_name, idle_cutoff_minutes)
                if terminated > 0:
                    print(f"💀 Terminated {terminated} idle connections")

        except Exception as e:
            print(f"❌ Error monitoring DB {self.db_name}: {e}")

    def terminate_idle_connections(self, idle_cutoff_minutes: int = 1, session: Session = None) -> int:
        """
        Terminates idle PostgreSQL connections idle for more than the specified number of minutes.
        """
        external_session = session is not None
        if not external_session:
            session = self.get_session()

        try:
            if self.engine.url.drivername.startswith("postgresql"):
                kill_stmt = text("""
                                 SELECT pg_terminate_backend(pid)
                                 FROM pg_stat_activity
                                 WHERE state = 'idle'
                                   AND state_change < now() - (:minutes || ' minutes')::interval
                      AND pid <> pg_backend_pid()
                      AND datname = :db_name;
                                 """)
                result = session.execute(kill_stmt, {'minutes': str(idle_cutoff_minutes), 'db_name': self.db_name})
                if not external_session:
                    session.commit()
                return result.rowcount
            return 0
        finally:
            if not external_session:
                session.close()


class GeoDBManager(DBManager):
    @staticmethod
    def get_geometry_cols(table: Table) -> list:
        geom_cols = [col for col in list(table.columns) if 'geometry' in str(col.type)]
        return geom_cols

    async def get_tile_envelop(self, x, y, z) -> gpd.GeoDataFrame:
        query = f"SELECT ST_AsText( ST_TileEnvelope({z}, {x}, {y})) as envelope;"
        res = await self.execute_query_as_one(query)
        polygon = wkt.loads(res['envelope'])
        # gdf = gpd.GeoDataFrame({"geometry": [polygon]}, geometry='geometry', crs='EPSG:3857')
        return polygon

    def get_geom_col_srid(self, tbl, geom_col):
        try:
            with self.managed_session() as session:
                res = session.query(func.ST_SRID(tbl.c[geom_col.name])).first()
                return res[0] if len(res) > 0 else geom_col.type.srid if geom_col.type.srid != -1 else 0
        except Exception as e:
            srid = geom_col.type.srid if geom_col.type.srid != -1 else 0
            return srid

    @staticmethod
    def data_to_gdf(data, geom_col, srid=0, is_wkb=True):
        # data = list(data)
        # data = [row for row in data]
        if len(data) > 0:
            gdf = gpd.GeoDataFrame(data)
            # gdf = gdf.dropna(axis=0)
            if is_wkb:
                gdf["geom"] = gdf[geom_col].apply(
                    lambda x: wkb.loads(bytes(x.data)) if isinstance(x, WKBElement) else wkb.loads(x, hex=True))
            else:
                gdf["geom"] = gdf[geom_col].apply(lambda x: wkt.loads(str(x)))
            if geom_col != "geom":
                gdf = gdf.drop(geom_col, axis=1)
            gdf = gdf.set_geometry("geom")
            if srid != 0:
                gdf.crs = srid
            return gdf
        else:
            return gpd.GeoDataFrame()

    def table_to_gdf(self, tbl: Union[Table, str], geom_col_name="geom", limit=-1):
        if isinstance(tbl, str):
            tbl = self.get_sqlalchemy_table(tbl)
        geom_cols = self.get_geometry_cols(tbl)
        # data = self.get_all_data(tbl, limit)
        query = Select(tbl)
        data = self.get_query_data(query)
        geom_col = geom_cols[0]
        srid = self.get_geom_col_srid(tbl, geom_col)
        # geom_col_name = geom_col.name
        return self.data_to_gdf(data, geom_col_name, srid)

    def execute_query_as_gdf(self, query, srid, geom_col='geom', is_wkb=True, session: Optional[Session] = None):
        data = self.get_query_data(query, session)
        if data and len(data) > 0:
            return self.data_to_gdf(data, geom_col, srid, is_wkb)
        return gpd.GeoDataFrame()

    def get_spatial_table_names(self, schema=None) -> list:
        inspector = inspect(self.engine)
        # schema = 'public'
        table_names = []
        # table_names = inspector.get_table_names(schema=schema) + inspector.get_view_names(
        #     schema=schema) + inspector.get_materialized_view_names(schema=schema)
        for table_name in inspector.get_table_names(schema=schema):
            try:
                table = self.get_sqlalchemy_table(table_name)
                if table is not None:
                    geom_cols = self.get_geometry_cols(table)
                    if len(geom_cols) > 0:
                        table_names.append(table_name)
            except Exception as e:
                print("error in getting table", table_name)
        return table_names

    def create_xyz_cache_table(self, table_name: str):
        """
        Create a table for XYZ cache data.
        """
        meta_data = MetaData()
        xyz_table = Table(table_name, meta_data,
                          Column('id', Integer, primary_key=True, autoincrement=True),
                          Column('x', Integer),
                          Column('y', Integer),
                          Column('z', Integer),
                          Column('mvt', String))
        meta_data.create_all(self.engine)
        print(f"Table '{table_name}' created.")
        return xyz_table

    def delete_xyz_cache_table(self, table_name: str):
        """
        Drop the specified XYZ cache table.
        """
        meta_data = MetaData()
        xyz_table = Table(table_name, meta_data, autoload_with=self.engine)
        xyz_table.drop(self.engine, checkfirst=True)
        print(f"Table '{table_name}' deleted.")
