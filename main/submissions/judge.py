import subprocess
import tempfile
import os
import time
import shutil
from django.conf import settings

class Judge:
    def __init__(self):
        self.time_limit = 2.0  # seconds
        self.memory_limit = 256  # MB (not enforced in this simple version)
    
    def judge_submission(self, submission):
        """Judge a submission against all test cases"""
        problem = submission.problem
        test_cases = problem.testcases.all()
        
        if not test_cases.exists():
            return {
                'verdict': 'No Test Cases',
                'score': 0,
                'total_score': 0,
                'details': []
            }
        
        results = []
        total_score = sum(tc.points for tc in test_cases)
        earned_score = 0
        
        for test_case in test_cases:
            result = self.run_test_case(submission, test_case)
            
            # Fix: Check if result is None
            if result is None:
                result = {
                    'status': 'Judge Error',
                    'output': 'Internal judge error',
                    'expected': test_case.expected_output,
                    'runtime': 0
                }
            
            results.append(result)
            
            if result['status'] == 'Accepted':
                earned_score += test_case.points
                
            # If any test case fails completely, stop judging
            if result['status'] in ['Time Limit Exceeded', 'Runtime Error', 'Compilation Error']:
                break
        
        # Determine final verdict
        if earned_score == total_score:
            verdict = 'Accepted'
        elif earned_score > 0:
            verdict = 'Partial Accepted'
        else:
            # Check what type of error occurred
            if any(r['status'] == 'Time Limit Exceeded' for r in results):
                verdict = 'Time Limit Exceeded'
            elif any(r['status'] == 'Runtime Error' for r in results):
                verdict = 'Runtime Error'
            elif any(r['status'] == 'Compilation Error' for r in results):
                verdict = 'Compilation Error'
            else:
                verdict = 'Wrong Answer'
        
        return {
            'verdict': verdict,
            'score': earned_score,
            'total_score': total_score,
            'details': results
        }
    
    def run_test_case(self, submission, test_case):
        """Run code against a single test case"""
        try:
            language = submission.language.lower()
            if language == 'python':
                return self.run_python(submission.code, test_case)
            elif language in ['cpp', 'c++']:
                return self.run_cpp(submission.code, test_case)
            elif language == 'java':
                return self.run_java(submission.code, test_case)
            elif language in ['javascript', 'js', 'node']:
                return self.run_javascript(submission.code, test_case)
            else:
                return {
                    'status': 'Unsupported Language',
                    'output': f'Language {submission.language} is not supported',
                    'expected': test_case.expected_output,
                    'runtime': 0
                }
        except Exception as e:
            return {
                'status': 'Judge Error',
                'output': str(e),
                'expected': test_case.expected_output,
                'runtime': 0
            }
    
    def run_python(self, code, test_case):
        code_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            start_time = time.time()
            process = subprocess.run(
                ['python', code_file],
                input=test_case.input_data,
                capture_output=True,
                text=True,
                timeout=self.time_limit
            )
            runtime = time.time() - start_time
            
            # Clean up file
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            
            if process.returncode != 0:
                return {
                    'status': 'Runtime Error',
                    'output': process.stderr,
                    'expected': test_case.expected_output,
                    'runtime': runtime
                }
            
            output = process.stdout.strip()
            expected = test_case.expected_output.strip()
            
            if output == expected:
                status = 'Accepted'
            else:
                status = 'Wrong Answer'
            
            return {
                'status': status,
                'output': output,
                'expected': expected,
                'runtime': runtime
            }
            
        except subprocess.TimeoutExpired:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            return {
                'status': 'Time Limit Exceeded',
                'output': '',
                'expected': test_case.expected_output,
                'runtime': self.time_limit
            }
        except Exception as e:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            return {
                'status': 'Runtime Error',
                'output': str(e),
                'expected': test_case.expected_output,
                'runtime': 0
            }
    
    def run_cpp(self, code, test_case):
        code_file = None
        exe_file = None
        try:
            # Create temporary C++ file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            exe_file = code_file.replace('.cpp', '.exe')
            
            # Compile C++ code
            compile_process = subprocess.run(
                ['g++', '-o', exe_file, code_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_process.returncode != 0:
                return {
                    'status': 'Compilation Error',
                    'output': compile_process.stderr,
                    'expected': test_case.expected_output,
                    'runtime': 0
                }
            
            # Run compiled executable
            start_time = time.time()
            process = subprocess.run(
                [exe_file],
                input=test_case.input_data,
                capture_output=True,
                text=True,
                timeout=self.time_limit
            )
            runtime = time.time() - start_time
            
            # Clean up files
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            if exe_file and os.path.exists(exe_file):
                os.unlink(exe_file)
            
            if process.returncode != 0:
                return {
                    'status': 'Runtime Error',
                    'output': process.stderr,
                    'expected': test_case.expected_output,
                    'runtime': runtime
                }
            
            output = process.stdout.strip()
            expected = test_case.expected_output.strip()
            
            if output == expected:
                status = 'Accepted'
            else:
                status = 'Wrong Answer'
            
            return {
                'status': status,
                'output': output,
                'expected': expected,
                'runtime': runtime
            }
            
        except subprocess.TimeoutExpired:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            if exe_file and os.path.exists(exe_file):
                os.unlink(exe_file)
            return {
                'status': 'Time Limit Exceeded',
                'output': '',
                'expected': test_case.expected_output,
                'runtime': self.time_limit
            }
        except Exception as e:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            if exe_file and os.path.exists(exe_file):
                os.unlink(exe_file)
            return {
                'status': 'Runtime Error',
                'output': str(e),
                'expected': test_case.expected_output,
                'runtime': 0
            }
    
    def run_java(self, code, test_case):
        temp_dir = None
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp()
            
            # Extract class name from code
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', code)
            if not class_match:
                return {
                    'status': 'Compilation Error',
                    'output': 'No public class found in Java code',
                    'expected': test_case.expected_output,
                    'runtime': 0
                }
            
            class_name = class_match.group(1)
            java_file = os.path.join(temp_dir, f'{class_name}.java')
            
            # Write Java code to file
            with open(java_file, 'w') as f:
                f.write(code)
            
            # Compile Java code
            compile_process = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_process.returncode != 0:
                return {
                    'status': 'Compilation Error',
                    'output': compile_process.stderr,
                    'expected': test_case.expected_output,
                    'runtime': 0
                }
            
            # Run Java program
            start_time = time.time()
            process = subprocess.run(
                ['java', '-cp', temp_dir, class_name],
                input=test_case.input_data,
                capture_output=True,
                text=True,
                timeout=self.time_limit
            )
            runtime = time.time() - start_time
            
            # Clean up
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            
            if process.returncode != 0:
                return {
                    'status': 'Runtime Error',
                    'output': process.stderr,
                    'expected': test_case.expected_output,
                    'runtime': runtime
                }
            
            output = process.stdout.strip()
            expected = test_case.expected_output.strip()
            
            if output == expected:
                status = 'Accepted'
            else:
                status = 'Wrong Answer'
            
            return {
                'status': status,
                'output': output,
                'expected': expected,
                'runtime': runtime
            }
            
        except subprocess.TimeoutExpired:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {
                'status': 'Time Limit Exceeded',
                'output': '',
                'expected': test_case.expected_output,
                'runtime': self.time_limit
            }
        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {
                'status': 'Runtime Error',
                'output': str(e),
                'expected': test_case.expected_output,
                'runtime': 0
            }
    
    def run_javascript(self, code, test_case):
        code_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                code_file = f.name
            
            start_time = time.time()
            process = subprocess.run(
                ['node', code_file],
                input=test_case.input_data,
                capture_output=True,
                text=True,
                timeout=self.time_limit
            )
            runtime = time.time() - start_time
            
            # Clean up file
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            
            if process.returncode != 0:
                return {
                    'status': 'Runtime Error',
                    'output': process.stderr,
                    'expected': test_case.expected_output,
                    'runtime': runtime
                }
            
            output = process.stdout.strip()
            expected = test_case.expected_output.strip()
            
            if output == expected:
                status = 'Accepted'
            else:
                status = 'Wrong Answer'
            
            return {
                'status': status,
                'output': output,
                'expected': expected,
                'runtime': runtime
            }
            
        except subprocess.TimeoutExpired:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            return {
                'status': 'Time Limit Exceeded',
                'output': '',
                'expected': test_case.expected_output,
                'runtime': self.time_limit
            }
        except Exception as e:
            if code_file and os.path.exists(code_file):
                os.unlink(code_file)
            return {
                'status': 'Runtime Error',
                'output': str(e),
                'expected': test_case.expected_output,
                'runtime': 0
            }