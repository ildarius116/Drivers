import sys
import requests
from requests.auth import HTTPDigestAuth, HTTPBasicAuth
import base64
import logging
import json
import urllib.parse
from flask import Flask, request

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.errorhandler(404)
def not_found(e):
    logger.info("NOT FOUND - 404", exc_info=e)
    return f"NOT FOUND - 404 \n {e}"


# token = ''

def get_access_token(url, headers=None):
    logger.info("try to get_access_token")
    try:
        response = requests.post(
            url,
            data={},
            auth=('webTatNeftb', 'tat!Nb22'),
            timeout=30,
        )
        logger.info(f"response: {response}")
        logger.info(f"response.content: {response.content}")
    except Exception as ex:
        logger.exception("request not able", exc_info=ex)
    else:
        logger.info(f"response_return: {response}")
        return response


def get_patient_simple(url):
    logger.info("try to get_patient_simple")
    try:
        response = requests.get(
            url,
            auth=('webTatNeftb', 'tat!Nb22'),
            timeout=30,
        )
        logger.info(f"response: {response}")
        logger.info(f"response.content: {response.content}")
    except Exception as ex:
        logger.exception("request not able", exc_info=ex)
    else:
        logger.info(f"response_return: {response}")
        return response


def get_patient_token(url, headers):
    logger.info("try to get_patient_token")
    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=30,
        )
        logger.info(f"response: {response}")
        logger.info(f"response.content: {response.content}")
    except Exception as ex:
        logger.exception("request not able", exc_info=ex)
    else:
        logger.info(f"response_return: {response}")
        return response


@app.route('/')
def start_page():
    logger.info("start_page")
    return 'Hello world!'


@app.route('/token')
def get_token_page():
    logger.info("try to get_token")
    try:
        token = get_access_token("https://gist-ws2.ezdrav.ru:8779/APIv2/auth")
        logger.info(f"token: {token.content.decode()}")
        return f'GOT token - {token.content.decode()} '
    except Exception as ex:
        logger.exception("token not able", exc_info=ex)
        return "token not able"


@app.route('/request/<int:i>', methods=['GET'])
def get_find_pat_page(i):
    logger.info("try to request_by_pattern")
    data = [
        'number=981245',
        'number=275183',
        'lastName=%D0%98%D0%B2%D0%B0%D0%BD%D0%BE%D0%B2&firstName=%D0%98%D0%B2%D0%B0%D0%BD',
        'lastName=%D1%82%D0%B5%D1%81%D1%82&firstName=%D0%BF%D0%B0%D1%86&middleName=%D0%B8%D0%B2%D0%B0%D0%BD'
    ]
    path = f'find_pat?{data[i]}'
    try:
        logger.info(f"https://gist-ws2.ezdrav.ru:8779/APIv2/{path}")
        patient = get_patient_simple(f"https://gist-ws2.ezdrav.ru:8779/APIv2/{path}")
        logger.info(f"patient: {patient}")
        print('patient', patient)
        return patient.content.decode()
    except Exception as ex:
        logger.exception("Patient not able", exc_info=ex)
        return {}


@app.route('/request_login', methods=['POST'])
def get_find_pat_login_page():
    logger.info("try to request_by_login")
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()
        path = json_data['path']
        logger.info(f"path: {path}")
    try:
        logger.info(f"https://gist-ws2.ezdrav.ru:8779/{path}")
        patient = get_patient_simple(f"https://gist-ws2.ezdrav.ru:8779/{path}")
        logger.info(f"patient: {patient}")
        # print('patient', patient)
        return patient.content.decode()
    except Exception as ex:
        logger.exception("patient not able", exc_info=ex)
        return {}


@app.route('/request_token', methods=['POST'])
def get_find_pat_token_page():
    logger.info("try to request_by_token")
    token = get_access_token("https://gist-ws2.ezdrav.ru:8779/APIv2/auth")
    logger.info("try to get_pat_token_page")
    headers = {'Autorization': f'bearer {token.content.decode()}'}
    logger.info(f"headers: {headers}")
    content_type = request.headers.get('Content-Type')
    if content_type == 'application/json':
        json_data = request.get_json()
        path = json_data['path']
        logger.info(f"path: {path}")
    try:
        logger.info(f"https://gist-ws2.ezdrav.ru:8779/{path}")
        patient = get_patient_token(f"https://gist-ws2.ezdrav.ru:8779/{path}", headers=headers, )
        logger.info(f"patient: {patient}")
        # print('patient', patient)
        return patient.content.decode()
    except Exception as ex:
        logger.exception("patient not able", exc_info=ex)
        return {}


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        # filename='logger.log',
                        format="%(asctime)s - %(levelname)s - %(message)s",
                        datefmt='%HH:%MM:%SS',
                        )
    logger.info("Start app")
    app.run(debug=True, host='0.0.0.0', port=5000)
    logger.info("Stop app")

# EXAMPLES
# curl --location 'http://127.0.0.1:5000/request_login/' --header 'Content-Type: application/json' --data '{"path": "APIv2/find_pat?number=803791"}'
# curl --location 'http://127.0.0.1:5000/request_login/' --header 'Content-Type: application/json' --data '{"path": "APIv2/find_pat?lastName=%D0%98%D0%B2%D0%B0%D0%BD%D0%BE%D0%B2&firstName=%D0%98%D0%B2%D0%B0%D0%BD"}'
