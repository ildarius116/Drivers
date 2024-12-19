import os
import requests
import logging

from dotenv import load_dotenv

from main.drivers.driver_proxy.drivers.mek_7300.handler_data import create_data
from main.drivers.driver_proxy.models import Analyzes, add_analyze, delete_all_analyzes, delete_analyze

logger = logging.getLogger(__name__)

# # список (буферное хранилище) всех не отправленных результатов анализа проб.
# probes_list = []

# буфер открытых портов
opened_ports = []


def set_results(data: dict) -> str:
    """
    Функция собирает несколько результатов анализов в серию результатов
    :param data словарь со всеми анализами на одну пробу.
    :return: result_text - суммарный результат анализов одной пробы
    """
    result_text = ''
    for key, data_dict in data['probe_results'].items():
        comment_key = f"{int(key[:1]) + 1}C"
        comment = data.get('probe_comments', {}).get(comment_key, None)
        result_text += set_result(data_dict, comment)
        pass
    return result_text


def set_result(data: dict, comment: dict) -> str:
    """
    Функция формирует вывод информации по одному конкретному анализу

    :param
            data - словарь с результатами анализа на каждый параметр (BE(B), Ca, Hct и т.д.)
            comment - словарь комментарием на результат анализа

    :return
            result - результат анализа на один из параметров

    """
    comment_str = None
    flags_str = False
    result = None
    if comment:
        comment_str = f"{comment.get('def_add_info')}-{comment.get('add_info_1')}"
        if comment.get('add_info_2', None):
            comment_str += f"-{comment.get('add_info_2', None)}"
    # print('set_result data:', data)
    if '<' in data['result'] or '>' in data['result']:
        # по-умолчанию, знак "<"
        par = '&lt;'
        data['result'] = data['result'].replace('<', '')
        # если знак ">", то переписываем переменные
        if '>' in data['result']:
            par = '&gt;'
            data['result'] = data['result'].replace('>', '')
        result = f"""<Results>
                    <Mnemonics>{data['mnemonics']}</Mnemonics>
                    <ResultDate>{data['probe_date']}</ResultDate>
                    <ResultPrefix>{par}</ResultPrefix>
                    <ResultNumber>{data['result']}</ResultNumber>
                    <ResultString/>
                    <Unit>{data['units']}</Unit>
                    <Note/>
                    <Comment>{comment_str}</Comment>
                    <NormalUp/>
                    <NormalDown/>
                    <Patologic>{'HIGH'}</Patologic>
                    <PatologicFlag>{flags_str}</PatologicFlag> 
                </Results>"""
    elif data.get('range', None):
        min_max = data['range'].split('-')
        if not data['result']:
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{data['probe_date']}</ResultDate>
                        <ResultPrefix/>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString/>
                        <Unit>{data['units']}</Unit>
                        <Note/>
                        <Comment>{comment_str}</Comment>
                        <NormalUp>{min_max[1]}</NormalUp>
                        <NormalDown>{min_max[0]}</NormalDown>
                        <Patologic>{'HIGH'}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
        else:
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{data['probe_date']}</ResultDate>
                        <ResultPrefix/>
                        <ResultNumber>{data['result']}</ResultNumber>
                        <ResultString/>
                        <Unit>{data['units']}</Unit>
                        <Note/>
                        <Comment>{comment_str}</Comment>
                        <NormalUp>{min_max[1]}</NormalUp>
                        <NormalDown>{min_max[0]}</NormalDown>
                        <Patologic>{'HIGH'}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
    # если в данных слово "range" отсутствует
    elif not data.get('range', None):
        # пробуем собрать СОАП данные
        try:
            # если результат - это число
            data['result'] = float(data['result'])
            result = f"""<Results>
                            <Mnemonics>{data['mnemonics']}</Mnemonics>
                            <ResultDate>{data['probe_date']}</ResultDate>
                            <ResultPrefix/>
                            <ResultNumber>{data['result']}</ResultNumber>
                            <ResultString/>
                            <Unit>{data['units']}</Unit>
                            <Note/>
                            <Comment>{comment_str}</Comment>
                            <NormalUp/>
                            <NormalDown/>
                            <Patologic>{'HIGH'}</Patologic>
                            <PatologicFlag>{flags_str}</PatologicFlag> 
                        </Results>"""
        # если результат - это не число
        except:
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{data['probe_date']}</ResultDate>
                        <ResultPrefix>{data['result']}</ResultPrefix>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString/>
                        <Unit>{data.get('units')}</Unit>
                        <Note>{data.get('result_status')}</Note>
                        <Comment>{comment_str}</Comment>
                        <NormalUp/>
                        <NormalDown/>
                        <Patologic>{'HIGH'}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
    if not result:
        logger.info(f"mek7300 set_result ... Отсутствует result! ... Data: {data}")
    return result


def create_soap(data: dict = None, raw_line: str = None, device_id: str = '') -> str:
    """
    Функция собирает воедино данные (анализы по каждому параметру) взятой пробы,
    затем помещает их в список, полученных проб.

    :param
            data - словарь данных пробы
            raw_line - чистая строка данных полученная от анализатора
            device_id - ID анализатора
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
                                <ResultDate xsi:type="xs:dateTime">{data['probe_header']['transmission_date']}</ResultDate>
                                <Probes>
                                    <ProbeNumber>{data['test_order_info']['specimen_ID']}</ProbeNumber>
                                    <SerialNumber xsi:nil="true"/>
                                    <ProbeDate>{data['probe_header']['transmission_date']}</ProbeDate>
                                    <CITO>{'false'}</CITO>
                                    <QualityControl>{'false'}</QualityControl>
                                        {set_results(data)}
                                    <RawData>{raw_line}</RawData>
                                </Probes>
                            </Data>
                        </DeviceMessage>
                    </dev:SendResults>
               </soap:Body>
            </soap:Envelope>
            """
    except Exception as ex:
        logger.info(f"set_probes ... Необработанные данные: {data}")
        logger.exception(ex)
        res_text = ""
    return res_text


def get_results_from_probes_list(probes_list: list) -> str:
    """
    Функция вынимает данные из списка полученных проб и формирует строковое поле со всем результатами анализа проб,
    находящихся в списке.
    :param
        probes_list - список с пробами (текстовыми полями)

    :return
        results_text - строковое поле с результатами
    """
    probes_text = ''
    for probe in probes_list:
        probes_text += probe
    results_text = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:dev="http://www.medrc.ru/lis/DeviceExchange" xmlns:dev1="http://www.medrc.ru/DeviceExchange">
        <soap:Header/>
        <soap:Body>
            <dev:SendResults>
                <DeviceMessage xmlns="http://www.medrc.ru/DeviceExchange" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    {probes_text}
                </DeviceMessage>
            </dev:SendResults>
        </soap:Body>
    </soap:Envelope>
    """

    return results_text


def send_soap() -> dict:
    """
    Функция посылает результаты анализа проб в LIS
    :param result: словарь с результатами анализов последней полученной пробы
    :param line: строка с прямыми данными, полученными от анализатора для последней полученной пробы
    :param probes_in_buffer: строка с предыдущими результатами анализов (из буферной БД)
    :return:
    """
    # адрес ЛИС сервера
    url = os.getenv('LIS_URL')
    # логин и пароль сервера
    authentication = eval(os.getenv('AUTH'))
    # заголовок сообщения
    headers = {'Content-Type': 'text/xml; charset=utf-8'}

    probes_list = []
    status = {'status': []}
    # создание списка отчетов из имеющихся в буферной БД
    probes_is_in_buffer = Analyzes.get_all_analyzes()
    for n, probe in enumerate(probes_is_in_buffer):
        probes_list.append(probe.probe_results)
        # получаем данные в СОАП формате для LISа из БД
        probe_result = probe.probe_results
        # попытка отправить все имеющиеся в памяти отчеты
        try:
            logger.info("Trying to send probes:")
            # logger.info(f"Headers: {headers}")
            # logger.info(f"Authentication: {authentication}")
            # logger.info(f"Data: \n{probe_result}")
            response = requests.request(method="POST",
                                        url=url,
                                        headers=headers,
                                        data=probe_result,
                                        auth=authentication,
                                        timeout=80)
        except OSError as ex:
            logger.info(f"Data: \n{probe_result}")
            logger.error(f"OSError is raised: {ex.__doc__}")
            logger.error(f"OSError is raised: {ex.__context__}")
            status['status'].append({n: f"Exception is raised: {ex.__context__}"})
        except Exception as ex:
            logger.info(f"Data: \n{probe_result}")
            logger.error(f"Exception is raised: {ex.__doc__}")
            logger.error(f"Exception is raised: {ex.__context__}")
            status['status'].append({n: f"Exception is raised: {ex.__context__}"})

        else:
            # если статус код = 200, значит данные были приняты и можно из буфера текущие результаты
            if response.status_code == 200:
                # analyze_db.delete_analyze(probe)
                delete_analyze(probe)
                logger.info(f"status_code: {response.status_code}")
                logger.info(f"Probe {probe} is deleted from buffer")
                logger.info(f"response.text: {response.text}")
            # в остальных случаях, данные из буферной БД не удаляются
            else:
                logger.info(f"Data: \n{probe_result}")
                logger.warning(f"status_code: {response.status_code}")
                logger.warning(f"Probes buffer is not cleared")
                logger.warning(f"response.text: {response.text}")
            status['status'].append({n: response.status_code})
    return status


if __name__ == '__main__':
    # считывания пространства окружения
    load_dotenv()
    # конфигурирование логгера
    logging.basicConfig(level=logging.INFO,
                        # filename='logger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    logger.info("Start app")
    # TODO
    # временное считывание логов из файла
    with open('../emulators/logs/MEK7300_clear_2.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    res = main(content)
    logger.info(f"result: {res}")
    # res = set_results(res)
    # logger.info(f"set_results: {res}")
    content_in_line = ''.join(content)
    res = set_probes(res, content_in_line)
    logger.info(f"set_probes: {res}")
    # send_soap()
    logger.info("Stop app")
