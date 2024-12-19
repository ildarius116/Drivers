import logging

import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, Text, select, Boolean, BOOLEAN
from sqlalchemy.orm import sessionmaker, declarative_base, Query

engine = create_engine("sqlite:///proxy_database.db")
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

logger = logging.getLogger(__name__)


class Analyzes(Base):
    """
    Класс для создания буферной базы (таблицы) для временного хранения результатов анализов.

    Params:
        id - идентификатор анализа в БД
        analyzer - название анализатора
        device_id - номер анализатор
        probe_results - прямые данные принятые от анализатора преобразованные в список в виде строки
        tries - количество попыток отправить результат
        error_text - текст ошибки отправки результата
    """
    __tablename__: str = 'probes'

    id = Column(Integer, primary_key=True)
    analyzer = Column(Text, nullable=True)
    device_id = Column(Text, nullable=True)
    probe_results = Column(Text, nullable=True)
    ready_status = Column(Text, default="False")
    lines_list = Column(Text, nullable=True)
    raw_line = Column(Text, nullable=True)
    message_id = Column(Text, nullable=True)
    tries = Column(Integer, nullable=True)
    error_text = Column(Text, nullable=True)
    work_list = Column(Boolean, default=False)
    buffer = Column(Boolean, default=False)

    @classmethod
    def get_all_analyzes(cls) -> list:
        """Вывод всех анализов из таблицы"""
        return session.query(Analyzes).all()

    @classmethod
    def get_all_analyzes_with_probe_results(cls) -> list:
        """Вывод всех анализов из таблицы"""
        # return session.query(Analyzes).filter(Analyzes.probe_results is not None).all()
        return session.query(Analyzes).filter(Analyzes.ready_status == "True").all()

    @classmethod
    def get_all_worklists(cls) -> list:
        """Вывод всех анализов из таблицы"""
        return session.query(Analyzes).filter(Analyzes.work_list == True).all()

    @classmethod
    def get_all_buffers(cls) -> list:
        """Вывод всех анализов из таблицы"""
        return session.query(Analyzes).filter(Analyzes.buffer == True).all()


# создание базы
Base.metadata.create_all(bind=engine)


def add_analyze(analyzer: str,
                device_id: str,
                probe_results: str = '',
                lines_list: str = '',
                raw_line: str = '',
                message_id: str = '',
                work_list: bool = False,
                buffer: bool = False,
                ) -> Analyzes:
    """
    Добавление анализов в таблицу
    :param analyzer: название анализатора
    :param device_id: номер анализатор
    :param data: данные анализов в текстовом многострочном SOAP формате
    """
    new_analyze = Analyzes(analyzer=analyzer,
                           device_id=device_id,
                           probe_results=probe_results,
                           lines_list=lines_list,
                           raw_line=raw_line,
                           work_list=work_list,
                           message_id=message_id,
                           buffer=buffer,
                           )
    session.add(new_analyze)
    session.commit()
    return new_analyze


def get_analyze_by_id(analyze_id: int) -> Query:
    """
    Выведение одного анализа по переданному id
    """
    stmt = select(Analyzes).where(Analyzes.id == analyze_id)
    analyze_exec = session.execute(stmt)
    try:
        analyze = analyze_exec.fetchone()[0]
        session.commit()
        return analyze
    except Exception as ex:
        return ex


def get_buffer(device_id: str) -> Query:
    """
    Выведение одного анализа по переданному id
    """
    # stmt = select(Analyzes).where(Analyzes.buffer is True).where(Analyzes.device_id == device_id)
    # stmt = select(Analyzes).where(Analyzes.buffer is True)
    # analyze_exec = session.execute(stmt)
    # try:
    #     analyze = analyze_exec.fetchone()[0]
    #     session.commit()
    #     return analyze
    # except Exception as ex:
    #     return ex

    return session.query(Analyzes).filter(Analyzes.buffer == True).all()


def get_analyzes(device_id: str) -> Query:
    """
    Выведение одного анализа по переданному id
    """
    analyzes = session.query(Analyzes).filter(Analyzes.device_id == device_id).all()
    return analyzes


def edit_analyze(analyze: Analyzes,
                 tries: int = 0,
                 error_text: str = '',
                 probe_results: str = '',
                 ready_status: str = "False",
                 lines_list: str = '',
                 raw_line: str = None) -> Query:
    """
    Редактирование анализов в таблице
    :param analyze: данные анализов
    :param tries: количество попыток отправить результат
    :param error_text: текст ошибки отправки результата
    """

    if analyze.tries:
        analyze.tries += 1
    else:
        analyze.tries = 1
    if analyze.tries and tries:
        analyze.tries = tries
    if error_text:
        analyze.error_text = error_text
    if probe_results:
        analyze.probe_results = probe_results
    if ready_status:
        analyze.ready_status = ready_status
    if lines_list:
        analyze.lines_list = lines_list
    if raw_line is not None:
        analyze.raw_line = raw_line
    session.commit()
    return analyze


def delete_all_analyzes() -> str:
    """Удаление всех анализов из таблицы"""
    analyzes = session.query(Analyzes).all()
    try:
        for analyze in analyzes:
            session.query(Analyzes).filter(Analyzes.id == analyze.id).delete()
            session.commit()
        logger.debug(f"Удаление всех анализов из таблицы Success!")
        return "Удаление всех анализов из таблицы Success!"
    except Exception as ex:
        logger.exception(f"Удаление всех анализов из таблицы Exception: \n{ex}")
        return f"Удаление всех анализов из таблицы Exception: \n{ex}"


def delete_analyze(analyze) -> str:
    """Удаление анализа из таблицы"""
    try:
        session.query(Analyzes).filter(Analyzes.id == analyze.id).delete()
        session.commit()
        logger.debug(f"Удаление анализа {analyze.id} - {analyze} из таблицы Success!")
        return f"Удаление анализа {analyze.id} - {analyze} из таблицы Success!"
    except Exception as ex:
        logger.exception(f"Удаление анализа {analyze.id} - {analyze} из таблицы Exception: \n{ex}")
        return f"Удаление анализа {analyze.id} - {analyze} из таблицы Exception: \n{ex}"


def delete_analyze_by_id(analyze_id) -> (None, Analyzes):
    """Удаление анализа из таблицы"""
    try:
        session.query(Analyzes).filter(Analyzes.id == analyze_id).delete()
        session.commit()
        logger.debug(f"Удаление анализа {analyze_id} из таблицы Success!")
        return f"Удаление анализа {analyze_id} из таблицы Success!"
    except Exception as ex:
        logger.exception(f"Удаление анализа {analyze_id} из таблицы Exception: \n{ex}")
        return f"Удаление анализа {analyze_id} из таблицы Exception: \n{ex}"
