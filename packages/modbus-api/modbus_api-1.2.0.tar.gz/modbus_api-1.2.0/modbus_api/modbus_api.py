"""封装Modbus读写方法."""
import logging
import os
import pathlib
import struct
from logging.handlers import TimedRotatingFileHandler
from typing import Union, List

from modbus_tk import modbus_tcp
from modbus_tk import defines as cst


from modbus_api.exception import PLCConnectError, PLCReadError, PLCWriteError


class ModbusApi:
    """ModbusApi class."""
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"


    def __init__(self, plc_ip: str, port: int = 502, plc_name: str = ""):
        """ModbusApi 构造方法.

        Args:
            plc_ip: plc ip address.
            port: port number.
            plc_name: plc name.
        """
        logging.basicConfig(level=logging.INFO, encoding="UTF-8", format=self.LOG_FORMAT)

        self.plc_ip = plc_ip
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.plc_name = plc_name if plc_name else self.plc_ip

        self.client = modbus_tcp.TcpMaster(host=plc_ip, port=port)
        self._connection_state = False

        self._file_handler = None  # 保存日志的处理器
        self._initial_log_config()

    def _initial_log_config(self) -> None:
        """日志配置."""
        self._create_log_dir()
        self.logger.addHandler(self.file_handler)  # handler_passive 日志保存到统一文件

    @staticmethod
    def _create_log_dir():
        """判断log目录是否存在, 不存在就创建."""
        log_dir = pathlib.Path(f"{os.getcwd()}/log")
        if not log_dir.exists():
            os.mkdir(log_dir)

    @property
    def file_handler(self) -> TimedRotatingFileHandler:
        """设置保存日志的处理器, 每隔 24h 自动生成一个日志文件.

        Returns:
            TimedRotatingFileHandler: 返回 TimedRotatingFileHandler 日志处理器.
        """
        if self._file_handler is None:
            self._file_handler = TimedRotatingFileHandler(
                f"{os.getcwd()}/log/plc_{self.plc_name}.log",
                when="D", interval=1, backupCount=10, encoding="UTF-8"
            )
            self._file_handler.namer = self._custom_log_name
            self._file_handler.setFormatter(logging.Formatter(self.LOG_FORMAT))
        return self._file_handler

    def _custom_log_name(self, log_path: str):
        """自定义新生成的日志名称.

        Args:
            log_path: 原始的日志文件路径.

        Returns:
            str: 新生成的自定义日志文件路径.
        """
        _, suffix, date_str = log_path.split(".")
        new_log_path = f"{os.getcwd()}/log/plc_{self.plc_name}_{date_str}.{suffix}"
        return new_log_path

    @property
    def ip(self):
        """获取plc ip."""
        return self.plc_ip

    @property
    def open_state(self) -> bool:
        """Return the connection state of the PLC.

        Returns:
            bool: True if the connection is open, False otherwise.
        """
        return self._connection_state

    def communication_open(self) -> bool:
        """Open the connection to the PLC.

        Returns:
            bool: True if the connection is open, False otherwise.

        Raises:
            PLCConnectError: If the connection is not open.
        """
        try:
            if not self._connection_state:
                self.client.open()
            self._connection_state = True
            return True
        except Exception as e:
            self.logger.error("Error connecting to PLC: %s", e)
            raise PLCConnectError(f"Error connecting to PLC: {e}") from e

    def communication_close(self):
        """Close the connection to the PLC."""
        if self._connection_state:
            self.client.close()
            self._connection_state = False
            self.logger.info("Closed connection to PLC")

    def read_bool(self, address: int, bit_index: int, save_log=True) -> bool:
        """Read a specific boolean bit from the PLC at a given address.

        Args:
            address: The address to read from.
            bit_index: The index of the bit within the address to read.
            save_log: Whether to save the log or not.

        Returns:
            bool: The value of the specified bit.
        """
        try:
            registers = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=1
            )
            value = (registers[0] & (1 << bit_index)) != 0
            if save_log:
                self.logger.info("读取 bool 地址 %s 值为: %s, bit 位是: %s", address, value, bit_index)
            return value
        except Exception as e:
            self.logger.error("读取保持寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取保持寄存器时出错: {e}") from e

    def read_int(self, address: int, count: int = 1, save_log=True) -> int:
        """Read an integer value from the PLC.
        Args:
            address: The address to read from.
            count: The number of values to read.
            save_log: Whether to save the log or not.

        Returns:
            int: The value read from the PLC.
        """
        try:
            registers = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=count
            )
            if count == 1:
                int_value = registers[0]
            else:
                int_value = registers
            if save_log:
                self.logger.info("读取 int 地址 %s 值为: %s", address, int_value)
            return int_value
        except Exception as e:
            self.logger.error("读取输入寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取输入寄存器时出错: {e}") from e

    def read_str(self, address: int, count: int, save_log=True) -> str:
        """Read a string value from the PLC.

        Args:
            address: The address to read from.
            count: The number of values to read.
            save_log: Whether to save the log or not.

        Returns:
            str: The value read from the PLC.
        """
        try:
            results = self.client.execute(1, cst.READ_HOLDING_REGISTERS, address, quantity_of_x=count)
            byte_data = b"".join(struct.pack(">H", result) for result in results)
            value_str = byte_data.decode("UTF-8").strip("\x00")
            if save_log:
                self.logger.info("读取 str 地址 %s 值为: %s, 长度为: %s", address, value_str, count)
            return value_str
        except Exception as e:
            self.logger.error("读取输入寄存器时出错: %s", str(e))
            raise PLCReadError(f"读取输入寄存器时出错: {e}") from e

    def write_bool(self, address: int, bit_index: int, value: bool, save_log=True) -> None:
        """Write a specific boolean bit to the PLC at a given address.

        Args:
            address: The address to write to.
            bit_index: The index of the bit within the address to write.
            value: The boolean value to write.
            save_log: Whether to save the log or not.
        """
        try:
            coils = self.client.execute(
                slave=1, function_code=cst.READ_HOLDING_REGISTERS, starting_address=address, quantity_of_x=1
            )
            current_value = coils[0]
            if value:
                new_value = current_value | (1 << bit_index)
            else:
                new_value = current_value & ~(1 << bit_index)
            self.client.execute(
                slave=1, function_code=cst.WRITE_SINGLE_REGISTER, starting_address=address, output_value=new_value)
            if save_log:
                self.logger.info("向 bool 地址 %s 写入值 %s, bit 位是: %s", address, value, bit_index)
        except Exception as e:
            self.logger.error("写入保持寄存器时出错: %s", str(e))
            raise PLCWriteError(f"写入保持寄存器时出错: {e}") from e

    def write_int(self, address: int, value: Union[int, List[int]], save_log=True) -> None:
        """Write an integer value to the PLC.

        Args:
            address: The address to write to.
            value: The integer value or list of integer values to write.
            save_log: Whether to save the log or not.
        """
        if isinstance(value, int):
            value = [value]
        try:
            self.client.execute(
                slave=1, function_code=cst.WRITE_MULTIPLE_REGISTERS, starting_address=address, output_value=value
            )
            if save_log:
                self.logger.info("向 int 地址 %s 写入值 %s", address, value)
        except Exception as e:
            self.logger.error("写入输入寄存器时出错: %s", str(e))
            raise PLCWriteError(f"写入输入寄存器时出错: {e}") from e

    # pylint: disable=R0913, R0917
    def execute_read(self, data_type, address, size=1, bit_index=0, save_log=True) -> Union[int, str, bool]:
        """Execute read function based on data_type.

        Args:
            data_type: The data type to read.
            address: The address to read from.
            size: The number of values to read.
            bit_index: The index of the bit within the address to read.
            save_log: Whether to save the log or not.

        Returns:
            Union[int, str, bool]: The value read from the PLC.
        """
        if data_type == "bool":
            return self.read_bool(address, bit_index, save_log)
        if data_type == "int":
            return self.read_int(address, size, save_log)
        if data_type == "str":
            return self.read_str(address, size, save_log)
        raise ValueError(f"Invalid data type: {data_type}")

    # pylint: disable=R0913, R0917
    def execute_write(self, data_type, address, value, bit_index=0, save_log=True):
        """Execute write function based on data_type.

        Args:
            data_type: The data type to write.
            address: The address to write to.
            value: The value to write.
            bit_index: The index of the bit within the address to write.
            save_log: Whether to save the log or not.
        """
        if data_type == "bool":
            self.write_bool(address, bit_index, value, save_log)
        elif data_type == "int":
            self.write_int(address, value, save_log)
        elif data_type == "str":
            pass
        else:
            raise ValueError(f"Invalid data type: {data_type}")
