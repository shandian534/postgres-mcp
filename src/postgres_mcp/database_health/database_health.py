from __future__ import annotations

import logging
from enum import Enum
from typing import List

import mcp.types as types

from .buffer_health_calc import BufferHealthCalc
from .connection_health_calc import ConnectionHealthCalc
from .constraint_health_calc import ConstraintHealthCalc
from .index_health_calc import IndexHealthCalc
from .replication_calc import ReplicationCalc
from .sequence_health_calc import SequenceHealthCalc
from .vacuum_health_calc import VacuumHealthCalc

ResponseType = List[types.TextContent | types.ImageContent | types.EmbeddedResource]

logger = logging.getLogger(__name__)


class HealthType(str, Enum):
    INDEX = "index"
    CONNECTION = "connection"
    VACUUM = "vacuum"
    SEQUENCE = "sequence"
    REPLICATION = "replication"
    BUFFER = "buffer"
    CONSTRAINT = "constraint"
    ALL = "all"


class DatabaseHealthTool:
    """Tool for analyzing database health metrics."""
    '''
    def __init__(self, sql_driver):
__init__ 是 Python 类中的特殊方法，也被称为构造函数。当创建类的实例时，__init__ 方法会自动调用，用于初始化对象的属性。
self 是类方法的第一个参数，代表类的实例本身。在调用类方法时，Python 会自动将实例作为 self 参数传递给方法。
sql_driver 是 __init__ 方法的参数，它是一个外部传入的值，代表 SQL 驱动对象，用于后续与数据库进行交互。
    '''
    def __init__(self, sql_driver):
        self.sql_driver = sql_driver

    async def health(self, health_type: str) -> str:
        """Run database health checks for the specified components.

        Args:
            health_type: Comma-separated list of health check types to perform
                         Valid values: index, connection, vacuum, sequence, replication, buffer, constraint, all

        Returns:
            A string with the health check results
        """
        try:
            result = ""
            try:
                #这是集合推导式，是一种简洁创建集合的语法。它会遍历 health_type.split(",") 返回列表中的每个元素 x，对 x 进行 strip 处理后转换为 HealthType 枚举实例，再将这些实例添加到集合中。由于集合的特性是元素唯一，所以重复的枚举实例会被自动去重。
                health_types = {HealthType(x.strip()) for x in health_type.split(",")}
            except ValueError:
                return (
                    f"Invalid health types provided: '{health_type}'. "
                    + f"Valid values are: {', '.join(sorted([t.value for t in HealthType]))}. "
                    + "Please try again with a comma-separated list of valid health types."
                )

            #HealthType 是代码中定义的枚举类，for t in HealthType 会遍历 HealthType 枚举类中的所有枚举成员。
            #这是列表推导式中的条件判断部分，它会过滤掉 HealthType.ALL 这个枚举成员。也就是说，只有当 t 不等于 HealthType.ALL 时，才会执行后续的操作。
            if HealthType.ALL in health_types:
                health_types = [t.value for t in HealthType if t != HealthType.ALL]

            if HealthType.INDEX in health_types:
                index_health = IndexHealthCalc(self.sql_driver)
                result += "Invalid index check: " + await index_health.invalid_index_check() + "\n"
                result += "Duplicate index check: " + await index_health.duplicate_index_check() + "\n"
                result += "Index bloat: " + await index_health.index_bloat() + "\n"
                result += "Unused index check: " + await index_health.unused_indexes() + "\n"

            if HealthType.CONNECTION in health_types:
                connection_health = ConnectionHealthCalc(self.sql_driver)
                result += "Connection health: " + await connection_health.connection_health_check() + "\n"

            if HealthType.VACUUM in health_types:
                vacuum_health = VacuumHealthCalc(self.sql_driver)
                result += "Vacuum health: " + await vacuum_health.transaction_id_danger_check() + "\n"

            if HealthType.SEQUENCE in health_types:
                sequence_health = SequenceHealthCalc(self.sql_driver)
                result += "Sequence health: " + await sequence_health.sequence_danger_check() + "\n"

            if HealthType.REPLICATION in health_types:
                replication_health = ReplicationCalc(self.sql_driver)
                result += "Replication health: " + await replication_health.replication_health_check() + "\n"

            if HealthType.BUFFER in health_types:
                buffer_health = BufferHealthCalc(self.sql_driver)
                result += "Buffer health for indexes: " + await buffer_health.index_hit_rate() + "\n"
                result += "Buffer health for tables: " + await buffer_health.table_hit_rate() + "\n"

            if HealthType.CONSTRAINT in health_types:
                constraint_health = ConstraintHealthCalc(self.sql_driver)
                result += "Constraint health: " + await constraint_health.invalid_constraints_check() + "\n"

            return result if result else "No health checks were performed."
        except Exception as e:
            logger.error(f"Error calculating database health: {e}", exc_info=True)
            return f"Error calculating database health: {e}"
