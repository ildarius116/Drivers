import logging
from dotenv import load_dotenv

# конфигурирование логгера
logger = logging.getLogger(__name__)


def set_worklist(data: dict = None, device_id: str = '') -> str:
    """
    Функция формирует текстовый СОАП запрос на получение данных по рабочему листу (Worklist)
    :param
            data - словарь данных пробы
            device_id - номер анализатора
    :return:
            res_text - итоговый текст
    """
    # TODO
    #   device_id - временная заглушка пока нет в базе ЛИС данных о реальных анализаторах
    if not device_id:
        device_id = '000000002'
    if data['test_order_info']:
        sample_id = data['test_order_info']['sample_id']
    else:
        sample_id = data['request_info']['2Q']['sample_id']
    res_text = f"""<dev:GetWorklist>
         <dev:DeviceID>{device_id}</dev:DeviceID>
         <dev:ProbeNumber>{sample_id}</dev:ProbeNumber>
      </dev:GetWorklist>
    """
    return res_text


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
    # проход по списку результатов анализов проб
    for results_dict in results_list:
        is_final = results_dict.get('result_type', ) == 'Final result'
        # если это "финальный" результат пробы
        if is_final:
            comment = results_dict.get('probe_comments', {})
            # добавляем его в список на отправку
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
    comment_str = ''
    note = ''
    # если есть комментарий
    if comment:
        comment_str = comment['comment']
    # если есть патологии
    if data.get('flags'):
        flags_str = "true"
        patologic = ", ".join(data.get('flags'))
        char_to_replace = {'<': '&lt;', '>': '&gt;'}
        for key, value in char_to_replace.items():
            patologic = patologic.replace(key, value)
    else:
        flags_str = "false"
        patologic = ''
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
                    <Mnemonics>{data['test_code']}</Mnemonics>
                    <ResultDate>{date}</ResultDate>
                    <ResultPrefix>{par}</ResultPrefix>
                    <ResultNumber>{data['result']}</ResultNumber>
                    <ResultString/>
                    <Unit>{data.get('units', "")}</Unit>
                    <Note>{note}</Note>
                    <Comment>{comment_str}</Comment>
                    <NormalUp/>
                    <NormalDown/>
                    <Patologic>{patologic}</Patologic>
                    <PatologicFlag>{flags_str}</PatologicFlag> 
                </Results>"""

    # если в данных есть слово "range"
    elif data.get('range', None):
        min_max = data['range'].split(' TO ')
        result = f"""<Results>
                    <Mnemonics>{data['test_code']}</Mnemonics>
                    <ResultDate>{date}</ResultDate>
                    <ResultPrefix/>
                    <ResultNumber>{data['result']}</ResultNumber>
                    <ResultString/>
                    <Unit>{data.get('units', "")}</Unit>
                    <Note>{note}</Note>
                    <Comment>{comment_str}</Comment>
                    <NormalUp>{min_max[1]}</NormalUp>
                    <NormalDown>{min_max[0]}</NormalDown>
                    <Patologic>{patologic}</Patologic>
                    <PatologicFlag>{flags_str}</PatologicFlag> 
                </Results>"""
    # если в данных слово "range" отсутствует
    elif not data.get('range', None):
        # пробуем собрать СОАП данные
        try:
            # если результат - это число
            data['result'] = float(data['result'])
            result = f"""<Results>
                        <Mnemonics>{data['test_code']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix/>
                        <ResultNumber>{data['result']}</ResultNumber>
                        <ResultString/>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note>{note}</Note>
                        <Comment>{comment_str}</Comment>
                        <NormalUp/>
                        <NormalDown/>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
        # если результат - это не число
        except:
            result = f"""<Results>
                        <Mnemonics>{data['test_code']}</Mnemonics>
                        <ResultDate>{date}</ResultDate>
                        <ResultPrefix/>
                        <ResultNumber xsi:nil="true"/>
                        <ResultString/>{data['result']}</ResultString>
                        <Unit>{data.get('units', "")}</Unit>
                        <Note>{note}</Note>
                        <Comment>{comment_str}</Comment>
                        <NormalUp/>
                        <NormalDown/>
                        <Patologic>{patologic}</Patologic>
                        <PatologicFlag>{flags_str}</PatologicFlag> 
                    </Results>"""
    # в остальных случаях
    else:
        logger.info(f"set_result ... Unprocessed data: {data['result']}")
        result = f"""<Results>
                    <Mnemonics>{data['test_code']}</Mnemonics>
                    <ResultDate>{date}</ResultDate>
                    <ResultPrefix/>
                    <ResultNumber xsi:nil="true"/>
                    <ResultString>{data['result']}</ResultString>
                    <Unit>{data.get('units', "")}</Unit>
                    <Note>{note}</Note>
                    <Comment>{comment_str}</Comment>
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
    try:
        if data['test_order_info']:
            sample_id = data['test_order_info']['sample_id']
        else:
            sample_id = data['request_info'].get('Q', {}).get('sample_id', '')
    except Exception as ex:
        logger.exception(f"create_soap sample_id ... Unprocessed data: {data}")
        logger.exception(ex)
        sample_id = ""
    try:
        if data['probe_date']:
            date = data['probe_date']
        else:
            date = data['probe_header']['transmission_date']
    except Exception as ex:
        logger.exception(f"create_soap date ... Unprocessed data: {data}")
        logger.exception(ex)
        sample_id = ""
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
                                    <ProbeNumber>{sample_id}</ProbeNumber>
                                    <SerialNumber xsi:nil="true"/>
                                    <ProbeDate>{data['probe_header']['transmission_date']}</ProbeDate>
                                    <CITO>{'false'}</CITO>
                                    <QualityControl>{'false'}</QualityControl>
                                        {set_results(data, data['probe_date'])}
                                    <RawData>{raw_line}</RawData>
                                </Probes>
                            </Data>
                        </DeviceMessage>
                    </dev:SendResults>
               </soap:Body>
            </soap:Envelope>
            """
    except Exception as ex:
        logger.info(f"create_soap ... Unprocessed data: {data}")
        logger.exception(ex)
        res_text = ""
    return res_text


if __name__ == '__main__':
    # считывания пространства окружения
    load_dotenv()
    # конфигурирование логгера
    logging.basicConfig(level=logging.INFO,
                        # filename='i2000sr_logger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%Y-%m-%d %H:%M:%S',
                        )
    logger.info("Start app")
    # временное считывание логов из файла
    with open('../emulators/logs/Architect_i2000SR_clear.log', 'r', encoding='windows-1251') as file:
        content = file.readlines()
    res = main(content)
    logger.info(f"result: {res}")
    content_in_line = ''.join(content)
    res = set_probes(res, content_in_line)
    logger.info(f"set_probes: {res}")
    logger.info("Stop app")
