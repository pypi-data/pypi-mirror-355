import os
import ast
from typing import List, Union, Dict, Any
import glob
from collections import defaultdict
from datetime import datetime
import json

class TestAnalyzer:
    def __init__(self):
        self.output = {}
        self.stats = {
            'total_files': 0,
            'total_classes': 0,
            'total_tests': 0,
            'total_decorated': 0,
            'class_stats': defaultdict(int),
            'marker_stats': defaultdict(int),
            'marker_usage': defaultdict(int),
            'file_info': {}
        }
        self.include_decorators = None
        self.exclude_decorators = None

    def set_decorator_filters(self, include: List[str] = None, exclude: List[str] = None):
        """Set decorator filters for analysis."""
        # Convert decorator names to lowercase and strip any arguments
        self.include_decorators = [d.split('(')[0].strip().lower() for d in include] if include else None
        self.exclude_decorators = [d.split('(')[0].strip().lower() for d in exclude] if exclude else None

    def should_include_decorator(self, decorator: str) -> bool:
        """Check if a decorator should be included based on the current filters."""
        # Extract base decorator name (without arguments)
        base_decorator = decorator.split('(')[0].strip().lower()
        
        # If exclude list is set, check if decorator should be excluded
        if self.exclude_decorators:
            for exclude_pattern in self.exclude_decorators:
                if exclude_pattern.lower() in base_decorator:
                    return False
        
        # If include list is set, check if decorator should be included
        if self.include_decorators:
            for include_pattern in self.include_decorators:
                if include_pattern.lower() in base_decorator:
                    return True
            return False
        
        return True

    def get_decorator_name(self, decorator: ast.AST) -> str:
        """Get the full name of a decorator, including any arguments."""
        if isinstance(decorator, ast.Call):
            # Handle decorators with arguments
            if isinstance(decorator.func, ast.Attribute):
                # Handle cases like @pytest.mark.parametrize
                parts = []
                current = decorator.func
                while isinstance(current, ast.Attribute):
                    parts.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    parts.append(current.id)
                decorator_name = '.'.join(reversed(parts))
            else:
                # Handle cases like @decorator
                decorator_name = self.get_decorator_name(decorator.func)
            
            # Add arguments
            args = []
            # Add positional arguments
            for arg in decorator.args:
                if isinstance(arg, ast.Constant):
                    args.append(repr(arg.value))
                elif isinstance(arg, ast.Name):
                    args.append(arg.id)
            # Add keyword arguments
            for kw in decorator.keywords:
                if isinstance(kw.value, ast.Constant):
                    args.append(f"{kw.arg}={repr(kw.value.value)}")
                elif isinstance(kw.value, ast.Name):
                    args.append(f"{kw.arg}={kw.value.id}")
            
            return f"{decorator_name}({', '.join(args)})"
        elif isinstance(decorator, ast.Name):
            # Handle simple decorators like @skip
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            # Handle attribute decorators like @pytest.mark.skip
            parts = []
            current = decorator
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return str(decorator)

    def get_decorators(self, node) -> List[str]:
        """Extract decorator names from a node."""
        decorators = []
        if hasattr(node, 'decorator_list'):
            for decorator in node.decorator_list:
                decorator_name = self.get_decorator_name(decorator)
                decorators.append(decorator_name)
                # Update marker statistics
                self.stats['marker_stats'][decorator_name] += 1
        return decorators

    def analyze_file(self, file_path: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Analyze a single Python file for test classes and methods."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with latin-1 encoding if utf-8 fails
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        tree = ast.parse(content)
        result = {}
        unknown_class_methods = {}
        
        # First pass: collect all class nodes
        class_nodes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_nodes.append(node)
        
        # Second pass: process all nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                # Check if the function is at module level (not inside a class)
                is_in_class = False
                for class_node in class_nodes:
                    if node in class_node.body:
                        is_in_class = True
                        break
                
                if not is_in_class:
                    method_name = node.name
                    decorators = []
                    
                    # Get decorators
                    for decorator in node.decorator_list:
                        decorator_str = self.get_decorator_name(decorator)
                        if decorator_str:
                            decorators.append(decorator_str)
                    
                    # Get docstring
                    docstring = ast.get_docstring(node)
                    
                    unknown_class_methods[method_name] = {
                        'decorators': decorators,
                        'description': docstring
                    }
                    
                    # Update marker statistics
                    for decorator in decorators:
                        self.stats['marker_usage'][decorator] = self.stats['marker_usage'].get(decorator, 0) + 1
            
            elif isinstance(node, ast.ClassDef):
                # Check if it's a test class
                if node.name.startswith('Test'):
                    class_name = node.name
                    methods = {}
                    
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            # Check if it's a test method
                            if item.name.startswith('test_'):
                                method_name = item.name
                                decorators = []
                                
                                # Get decorators
                                for decorator in item.decorator_list:
                                    decorator_str = self.get_decorator_name(decorator)
                                    if decorator_str:
                                        decorators.append(decorator_str)
                                
                                # Get docstring
                                docstring = ast.get_docstring(item)
                                
                                methods[method_name] = {
                                    'decorators': decorators,
                                    'description': docstring
                                }
                                
                                # Update marker statistics
                                for decorator in decorators:
                                    self.stats['marker_usage'][decorator] = self.stats['marker_usage'].get(decorator, 0) + 1
                    
                    if methods:
                        result[class_name] = methods
                        self.stats['total_classes'] += 1
                        self.stats['total_tests'] += len(methods)
                        self.stats['class_stats'][class_name] = len(methods)
                        
                        # Count decorated tests
                        decorated_count = sum(1 for method_info in methods.values() if method_info['decorators'])
                        self.stats['total_decorated'] += decorated_count
        
        # Add unknown class methods if any exist
        if unknown_class_methods:
            result['UnknownClass'] = unknown_class_methods
            self.stats['total_classes'] += 1
            self.stats['total_tests'] += len(unknown_class_methods)
            self.stats['class_stats']['UnknownClass'] = len(unknown_class_methods)
            
            # Count decorated tests
            decorated_count = sum(1 for method_info in unknown_class_methods.values() if method_info['decorators'])
            self.stats['total_decorated'] += decorated_count
        
        return result

    def analyze_path(self, path: Union[str, List[str]]) -> None:
        """Analyze Python files in the given path(s)."""
        # Handle both string and list inputs
        if isinstance(path, list) and len(path) == 1 and ' ' in path[0]:
            paths = path[0].split()
        elif isinstance(path, str):
            paths = [path]
        else:
            paths = path
        
        for path in paths:
            # Skip non-test files early
            if os.path.isfile(path):
                if not (path.endswith('_test.py') or os.path.basename(path).startswith('test_')):
                    continue
                self.stats['total_files'] += 1
                result = self.analyze_file(path)
                if result:
                    self.output[path] = result
            else:
                # Find all Python files in the directory
                for file_path in glob.glob(os.path.join(path, '**', '*.py'), recursive=True):
                    # Skip non-test files
                    if not (file_path.endswith('_test.py') or os.path.basename(file_path).startswith('test_')):
                        continue
                    self.stats['total_files'] += 1
                    result = self.analyze_file(file_path)
                    if result:
                        self.output[file_path] = result

    def write_to_txt(self, output_file: str):
        """Write the analysis results to a text file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write statistics first
            f.write("="*80 + "\n")
            f.write("TEST ANALYSIS STATISTICS\n")
            f.write("="*80 + "\n\n")
            
            # Overall statistics table
            f.write("Overall Statistics:\n")
            f.write("┌" + "─"*30 + "┬" + "─"*15 + "┐\n")
            f.write("│" + "Metric".ljust(30) + "│" + "Count".ljust(15) + "│\n")
            f.write("├" + "─"*30 + "┼" + "─"*15 + "┤\n")
            f.write("│" + "Total Files Analyzed".ljust(30) + "│" + str(self.stats['total_files']).ljust(15) + "│\n")
            f.write("│" + "Total Test Classes".ljust(30) + "│" + str(self.stats['total_classes']).ljust(15) + "│\n")
            f.write("│" + "Total Test Cases".ljust(30) + "│" + str(self.stats['total_tests']).ljust(15) + "│\n")
            f.write("│" + "Decorated Tests".ljust(30) + "│" + str(self.stats['total_decorated']).ljust(15) + "│\n")
            f.write("│" + "Undecorated Tests".ljust(30) + "│" + str(self.stats['total_tests'] - self.stats['total_decorated']).ljust(15) + "│\n")
            f.write("└" + "─"*30 + "┴" + "─"*15 + "┘\n\n")
            
            # Class-wise statistics table
            f.write("Class-wise Statistics:\n")
            f.write("┌" + "─"*50 + "┬" + "─"*15 + "┐\n")
            f.write("│" + "Class Name".ljust(50) + "│" + "Test Cases".ljust(15) + "│\n")
            f.write("├" + "─"*50 + "┼" + "─"*15 + "┤\n")
            
            # Sort classes by number of test cases (descending)
            sorted_classes = sorted(self.stats['class_stats'].items(), 
                                 key=lambda x: x[1], 
                                 reverse=True)
            
            for class_name, test_count in sorted_classes:
                f.write("│" + class_name.ljust(50) + "│" + str(test_count).ljust(15) + "│\n")
            
            f.write("└" + "─"*50 + "┴" + "─"*15 + "┘\n\n")

            # Marker statistics table
            f.write("Marker Statistics:\n")
            f.write("┌" + "─"*50 + "┬" + "─"*15 + "┐\n")
            f.write("│" + "Marker Name".ljust(50) + "│" + "Usage Count".ljust(15) + "│\n")
            f.write("├" + "─"*50 + "┼" + "─"*15 + "┤\n")
            
            # Group markers by their base name (without arguments)
            marker_groups = {}
            for marker, count in self.stats['marker_usage'].items():
                # Extract base marker name (e.g., 'pytest.mark.skip' from 'pytest.mark.skip(reason=...)')
                base_marker = marker.split('(')[0].strip()
                marker_groups[base_marker] = marker_groups.get(base_marker, 0) + count
            
            # Sort markers by usage count (descending)
            sorted_markers = sorted(marker_groups.items(),
                                 key=lambda x: x[1],
                                 reverse=True)
            
            for marker_name, count in sorted_markers:
                f.write("│" + marker_name.ljust(50) + "│" + str(count).ljust(15) + "│\n")
            
            f.write("└" + "─"*50 + "┴" + "─"*15 + "┘\n")
            
            # Grand total
            f.write("\n" + "─"*80 + "\n")
            f.write(f"Grand Total: {self.stats['total_tests']} test cases\n")
            
            # Add a separator between statistics and test files
            f.write("\n" + "="*80 + "\n\n")
            
            # Write detailed analysis of test files
            for file_path, classes in self.output.items():
                f.write(f"File: {file_path}\n")
                f.write("=" * (len(file_path) + 7) + "\n\n")
                
                for class_name, methods in classes.items():
                    # Filter methods based on decorators
                    filtered_methods = {}
                    for method_name, method_info in methods.items():
                        decorators = method_info.get('decorators', [])
                        # If no filters are set, include all methods
                        if not (self.include_decorators or self.exclude_decorators):
                            filtered_methods[method_name] = method_info
                        else:
                            # Check if method should be included based on decorators
                            should_include = True
                            
                            # If exclude list is set, check if any decorator matches
                            if self.exclude_decorators:
                                if any(not self.should_include_decorator(d) for d in decorators):
                                    should_include = False
                            
                            # If include list is set, check if all required decorators are present
                            if should_include and self.include_decorators:
                                # Check if all required decorators are present
                                required_decorators = set(d.lower() for d in self.include_decorators)
                                method_decorators = set(d.split('(')[0].strip().lower() for d in decorators)
                                if not required_decorators.issubset(method_decorators):
                                    should_include = False
                            
                            if should_include:
                                filtered_methods[method_name] = method_info
                    
                    if filtered_methods:
                        f.write(f"{class_name}:\n")
                        
                        # Sort methods by name for consistent ordering
                        sorted_methods = sorted(filtered_methods.items(), key=lambda x: x[0])
                        
                        for i, (method_name, method_info) in enumerate(sorted_methods, 1):
                            decorators = method_info.get('decorators', [])
                            description = method_info.get('description')
                            
                            # Write test case name
                            f.write(f"    {i}. {method_name}\n")
                            
                            # Write decorators if present
                            if decorators:
                                f.write(f"        decorators: [{', '.join(decorators)}]\n")
                            
                            # Write description if present
                            if description:
                                f.write(f"        desc: {description}\n")
                            
                            # Add a blank line between test cases
                            f.write("\n")

    def write_to_html(self, output_file):
        """Write analysis results to an HTML file with dynamic color assignment."""
        # Read the template file
        template_path = os.path.join(os.path.dirname(__file__), 'templates', 'report_template.html')
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            print(f"Error: Template file not found at {template_path}")
            return
        except Exception as e:
            print(f"Error reading template file: {e}")
            return

        # Prepare data for charts
        class_data = {}
        for class_name, test_count in sorted(self.stats['class_stats'].items(), 
                                          key=lambda x: x[1], 
                                          reverse=True):
            class_data[class_name] = test_count

        marker_data = {}
        for marker, count in sorted(self.stats['marker_usage'].items(),
                                 key=lambda x: x[1],
                                 reverse=True):
            base_marker = marker.split('(')[0].strip()
            marker_data[base_marker] = marker_data.get(base_marker, 0) + count

        # Write the report
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                formatted_template = template.format(
                    timestamp=timestamp,
                    total_files=len(self.output),
                    total_classes=len(self.stats['class_stats']),
                    total_tests=self.stats['total_tests'],
                    total_decorated=self.stats['total_decorated'],
                    class_stats=self._generate_class_stats_rows(),
                    marker_stats=self._generate_marker_stats_rows(),
                    test_cases=self._generate_test_cases_html(),
                    class_data=json.dumps(class_data),
                    marker_data=json.dumps(marker_data)
                )
                f.write(formatted_template)
        except KeyError as e:
            print(f"\nError: Missing template variable: {e}")
            print("Template variables found in the template:")
            import re
            template_vars = re.findall(r'\{([^}]+)\}', template)
            print(f"Found variables: {set(template_vars)}")
            raise
        except Exception as e:
            print(f"\nError writing HTML file: {e}")
            raise

    def write_to_markdown(self, output_file: str):
        """Write the analysis results to a Markdown file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write statistics first
            f.write("# Test Analysis Report\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            
            # Overall statistics
            f.write("## Overall Statistics\n\n")
            f.write("| Metric | Count |\n")
            f.write("|--------|-------|\n")
            f.write(f"| Total Files Analyzed | {self.stats['total_files']} |\n")
            f.write(f"| Total Test Classes | {self.stats['total_classes']} |\n")
            f.write(f"| Total Test Cases | {self.stats['total_tests']} |\n")
            f.write(f"| Decorated Tests | {self.stats['total_decorated']} |\n")
            f.write(f"| Undecorated Tests | {self.stats['total_tests'] - self.stats['total_decorated']} |\n\n")
            
            # Class-wise statistics
            f.write("## Class-wise Statistics\n\n")
            f.write("| Class Name | Test Cases |\n")
            f.write("|------------|------------|\n")
            
            for class_name, test_count in sorted(self.stats['class_stats'].items(), 
                                              key=lambda x: x[1], 
                                              reverse=True):
                f.write(f"| {class_name} | {test_count} |\n")
            
            f.write("\n")
            
            # Marker statistics
            f.write("## Marker Statistics\n\n")
            f.write("| Marker Name | Usage Count |\n")
            f.write("|-------------|-------------|\n")
            
            marker_groups = {}
            for marker, count in self.stats['marker_usage'].items():
                base_marker = marker.split('(')[0].strip()
                marker_groups[base_marker] = marker_groups.get(base_marker, 0) + count
            
            for marker_name, count in sorted(marker_groups.items(),
                                          key=lambda x: x[1],
                                          reverse=True):
                f.write(f"| {marker_name} | {count} |\n")
            
            f.write("\n")
            
            # Test cases
            f.write("## Test Cases\n\n")
            
            for file_path, classes in self.output.items():
                f.write(f"### {file_path}\n\n")
                
                for class_name, methods in classes.items():
                    # Filter methods based on decorators
                    filtered_methods = {}
                    for method_name, method_info in methods.items():
                        decorators = method_info.get('decorators', [])
                        # If no filters are set, include all methods
                        if not (self.include_decorators or self.exclude_decorators):
                            filtered_methods[method_name] = method_info
                        else:
                            # Check if method should be included based on decorators
                            should_include = True
                            
                            # If exclude list is set, check if any decorator matches
                            if self.exclude_decorators:
                                if any(not self.should_include_decorator(d) for d in decorators):
                                    should_include = False
                            
                            # If include list is set, check if all required decorators are present
                            if should_include and self.include_decorators:
                                # Check if all required decorators are present
                                required_decorators = set(d.lower() for d in self.include_decorators)
                                method_decorators = set(d.split('(')[0].strip().lower() for d in decorators)
                                if not required_decorators.issubset(method_decorators):
                                    should_include = False
                            
                            if should_include:
                                filtered_methods[method_name] = method_info
                    
                    if filtered_methods:
                        f.write(f"#### {class_name}\n\n")
                        
                        # Sort methods by name for consistent ordering
                        sorted_methods = sorted(filtered_methods.items(), key=lambda x: x[0])
                        
                        for i, (method_name, method_info) in enumerate(sorted_methods, 1):
                            decorators = method_info.get('decorators', [])
                            description = method_info.get('description')
                            
                            f.write(f"{i}. **{method_name}**\n")
                            
                            if decorators:
                                f.write(f"   - Decorators: `{', '.join(decorators)}`\n")
                            
                            if description:
                                f.write(f"   - Description: {description}\n")
                            
                            f.write("\n")

    def write_to_file(self, output_file: str, format: str = 'html'):
        """Write the analysis results to a file in the specified format."""
        if format.lower() == 'txt':
            self.write_to_txt(output_file)
        elif format.lower() == 'md':
            self.write_to_markdown(output_file)
        else:  # default to html
            self.write_to_html(output_file)

    def _generate_class_stats_rows(self):
        """Generate HTML rows for class statistics."""
        rows = []
        for class_name, test_count in sorted(self.stats['class_stats'].items(), 
                                          key=lambda x: x[1], 
                                          reverse=True):
            rows.append(f"""
                <tr>
                    <td>{class_name}</td>
                    <td>{test_count}</td>
                </tr>""")
        return '\n'.join(rows)

    def _generate_marker_stats_rows(self):
        """Generate HTML rows for marker statistics."""
        rows = []
        marker_groups = {}
        for marker, count in self.stats['marker_usage'].items():
            base_marker = marker.split('(')[0].strip()
            marker_groups[base_marker] = marker_groups.get(base_marker, 0) + count
        
        for marker_name, count in sorted(marker_groups.items(),
                                      key=lambda x: x[1],
                                      reverse=True):
            rows.append(f"""
                <tr>
                    <td>{marker_name}</td>
                    <td>{count}</td>
                </tr>""")
        return '\n'.join(rows)

    def _generate_test_cases_html(self):
        """Generate HTML for test cases section."""
        html = []
        for file_path, classes in self.output.items():
            html.append(f"""
            <div class="file-section">
                <div class="file-header">
                    <h3>{file_path}</h3>
                </div>""")
            
            for class_name, methods in classes.items():
                # Filter methods based on decorators
                filtered_methods = {}
                for method_name, method_info in methods.items():
                    decorators = method_info.get('decorators', [])
                    # If no filters are set, include all methods
                    if not (self.include_decorators or self.exclude_decorators):
                        filtered_methods[method_name] = method_info
                    else:
                        # Check if method should be included based on decorators
                        should_include = True
                        
                        # If exclude list is set, check if any decorator matches
                        if self.exclude_decorators:
                            if any(not self.should_include_decorator(d) for d in decorators):
                                should_include = False
                        
                        # If include list is set, check if all required decorators are present
                        if should_include and self.include_decorators:
                            # Check if all required decorators are present
                            required_decorators = set(d.lower() for d in self.include_decorators)
                            method_decorators = set(d.split('(')[0].strip().lower() for d in decorators)
                            if not required_decorators.issubset(method_decorators):
                                should_include = False
                        
                        if should_include:
                            filtered_methods[method_name] = method_info
                
                if filtered_methods:
                    html.append(f"""
                <div class="class-section">
                    <h3>{class_name}</h3>""")
                    
                    # Sort methods by name for consistent ordering
                    sorted_methods = sorted(filtered_methods.items(), key=lambda x: x[0])
                    
                    for i, (method_name, method_info) in enumerate(sorted_methods, 1):
                        decorators = method_info.get('decorators', [])
                        description = method_info.get('description')
                        
                        html.append(f"""
                    <div class="test-case">
                        <h3>{i}. {method_name}</h3>""")
                        
                        if decorators:
                            html.append("""
                        <div class="decorators">""")
                            for decorator in decorators:
                                html.append(f"""
                            <span class="decorator">{decorator}</span>""")
                            html.append("""
                        </div>""")
                        
                        if description:
                            html.append(f"""
                        <div class="description">{description}</div>""")
                        
                        html.append("""
                    </div>""")
                    
                    html.append("""
                </div>""")
            
            html.append("""
            </div>""")
        
        return '\n'.join(html) 