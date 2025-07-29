from __future__ import annotations
from typing import Any, Optional, ClassVar, Generator, Type
import threading
from contextlib import contextmanager
from pydantic import BaseModel, field_validator, ValidationError, model_validator
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import url as sqlalchemy_url
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool, NullPool, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from sibi_dst.utils import Logger
from ._sql_model_builder import SqlAlchemyModelBuilder


class SqlAlchemyConnectionConfig(BaseModel):
    """
    Thread-safe, registry-backed SQLAlchemy connection manager with:
      - Shared engine reuse
      - Active connection tracking
      - Idle-pool and database-level cleanup
      - Dynamic ORM model building via SqlAlchemyModelBuilder
      - Optional session factory
    """
    connection_url: str
    table: Optional[str] = None
    model: Optional[Any] = None
    engine: Optional[Engine] = None
    logger: Logger = None
    debug: bool = False

    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 300
    pool_pre_ping: bool = True
    poolclass: Type = QueuePool

    session_factory: Optional[sessionmaker] = None
    _owns_engine: bool = False

    _engine_registry: ClassVar[dict[tuple, Engine]] = {}
    _registry_lock: ClassVar[threading.Lock] = threading.Lock()
    _active_connections: ClassVar[int] = 0

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    @field_validator("pool_size", "max_overflow", "pool_timeout", "pool_recycle")
    @classmethod
    def _validate_pool_params(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Pool parameters must be non-negative")
        return v

    @model_validator(mode="after")
    def _init_all(self) -> SqlAlchemyConnectionConfig:
        self._init_logger()
        self._init_engine()
        self._validate_conn()
        self._build_model()
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        return self

    def _init_logger(self) -> None:
        self.logger = self.logger or Logger.default_logger(logger_name=self.__class__.__name__)
        self.logger.set_level(Logger.DEBUG if self.debug else Logger.INFO)

    def _engine_key(self) -> tuple:
        parsed = sqlalchemy_url.make_url(self.connection_url)
        query = {k: v for k, v in parsed.query.items() if not k.startswith("pool_")}
        normalized = parsed.set(query=query)
        key = [str(normalized)]
        if self.poolclass not in (NullPool, StaticPool):
            key += [self.pool_size, self.max_overflow, self.pool_timeout, self.pool_recycle, self.pool_pre_ping, self.table]
        return tuple(key)

    def _init_engine(self) -> None:
        key = self._engine_key()
        with self._registry_lock:
            existing = self._engine_registry.get(key)
            if existing:
                self.engine = existing
                self._owns_engine = False
                self.logger.debug(f"Reusing engine {key}")
            else:
                self.logger.debug(f"Creating engine {key}")
                self.engine = create_engine(
                    self.connection_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_timeout=self.pool_timeout,
                    pool_recycle=self.pool_recycle,
                    pool_pre_ping=self.pool_pre_ping,
                    poolclass=self.poolclass,
                )
                self._attach_events()
                self._engine_registry[key] = self.engine
                self._owns_engine = True

    def _attach_events(self) -> None:
        event.listen(self.engine, "checkout", self._on_checkout)
        event.listen(self.engine, "checkin", self._on_checkin)

    def _on_checkout(self, *args) -> None:
        with self._registry_lock:
            type(self)._active_connections += 1
        self.logger.debug(f"Checked out, active: {self.active_connections}")

    def _on_checkin(self, *args) -> None:
        with self._registry_lock:
            type(self)._active_connections = max(type(self)._active_connections - 1, 0)
        self.logger.debug(f"Checked in, active: {self.active_connections}")

    @property
    def active_connections(self) -> int:
        return type(self)._active_connections

    def _validate_conn(self) -> None:
        try:
            with self.managed_connection() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.debug("Connection OK")
        except OperationalError as e:
            self.logger.error(f"Connection failed: {e}")
            raise ValidationError(f"DB connection failed: {e}")

    @contextmanager
    def managed_connection(self) -> Generator[Any, None, Any]:
        conn = self.engine.connect()
        try:
            yield conn
        finally:
            conn.close()

    def get_session(self) -> Session:
        if not self.session_factory:
            raise RuntimeError("Session factory not initialized")
        return self.session_factory()

    def _build_model(self) -> None:
        """Dynamically build and assign the ORM model if table is set"""
        if not self.table or not self.engine:
            return
        try:
            builder = SqlAlchemyModelBuilder(self.engine, self.table)
            self.model = builder.build_model()
            self.logger.debug(f"Model built for table: {self.table}")
        except Exception as e:
            self.logger.error(f"Model build failed: {e}")
            raise ValidationError(f"Model construction error: {e}") from e

    def dispose_idle_connections(self) -> int:
        key = self._engine_key()
        with self._registry_lock:
            if self._engine_registry.get(key) is not self.engine:
                self.logger.debug("Engine changed")
                return 0
            pool = self.engine.pool
            if isinstance(pool, QueuePool):
                count = pool.checkedin()
                pool.dispose()
                self.logger.debug(f"Disposed {count}")
                return count
            self.logger.warning(f"No idle dispose for {type(pool).__name__}")
            return 0

    def terminate_idle_connections(self, idle_seconds: int = 300) -> int:
        terminated = 0
        dialect = self.engine.dialect.name
        with self.managed_connection() as conn:
            if dialect == 'postgresql':
                res = conn.execute(text(
                    f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    f"WHERE state='idle' AND (now() - query_start) > interval '{idle_seconds} seconds' "
                    f"AND pid<>pg_backend_pid()"
                ))
                terminated = res.rowcount
            elif dialect == 'mysql':
                for row in conn.execute(text("SHOW PROCESSLIST")):
                    if row.Command == 'Sleep' and row.Time > idle_seconds:
                        conn.execute(text(f"KILL {row.Id}"))
                        terminated += 1
            else:
                self.logger.warning(f"Idle termination not supported: {dialect}")
        self.logger.debug(f"Terminated {terminated}")
        return terminated

    def close(self) -> None:
        with self._registry_lock:
            key = self._engine_key()
            if not self._owns_engine:
                self.logger.debug("Not owner, skipping close")
                return
            if self._engine_registry.get(key) != self.engine:
                self.logger.debug("Engine not in registry")
                return
            self.engine.dispose()
            del self._engine_registry[key]
            type(self)._active_connections = 0
            self.logger.debug(f"Engine closed {key}")
