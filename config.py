LDAP_SERVER = 'ldaps://ldap.cs.prv'
LDAP_PORT = 636
LDAP_USE_SSL = True




DEP_LIST = ["ИМО", "ПМиК", "МА", "ГиТ", "ТВиАД", "ТМОМИ"]
TUTOR_POSITIONS = ["преподаватель", "ст. преподаватель", "доцент", "профессор", "заведующий кафедрой", "другая"]
TUTOR_RANKS = ["без звания", "доцент", "профессор"]

REPORT_DATA_MAP = {
    "int-report": ("report", 0, []),
    "int-slides": ("slides", 1, []),
    "fin-preport": ("practic_report", 2, ['4', '6']),
    "fin-report": ("final_report", 3, []),
    "fin-slides": ("final_slides", 4, []),
    "fin-antiplagiat": ("antiplagiat", 5, ['4', '6']),
    "fin-sup-review": ("review", 6, ['4', '6']),
    "fin-review": ("final_review", 7, ['6'])
}

DEADLINES = {
    "interim_reports_date": {
        "1": "30.12",
        "2": "30.12",
        "3": "30.12",
        "4": "30.12",
        "5": "30.12",
        "6": "30.12"
    },
    "final_reports_date": {
        "1": "30.05",
        "2": "30.05",
        "3": "30.05",
        "4": "30.05",
        "5": "30.05",
        "6": "30.05"
    }
}