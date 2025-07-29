import cmd
import sys
import os

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
        print(f"- OS: {sys.platform}")
        print(f"- Python Version: {sys.version}")
        print(f"- User: {os.getlogin()}")

    def do_cwd(self, arg):
        """Show current working directory"""
        print(f"\nCurrent Working Directory: {os.getcwd()}")

def main():
    EverythingCLI().cmdloop()

if __name__ == '__main__':
    main()
