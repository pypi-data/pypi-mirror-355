import sys
import os
import re
from datetime import datetime

def ask_email(support=[""], loop=False):
    popular_domains = ["gmail.com", "mail.ru", "yahoo.com", "outlook.com", 
                      "microsoft.com", "edu.com", "hotmail.com", "yandex.ru", 
                      "rambler.ru", "live.com", "icloud.com", "protonmail.com"]

    supported_domains = []
    if "" in support or "all" in support:
        supported_domains.extend(popular_domains)

    for item in support:
        if item not in ["", "all"] and item not in supported_domains:
            if item.startswith("@"): 
                supported_domains.append(item[1:])
            else:
                if "." not in item:
                    supported_domains.append(f"{item}.com")
                else:
                    supported_domains.append(item)

    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    while True:
        email = input("Введите email: ")
        
        if not email_regex.match(email):
            if loop:
                print("Неверный формат email. Попробуйте еще раз.")
                continue
            else:
                print("Ошибка: Неверный формат email. Используйте формат: имя@домен.зона")
                return None

        domain = email.split('@')[1]
        
        if supported_domains and domain not in supported_domains:
            if loop:
                print(f"Email с доменом '{domain}' не поддерживается. Попробуйте другой.")
                continue
            else:
                print(f"Ошибка: Email с доменом '{domain}' не поддерживается. Разрешенные домены: {', '.join(supported_domains)}")
                return None

        return email

def ask_password(mask="*", minLength=1, maxLength=24, check_easy=True, loop=False, needUpper=False, needSpecchar=False):
    easy_passwords = {"123", "qwerty", "qwe", "qwe123", "123321", "123456", "1234", "12345", "54321", "654321", "321", "4321", "987654321", "9876543210", "1234qwerty", "1234qwe", "123456qwe", "123456789qwerty", "qwerty123", "qwerty1234", "qwerty123456", "qwerty123456789", "qwe123456789", "qwe1234", "qwe123456"}
    
    def is_easy_password(pw):
        return any(easy in pw for easy in easy_passwords)
    
    def has_upper(pw):
        return any(c.isupper() for c in pw)
    
    def has_special_char(pw):
        return bool(re.search(r"[^a-zA-Z0-9]", pw))
    
    def input_password_masked():
        password = ''
        if mask is None:
            password = input()
            return password
            
        if sys.platform == 'win32':
            import msvcrt
            while True:
                ch = msvcrt.getch()
                if ch in [b'\r', b'\n']:
                    print('')
                    break
                elif ch == b'\x08':
                    if len(password) > 0:
                        password = password[:-1]
                        sys.stdout.write('\b \b')
                        sys.stdout.flush()
                else:
                    password += ch.decode('utf-8')
                    sys.stdout.write(mask)
                    sys.stdout.flush()
        else:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                while True:
                    ch = sys.stdin.read(1)
                    if ch == '\n' or ch == '\r':
                        print('')
                        break
                    elif ch == '\x7f':
                        if len(password) > 0:
                            password = password[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    else:
                        password += ch
                        sys.stdout.write(mask)
                        sys.stdout.flush()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return password

    while True:
        print(f"Введите пароль (длина от {minLength} до {maxLength}): ", end='', flush=True)
        pw = input_password_masked()
        
        if len(pw) < minLength or len(pw) > maxLength:
            print("Ошибка: длина пароля не соответствует требованиям.")
            if not loop:
                return None
            continue
        if check_easy and is_easy_password(pw):
            print("Ошибка: пароль слишком простой.")
            if not loop:
                return None
            continue
        if needUpper and not has_upper(pw):
            print("Ошибка: пароль должен содержать хотя бы одну заглавную букву.")
            if not loop:
                return None
            continue
        if needSpecchar and not has_special_char(pw):
            print("Ошибка: пароль должен содержать хотя бы один специальный символ.")
            if not loop:
                return None
            continue
        return pw

def ask_file(ext=".txt", name="any", startWith="any", loop=False):
    while True:
        path = input("Введите путь к файлу: ")
        try:
            if not os.path.isfile(path):
                raise FileNotFoundError("Файл не найден")
            if ext != "any" and not path.endswith(ext):
                raise ValueError(f"Файл должен иметь расширение {ext}")
            base_name = os.path.basename(path)
            if name != "any" and name not in base_name:
                raise ValueError(f"Имя файла должно содержать '{name}'")
            if startWith != "any" and not base_name.startswith(startWith):
                raise ValueError(f"Имя файла должно начинаться с '{startWith}'")
            return path
        except Exception as e:
            print(e)
            if not loop:
                break
    return None

def ask_folder(isEmpty=True, loop=False):
    while True:
        path = input("Введите путь к папке: ")
        try:
            if not os.path.isdir(path):
                raise NotADirectoryError("Папка не найдена")
            if isEmpty and os.listdir(path):
                raise ValueError("Папка не пуста")
            if not isEmpty and not os.listdir(path):
                raise ValueError("Папка пуста")
            return path
        except Exception as e:
            print(e)
            if not loop:
                break
    return None

def ask_birthdate(format="dd.mm.yyyy", minAge=0, maxAge=150, loop=False):
    while True:
        date_str = input(f"Введите дату рождения ({format}): ")
        try:
            if format == "dd.mm.yyyy":
                birth_date = datetime.strptime(date_str, "%d.%m.%Y")
            elif format == "mm/dd/yyyy":
                birth_date = datetime.strptime(date_str, "%m/%d/%Y")
            elif format == "yyyy-mm-dd":
                birth_date = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                raise ValueError("Неподдерживаемый формат даты")
            
            today = datetime.now()
            age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            
            if birth_date > today:
                raise ValueError("Дата рождения не может быть в будущем")
            if age < minAge:
                raise ValueError(f"Возраст должен быть не менее {minAge} лет")
            if age > maxAge:
                raise ValueError(f"Возраст должен быть не более {maxAge} лет")
            
            return birth_date
        except ValueError as e:
            if "does not match format" in str(e):
                print(f"Неверный формат даты. Используйте {format}")
            else:
                print(e)
            if not loop:
                break
    return None

def ask_age(minAge=0, maxAge=150, loop=False):
    while True:
        age_str = input("Введите возраст: ")
        try:
            age = int(age_str)
            if age < minAge:
                raise ValueError(f"Возраст должен быть не менее {minAge}")
            if age > maxAge:
                raise ValueError(f"Возраст должен быть не более {maxAge}")
            return age
        except ValueError as e:
            if "invalid literal" in str(e):
                print("Возраст должен быть числом")
            else:
                print(e)
            if not loop:
                break
    return None

def ask_str(min=0, max=float('inf'), languages=["ru", "en"], restrictNums=True, loop=False):
    while True:
        text = input("Введите строку: ")
        try:
            if len(text) < min:
                raise ValueError(f"Строка должна содержать не менее {min} символов")
            if len(text) > max:
                raise ValueError(f"Строка должна содержать не более {max} символов")
            
            if restrictNums and any(char.isdigit() for char in text):
                raise ValueError("Строка не должна содержать цифры")
            
            if isinstance(languages, str):
                languages = [languages]
            
            valid_chars = set()
            for lang in languages:
                if lang == "ru":
                    valid_chars.update("абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")
                elif lang == "en":
                    valid_chars.update("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
            
            valid_chars.update(" .,!?-:;()[]{}\"'")
            
            if not all(char in valid_chars or char.isdigit() for char in text):
                lang_names = {"ru": "русский", "en": "английский"}
                allowed_langs = ", ".join([lang_names.get(lang, lang) for lang in languages])
                raise ValueError(f"Строка должна содержать только символы языков: {allowed_langs}")
            
            return text
        except ValueError as e:
            print(e)
            if not loop:
                break
    return None

def ask_num(min=float('-inf'), max=float('inf'), even=False, odd=False, only=None, loop=False):
    while True:
        num_str = input("Введите число: ")
        try:
            num = int(num_str)
            
            if num < min:
                raise ValueError(f"Число должно быть не менее {min}")
            if num > max:
                raise ValueError(f"Число должно быть не более {max}")
            
            if only is not None and num not in only:
                raise ValueError(f"Число должно быть одним из: {only}")
            
            if even and num % 2 != 0:
                raise ValueError("Число должно быть четным")
            if odd and num % 2 == 0:
                raise ValueError("Число должно быть нечетным")
            
            return num
        except ValueError as e:
            if "invalid literal" in str(e):
                print("Введите корректное число")
            else:
                print(e)
            if not loop:
                break
    return None

def ask_choice(choice=[], loop=False):
    while True:
        print("Выберите один из вариантов:")
        for i, option in enumerate(choice, 1):
            print(f"{i}. {option}")
        
        user_input = input("Ваш выбор: ")
        try:
            if user_input in choice:
                return user_input
            elif user_input.isdigit() and 1 <= int(user_input) <= len(choice):
                return choice[int(user_input) - 1]
            else:
                raise ValueError(f"Выберите один из предложенных вариантов: {', '.join(choice)}")
        except ValueError as e:
            print(e)
            if not loop:
                break
    return None
