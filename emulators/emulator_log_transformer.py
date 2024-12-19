import os

# from pytz import unicode
STX = bytes.fromhex("02")
ETX = bytes.fromhex("03")
EOT = bytes.fromhex("04")
ENQ = bytes.fromhex("05")
ACK = bytes.fromhex("06")
LF = bytes.fromhex("0A")
CR = bytes.fromhex("0D")
NAK = bytes.fromhex("15")
ETB = bytes.fromhex("17")


def write_to_em_log(file_name: str, data: list) -> None:
    """
    Функция записи данных в файл
    """
    with open(file_name, 'w') as file:
        file.writelines(data)
        print('data_has_been_wrote_in_file!')


def save_em_log(file_name: str, data: list) -> None:
    """
    Функция сохранения данных в файл
    """
    file_is_exists = os.path.exists(file_name)
    if file_is_exists:
        answer = input(f"File {file_name} already exists! Rewrite it? (y/N) ")
        if answer and (answer.lower() == "y" or answer.lower() == "yes"):
            write_to_em_log(file_name, data)
        else:
            file_name = input("Enter the file_name (only): <file_name>.log: ")
            file_name = f'logs/{file_name}.log'
            write_to_em_log(file_name, data)
    else:
        write_to_em_log(file_name, data)


def cd_ruby_transformer(load_file_name: str, save_file_name: str) -> None:
    """
    Основная функция обработки данных из ЛОГ-файла
    """
    file_is_exists = os.path.exists(load_file_name)
    data_list = []
    if file_is_exists:
        with open(load_file_name, 'rb') as file:
            content = file.readlines()
            for line in content:
                line = line.decode(encoding='windows-1251')
                if "b'\\x04\\x05'" in line:
                    data_list.append("b'\\x04\\x05\n")
                elif "b'\\x04'" in line:
                    data_list.append("b'\\x04\n")
                elif "b'\\x05'" in line:
                    data_list.append("b'\\x05\n")
                # elif "b'\\x02" in line:
                #     line_list = line.split('STX: ')
                #     print('STX line!!!', line_list[-1])
                #     data_list.append(line_list[-1])
                elif "STX" in line:
                    line_list = line.split('STX: ')
                    data_list.append(line_list[-1])
        # print('data_list:', data_list)
        save_em_log(save_file_name, data_list)
    else:
        print(f"Can't file {load_file_name}. It does not exists!")


def eleven_transformer(load_file_name: str, save_file_name: str) -> None:
    """
    Основная функция (первичной) обработки полученных данных
    """
    file_is_exists = os.path.exists(load_file_name)
    data_list = []
    if file_is_exists:
        with open(load_file_name, 'rb') as file:
            content = file.readlines()
            for line in content:
                line = line.decode(encoding='windows-1251')
                if "b'\\x04\\x05'" in line:
                    data_list.append("<EOT><ENQ>\n")
                elif "b'\\x04'" in line:
                    data_list.append("<EOT>\n")
                elif "b'\\x05'" in line:
                    data_list.append("<ENQ>\n")
                # elif "b'\\x02" in line:
                #     line_list = line.split('STX: ')
                #     print('STX line!!!', line_list[-1])
                #     data_list.append(line_list[-1])
                elif "STX" in line:
                    line_list = line.split('STX: ')
                    line = line_list[-1]
                    char_to_replace = {"b'\\x02": "<STX>", r"\r": "<CR>", r"\x17": "<ETB>", r"\n'": "<LF>", r"\x03": "<ETX>", "\n": "", " ": "`"}
                    for key, value in char_to_replace.items():
                        line = line.replace(key, value)
                    data_list.append(line)
        # print('data_list:', data_list)
        save_em_log(save_file_name, data_list)
    else:
        print(f"Can't file {load_file_name}. It does not exists!")


if __name__ == '__main__':
    # load_file_name = 'logs/driver_logger - cd_ruby_00.log'
    # save_file_name = 'logs/em_log_cd_ruby_01.log'
    load_file_name = 'logs/driver_logger - eleven_01.log'
    save_file_name = 'logs/em_log_eleven_02.log'

    # file_name = 'logs/em_log_cd_ruby_00.log'

    # cd_ruby_transformer(load_file_name, save_file_name)
    eleven_transformer(load_file_name, save_file_name)
