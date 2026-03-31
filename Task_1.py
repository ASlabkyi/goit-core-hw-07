from collections import UserDict
from datetime import datetime, timedelta
from functools import wraps

class AddressBookError(ValueError):
    pass

class InvalidName(AddressBookError):
    pass

class InvalidPhoneNumber(AddressBookError):
    pass

class InvalidDateFormat(AddressBookError):
    pass

class PhoneNotFound(AddressBookError):
    pass

class BirthdayNotFound(AddressBookError):
    pass

class ContactAlreadyExists(AddressBookError):
    pass

class ContactNotFound(AddressBookError):
    pass

class ThereIsNoContacts(AddressBookError):
    pass

class NoBirthdaysInSevenDays(AddressBookError):
    pass

class InputError(AddressBookError):
    pass

def input_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AddressBookError as e:
            return str(e)
        except AttributeError as e:
            return "Contact not found"
    return wrapper

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    def __init__(self, name):
        if name.strip():
            super().__init__(name)
        else:
            raise InvalidName('Name must not be empty')

class Phone(Field):
    def __init__(self, value):
        value_str = str(value)
        if len(value_str) == 10 and value_str.isdigit():
            super().__init__(value)
        else:
            raise InvalidPhoneNumber('Phone number must be 10 digits')

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, '%d.%m.%Y').date()
            super().__init__(value)
        except ValueError:
            raise InvalidDateFormat('Invalid date format. Use DD.MM.YYYY')

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_birthday(self, date_str):
        self.birthday = Birthday(date_str)

    def show_birthday(self):
        if self.birthday is None:
            return None
        return self.birthday.value

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def find_phone(self, number):
        return next((p for p in self.phones if p.value == number), None)

    def remove_phone(self, number):
        phone = self.find_phone(number)
        if not phone:
            raise PhoneNotFound('Phone not found')
        self.phones.remove(phone)

    def edit_phone(self, old_number, new_number):
        old_phone = self.find_phone(old_number)
        new_phone = Phone(new_number)
        if not old_phone:
            raise PhoneNotFound('Phone not found')
        i = self.phones.index(old_phone)
        self.phones[i] = new_phone

    def __str__(self):
        birthday = self.birthday.value if self.birthday else "Birthday not found"
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        key = record.name.value
        if key in self.data:
            raise ContactAlreadyExists(f'Contact {key} already exists')
        self.data[key] = record

    def find(self, name):
            return self.data.get(name, None)

    def delete(self, name):
        if name in self.data:
            del self.data[name]
        else:
            raise ContactNotFound(f'Contact {name} not found')

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue
            date_str = record.birthday.value
            birthday_this_year = datetime.strptime(date_str, '%d.%m.%Y').date().replace(year=today.year)

            if birthday_this_year < today:
                birthday_this_year = birthday_this_year.replace(year=today.year + 1)

            if birthday_this_year.weekday() == 5:
                birthday_this_year += timedelta(days=2)
            elif birthday_this_year.weekday() == 6:
                birthday_this_year += timedelta(days=1)

            if 0 <= (birthday_this_year - today).days < 7:
                upcoming_birthdays.append({'name': record.name.value, 'birthday': birthday_this_year.strftime('%d.%m.%Y')})

        return upcoming_birthdays

    def __str__(self):
        return '\n'.join((str(record) for record in self.data.values()))

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    if len(args) != 2:
        raise InputError('Input error! Use format: cmd name number.')
    name, phone, *_ = args
    record = book.find(name)
    message = 'Contact updated'
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = 'Contact added'
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_phone(args, book: AddressBook):
    if len(args) != 3:
        raise InputError('Input error! Use format: cmd name old_number new_number.')
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    record.edit_phone(old_phone, new_phone)
    return 'Phone updated'

@input_error
def show_phone(args, book: AddressBook):
    if len(args) != 1:
        raise InputError('Input error! Use format: cmd name.')
    name, *_ = args
    record = book.find(name)
    return '; '.join(p.value for p in record.phones)

@input_error
def show_all_contacts(book: AddressBook):
    result = []
    if not book.data:
        raise ThereIsNoContacts(f'Contacts not found')
    for record in book.data.values():
        result.append(str(record))
    return  '\n'.join(result)

@input_error
def add_birthday(args, book: AddressBook):
    if len(args) != 2:
        raise InputError('Input error! Use format: cmd name birthday.')
    name, birthday, *_ = args
    record = book.find(name)
    record.add_birthday(birthday)
    return 'Birthday added'

@input_error
def show_birthday(args, book: AddressBook):
    if len(args) != 1:
        raise InputError('Input error! Use format: cmd name.')
    name, *_ = args
    record = book.find(name)
    if not record.birthday:
        raise BirthdayNotFound(f"{name}'s birthday not added")
    return record.birthday.value

@input_error
def birthdays(book: AddressBook):
    birthdays = book.get_upcoming_birthdays()
    lines = []
    if not birthdays:
        raise NoBirthdaysInSevenDays('No birthdays in the next 7 days')
    for items in birthdays:
        lines.append(f'{items["name"]}: {items["birthday"]}')
    return '\n'.join(lines)


def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        if not user_input.strip():
            print("Please enter a command!")
            continue
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_phone(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all_contacts(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()