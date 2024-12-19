import re
import logging
from dotenv import load_dotenv

from driver_rs232_port.drivers.i2000sr.handler_data import create_data
from driver_rs232_port.models import Analyzes, add_analyze, delete_all_analyzes, delete_analyze

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
    results_list = data['probe_results']
    for results_dict in results_list:
        # comment_key = f"{int(key[:-1]) + 1}C"
        # comment = data.get('probe_comments', {}).get(comment_key, None)
        comment = results_dict.get('probe_comments', {})
        result_text += set_result(results_dict, comment, date)
    return result_text


def set_result(data: dict, comment: dict, date: str) -> str:
    """
    Функция формирует вывод информации по одному конкретному анализу

    :param
            data - словарь с результатами анализа на каждый параметр (BE(B), Ca, Hct и т.д.)
            comment - словарь комментарием на результат анализа

    :return
            result - результат анализа на один из параметров

    """
    # если есть патологии
    if data.get('flags'):
        flags_str = "true"
        patologic = ''
    else:
        flags_str = "false"
        patologic = ''
    # если есть комментарий
    if comment:
        comment_str = comment['comment']
    else:
        comment_str = ''
    # если результат "без замечаний"
    if data['result_status'] == "F":
        result_status = ''
    else:
        result_status = data['result_status']
    # если в результатах встречаются знак "<" или ">"
    if (isinstance(data['result'], str) and
            ('<' in data['result'] or '>' in data['result'] or
             '&lt;' in data['result'] or '&gt;' in data['result'])):
        # по-умолчанию, знак "<"
        par = '&lt;'
        data['result'] = data['result'].replace('<', '')
        data['result'] = data['result'].replace('&lt;', '')
        # если знак ">", то переписываем переменные
        if '>' or '&gt;' in data['result']:
            par = '&gt;'
            data['result'] = data['result'].replace('>', '')
            data['result'] = data['result'].replace('&gt;', '')
        result = f"""<Results>
                    <Mnemonics>{data['mnemonics']}</Mnemonics>
                    <ResultDate>{date}</ResultDate>
                    <ResultPrefix>{par}</ResultPrefix>
                    <ResultNumber>{data['result']}</ResultNumber>
                    <ResultString xsi:nil="true"/>
                    <Unit>{data.get('units', "")}</Unit>
                    <Note>{result_status}</Note>
                    <Comment>{comment_str}</Comment>
                    <NormalUp></NormalUp>
                    <NormalDown></NormalDown>
                    <Patologic>{patologic}</Patologic>
                    <PatologicFlag>{flags_str}</PatologicFlag> 
                </Results>"""
    # если в данных есть слово "range"
    elif isinstance(data['result'], str) and data.get('range', None):
        min_max = data['range'].split('`TO`')
        result = f"""<Results>
                    <Mnemonics>{data['mnemonics']}</Mnemonics>
                    <ResultDate>{date}</ResultDate>
                    <ResultPrefix xsi:nil="true"/>
                    <ResultNumber>{data['result']}</ResultNumber>
                    <ResultString xsi:nil="true"/>
                    <Unit>{data.get('units', "")}</Unit>
                    <Note>{result_status}</Note>
                    <Comment>{comment_str}</Comment>
                    <NormalUp>{min_max[1]}</NormalUp>
                    <NormalDown>{min_max[0]}</NormalDown>
                    <Patologic>{patologic}</Patologic>
                    <PatologicFlag>{flags_str}</PatologicFlag> 
                </Results>"""
    # если в результатах встречаются знак "^"
    elif isinstance(data['result'], str) and '^' in data['result']:
        result_prefix, result_number = re.split(r'[|^]', data['result'])
        # пробуем преобразовать результат в число
        try:
            result_number = float(result_number)
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix>{result_prefix}</ResultPrefix>
                        <ResultNumber>{result_number}</ResultNumber>
                        <ResultString xsi:nil="true"/>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note>{result_status}</Note>
                        <Comment>{comment_str}</Comment>
                        <NormalUp></NormalUp>
                        <NormalDown></NormalDown>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""

        # если результат - это не число
        except:
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix>{result_prefix}</ResultPrefix>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString>{result_number}</ResultString>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note>{result_status}</Note>
                        <Comment>{comment_str}</Comment>
                        <NormalUp></NormalUp>
                        <NormalDown></NormalDown>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
    # в остальных случаях
    else:
        # пробуем собрать СОАП данные
        try:
            data['result'] = float(data['result'])
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix xsi:nil="true"/>
                        <ResultNumber>{data['result']}</ResultNumber>
                        <ResultString xsi:nil="true"/>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note>{result_status}</Note>
                        <Comment>{comment_str}</Comment>
                        <NormalUp></NormalUp>
                        <NormalDown></NormalDown>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
            # если результат - это не число
        except:
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix xsi:nil="true"/>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString>{data['result']}</ResultString>
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
                                <ResultDate xsi:type="xs:dateTime">{data['probe_header'].get('transmission_date')}</ResultDate>
                                <Probes>
                                    <ProbeNumber>{data['test_order_info'].get('bar_code_ID')}</ProbeNumber>
                                    <SerialNumber>{data['test_order_info'].get('probe_number')}</SerialNumber>
                                    <ProbeDate>{data['probe_results'][0]['result_date']}</ProbeDate>
                                    <CITO>{'false'}</CITO>
                                    <QualityControl>{'false'}</QualityControl>
                                        {set_results(data, data['probe_results'][0]['result_date'])}
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
