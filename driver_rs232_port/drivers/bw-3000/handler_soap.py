import re
import logging
from dotenv import load_dotenv

from main.drivers.driver_proxy.drivers.i2000sr.handler_data import create_data
from main.drivers.driver_proxy.models import Analyzes, add_analyze, delete_all_analyzes, delete_analyze

# конфигурирование логгера
logger = logging.getLogger(__name__)


def set_results(data: dict, date: str) -> str:
    """
    Функция собирает несколько результатов анализов в серию результатов

    :param
            data - словарь со всеми анализами на одну пробу
            date - дата пробы

    :return
            result_text - суммарный результат анализов одной пробы
    """
    result_text = ''
    results_list = data['results']
    for results_dict in results_list:
        comment = results_dict.get('probe_comments', {})
        result_text += set_result(results_dict, comment, date)
    return result_text


def set_result(data: dict, comment: dict, date: str) -> str:
    """
    Функция формирует вывод информации по одному конкретному анализу

    :param
            data - словарь с результатами анализа на каждый параметр (BE(B), Ca, Hct и т.д.)

    :return
            result - результат анализа на один из параметров

    """
    
    # если есть комментарий
    if comment:
        comment_str = comment['comment']
    else:
        comment_str = ''

    if data.get("result_number") == '-':
        result_number = 'xsi:nil="true"'
    else:
        result_number = data.get("result_number")

    if data.get("result_string") == '-':
        result_string = 'xsi:nil="true"'
    else:
        result_string = data.get("result_string")

    result_status = ""
    flags_str = "false"
    patologic = ""
    par = 'xsi:nil="true"'
    
    result = f"""<Results>
                <Mnemonics>{data['mnemonics']}</Mnemonics>
                <ResultDate>{date}</ResultDate>
                <ResultPrefix>{par}</ResultPrefix>
                <ResultNumber>{result_number}</ResultNumber>
                <ResultString>{result_string}</ResultString>
                <Unit>{data.get('units', "")}</Unit>
                <Note>{result_status}</Note>
                <Comment>{comment_str}</Comment>
                <NormalUp></NormalUp>
                <NormalDown></NormalDown>
                <Patologic>{patologic}</Patologic>
                <PatologicFlag>{flags_str}</PatologicFlag> 
            </Results>"""
    
    return result
    
    


def create_soap(data: dict = None, raw_line: str = None, device_id: str = '') -> str:
    """
    Функция собирает воедино данные взятой пробы и создает СОАП текст с данными этой пробы

    :param
            data - словарь данных пробы
            lines - чистая строка данных полученная от анализатора
    :return:
            res_text - итоговый текст
    """
    try:
        res_text = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:dev="http://www.medrc.ru/lis/DeviceExchange" xmlns:dev1="http://www.medrc.ru/DeviceExchange">
               <soap:Header/>
               <soap:Body>
                    <dev:SendResults>
                        <DeviceMessage xmlns="http://www.medrc.ru/DeviceExchange" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                            <Data>
                                <DeviceID xsi:type="xs:string">{device_id}</DeviceID>
                                <ResultDate xsi:type="xs:dateTime">{data.get('resultDate')}</ResultDate>
                                <Probes>
                                    <ProbeNumber>{data.get('number')}</ProbeNumber>
                                    <SerialNumber>{"0"}</SerialNumber>
                                    <ProbeDate>{data.get('resultDate')}</ProbeDate>
                                    <CITO>{'false'}</CITO>
                                    <QualityControl>{'false'}</QualityControl>
                                        {set_results(data, data.get('resultDate'))}
                                    <RawData>{raw_line}</RawData>
                                </Probes>
                            </Data>
                        </DeviceMessage>
                    </dev:SendResults>
               </soap:Body>
            </soap:Envelope>
            """
    except Exception as ex:
        logger.exception(f"set_probes ... Unprocessed data: {data}")
        logger.exception(ex)
        res_text = ""
    return res_text


if __name__ == '__main__':
    # считывания пространства окружения
    load_dotenv()
    # конфигурирование логгера
    logging.basicConfig(level=logging.INFO,
                        # filename='eleven_logger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    logger.info("Start app")
    # временное считывание логов из файла
    with open('../emulators/logs/Eleven_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    res = create_data(content)
    logger.info(f"result: {res}")
    # res = set_results(res)
    # logger.info(f"set_results: {res}")
    content_in_line = ''.join(content)
    res = create_soap(res, content_in_line)
    logger.info(f"set_probes: {res}")
    logger.info("Stop app")
