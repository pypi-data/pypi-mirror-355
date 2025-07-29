from loguru import logger

try:
    from TypeConversion import res  # 调用公共类，输入模块
    from TypeConversion import invoke
    from TypeConversion import invoke_enum
    logger.debug(f"res: {res}")
except Exception as error:
    logger.error(f"导入公共输入类失败: {error}")
    raise error