from django.db import connection


def check_db_health() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False
