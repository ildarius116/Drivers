import os
import re
import requests
import logging

from dotenv import load_dotenv

from main.drivers.driver_proxy.drivers.gem_3000.handler_data import create_data
from main.drivers.driver_proxy.models import Analyzes, delete_analyze

logger = logging.getLogger(__name__)

# буфер открытых портов
opened_ports = []


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
    for data_dict in data.values():
        result_text += set_result(data_dict, date)
    return result_text


def set_result(data: dict, date: str) -> str:
    """
    Функция формирует вывод информации по одному конкретному анализу

    :param
            data - словарь со всеми анализами на одну пробу
            date - дата пробы

    :return
            result_text - суммарный результат анализов одной пробы
    """
    # если есть результат и это число
    if isinstance(data.get('result'), float):
        result = f"""<Results>
                    <Mnemonics>{data['mnemonics']}</Mnemonics>
                    <ResultDate>{date}</ResultDate>
                    <ResultPrefix/>
                    <ResultNumber>{data['result']}</ResultNumber>
                    <ResultString/>
                    <Unit>{data['parameter']}</Unit>
                    <Note>{data['Note']}</Note>
                    <Comment>{data['Comment']}</Comment>
                    <NormalUp>{data['period_max']}</NormalUp>
                    <NormalDown>{data['period_min']}</NormalDown>
                    <Patologic>{'HIGH'}</Patologic>
                    <PatologicFlag>{'true'}</PatologicFlag> 
                </Results>"""
    # в остальных случаях
    else:
        logger.info(f"else data: {data}")
        logger.info(f"else data['result']: {data['result']}")

        # поиск наличия числового значения в результатах
        try:
            result_type = re.findall(r'\d+', data['result'])[0]
            logger.info(f"else result_type: {result_type}")
        except:
            logger.info(f"OUT OF INDEX re.findall - data['result']: {data['result']}")
            result_type = ''

        # если в результатах встречаются знак "<" или ">"
        if '<' in result_type or '>' in result_type:
            # по-умолчанию, знак "<"
            par = '&lt;'
            data['result'] = data['result'].replace('<', '')
            # если знак ">", то переписываем переменные
            if '>' in result_type:
                par = '&gt;'
                data['result'] = data['result'].replace('>', '')

            logger.info(f"else if data if '<' in result_type or '>' in result_type data['result']: {data['result']}")

            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix>{par}</ResultPrefix>
                        <ResultNumber>{data['result']}</ResultNumber>
                        <ResultString/>
                        <Unit>{data['parameter']}</Unit>
                        <Note>{data['Note']}</Note>
                        <Comment>{data['Comment']}</Comment>
                        <NormalUp>{data['period_max']}</NormalUp>
                        <NormalDown>{data['period_min']}</NormalDown>
                        <Patologic>{'HIGH'}</Patologic>
                        <PatologicFlag>{'true'}</PatologicFlag> 
                    </Results>"""
        else:
            logger.info(f"else if data else data['result']: {data['result']}")

            result = f"""<Results>
                        <Mnemonics>{data['mnemonics']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix/>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString>{data['result']}</ResultString>
                        <Unit>{data['parameter']}</Unit>
                        <Note>{data['Note']}</Note>
                        <Comment>{data['Comment']}</Comment>
                        <NormalUp>{data['period_max']}</NormalUp>
                        <NormalDown>{data['period_min']}</NormalDown>
                        <Patologic>{'HIGH'}</Patologic>
                        <PatologicFlag>{'true'}</PatologicFlag> 
                    </Results>"""
    return result


def create_soap(data: dict = None, raw_line: str = None, device_id: str = '') -> str:
    """
    Функция собирает воедино данные (анализы по каждому параметру) взятой пробы,
    затем помещает их в список, полученных проб

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
                                <ResultDate xsi:type="xs:dateTime">{data['result_date']}</ResultDate>
                                <Probes>
                                    <ProbeNumber>{data['probe_number']}</ProbeNumber>
                                    <SerialNumber xsi:nil="true"/>
                                    <ProbeDate>{data['probe_date']}</ProbeDate>
                                    <CITO>{'false'}</CITO>
                                    <QualityControl>{'false'}</QualityControl>
                                        {set_results(data['probe_results'], data['result_date'])}
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

    :param None

    :return: None
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
                        # filename='eleven_logger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    logger.info("Start app")
    # TODO
    # временное считывание логов из файла
    with open('../emulators/logs/GEM_3000_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    res = create_data(content)
    logger.info(f"result: {res}")
    # res = set_results(res)
    # logger.info(f"set_results: {res}")
    content_in_line = ''.join(content)
    res = set_probes(res, content_in_line)
    logger.info(f"set_probes: {res}")
    # send_soap()
    logger.info("Stop app")
