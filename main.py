import json
import os
from enum import Enum
from typing import List, Optional, Dict, Any
from collections import deque
from abc import ABC, abstractmethod

# ==================== Модели (Model) ====================

class Priority(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

class Status(Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"

class Task:
    """Базовый класс задачи"""
    def __init__(self, title: str, description: str, priority: Priority, status: Status = Status.TODO):
        self._title = title
        self._description = description
        self._priority = priority
        self._status = status
    
    # Геттеры и сеттеры
    @property
    def title(self) -> str:
        return self._title
    
    @title.setter
    def title(self, value: str):
        if not value or not value.strip():
            raise ValueError("Название задачи не может быть пустым")
        self._title = value.strip()
    
    @property
    def description(self) -> str:
        return self._description
    
    @description.setter
    def description(self, value: str):
        self._description = value.strip() if value else ""
    
    @property
    def priority(self) -> Priority:
        return self._priority
    
    @priority.setter
    def priority(self, value: Priority):
        self._priority = value
    
    @property
    def status(self) -> Status:
        return self._status
    
    @status.setter
    def status(self, value: Status):
        self._status = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация задачи в словарь"""
        return {
            "title": self._title,
            "description": self._description,
            "priority": self._priority.value,
            "status": self._status.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Десериализация задачи из словаря"""
        priority = Priority(data["priority"])
        status = Status(data["status"])
        return cls(data["title"], data["description"], priority, status)
    
    def __str__(self) -> str:
        return f"[{self._status.value}] {self._title} (Приоритет: {self._priority.value}) - {self._description}"

class UrgentTask(Task):
    """Подкласс срочных задач (наследование)"""
    def __init__(self, title: str, description: str, deadline: str):
        super().__init__(title, description, Priority.HIGH)
        self._deadline = deadline
    
    @property
    def deadline(self) -> str:
        return self._deadline
    
    def __str__(self) -> str:
        return super().__str__() + f" [Дедлайн: {self._deadline}]"
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["type"] = "urgent"
        data["deadline"] = self._deadline
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UrgentTask':
        return cls(data["title"], data["description"], data["deadline"])

class TaskManager:
    """Модель для хранения и обработки данных"""
    def __init__(self):
        self._tasks: List[Task] = []
        self._priority_queue: deque = deque()  # Очередь задач по приоритету
        self._undo_stack: List[List[Task]] = []  # Стек для отмены действий
        
    def add_task(self, task: Task):
        """Добавление задачи"""
        self._save_state()
        self._tasks.append(task)
        self._update_priority_queue()
    
    def update_task(self, index: int, title: str = None, description: str = None, 
                   priority: Priority = None, status: Status = None):
        """Редактирование задачи"""
        if 0 <= index < len(self._tasks):
            self._save_state()
            task = self._tasks[index]
            if title:
                task.title = title
            if description is not None:
                task.description = description
            if priority:
                task.priority = priority
            if status:
                task.status = status
            self._update_priority_queue()
    
    def delete_task(self, index: int):
        """Удаление задачи"""
        if 0 <= index < len(self._tasks):
            self._save_state()
            del self._tasks[index]
            self._update_priority_queue()
    
    def get_tasks(self, status: Optional[Status] = None, priority: Optional[Priority] = None) -> List[Task]:
        """Получение задач с фильтрацией"""
        filtered = self._tasks
        if status:
            filtered = [t for t in filtered if t.status == status]
        if priority:
            filtered = [t for t in filtered if t.priority == priority]
        return filtered
    
    def undo(self) -> bool:
        """Отмена последнего действия"""
        if self._undo_stack:
            self._tasks = self._undo_stack.pop()
            self._update_priority_queue()
            return True
        return False
    
    def _save_state(self):
        """Сохранение состояния в стек для отмены"""
        self._undo_stack.append([self._copy_task(t) for t in self._tasks])
    
    def _copy_task(self, task: Task) -> Task:
        """Копирование задачи"""
        return Task(task.title, task.description, task.priority, task.status)
    
    def _update_priority_queue(self):
        """Обновление очереди приоритетов"""
        self._priority_queue.clear()
        # Сортируем по приоритету: HIGH, MEDIUM, LOW
        sorted_tasks = sorted(self._tasks, key=lambda t: (
            0 if t.priority == Priority.HIGH else 1 if t.priority == Priority.MEDIUM else 2
        ))
        for task in sorted_tasks:
            self._priority_queue.append(task)
    
    def get_priority_queue(self) -> deque:
        """Получение очереди приоритетов"""
        return self._priority_queue
    
    def save_to_file(self, filename: str = "tasks.json"):
        """Сохранение в JSON файл"""
        data = {
            "tasks": [task.to_dict() for task in self._tasks]
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    
    def load_from_file(self, filename: str = "tasks.json"):
        """Загрузка из JSON файла"""
        if not os.path.exists(filename):
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self._tasks = []
        for task_data in data.get("tasks", []):
            if task_data.get("type") == "urgent":
                self._tasks.append(UrgentTask.from_dict(task_data))
            else:
                self._tasks.append(Task.from_dict(task_data))
        self._update_priority_queue()

# ==================== View (Представление) ====================

class ConsoleView:
    """Класс для отображения информации и ввода данных"""
    
    @staticmethod
    def show_menu():
        """Отображение главного меню"""
        print("\n" + "="*50)
        print("TASK MANAGER")
        print("="*50)
        print("1. Показать все задачи")
        print("2. Добавить задачу")
        print("3. Редактировать задачу")
        print("4. Удалить задачу")
        print("5. Фильтровать задачи")
        print("6. Показать очередь приоритетов")
        print("7. Отменить последнее действие")
        print("8. Сохранить в файл")
        print("9. Загрузить из файла")
        print("0. Выход")
        print("="*50)
    
    @staticmethod
    def show_tasks(tasks: List[Task], title: str = "Список задач"):
        """Отображение списка задач"""
        print(f"\n{title}:")
        if not tasks:
            print("  Нет задач")
            return
        
        for i, task in enumerate(tasks):
            print(f"{i+1}. {task}")
    
    @staticmethod
    def get_task_input() -> tuple:
        """Ввод данных новой задачи"""
        print("\n--- Добавление новой задачи ---")
        
        while True:
            title = input("Название: ").strip()
            if title:
                break
            print("Ошибка: Название не может быть пустым!")
        
        description = input("Описание: ").strip()
        
        while True:
            print("Приоритет: 1 - Low, 2 - Medium, 3 - High")
            priority_choice = input("Выберите (1-3): ").strip()
            if priority_choice == "1":
                priority = Priority.LOW
                break
            elif priority_choice == "2":
                priority = Priority.MEDIUM
                break
            elif priority_choice == "3":
                priority = Priority.HIGH
                break
            else:
                print("Ошибка: Неверный выбор!")
        
        # Спросить, срочная ли задача
        is_urgent = input("Срочная задача? (y/n): ").strip().lower() == 'y'
        if is_urgent:
            deadline = input("Дедлайн: ").strip()
            return UrgentTask(title, description, deadline)
        
        return Task(title, description, priority)
    
    @staticmethod
    def get_task_selection(max_index: int) -> Optional[int]:
        """Выбор задачи по номеру"""
        while True:
            try:
                choice = input(f"Выберите номер задачи (1-{max_index}): ").strip()
                if not choice:
                    return None
                index = int(choice) - 1
                if 0 <= index < max_index:
                    return index
                print(f"Ошибка: Введите число от 1 до {max_index}")
            except ValueError:
                print("Ошибка: Введите корректное число!")
    
    @staticmethod
    def get_edit_input(task: Task) -> dict:
        """Ввод данных для редактирования задачи"""
        updates = {}
        
        print("\n--- Редактирование задачи ---")
        print(f"Текущее название: {task.title}")
        new_title = input("Новое название (Enter - оставить без изменений): ").strip()
        if new_title:
            updates['title'] = new_title
        
        print(f"Текущее описание: {task.description}")
        new_desc = input("Новое описание (Enter - оставить без изменений): ").strip()
        if new_desc:
            updates['description'] = new_desc
        
        print(f"Текущий приоритет: {task.priority.value}")
        print("Выберите новый приоритет: 1-Low, 2-Medium, 3-High (Enter - без изменений)")
        priority_choice = input("Ваш выбор: ").strip()
        if priority_choice in ['1', '2', '3']:
            priority_map = {'1': Priority.LOW, '2': Priority.MEDIUM, '3': Priority.HIGH}
            updates['priority'] = priority_map[priority_choice]
        
        print(f"Текущий статус: {task.status.value}")
        print("Выберите новый статус: 1-To Do, 2-In Progress, 3-Done (Enter - без изменений)")
        status_choice = input("Ваш выбор: ").strip()
        if status_choice in ['1', '2', '3']:
            status_map = {'1': Status.TODO, '2': Status.IN_PROGRESS, '3': Status.DONE}
            updates['status'] = status_map[status_choice]
        
        return updates
    
    @staticmethod
    def show_filter_menu() -> tuple:
        """Меню фильтрации"""
        print("\n--- Фильтрация задач ---")
        print("Фильтр по статусу:")
        print("1. To Do")
        print("2. In Progress")
        print("3. Done")
        print("0. Без фильтра")
        
        status = None
        status_choice = input("Выберите (0-3): ").strip()
        if status_choice == '1':
            status = Status.TODO
        elif status_choice == '2':
            status = Status.IN_PROGRESS
        elif status_choice == '3':
            status = Status.DONE
        
        print("\nФильтр по приоритету:")
        print("1. Low")
        print("2. Medium")
        print("3. High")
        print("0. Без фильтра")
        
        priority = None
        priority_choice = input("Выберите (0-3): ").strip()
        if priority_choice == '1':
            priority = Priority.LOW
        elif priority_choice == '2':
            priority = Priority.MEDIUM
        elif priority_choice == '3':
            priority = Priority.HIGH
        
        return status, priority
    
    @staticmethod
    def show_message(message: str, is_error: bool = False):
        """Отображение сообщения"""
        prefix = "ОШИБКА: " if is_error else "✓ "
        print(f"{prefix}{message}")
    
    @staticmethod
    def show_priority_queue(queue: deque):
        """Отображение очереди приоритетов"""
        print("\n--- Очередь задач по приоритету (от высокого к низкому) ---")
        if not queue:
            print("  Очередь пуста")
        else:
            for i, task in enumerate(queue, 1):
                print(f"{i}. {task}")

# ==================== Controller ====================

class MenuController:
    """Контроллер для обработки команд пользователя"""
    
    def __init__(self, model: TaskManager, view: ConsoleView):
        self._model = model
        self._view = view
    
    def run(self):
        """Запуск основного цикла программы"""
        while True:
            self._view.show_menu()
            choice = input("Выберите действие: ").strip()
            
            if choice == '1':
                self._show_all_tasks()
            elif choice == '2':
                self._add_task()
            elif choice == '3':
                self._edit_task()
            elif choice == '4':
                self._delete_task()
            elif choice == '5':
                self._filter_tasks()
            elif choice == '6':
                self._show_priority_queue()
            elif choice == '7':
                self._undo_action()
            elif choice == '8':
                self._save_to_file()
            elif choice == '9':
                self._load_from_file()
            elif choice == '0':
                self._view.show_message("До свидания!")
                break
            else:
                self._view.show_message("Неверный выбор! Попробуйте снова.", is_error=True)
    
    def _show_all_tasks(self):
        """Показать все задачи"""
        tasks = self._model.get_tasks()
        self._view.show_tasks(tasks, "Все задачи")
    
    def _add_task(self):
        """Добавить задачу"""
        task = self._view.get_task_input()
        self._model.add_task(task)
        self._view.show_message(f"Задача '{task.title}' успешно добавлена!")
    
    def _edit_task(self):
        """Редактировать задачу"""
        tasks = self._model.get_tasks()
        if not tasks:
            self._view.show_message("Нет задач для редактирования!", is_error=True)
            return
        
        self._view.show_tasks(tasks, "Выберите задачу для редактирования")
        index = self._view.get_task_selection(len(tasks))
        
        if index is not None:
            updates = self._view.get_edit_input(tasks[index])
            try:
                self._model.update_task(
                    index,
                    title=updates.get('title'),
                    description=updates.get('description'),
                    priority=updates.get('priority'),
                    status=updates.get('status')
                )
                self._view.show_message("Задача успешно обновлена!")
            except ValueError as e:
                self._view.show_message(str(e), is_error=True)
    
    def _delete_task(self):
        """Удалить задачу"""
        tasks = self._model.get_tasks()
        if not tasks:
            self._view.show_message("Нет задач для удаления!", is_error=True)
            return
        
        self._view.show_tasks(tasks, "Выберите задачу для удаления")
        index = self._view.get_task_selection(len(tasks))
        
        if index is not None:
            task_title = tasks[index].title
            confirm = input(f"Вы уверены, что хотите удалить задачу '{task_title}'? (y/n): ").strip().lower()
            if confirm == 'y':
                self._model.delete_task(index)
                self._view.show_message(f"Задача '{task_title}' удалена!")
            else:
                self._view.show_message("Удаление отменено")
    
    def _filter_tasks(self):
        """Фильтрация задач"""
        status, priority = self._view.show_filter_menu()
        filtered = self._model.get_tasks(status, priority)
        
        title_parts = []
        if status:
            title_parts.append(f"Статус: {status.value}")
        if priority:
            title_parts.append(f"Приоритет: {priority.value}")
        
        title = "Отфильтрованные задачи" + (f" ({', '.join(title_parts)})" if title_parts else "")
        self._view.show_tasks(filtered, title)
    
    def _show_priority_queue(self):
        """Показать очередь приоритетов"""
        queue = self._model.get_priority_queue()
        self._view.show_priority_queue(queue)
    
    def _undo_action(self):
        """Отмена последнего действия"""
        if self._model.undo():
            self._view.show_message("Последнее действие отменено!")
        else:
            self._view.show_message("Нечего отменять!", is_error=True)
    
    def _save_to_file(self):
        """Сохранить в файл"""
        try:
            self._model.save_to_file()
            self._view.show_message("Задачи сохранены в файл 'tasks.json'")
        except Exception as e:
            self._view.show_message(f"Ошибка при сохранении: {e}", is_error=True)
    
    def _load_from_file(self):
        """Загрузить из файла"""
        try:
            self._model.load_from_file()
            self._view.show_message("Задачи загружены из файла 'tasks.json'")
        except Exception as e:
            self._view.show_message(f"Ошибка при загрузке: {e}", is_error=True)

# ==================== Главная функция ====================

def main():
    """Точка входа в программу"""
    model = TaskManager()
    view = ConsoleView()
    controller = MenuController(model, view)
    
    # Попытка загрузить сохраненные задачи при запуске
    try:
        model.load_from_file()
    except:
        pass
    
    controller.run()

if __name__ == "__main__":
    main()
