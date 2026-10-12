"""
WorkPulse - Employee Service
Provides high-level business operations for managing employees, performance records, and queries.
"""

from database.db_manager import (
    get_all_employees, add_employee, update_employee,
    delete_employee, get_employee_history, import_records_from_df
)
from utils.validation import validate_employee_input


def fetch_employees_dataset(db_path="data/workpulse.db"):
    """Fetches all employees from SQLite."""
    return get_all_employees(db_path)


def create_new_employee(employee_code, employee_name, department, experience_years,
                        attendance_rate, task_completion_rate, training_hours,
                        previous_performance, performance_category, review_date,
                        db_path="data/workpulse.db"):
    """Validates inputs and saves new employee record."""
    is_valid, errors = validate_employee_input(
        employee_code=employee_code,
        employee_name=employee_name,
        department=department,
        experience_years=experience_years,
        attendance_rate=attendance_rate,
        task_completion_rate=task_completion_rate,
        training_hours=training_hours,
        previous_performance=previous_performance,
        performance_category=performance_category
    )
    if not is_valid:
        return False, "; ".join(errors)

    try:
        emp_id = add_employee(
            employee_code=employee_code.strip(),
            employee_name=employee_name.strip(),
            department=department.strip(),
            experience_years=float(experience_years),
            attendance_rate=float(attendance_rate),
            task_completion_rate=float(task_completion_rate),
            training_hours=float(training_hours),
            previous_performance=float(previous_performance),
            performance_category=performance_category.strip(),
            review_date=str(review_date),
            db_path=db_path
        )
        return True, f"Employee '{employee_code}' successfully registered (ID: {emp_id})."
    except Exception as e:
        return False, str(e)


def modify_employee(employee_id, employee_name, department, experience_years,
                    attendance_rate, task_completion_rate, training_hours,
                    previous_performance, performance_category, review_date,
                    db_path="data/workpulse.db"):
    """Validates and updates an existing employee."""
    is_valid, errors = validate_employee_input(
        employee_code="EXISTING",
        employee_name=employee_name,
        department=department,
        experience_years=experience_years,
        attendance_rate=attendance_rate,
        task_completion_rate=task_completion_rate,
        training_hours=training_hours,
        previous_performance=previous_performance,
        performance_category=performance_category
    )
    if not is_valid:
        return False, "; ".join(errors)

    try:
        update_employee(
            employee_id=employee_id,
            employee_name=employee_name.strip(),
            department=department.strip(),
            experience_years=float(experience_years),
            attendance_rate=float(attendance_rate),
            task_completion_rate=float(task_completion_rate),
            training_hours=float(training_hours),
            previous_performance=float(previous_performance),
            performance_category=performance_category.strip(),
            review_date=str(review_date),
            db_path=db_path
        )
        return True, "Employee record updated successfully."
    except Exception as e:
        return False, str(e)


def remove_employee(employee_id, db_path="data/workpulse.db"):
    """Deletes an employee record from the database."""
    try:
        delete_employee(employee_id, db_path)
        return True, "Employee deleted successfully."
    except Exception as e:
        return False, str(e)


def fetch_employee_history(employee_id, db_path="data/workpulse.db"):
    """Retrieves chronological review history for an employee."""
    return get_employee_history(employee_id, db_path)
