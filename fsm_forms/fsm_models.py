from aiogram.filters.state import StatesGroup, State


class MainDialog(StatesGroup):
    welcome = State()
    who_are_you = State()
    intresting = State()
    planing = State()
    repair_compleat = State()
    electrik = State()
    main_menu = State()


class Solutions(StatesGroup):
    menu = State()

class Lighting(StatesGroup):
    stage_1 = State()
    stage_2 = State()
    stage_3 = State()
    stage_4 = State()
    stage_5 = State()
    stage_6 = State()

class Curtains(StatesGroup):
    stage_1 = State()

class Climate(StatesGroup):
    stage_1 = State()
    stage_2 = State()
    stage_3 = State()
    stage_4 = State()
    stage_5 = State()
    stage_6 = State()

class Leak(StatesGroup):
    stage_1 = State()

class Gates(StatesGroup):
    stage_1 = State()

class Safety(StatesGroup):
    stage_1 = State()
    stage_2 = State()
    stage_3 = State()
    stage_4 = State()

class Saving(StatesGroup):
    stage_1 = State()
    stage_2 = State()
    stage_3 = State()

class Scenarios(StatesGroup):
    stage_1 = State()
    stage_2 = State()
    stage_3 = State()
    stage_4 = State()
    stage_5 = State()
    stage_6 = State()

class Control(StatesGroup):
    stage_1 = State()
    stage_2 = State()
    stage_3 = State()
    stage_4 = State()

class Education(StatesGroup):
    education_menu = State()
    lesson_0 = State()
    lesson_01 = State()
    lesson_1 = State()
    lesson_11 = State()
    lesson_2 = State()
    lesson_21 = State()
    lesson_3 = State()
    lesson_31 = State()
    lesson_4 = State()
    lesson_41 = State()
    lesson_5 = State()
    lesson_51 = State()
    lesson_6 = State()
    lesson_61 = State()
    lesson_7 = State()
    lesson_71 = State()
    lesson_8 = State()
    lesson_81 = State()
    lesson_9 = State()
    lesson_91 = State()

class Examples(StatesGroup):
    pass

class Contact(StatesGroup):
    pass

class Contacting(StatesGroup):
    get_phone = State()

class Admin(StatesGroup):
    menu = State()
    delete_user_input = State()
    add_admin_input = State()
    result = State()
