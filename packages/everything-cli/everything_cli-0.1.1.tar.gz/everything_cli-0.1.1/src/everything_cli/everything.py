import cmd
import sys
import os
import platform
import subprocess
import datetime
import shutil
import webbrowser
import json

class EverythingCLI(cmd.Cmd):
    intro = 'Welcome to the Everything CLI. Type help or ? to list commands.\n'
    prompt = 'everything> '

    def do_exit(self, arg):
        """Exit the CLI"""
        print("Goodbye!")
        return True

    def do_list(self, arg):
        """List available commands"""
        print("\nAvailable commands:")
        print("- list: Show available commands")
        print("- help: Get help about commands")
        print("- exit: Exit the CLI")
        print("- sysinfo: Show system information")
        print("- cwd: Show current working directory")
        print("- date: Show current date and time")
        print("- web: Open web browser")
        print("- clean: Clean build files")
        print("- version: Show Python version")
        print("- disk: Show disk usage")
        print("- python: Run Python code")
        print("- run: Run a command")

    def do_help(self, arg):
        """Get help about commands"""
        if arg:
            try:
                func = getattr(self, 'do_' + arg)
                print(func.__doc__ or "No help available for this command")
            except AttributeError:
                print(f"No help available for '{arg}'")
        else:
            print("\nAvailable commands:")
            for name in dir(self):
                if name.startswith('do_'):
                    cmd = name[3:]
                    doc = getattr(self, name).__doc__
                    print(f"- {cmd}: {doc or 'No description'}")

    def do_sysinfo(self, arg):
        """Show system information"""
        print(f"\nSystem Information:")
        print(f"- OS: {platform.system()} {platform.release()}")
        print(f"- Architecture: {platform.machine()}")
        print(f"- Python Version: {sys.version}")
        print(f"- Processor: {platform.processor()}")
        print(f"- User: {os.getlogin()}")

    def do_cwd(self, arg):
        """Show current working directory"""
        print(f"\nCurrent Working Directory: {os.getcwd()}")

    def do_date(self, arg):
        """Show current date and time"""
        now = datetime.datetime.now()
        print(f"\nCurrent Date and Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    def do_web(self, arg):
        """Open web browser to specified URL or default search page"""
        if arg:
            webbrowser.open(arg)
        else:
            webbrowser.open("https://www.google.com")

    def do_clean(self, arg):
        """Clean build files and cache"""
        print("\nCleaning build files...")
        dirs_to_clean = ['build', 'dist', '__pycache__']
        for dir_name in dirs_to_clean:
            try:
                shutil.rmtree(dir_name)
                print(f"Removed {dir_name}")
            except FileNotFoundError:
                pass

    def do_version(self, arg):
        """Show Python version"""
        print(f"\nPython Version: {sys.version}")

    def do_disk(self, arg):
        """Show disk usage"""
        print("\nDisk Usage:")
        total, used, free = shutil.disk_usage(os.getcwd())
        print(f"Total: {total // (2**30)} GB")
        print(f"Used: {used // (2**30)} GB")
        print(f"Free: {free // (2**30)} GB")

    def do_python(self, arg):
        """Run Python code"""
        if not arg:
            print("\nPlease provide Python code to execute")
            return
        try:
            result = eval(arg)
            print(f"\nResult: {result}")
        except Exception as e:
            print(f"\nError: {str(e)}")

    def do_run(self, arg):
        """Run a system command"""
        if not arg:
            print("\nPlease provide a command to run")
            return
        try:
            result = subprocess.run(arg, shell=True, capture_output=True, text=True)
            print("\nCommand Output:")
            print(result.stdout)
            if result.stderr:
                print("\nError Output:")
                print(result.stderr)
        except Exception as e:
            print(f"\nError: {str(e)}")

def main():
    EverythingCLI().cmdloop()

if __name__ == '__main__':
    main()
