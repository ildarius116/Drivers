import logging

from dotenv import load_dotenv

from driver_rs232_port.drivers.bc_30s.handler_data import create_data

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
        comment = results_dict.get('probe_comments', {})
        result_text += set_result(results_dict, comment, date)
    return result_text


def set_result(data: dict, comment: dict, date: str) -> str:
    """
    Функция формирует вывод информации по одному конкретному анализу

    :param
            data - словарь с результатами анализа на каждый параметр (BE(B), Ca, Hct и т.д.)
            comment - словарь c комментарием на результат анализа
            date - дата пробы

    :return
            result - результат анализа на один из параметров
    """
    # если есть патологии
    if data.get('flag'):
        flags_str = "true"
        patologic = data.get('flag')
    else:
        flags_str = "false"
        patologic = ''

    # если результат - это число
    if data['value_type'] == 'NM':
        references_range = data.get('references_range')
        if references_range and references_range != '-':
            range_left, range_right = data.get('references_range').split('-')
        else:
            range_left, range_right = None, None

        # если в данных есть параметр "range"
        if range_left and range_right:
            result = f"""<Results>
                            <Mnemonics>{data['mnemonics_name']}</Mnemonics>
                            <ResultDate>{date}</ResultDate>
                            <ResultPrefix/>
                            <ResultNumber>{data['result']}</ResultNumber>
                            <ResultString/>
                            <Unit>{data.get('units', "")}</Unit>
                            <Note></Note>
                            <Comment></Comment>
                            <NormalUp>{range_left}</NormalUp>
                            <NormalDown>{range_right}</NormalDown>
                            <Patologic>{patologic}</Patologic>
                            <PatologicFlag>{flags_str}</PatologicFlag> 
                        </Results>"""
        else:
            data['result'] = float(data['result'])
            result = f"""<Results>
                        <Mnemonics>{data['mnemonics_name']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix/>
                        <ResultNumber>{data['result']}</ResultNumber>
                        <ResultString/>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note></Note>
                        <Comment></Comment>
                        <NormalUp/>
                        <NormalDown/>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
    # в остальных случаях
    else:
        result = f"""<Results>
                        <Mnemonics>{data['mnemonics_name']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix xsi:nil="true"/>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString>{data['result']}</ResultString>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note></Note>
                        <Comment></Comment>
                        <NormalUp/>
                        <NormalDown/>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
    return result


def create_soap(data: dict = None, raw_line: str = None, device_id: str = '') -> str:
    """
    Функция собирает воедино данные взятой пробы и создает СОАП текст с данными этой пробы

    :param
            data - словарь данных пробы
            raw_line - чистая строка данных полученная от анализатора
            device_id - ID анализатора
    :return:
            res_text - итоговый текст
    """
    cito = 'false'

    try:
        res_text = f"""<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:dev="http://www.medrc.ru/lis/DeviceExchange" xmlns:dev1="http://www.medrc.ru/DeviceExchange">
               <soap:Header/>
               <soap:Body>
                    <dev:SendResults>
                        <DeviceMessage xmlns="http://www.medrc.ru/DeviceExchange" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                            <Data>
                                <DeviceID xsi:type="xs:string">{device_id}</DeviceID>
                                <ResultDate xsi:type="xs:dateTime">{data['probe_header']['message_date']}</ResultDate>
                                <Probes>
                                    <ProbeNumber>{data['order_info']['order_number']}</ProbeNumber>
                                    <SerialNumber>{data['order_info']['sample_id']}</SerialNumber>
                                    <ProbeDate>{data['order_info']['test_time']}</ProbeDate>
                                    <CITO>{cito}</CITO>
                                    <QualityControl>{'false'}</QualityControl>
                                        {set_results(data, data['order_info']['test_time'])}
                                    <RawData>{raw_line}</RawData>
                                </Probes>
                            </Data>
                        </DeviceMessage>
                    </dev:SendResults>
               </soap:Body>
            </soap:Envelope>
            """
    except Exception as ex:
        logger.exception(f"create_soap ... Unprocessed data: {data}")
        logger.exception(ex)
        res_text = ""
    return res_text


if __name__ == '__main__':
    # считывания пространства окружения
    load_dotenv()
    # конфигурирование логгера
    logging.basicConfig(level=logging.INFO,
                        # filename='cd_rubylogger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    logger.info("Start app")
    # временное считывание логов из файла
    with open('logs_bc_30s/CD_Ruby2_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    res = create_data(content)
    logger.info(f"result: {res}")
    # res = set_results(res)
    # logger.info(f"set_results: {res}")
    content_in_line = ''.join(content)
    res = create_soap(res, content_in_line)
    logger.info(f"set_probes: {res}")
    logger.info("Stop app")
