import os
import logging
import requests
import xmltodict

# конфигурирование логгера
logger = logging.getLogger(__name__)


def get_worklist_from_lis(data: dict = None, device_id: str = '') -> dict:
    """
    Функция запроса параметров Рабочего листа (worklist) из ЛИС

    :param
        data - номер анализатора
        device_id - номер анализатора

    :return:
        worklist_dict - словарь с параметрами рабочего листа (Worklist)
    """
    # получаем id пробы
    sample_id = data['query_definition']['sample_bar_code']

    # адрес ЛИС сервера
    url = os.getenv('LIS_URL')
    # логин и пароль сервера
    authentication = eval(os.getenv('AUTH'))
    # заголовок сообщения
    headers = {'Content-Type': 'text/xml; charset=utf-8'}
    # СОАП сообщение
    message = f"""
        <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://www.medrc.ru/lis/DeviceExchange">
           <soapenv:Header/>
           <soapenv:Body>
              <dev:GetWorklist>
                 <dev:DeviceID>{device_id}</dev:DeviceID>
                 <dev:ProbeNumber>{sample_id}</dev:ProbeNumber>
              </dev:GetWorklist>
           </soapenv:Body>
        </soapenv:Envelope>
    """
    worklist_dict = {}
    # попытка получить параметры COM порта из базы LIS
    try:
        logger.info(f"Trying to get Worklist for id: {device_id} and sample^ {sample_id}")
        # logger.info(f"Headers: {headers}")
        # logger.info(f"Authentication: {authentication}")
        # logger.info(f"Data: \n{payload}")
        response = requests.request("POST", url, headers=headers, data=message, auth=authentication, timeout=5)
    except OSError as ex:
        logger.info(f"Data: \n{message}")
        logger.error(f"OSError is raised: {ex.__doc__}")
        logger.error(f"OSError is raised: {ex.__context__}")
    except Exception as ex:
        logger.info(f"Data: \n{message}")
        logger.error(f"Exception is raised: {ex.__doc__}")
        logger.error(f"Exception is raised: {ex.__context__}")
    else:
        # если связь с базой есть и получены данные
        if response.status_code == 200:
            logger.info(f"status_code: {response.status_code}")
            logger.info(f"Worklist parameters for id:{device_id} are received")
            # logger.info(f"response.text: {response.text}")
            response_xml = response.text
            response_dict = xmltodict.parse(response_xml)
            worklist_dict['cito'] = response_dict['soap:Envelope']['soap:Body']['m:GetWorklistResponse'][
                'm:return'].get('d4p1:CITO', False)
            worklist_dict['date'] = response_dict['soap:Envelope']['soap:Body']['m:GetWorklistResponse'][
                'm:return'].get('d4p1:Date', None)
            worklist_dict['pacient'] = response_dict['soap:Envelope']['soap:Body']['m:GetWorklistResponse'][
                'm:return'].get('d4p1:Pacient', {})
            worklist_response = response_dict['soap:Envelope']['soap:Body']['m:GetWorklistResponse'][
                'm:return'].get('d4p1:Tests', [])
            if isinstance(worklist_response, list):
                worklist_codes = [data.get('d4p1:Test') for data in worklist_response if data]
            else:
                worklist_codes = [worklist_response.get('d4p1:Test')]
            worklist_dict['worklist'] = worklist_codes
            return worklist_dict
        # если связь с базой есть, но данные не получены
        else:
            logger.warning("Connection with LIS is exists, but Data are not received!")
            return {}
