import os
import ast
import re
import radon.metrics
import radon.complexity

class CodeInspector:
    def __init__(self, file_path):
        self.file_path = file_path
        self.code = self._read_file()
        self.tree = ast.parse(self.code)

    def _read_file(self):
        """Читання вмісту файлу"""
        with open(self.file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def analyze_complexity(self):
        """Аналіз циклomatичної складності"""
        try:
            complexity = radon.complexity.cc_visit(self.code)
            return [
                {
                    'function': block.name, 
                    'complexity': block.complexity, 
                    'lines': f"{block.lineno}-{block.endline}"
                } 
                for block in complexity
            ]
        except Exception as e:
            return [{'error': str(e)}]

    def check_code_style(self):
        """Перевірка стилю коду"""
        issues = []

        # Довжина рядків
        for i, line in enumerate(self.code.split('\n'), 1):
            if len(line) > 79:
                issues.append(f"Лінія {i}: Перевищена рекомендована довжина рядка (>79 символів)")

        # Іменування змінних
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Name):
                name = node.id
                if not re.match(r'^[a-z_][a-z0-9_]*$', name):
                    issues.append(f"Назва змінної '{name}' не відповідає PEP 8")

        return issues

    def detect_potential_bugs(self):
        """Пошук потенційних вразливостей"""
        bugs = []

        # Пошук незакритих файлів
        file_open_nodes = [
            node for node in ast.walk(self.tree) 
            if isinstance(node, ast.Call) and 
               isinstance(node.func, ast.Name) and 
               node.func.id == 'open'
        ]
        
        # Перевірка на наявність контекстних менеджерів
        for node in file_open_nodes:
            if not self._is_context_manager(node):
                bugs.append(f"Файл відкрито без контекстного менеджера (with)")

        return bugs

    def _is_context_manager(self, node):
        """Перевірка використання контекстного менеджера"""
        parent = getattr(node, 'parent', None)
        while parent:
            if isinstance(parent, ast.With):
                return True
            parent = getattr(parent, 'parent', None)
        return False

    def generate_report(self):
        """Генерація звіту інспекції"""
        return {
            "file": self.file_path,
            "complexity_analysis": self.analyze_complexity(),
            "style_issues": self.check_code_style(),
            "potential_bugs": self.detect_potential_bugs()
        }

def inspect_directory(directory):
    """Інспекція всіх Python-файлів у директорії"""
    reports = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                try:
                    inspector = CodeInspector(full_path)
                    reports.append(inspector.generate_report())
                except Exception as e:
                    print(f"Помилка інспекції файлу {full_path}: {e}")
    return reports

def main():
    # Приклад використання
    directory_path = './code'  # Поточна директорія
    inspection_reports = inspect_directory(directory_path)
    
    print("Звіти інспекції коду:")
    for report in inspection_reports:
        print(f"\nФайл: {report['file']}")
        print("Складність коду:")
        
        # Оновлена логіка виведення складності
        complexity_analysis = report['complexity_analysis']
        if complexity_analysis and 'error' in complexity_analysis[0]:
            print(f" - Помилка аналізу: {complexity_analysis[0]['error']}")
        else:
            for complexity in complexity_analysis:
                print(f" - {complexity.get('function', 'Невідома функція')}: {complexity.get('complexity', 'N/A')} (лінії {complexity.get('lines', 'N/A')})")
        
        print("\nПроблеми стилю:")
        for issue in report['style_issues']:
            print(f" - {issue}")
        
        print("\nПотенційні вразливості:")
        for bug in report['potential_bugs']:
            print(f" - {bug}")

if __name__ == "__main__":
    main()