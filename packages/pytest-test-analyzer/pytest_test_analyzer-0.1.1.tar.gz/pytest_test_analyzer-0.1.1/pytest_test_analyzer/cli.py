from .analyzer import TestAnalyzer
import argparse
import os
import sys

def validate_paths(paths):
    """Validate that all paths exist and are accessible."""
    invalid_paths = []
    for path in paths:
        if not os.path.exists(path):
            invalid_paths.append(path)
    return invalid_paths

def main():
    parser = argparse.ArgumentParser(
        description='Analyze Python test files and generate reports.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Analyze a single directory
  pytest-test-analyzer --path ./tests --output report.html --format html

  # Analyze multiple directories
  pytest-test-analyzer --path ./tests ./integration_tests --output report.html

  # Include only tests with specific decorators
  pytest-test-analyzer --path ./tests --include pytest.mark.sanity pytest.mark.regression

  # Exclude tests with specific decorators
  pytest-test-analyzer --path ./tests --exclude pytest.mark.skip pytest.mark.xfail
'''
    )
    
    parser.add_argument(
        '--path',
        nargs='+',
        required=True,
        help='Path(s) to Python test files or directories containing test files. Can specify multiple paths.'
    )
    
    parser.add_argument(
        '--output',
        default=None,
        help='Output file path for the analysis report (default: test_analytics.{format})'
    )
    
    parser.add_argument(
        '--include',
        nargs='+',
        help='Include only tests that have ALL of these decorators. Example: pytest.mark.sanity pytest.mark.regression'
    )
    
    parser.add_argument(
        '--exclude',
        nargs='+',
        help='Exclude tests that have ANY of these decorators. Example: pytest.mark.skip pytest.mark.xfail'
    )
    
    parser.add_argument(
        '--format',
        choices=['txt', 'html', 'md'],
        default='html',
        help='Output format for the analysis report (default: html)'
    )
    
    args = parser.parse_args()
    
    # Set default output file if not provided
    if args.output is None:
        args.output = f'test_analytics.{args.format}'
    
    # Validate paths before proceeding
    invalid_paths = validate_paths(args.path)
    if invalid_paths:
        print("\n❌ Error: The following path(s) do not exist:")
        for path in invalid_paths:
            print(f"   - {path}")
        print("\nPlease check the path(s) and try again.")
        sys.exit(1)
    
    analyzer = TestAnalyzer()
    analyzer.set_decorator_filters(args.include, args.exclude)
    analyzer.analyze_path(args.path)
    
    # Check if any files were analyzed
    if analyzer.stats['total_files'] == 0:
        print("\n⚠️  Warning: No test files were found in the specified paths.")
        print("Please check that:")
        print("   - The paths contain Python test files")
        print("   - Test files follow the naming convention (test_*.py or *_test.py)")
        print("   - You have read permissions for the files")
        sys.exit(1)
    
    analyzer.write_to_file(args.output, args.format)
    
    # Get absolute path for better visibility
    abs_output_path = os.path.abspath(args.output)
    print("\n✅ Analysis report generated successfully!")
    print(f"📄 Report location: {abs_output_path}")
    print(f"📊 Format: {args.format.upper()}")
    print(f"📈 Total files analyzed: {analyzer.stats['total_files']}")
    print(f"🧪 Total test cases: {analyzer.stats['total_tests']}")

if __name__ == '__main__':
    main()
